"""Actual Win32 calls, disposable jobs/children only. No allocation stress or ML."""
import ctypes as C
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import pytest
from lia_lab import windows_memory as w
from lia_lab.memory_resources import assess, settings

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='native Win32 API tests require Windows')
M = 1024**2


def job_api():
    api = w.NativeAPI()
    definitions = {
        'CreateJobObjectW': ([C.c_void_p, C.c_wchar_p], w.HANDLE),
        'OpenJobObjectW': ([w.DWORD, w.BOOL, C.c_wchar_p], w.HANDLE),
        'SetInformationJobObject': ([w.HANDLE, C.c_int32, C.c_void_p, w.DWORD], w.BOOL),
        'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
        'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
        'CloseHandle': ([w.HANDLE], w.BOOL),
    }
    for name, (args, result) in definitions.items():
        f = getattr(api.kernel, name); f.argtypes, f.restype = args, result
        setattr(api, name, f)
    return api


def checked(api, result):
    if not result:
        raise C.WinError(api.last_error())
    return result


@contextmanager
def disposable_job(api, process_limit=256*M, job_limit=384*M):
    name = 'Local\\LiaLab-test-' + uuid.uuid4().hex
    handle = checked(api, api.CreateJobObjectW(None, name))
    try:
        limits = w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.BasicLimitInformation.LimitFlags = 0x100 | 0x200 | 0x2000  # commit caps + kill on last handle close
        limits.ProcessMemoryLimit, limits.JobMemoryLimit = process_limit, job_limit
        checked(api, api.SetInformationJobObject(handle, 9, C.byref(limits), C.sizeof(limits)))
        yield handle, name
    finally:
        checked(api, api.CloseHandle(handle))


def query(api, handle):
    info = w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    checked(api, api.QueryInformationJobObject(handle, 9, C.byref(info), C.sizeof(info), None))
    return info


def assign(api, job, child):
    # Only our just-created disposable child. Never assign the test runner/user process.
    handle = checked(api, api.OpenProcess(0x100 | 0x1, False, child.pid))
    try:
        checked(api, api.AssignProcessToJobObject(job, handle))
    finally:
        checked(api, api.CloseHandle(handle))


