"""Read-only Win32 memory observations. No ML imports, allocations or job changes.

Fixed-width Win32 scalars and pointer-sized SIZE_T use native ABI alignment.
DLLs are opened only when NativeAPI is constructed on Windows.
"""
import ctypes as C
import os
import time

DWORD = C.c_uint32
BOOL = C.c_int32
SIZE_T = C.c_size_t
HANDLE = C.c_void_p
U64 = C.c_uint64


class MEMORYSTATUSEX(C.Structure):
    _fields_ = [('dwLength', DWORD), ('dwMemoryLoad', DWORD)] + [
        (n, U64) for n in ('ullTotalPhys', 'ullAvailPhys', 'ullTotalPageFile',
                          'ullAvailPageFile', 'ullTotalVirtual', 'ullAvailVirtual', 'ullAvailExtendedVirtual')]


class PERFORMANCE_INFORMATION(C.Structure):
    _fields_ = [('cb', DWORD)] + [(n, SIZE_T) for n in (
        'CommitTotal', 'CommitLimit', 'CommitPeak', 'PhysicalTotal', 'PhysicalAvailable',
        'SystemCache', 'KernelTotal', 'KernelPaged', 'KernelNonpaged', 'PageSize')] + [
        (n, DWORD) for n in ('HandleCount', 'ProcessCount', 'ThreadCount')]


