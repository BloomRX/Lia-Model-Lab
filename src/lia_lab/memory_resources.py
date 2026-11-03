"""Common resource contract: observations and policy are separate from authorization."""
from .io import LabError


def loading_envelope(elements, dtype, snapshot_bytes):
    if elements is None:
        return None
    resident = elements * (4 if dtype == 'float32' else 2)
    return resident * 3 // 2 + snapshot_bytes + 1024**3


def settings(policy='best-effort', margin_percent=None, uncertainty_margin_percent=10):
    if policy not in {'best-effort', 'balanced', 'strict'}:
        raise LabError('invalid memory policy')
    margin_percent = {'best-effort': 10, 'balanced': 20, 'strict': 30}[policy] if margin_percent is None else margin_percent
    if any(type(n) is not int or not 0 <= n <= 90 for n in (margin_percent, uncertainty_margin_percent)) or margin_percent + uncertainty_margin_percent > 90:
        raise LabError('invalid memory margins: integer percentages, total <= 90')
    return dict(policy=policy, margin_percent=margin_percent, uncertainty_margin_percent=uncertainty_margin_percent)


def observe(legacy=None):
    import platform
    if platform.system() == 'Windows':
        from .windows_memory import collect
        return collect()
    from .environment import memory
    ram = memory() if legacy is None else legacy
    return dict(platform='linux' if platform.system() == 'Linux' else 'unsupported',
                effective_total_bytes=ram['total_bytes'], effective_available_bytes=ram['available_bytes'],
                sources={'effective_available_bytes': 'Linux full visible cgroup-v2 hierarchy'}, errors=[])


def assess(observation, config=None, required_bytes=None):
    config = settings(**(config or {}))
    if required_bytes is not None and (type(required_bytes) is not int or required_bytes < 0):
        raise LabError('invalid memory requirement')
    windows = observation['platform'] == 'windows'
    dimensions, upper_bounds, warnings, missing, blockers = {}, {}, [], [], []

    def value(key):
        v = observation.get(key)
        if v is None:
            return None
        if type(v) is not int or v < 0:
            blockers.append('invalid observation: ' + key)
            return None
        return v

    total_key, available_key = ('physical_total_bytes', 'physical_available_bytes') if windows else ('effective_total_bytes', 'effective_available_bytes')
    total, physical = value(total_key), value(available_key)
    if physical is None or total is None:
        missing.append('physical availability/total unknown')
        blockers.append('host RAM unknown')
    elif total <= 0 or physical > total:
        blockers.append('inconsistent physical memory observation')
    else:
        dimensions[available_key] = physical
    if windows:
        caller = value('caller_commit_available_bytes')
        if caller is None:
            missing.append('caller commit availability unknown')
            blockers.append('caller commit availability unknown')
        else:
            dimensions['caller_commit_available_bytes'] = caller  # already remaining; do not subtract PrivateUsage
        limit, used = value('system_commit_limit_bytes'), value('system_commit_used_bytes')
        if limit is None or used is None:
            missing.append('system commit unknown')
        elif used > limit or limit == 0:
            blockers.append('inconsistent system commit observation')
        else:
            dimensions['system_commit_headroom_bytes'] = limit - used
        private = value('process_private_commit_bytes')
        if private is None:
            missing.append('process private commit unknown')
        job = observation['job']
        if job['in_any_job'] is None:
            missing.append('job membership unknown')
        elif job['in_any_job']:
            missing.append('job chain not enumerated; other applicable jobs may be hidden')
            if not job['limits_observed']:
                missing.append('immediate job limits unknown')
            for key in ('process_memory_limit_bytes', 'job_memory_limit_bytes'):
                cap = job.get(key)
                if cap is not None:
                    if type(cap) is not int or cap < 0:
                        blockers.append('invalid job limit: ' + key)
                        continue
                    upper_bounds[key] = cap
                    if key == 'process_memory_limit_bytes' and private is not None:
                        dimensions['process_commit_headroom_bytes'] = max(0, cap - private)
                    elif key == 'job_memory_limit_bytes':
                        # No current aggregate measurement: a cap alone is NOT headroom.
                        missing.append('aggregate job usage unknown')
            if config['policy'] == 'balanced':
                blockers.extend(m for m in missing if m != 'job chain not enumerated; other applicable jobs may be hidden')
        if config['policy'] == 'balanced':
            blockers.extend(m for m in missing if m in ('system commit unknown', 'process private commit unknown', 'job membership unknown'))
        if config['policy'] == 'strict':
            blockers.extend(missing)
        warnings.extend(f"{e['api']}: {e.get('winerror', e.get('issue'))}" for e in observation.get('errors', []))
    # Linux policies do not weaken or change the existing full-hierarchy capacity gate/margin.
    effective_margin = config['margin_percent'] + (config['uncertainty_margin_percent'] if missing else 0) if windows else 0
    estimated = min(dimensions.values()) if dimensions else None
    usable = estimated * (100 - effective_margin) // 100 if estimated is not None else None
    if required_bytes is not None:
        if usable is None or usable < required_bytes:
            blockers.append('host RAM/commit below memory loading envelope with margin')
        if any(required_bytes > cap * (100 - effective_margin) // 100 for cap in upper_bounds.values()):
            blockers.append('known job limit below memory loading envelope with margin')
    warnings.extend(missing)
    return dict(**config, state='blocked' if blockers else ('estimated-partial' if missing else 'constraints-observed'),
        allowed=not blockers, required_bytes=required_bytes, estimated_available_bytes=estimated,
        usable_after_margin_bytes=usable, effective_margin_percent=effective_margin,
        dimensions=dimensions, known_limit_upper_bounds=upper_bounds, warnings=warnings,
        blockers=list(dict.fromkeys(blockers)), reservation=False)


def compare(supervisor, worker):
    """JSON-ready deltas, including process/job changes, without claiming causality."""
    changes = {}
    for key in sorted(supervisor.keys() | worker.keys()):
        if key in {'observed_at_unix', 'sources', 'assessment'}:
            continue
        before, after = supervisor.get(key), worker.get(key)
        if before != after:
            changes[key] = dict(supervisor=before, worker=after,
                delta=after-before if type(before) is int and type(after) is int else None)
    return changes
