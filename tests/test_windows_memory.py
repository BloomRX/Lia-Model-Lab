"""Simulated Win32 ABI calls and resource policy; no DLLs/weights required."""
import copy
import ctypes as C
import pytest
from lia_lab import windows_memory as w
from lia_lab.memory_resources import assess, settings, compare
from lia_lab.io import LabError

G = 1024**3


class FakeAPI:
    def __init__(self, failures=(), in_job=False, flags=0, process_limit=0, job_limit=0):
        self.failures, self.in_job, self.flags = failures, in_job, flags
        self.process_limit, self.job_limit = process_limit, job_limit
        self.queries = 0

    def last_error(self): return 5
    def GetCurrentProcess(self): return -1

    def GlobalMemoryStatusEx(self, ptr):
        assert ptr._obj.dwLength == C.sizeof(w.MEMORYSTATUSEX)
        ptr._obj.ullTotalPhys, ptr._obj.ullAvailPhys, ptr._obj.ullAvailPageFile = 16*G, 8*G, 10*G
        return 'GlobalMemoryStatusEx' not in self.failures

    def GetPerformanceInfo(self, ptr, size):
        assert ptr._obj.cb == size == C.sizeof(w.PERFORMANCE_INFORMATION)
        ptr._obj.PageSize, ptr._obj.CommitLimit, ptr._obj.CommitTotal = 4096, 8*G//4096, 2*G//4096
        return 'GetPerformanceInfo' not in self.failures

    def GetProcessMemoryInfo(self, handle, ptr, size):
        assert handle == -1 and ptr._obj.cb == size == C.sizeof(w.PROCESS_MEMORY_COUNTERS_EX)
        ptr._obj.PrivateUsage, ptr._obj.WorkingSetSize = G, G//8
        return 'GetProcessMemoryInfo' not in self.failures

    def IsProcessInJob(self, process, job, ptr):
        assert process == -1 and job is None
        ptr._obj.value = self.in_job
        return 'IsProcessInJob' not in self.failures

    def QueryInformationJobObject(self, handle, cls, ptr, size, returned):
        assert handle is None and cls == 9 and size == C.sizeof(w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION)
        self.queries += 1
        ptr._obj.BasicLimitInformation.LimitFlags = self.flags
        ptr._obj.ProcessMemoryLimit, ptr._obj.JobMemoryLimit = self.process_limit, self.job_limit
        ptr._obj.PeakJobMemoryUsed = 999*G  # must never appear as current usage
        return 'QueryInformationJobObject' not in self.failures


def observation(**kwargs):
    return w.collect(FakeAPI(**kwargs))


def test_pages_working_set_and_commit_are_separate():
    o = observation()
    assert o['physical_total_bytes'] == 16*G and o['physical_available_bytes'] == 8*G
    assert o['system_commit_limit_bytes'] == 8*G and o['system_commit_used_bytes'] == 2*G
    assert o['caller_commit_available_bytes'] == 10*G
    assert o['process_private_commit_bytes'] == G and o['process_working_set_bytes'] == G//8
    a = assess(o, required_bytes=G)
    assert a['estimated_available_bytes'] == 6*G
    assert a['dimensions']['caller_commit_available_bytes'] == 10*G  # no double subtraction
    assert a['allowed'] and not a['reservation']


@pytest.mark.parametrize('policy', ['best-effort', 'balanced', 'strict'])
def test_no_job_is_observed_not_assumed(policy):
    api = FakeAPI()
    o = w.collect(api)
    assert o['job']['in_any_job'] is False and api.queries == 0
    assert assess(o, settings(policy), G)['allowed']


@pytest.mark.parametrize('key', ['physical_available_bytes', 'caller_commit_available_bytes'])
def test_scarce_primary_dimension_blocks_all(key):
    o = observation(); o[key] = G//2
    for policy in ('best-effort', 'balanced', 'strict'):
        assert not assess(o, settings(policy), G)['allowed']