def child_in_jobs(api, jobs, code):
    code = 'import sys; sys.stdin.readline();\n' + code
    with subprocess.Popen([sys.executable, '-c', code], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as child:
        try:
            for job in jobs:
                assign(api, job, child)
            stdout, stderr = child.communicate('collect\n', timeout=15)
            assert child.returncode == 0, stderr
            return json.loads(stdout)
        finally:
            if child.poll() is None:
                child.kill(); child.wait(timeout=5)


def explicit_collection(name):
    # The test owns this named job and closes the borrowed query handle itself.
    return """
import ctypes as C, json
from lia_lab.windows_memory import NativeAPI, HANDLE, DWORD, BOOL, collect
api = NativeAPI()
api.kernel.OpenJobObjectW.argtypes = [DWORD, BOOL, C.c_wchar_p]
api.kernel.OpenJobObjectW.restype = HANDLE
api.kernel.CloseHandle.argtypes = [HANDLE]
api.kernel.CloseHandle.restype = BOOL
h = api.kernel.OpenJobObjectW(4, False, NAME)
assert h
try:
    print(json.dumps(dict(explicit=collect(api, h), implicit=collect())))
finally:
    assert api.kernel.CloseHandle(h)
""".replace('NAME', repr(name))


def test_native_abi_sizes_offsets_and_signatures():
    if C.sizeof(C.c_void_p) != 8:
        pytest.skip('this ABI regression records Windows x64; x86 native coverage pending')
    assert C.sizeof(w.MEMORYSTATUSEX) == 64
    assert C.sizeof(w.PERFORMANCE_INFORMATION) == 104
    assert C.sizeof(w.PROCESS_MEMORY_COUNTERS_EX) == 80
    assert C.sizeof(w.JOBOBJECT_BASIC_LIMIT_INFORMATION) == 64
    assert C.sizeof(w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION) == 144
    assert w.PERFORMANCE_INFORMATION.CommitTotal.offset == 8
    assert w.JOBOBJECT_BASIC_LIMIT_INFORMATION.MinimumWorkingSetSize.offset == 24
    assert w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION.ProcessMemoryLimit.offset == 112
    api = w.NativeAPI()
    assert api.GetCurrentProcess.restype is w.HANDLE
    assert len(api.QueryInformationJobObject.argtypes) == 5


def test_native_machine_and_self_observations():
    o = w.collect()
    assert not o['errors'], o['errors']
    assert 0 <= o['physical_available_bytes'] <= o['physical_total_bytes']
    assert 0 <= o['system_commit_used_bytes'] <= o['system_commit_limit_bytes']
    assert o['caller_commit_available_bytes'] >= 0
    assert o['process_private_commit_bytes'] > 0 and o['process_working_set_bytes'] > 0
    assert type(o['job']['in_any_job']) is bool
    assert assess(o, required_bytes=1)['allowed']


def test_native_job_limits_child_collection_and_closed_handle():
    api = job_api()
    with disposable_job(api) as (job, name):
        limits = query(api, job)
        assert limits.ProcessMemoryLimit == 256*M and limits.JobMemoryLimit == 384*M
        reports = child_in_jobs(api, [job], explicit_collection(name))
        o = reports['explicit']
        assert reports['implicit']['job']['job_chain_coverage'] == 'immediate-only-chain-not-enumerated'
        assert o['job']['process_memory_limit_bytes'] == 256*M
        assert o['job']['job_memory_limit_bytes'] == 384*M
        assert o['job']['in_any_job'] is True and o['job']['current_usage_bytes'] is None
        assert o['process_private_commit_bytes'] > 0
        assert assess(o, required_bytes=1)['allowed']
        assert not assess(o, required_bytes=512*M)['allowed']
    info = w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    assert not api.QueryInformationJobObject(job, 9, C.byref(info), C.sizeof(info), None)
    assert api.last_error() == 6  # ERROR_INVALID_HANDLE: owned job handle released


def test_native_query_access_denied_on_restricted_owned_handle():
    api = job_api()
    with disposable_job(api) as (_, name):
        restricted = checked(api, api.OpenJobObjectW(0x2, False, name))  # SET_ATTRIBUTES, no QUERY
        try:
            info = w.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            assert not api.QueryInformationJobObject(restricted, 9, C.byref(info), C.sizeof(info), None)
            assert api.last_error() == 5  # actual ERROR_ACCESS_DENIED, not simulated
        finally:
            checked(api, api.CloseHandle(restricted))


def test_native_nested_jobs_report_immediate_only():
    api = job_api()
    with disposable_job(api, 384*M, 512*M) as (parent, _), disposable_job(api) as (job, name):
        o = child_in_jobs(api, [parent, job], explicit_collection(name))['explicit']
        assert o['job']['process_memory_limit_bytes'] == 256*M
        assert o['job']['job_chain_coverage'] == 'explicit-only-chain-not-enumerated'
        assert assess(o, settings('best-effort'), 1)['allowed']
        assert not assess(o, settings('strict'), 1)['allowed']


def test_native_worker_preflight_inside_job_before_any_ml_import(snapshot, tmp_path):
    api = job_api()
    code = """
from lia_lab.inference_worker import memory_preflight
from lia_lab.memory_resources import settings
from lia_lab.io import LabError, load
import json
request = dict(snapshot=SNAPSHOT, dtype='float32', memory_policy=settings('strict'), _request_sha256='synthetic-native-only')
try:
    memory_preflight(request, OUTPUT, load(MANIFEST))
except LabError as exc:
    assert 'worker memory preflight blocked' in str(exc)
else:
    raise AssertionError('strict must block incomplete job-chain coverage')
assert 'torch' not in sys.modules and 'transformers' not in sys.modules
print(json.dumps(load(REPORT)))
"""
    for placeholder, value in {'SNAPSHOT':str(snapshot[0]), 'OUTPUT':str(tmp_path/'results.json'),
                               'MANIFEST':str(snapshot[1]), 'REPORT':str(tmp_path/'memory-worker.json')}.items():
        code = code.replace(placeholder, repr(value))
    with disposable_job(api) as (job, _):
        data = child_in_jobs(api, [job], code)
    assert data['observation']['job']['in_any_job'] is True
    assert not data['assessment']['allowed']
    assert data['request_sha256'] == 'synthetic-native-only'
    assert not (tmp_path/'results.json').exists()