class PROCESS_MEMORY_COUNTERS_EX(C.Structure):
    _fields_ = [('cb', DWORD), ('PageFaultCount', DWORD)] + [(n, SIZE_T) for n in (
        'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
        'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(C.Structure):
    _fields_ = [('PerProcessUserTimeLimit', C.c_int64), ('PerJobUserTimeLimit', C.c_int64),
        ('LimitFlags', DWORD), ('MinimumWorkingSetSize', SIZE_T), ('MaximumWorkingSetSize', SIZE_T),
        ('ActiveProcessLimit', DWORD), ('Affinity', SIZE_T), ('PriorityClass', DWORD), ('SchedulingClass', DWORD)]


class IO_COUNTERS(C.Structure):
    _fields_ = [(n, U64) for n in ('ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
                                  'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(C.Structure):
    _fields_ = [('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION), ('IoInfo', IO_COUNTERS)] + [
        (n, SIZE_T) for n in ('ProcessMemoryLimit', 'JobMemoryLimit', 'PeakProcessMemoryUsed', 'PeakJobMemoryUsed')]


class NativeAPI:
    def __init__(self):
        if os.name != 'nt':
            raise OSError('Win32 memory API requires Windows')
        self.kernel = C.WinDLL('kernel32', use_last_error=True)
        self.psapi = C.WinDLL('psapi', use_last_error=True)
        signatures = {
            'GlobalMemoryStatusEx': (self.kernel, [C.POINTER(MEMORYSTATUSEX)], BOOL),
            'GetCurrentProcess': (self.kernel, [], HANDLE),
            'IsProcessInJob': (self.kernel, [HANDLE, HANDLE, C.POINTER(BOOL)], BOOL),
            'QueryInformationJobObject': (self.kernel, [HANDLE, C.c_int32, C.c_void_p, DWORD, C.POINTER(DWORD)], BOOL),
            'GetPerformanceInfo': (self.psapi, [C.POINTER(PERFORMANCE_INFORMATION), DWORD], BOOL),
            'GetProcessMemoryInfo': (self.psapi, [HANDLE, C.c_void_p, DWORD], BOOL),
        }
        for name, (dll, args, result) in signatures.items():
            function = getattr(dll, name)
            function.argtypes, function.restype = args, result
            setattr(self, name, function)

    @staticmethod
    def last_error():
        return C.get_last_error()  # thread-local copy of GetLastError via use_last_error


def collect(api=None, job_handle=None):
    """job_handle is an optional borrowed handle: verified membership, never closed here.

    NULL is the default documented immediate-job query, not an enumeration. Explicit
    handles are useful to callers which already own a job; this does not launch one.
    """
    api = NativeAPI() if api is None else api
    report = dict(platform='windows', observed_at_unix=time.time(), process_id=os.getpid(),
        physical_total_bytes=None, physical_available_bytes=None, system_commit_limit_bytes=None,
        system_commit_used_bytes=None, caller_commit_available_bytes=None,
        process_private_commit_bytes=None, process_working_set_bytes=None,
        sources={}, errors=[], job=dict(in_any_job=None, job_chain_coverage='unknown',
            query_mode='implicit-null' if job_handle is None else 'explicit-borrowed-handle',
            limits_observed=False, process_memory_limit_bytes=None, job_memory_limit_bytes=None,
            current_usage_bytes=None, current_usage_source=None))

    def call(name, *args):
        if not getattr(api, name)(*args):
            error = api.last_error()
            report['errors'].append({'api': name, 'winerror': error})
            return False
        return True

    global_info = MEMORYSTATUSEX(dwLength=C.sizeof(MEMORYSTATUSEX))
    if call('GlobalMemoryStatusEx', C.byref(global_info)):
        for key, value in [('physical_total_bytes', global_info.ullTotalPhys),
                           ('physical_available_bytes', global_info.ullAvailPhys),
                           ('caller_commit_available_bytes', global_info.ullAvailPageFile)]:
            report[key] = value
            report['sources'][key] = 'GlobalMemoryStatusEx'
    perf = PERFORMANCE_INFORMATION(cb=C.sizeof(PERFORMANCE_INFORMATION))
    if call('GetPerformanceInfo', C.byref(perf), C.sizeof(perf)):
        if perf.PageSize > 0:
            report['system_commit_limit_bytes'] = perf.CommitLimit * perf.PageSize
            report['system_commit_used_bytes'] = perf.CommitTotal * perf.PageSize
            report['sources']['system_commit_limit_bytes'] = 'GetPerformanceInfo.CommitLimit * PageSize'
            report['sources']['system_commit_used_bytes'] = 'GetPerformanceInfo.CommitTotal * PageSize'
        else:
            report['errors'].append({'api': 'GetPerformanceInfo', 'issue': 'invalid PageSize'})
    process = api.GetCurrentProcess()  # pseudo handle: never CloseHandle
    counters = PROCESS_MEMORY_COUNTERS_EX(cb=C.sizeof(PROCESS_MEMORY_COUNTERS_EX))
    if call('GetProcessMemoryInfo', process, C.byref(counters), C.sizeof(counters)):
        report['process_private_commit_bytes'] = counters.PrivateUsage
        report['process_working_set_bytes'] = counters.WorkingSetSize
        report['sources']['process_private_commit_bytes'] = 'GetProcessMemoryInfo.PrivateUsage'
        report['sources']['process_working_set_bytes'] = 'GetProcessMemoryInfo.WorkingSetSize'
    member = BOOL()
    if call('IsProcessInJob', process, None, C.byref(member)):
        job = report['job']
        job['membership_source'] = 'IsProcessInJob'
        job['in_any_job'] = bool(member.value)
        job['job_chain_coverage'] = 'immediate-only-chain-not-enumerated' if member.value else 'not_applicable'
        if member.value:
            if job_handle is not None:
                explicit_member = BOOL()
                if not call('IsProcessInJob', process, job_handle, C.byref(explicit_member)):
                    return report
                if not explicit_member.value:
                    report['errors'].append({'api': 'IsProcessInJob', 'issue': 'caller is not in supplied job'})
                    return report
                job['job_chain_coverage'] = 'explicit-only-chain-not-enumerated'
            limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            if call('QueryInformationJobObject', job_handle, 9, C.byref(limits), C.sizeof(limits), None):
                job['limits_observed'] = True
                job['limits_source'] = 'QueryInformationJobObject.JobObjectExtendedLimitInformation'
                flags = limits.BasicLimitInformation.LimitFlags
                job['limit_flags'] = flags
                if flags & 0x100:
                    job['process_memory_limit_bytes'] = limits.ProcessMemoryLimit
                if flags & 0x200:
                    job['job_memory_limit_bytes'] = limits.JobMemoryLimit
                # PeakJobMemoryUsed is deliberately NOT current usage. No undocumented classes.
    return report