def test_process_cap_uses_private_not_working_set():
    o = observation(in_job=True, flags=0x100, process_limit=2*G)
    a = assess(o, required_bytes=G//2)
    assert a['dimensions']['process_commit_headroom_bytes'] == G
    assert a['estimated_available_bytes'] == G and a['allowed']
    assert not assess(o, required_bytes=G)['allowed']


def test_aggregate_cap_is_not_headroom_or_peak():
    o = observation(in_job=True, flags=0x200, job_limit=2*G)
    assert o['job']['current_usage_bytes'] is None
    a = assess(o, required_bytes=G)
    assert a['allowed'] and a['effective_margin_percent'] == 20
    assert 'aggregate job usage unknown' in a['warnings']
    assert not any('job_headroom' in k for k in a['dimensions'])
    assert not assess(o, required_bytes=3*G)['allowed']
    for p in ('balanced', 'strict'):
        assert not assess(o, settings(p), G)['allowed']


@pytest.mark.parametrize('name', ['GlobalMemoryStatusEx', 'GetPerformanceInfo', 'GetProcessMemoryInfo', 'IsProcessInJob', 'QueryInformationJobObject'])
def test_failed_calls_stay_unknown_and_preserve_error(name):
    o = observation(failures={name}, in_job=True)
    assert o['errors'] == [{'api': name, 'winerror': 5}]
    a = assess(o, required_bytes=G)
    if name == 'GlobalMemoryStatusEx':
        assert not a['allowed'] and o['physical_total_bytes'] is None
    else:
        assert a['allowed'] and a['warnings']
        assert not assess(o, settings('balanced'), G)['allowed']
    if name == 'QueryInformationJobObject':
        assert o['job']['limits_observed'] is False
        assert o['job']['job_memory_limit_bytes'] is None


def test_ancestor_uncertainty_distinguishes_policies():
    o = observation(in_job=True)
    assert o['job']['job_chain_coverage'] == 'immediate-only-chain-not-enumerated'
    assert assess(o, settings('best-effort'), G)['allowed']
    assert assess(o, settings('balanced'), G)['allowed']
    assert not assess(o, settings('strict'), G)['allowed']


@pytest.mark.parametrize('key,value', [('physical_total_bytes',0), ('physical_available_bytes',17*G),
    ('system_commit_used_bytes',9*G), ('process_private_commit_bytes',-1), ('caller_commit_available_bytes',True)])
def test_inconsistent_information_blocks(key, value):
    o = observation(); o[key] = value
    assert not assess(o, required_bytes=G)['allowed']


def test_invalid_page_size_unknown():
    api = FakeAPI(); original = api.GetPerformanceInfo
    def invalid(ptr, size):
        original(ptr, size); ptr._obj.PageSize = 0; return True
    api.GetPerformanceInfo = invalid
    o = w.collect(api)
    assert o['system_commit_limit_bytes'] is None and o['errors']
    assert assess(o, required_bytes=G)['allowed']
    assert not assess(o, settings('balanced'), G)['allowed']


@pytest.mark.parametrize('args', [('unknown',), ('best-effort', -1), ('best-effort', True),
    ('strict', 81, 10), ('balanced', float('nan')), ('best-effort', 0, -1)])
def test_invalid_config(args):
    with pytest.raises(LabError): settings(*args)


def test_configurable_margins_and_worker_delta():
    o = observation()
    assert assess(o, settings('best-effort', 0, 0), 6*G)['allowed']
    assert not assess(o, settings('best-effort', 10, 0), 6*G)['allowed']
    worker = copy.deepcopy(o); worker['physical_available_bytes'] -= G
    worker['job']['in_any_job'] = True
    changes = compare(o, worker)
    assert changes['physical_available_bytes']['delta'] == -G
    assert changes['job']['worker']['in_any_job'] is True


def test_linux_capacity_and_margin_semantics_unchanged():
    o = dict(platform='linux', effective_total_bytes=100, effective_available_bytes=80)
    for p in ('best-effort', 'balanced', 'strict'):
        assert assess(o, settings(p), 80)['allowed']
        assert not assess(o, settings(p), 81)['allowed']


def test_plan_binds_policy_and_both_margins(snapshot, tmp_path):
    from lia_lab.inference import make_operation, operation_from_plan
    from lia_lab.authorization import consume_grant
    from support_authorization import fixture_grant
    op = make_operation(*snapshot, 'configs/inference-suite.json', tmp_path/'r', tmp_path/'a', 'fixture')
    assert operation_from_plan(op) == op
    store, grant = fixture_grant(tmp_path/'operator/grants.db', op)
    for key, val in [('memory_policy', 'strict'), ('memory_margin_percent', 20), ('memory_uncertainty_margin_percent', 15)]:
        other = make_operation(**dict(op['arguments'], **{key:val}))
        with pytest.raises(LabError, match='match'): consume_grant(store, grant, other)
    assert consume_grant(store, grant, op)['single_use']


def test_worker_binding_rejects_policy_change_before_claim(snapshot, tmp_path, monkeypatch):
    from lia_lab.inference import make_operation
    from lia_lab import inference_worker as worker
    from lia_lab.io import load
    op = make_operation(*snapshot, 'configs/inference-suite.json', tmp_path/'r', tmp_path/'a', 'fixture')
    r = {key: op['arguments'][key] for key in ('snapshot', 'snapshot_manifest', 'device', 'dtype', 'repeats', 'max_tokens', 'context')}
    r.update(seed=42, snapshot_manifest_sha256=op['snapshot_manifest_sha256'], suite=load('configs/inference-suite.json'), containment=op['containment'],
        memory_policy=settings('strict'), authorization={'operation':op, 'store':'unused', 'id':'unused'})
    monkeypatch.setattr(worker, 'claim_worker', lambda *a: pytest.fail('changed policy reached claim'))
    with pytest.raises(LabError, match='binding'): worker.validate_worker_grant(r)


def test_worker_rechecks_and_writes_blocked_report(snapshot, tmp_path, monkeypatch):
    from lia_lab import inference_worker as worker
    from lia_lab.io import load
    r = dict(snapshot=str(snapshot[0]), dtype='float32', memory_policy=settings(), _request_sha256='synthetic')
    o = observation(); o['physical_available_bytes'] = 1
    monkeypatch.setattr(worker, 'observe', lambda:o)
    with pytest.raises(LabError, match='worker memory preflight'): worker.memory_preflight(r, tmp_path/'results.json', load(snapshot[1]))
    data = load(tmp_path/'memory-worker.json')
    assert not data['assessment']['allowed'] and data['request_sha256'] == 'synthetic'


def test_no_import_side_effects_in_fresh_python():
    import subprocess, sys
    code = "import sys; from lia_lab import windows_memory, memory_resources, inference_worker; assert 'torch' not in sys.modules; assert 'transformers' not in sys.modules"
    subprocess.run([sys.executable, '-c', code], check=True, timeout=10)


@pytest.mark.parametrize('tamper', [False, True])
def test_supervisor_records_worker_measurement_difference(snapshot, tmp_path, monkeypatch, tamper):
    from lia_lab import inference
    from lia_lab.io import load, atomic_json, digest
    from test_inference import run_fixture
    supervisor = observation()
    env = inference.doctor()
    env['memory'] = supervisor
    env['dependencies'].update(torch='synthetic-only', transformers='synthetic-only')
    monkeypatch.setattr(inference, 'doctor', lambda _:env)
    def blocked_worker(command, env, log, timeout):
        request = load(command[-2])
        worker = copy.deepcopy(supervisor); worker['physical_available_bytes'] = 1
        data = dict(request_sha256=digest(command[-2]), observation=worker,
            assessment=assess(worker, request['memory_policy'],  # same sizing contract as supervisor
                inference.checkpoint_capacity(snapshot[0])*4*3//2 + load(snapshot[1])['total_bytes'] + G))
        if tamper:
            data['assessment']['margin_percent'] = 0
        atomic_json(tmp_path/'research/experiments/unit-fixture/memory-worker.json', data)
        return 1
    monkeypatch.setattr(inference, 'supervise', blocked_worker)
    record = run_fixture(snapshot, tmp_path)
    if tamper:
        assert record['memory_report_invalid'] and record['status'] == 'failed'
    else:
        assert record['status'] == 'blocked'
        assert record['memory_differences']['physical_available_bytes']['delta'] == 1-8*G
        assert not record['memory_worker']['assessment']['allowed']
