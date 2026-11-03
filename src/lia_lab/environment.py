"""Weight-free diagnostics. Device nodes are evidence, not driver compatibility."""
import importlib.metadata
import os
import platform
import shutil
from pathlib import Path


def dependencies():
    result = {}
    for name in ('torch', 'transformers', 'peft', 'bitsandbytes', 'safetensors', 'numpy', 'tokenizers', 'huggingface-hub', 'accelerate'):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def _mount_path(text):
    """mountinfo octal escapes, not URL escaping. Reject noncanonical paths."""
    import re
    text = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), text)
    path = Path(text)
    if not path.is_absolute() or any(x in {'.', '..'} for x in text.split('/')) or '\x00' in text:
        raise ValueError('unrecognized cgroup path')
    return path


def _v2_location(proc_root):
    entries = (Path(proc_root) / 'self/cgroup').read_text().splitlines()
    # Hybrid/v1 and ambiguous memberships are not implemented.
    if len(entries) != 1 or not entries[0].startswith('0::'):
        raise ValueError('unknown cgroup membership')
    membership = _mount_path(entries[0][3:])
    candidates = []
    for line in (Path(proc_root) / 'self/mountinfo').read_text().splitlines():
        left, right = line.split(' - ', 1)
        fields, fs = left.split(), right.split()
        if fs[0] != 'cgroup2':
            continue
        mount_root, mount = _mount_path(fields[3]), _mount_path(fields[4])
        if membership.is_relative_to(mount_root):
            candidates.append((mount_root, mount, mount / membership.relative_to(mount_root)))
    # Prefer a full hierarchy view. Hidden ancestors cannot be budgeted safely.
    full = [c for c in candidates if c[0] == Path('/')]
    if len(full) == 1:
        return full[0]
    if len(candidates) == 1:
        return candidates[0]  # correctly mapped, but caller must reject hidden ancestors
    raise ValueError('ambiguous/unmapped cgroup mount')


def memory(proc_root='/proc'):
    """Known Linux v2 full visible hierarchy only; no cgroup/v1/hidden ancestors -> null.

    Snapshot of capacity, not a reservation. Concurrent sibling allocations may
    still reduce headroom after this observation. Non-Linux is deliberately unknown.
    """
    unknown = {'total_bytes': None, 'available_bytes': None}
    try:
        values = {line.split(':')[0]: int(line.split()[1]) * 1024
                  for line in (Path(proc_root) / 'meminfo').read_text().splitlines() if ':' in line}
        available, total = values['MemAvailable'], values['MemTotal']
        if not 0 <= available <= total or total <= 0:
            return unknown
        mount_root, mount, node = _v2_location(proc_root)
        if mount_root != Path('/'):
            return unknown  # ancestors above mount root may impose tighter limits
        # A namespaced/bind-mounted subtree can be presented as mount root '/'.
        # Real v2 hierarchy root has no memory.max; if it exists, ancestors
        # may be hidden even though mountinfo says '/'. Do not guess their caps.
        if (mount / 'memory.max').exists():
            return unknown
        if 'memory' not in (mount / 'cgroup.controllers').read_text().split():
            return unknown
        while True:
            limit_path = node / 'memory.max'
            if node == mount and not limit_path.exists():
                # The real v2 hierarchy root has no memory.max on Linux.
                # Membership + cgroup2 mount + controller were proven above.
                pass
            else:
                limit_text = limit_path.read_text().strip()
                current = int((node / 'memory.current').read_text())
                if current < 0:
                    return unknown
                if limit_text != 'max':
                    limit = int(limit_text)
                    if limit < 0 or current > limit:
                        return unknown
                    total = min(total, limit)
                    available = min(available, limit - current)
            if node == mount:
                break
            node = node.parent
        return {'total_bytes': total, 'available_bytes': available}
    except (OSError, ValueError, KeyError, IndexError):
        return unknown


def rss():
    if platform.system() == 'Windows':
        from .windows_memory import collect
        return collect()['process_working_set_bytes']
    try:
        return next(int(line.split()[1]) * 1024 for line in
                    Path('/proc/self/status').read_text().splitlines() if line.startswith('VmRSS:'))
    except (OSError, StopIteration, ValueError):
        return None


def doctor(storage='.'):
    from .memory_resources import observe, assess
    ram = memory() if platform.system() != 'Windows' else None
    observation = observe(ram)
    observation['assessment'] = assess(observation)
    if ram is None:
        ram = {'total_bytes': observation['physical_total_bytes'],
               'available_bytes': observation['assessment']['estimated_available_bytes']}
    disk = shutil.disk_usage(storage)
    return {'schema_version': 1, 'evidence': 'observed-environment-not-inference',
            'python': platform.python_version(), 'os': platform.system(), 'machine': platform.machine(),
            'cpu_count': os.cpu_count(), 'ram': ram, 'memory': observation,
            'ram_contract': 'Windows multidimensional estimate; Linux full visible cgroup-v2 hierarchy; snapshot, not reservation', 'disk_free_bytes': disk.free,
            'device_nodes': {p: Path(p).exists() for p in ('/dev/nvidia0', '/dev/kfd', '/dev/dri')},
            'dependencies': dependencies(), 'gpu_runtime_verified': False,
            'recommendations': ['No automatic CUDA selection: choose cpu/cuda/rocm/mps explicitly.',
                'With limited RAM prefer a small reviewed GGUF on CPU/Vulkan in llama.cpp; that backend is not yet implemented by this CLI.',
                'For Transformers CPU reference use float32; memory is checked again against the real tensor inventory.',
                'Qwen3.5-4B is not a safe unquantized target on a 4 GB host; use a larger authorized environment.'],
            'note': 'Nodes/packages do not prove CUDA/ROCm/Vulkan support; worker probes torch after authorization.'}
