"""Suspended Win32 creation and owned Job lifecycle. Not a security sandbox.

Only the supervisor owns the unnamed Job handle. No breakaway or ML imports.
The ABI declarations reused from windows_memory do not collect observations.
"""
import ctypes as C
import os
from pathlib import Path
import subprocess
import time
import uuid
from .io import LabError
from .windows_memory import BOOL, DWORD, HANDLE, SIZE_T, JOBOBJECT_EXTENDED_LIMIT_INFORMATION

KILL_ON_CLOSE, JOB_MEMORY, ACTIVE_PROCESS = 0x2000, 0x200, 0x8
CREATE_FLAGS = 0x4 | 0x400 | 0x80000 | 0x08000000


class STARTUPINFOW(C.Structure):
    _fields_ = [('cb', DWORD), ('lpReserved', C.c_wchar_p), ('lpDesktop', C.c_wchar_p),
        ('lpTitle', C.c_wchar_p)] + [(n, DWORD) for n in ('dwX', 'dwY', 'dwXSize', 'dwYSize',
        'dwXCountChars', 'dwYCountChars', 'dwFillAttribute', 'dwFlags')] + [
        ('wShowWindow', C.c_uint16), ('cbReserved2', C.c_uint16), ('lpReserved2', C.c_void_p),
        ('hStdInput', HANDLE), ('hStdOutput', HANDLE), ('hStdError', HANDLE)]


class STARTUPINFOEXW(C.Structure):
    _fields_ = [('StartupInfo', STARTUPINFOW), ('lpAttributeList', C.c_void_p)]


class PROCESS_INFORMATION(C.Structure):
    _fields_ = [('hProcess', HANDLE), ('hThread', HANDLE), ('dwProcessId', DWORD), ('dwThreadId', DWORD)]


class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(C.Structure):
    _fields_ = [(n, C.c_int64) for n in ('TotalUserTime', 'TotalKernelTime', 'ThisPeriodTotalUserTime',
        'ThisPeriodTotalKernelTime')] + [(n, DWORD) for n in ('TotalPageFaultCount', 'TotalProcesses',
        'ActiveProcesses', 'TotalTerminatedProcesses')]


def contract(maximum_job_commit_bytes=None):
    if maximum_job_commit_bytes is not None and (type(maximum_job_commit_bytes) is not int or
            not 0 < maximum_job_commit_bytes < 2**63):
        raise LabError('invalid authorized job commit ceiling')
    return dict(version=1, method='CreateProcessW-CREATE_SUSPENDED-assign-verify-resume',
        active_process_limit=16, kill_on_job_close=True, allow_breakaway=False,
        maximum_job_commit_bytes=maximum_job_commit_bytes,
        commit_rule='min-approved-loading-envelope-and-observed-commit-after-authorized-margin',
        missing_commit_evidence='not-applied-with-reason', cleanup_timeout_seconds=5)


def select_commit_limit(config, observation, assessment):
    maximum = config['maximum_job_commit_bytes']
    if maximum is None:
        return None, 'no approved architecture loading envelope; no numeric commit cap'
    keys = ('caller_commit_available_bytes', 'system_commit_limit_bytes', 'system_commit_used_bytes')
    values = [observation.get(k) for k in keys]
    if any(type(n) is not int or n < 0 for n in values) or values[2] > values[1]:
        return None, 'commit dimensions unavailable/inconsistent; physical RAM is not a commit cap'
    margin = assessment.get('effective_margin_percent')
    if type(margin) is not int or not 0 <= margin <= 90:
        raise LabError('invalid authorized effective memory margin')
    headroom = min(values[0], values[1]-values[2]) * (100-margin) // 100
    if headroom < maximum:
        raise LabError('observed commit headroom below authorized launcher loading envelope')
    return min(maximum, headroom), None


def environment_block(env):
    if not isinstance(env, dict) or not env:
        raise LabError('explicit nonempty filtered Windows environment required')
    seen = set()
    for key, value in env.items():
        if (not isinstance(key, str) or not key or '=' in key or '\0' in key or
            not isinstance(value, str) or '\0' in value or key.casefold() in seen):
            raise LabError('invalid/ambiguous Windows environment')
        seen.add(key.casefold())
    return '\0'.join(f'{key}={env[key]}' for key in sorted(env, key=str.casefold)) + '\0\0'


class NativeAPI:
    def __init__(self):
        if os.name != 'nt' or C.sizeof(HANDLE) != 8:
            raise LabError('controlled launcher requires native Windows x64')
        self.dll = C.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([C.c_void_p, C.c_wchar_p], HANDLE),
            'SetHandleInformation': ([HANDLE, DWORD, DWORD], BOOL),
            'SetInformationJobObject': ([HANDLE, C.c_int32, C.c_void_p, DWORD], BOOL),
            'QueryInformationJobObject': ([HANDLE, C.c_int32, C.c_void_p, DWORD, C.c_void_p], BOOL),
            'GetCurrentProcess': ([], HANDLE),
            'CreateFileW': ([C.c_wchar_p, DWORD, DWORD, C.c_void_p, DWORD, DWORD, HANDLE], HANDLE),
            'DuplicateHandle': ([HANDLE, HANDLE, HANDLE, C.POINTER(HANDLE), DWORD, BOOL, DWORD], BOOL),
            'InitializeProcThreadAttributeList': ([C.c_void_p, DWORD, DWORD, C.POINTER(SIZE_T)], BOOL),
            'UpdateProcThreadAttribute': ([C.c_void_p, DWORD, SIZE_T, C.c_void_p, SIZE_T, C.c_void_p, C.c_void_p], BOOL),
            'DeleteProcThreadAttributeList': ([C.c_void_p], None),
            'CreateProcessW': ([C.c_wchar_p, C.c_wchar_p, C.c_void_p, C.c_void_p, BOOL, DWORD,
                C.c_void_p, C.c_wchar_p, C.c_void_p, C.POINTER(PROCESS_INFORMATION)], BOOL),
            'AssignProcessToJobObject': ([HANDLE, HANDLE], BOOL),
            'IsProcessInJob': ([HANDLE, HANDLE, C.POINTER(BOOL)], BOOL),
            'ResumeThread': ([HANDLE], DWORD),
            'WaitForSingleObject': ([HANDLE, DWORD], DWORD),
            'GetExitCodeProcess': ([HANDLE, C.POINTER(DWORD)], BOOL),
            'TerminateJobObject': ([HANDLE, DWORD], BOOL),
            'TerminateProcess': ([HANDLE, DWORD], BOOL),
            'CloseHandle': ([HANDLE], BOOL),
        }
        for name, (args, result) in signatures.items():
            f = getattr(self.dll, name); f.argtypes, f.restype = args, result

    def check(self, name, *args):
        result = getattr(self.dll, name)(*args)
        if not result:
            code = C.get_last_error()
            raise OSError(code, f'{name}: {C.FormatError(code).strip()}')
        return result

    def create_job(self, own):
        job = own('job', self.check('CreateJobObjectW', None, None))
        self.check('SetHandleInformation', job, 1, 0)
        return job

    def configure(self, job, limit, count):
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = KILL_ON_CLOSE | ACTIVE_PROCESS | (JOB_MEMORY if limit is not None else 0)
        info.BasicLimitInformation.ActiveProcessLimit = count
        info.JobMemoryLimit = limit or 0
        self.check('SetInformationJobObject', job, 9, C.byref(info), C.sizeof(info))
        observed = self.limits(job)
        if (observed.BasicLimitInformation.LimitFlags != info.BasicLimitInformation.LimitFlags or
            observed.BasicLimitInformation.ActiveProcessLimit != count or observed.JobMemoryLimit != info.JobMemoryLimit):
            raise LabError('configured Windows Job limits differ on readback')
        return info.BasicLimitInformation.LimitFlags

    def limits(self, job):
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        self.check('QueryInformationJobObject', job, 9, C.byref(info), C.sizeof(info), None)
        return info

    def spawn_suspended(self, command, env, log, cwd, own):
        import msvcrt
        current = self.dll.GetCurrentProcess()
        duplicate = HANDLE()
        self.check('DuplicateHandle', current, msvcrt.get_osfhandle(log.fileno()), current,
                   C.byref(duplicate), 0, True, 2)
        out = own('stdio-output', duplicate.value)
        stdin = self.dll.CreateFileW('NUL', 0x80000000, 3, None, 3, 0, None)
        if stdin in (None, HANDLE(-1).value):
            code = C.get_last_error(); raise OSError(code, 'CreateFileW(NUL) failed')
        own('stdio-input', stdin)
        self.check('SetHandleInformation', stdin, 1, 1)
        inherited = (HANDLE * 2)(stdin, out)
        size = SIZE_T()
        result = self.dll.InitializeProcThreadAttributeList(None, 1, 0, C.byref(size))
        error = C.get_last_error()
        if result or error != 122 or not 0 < size.value <= 1024*1024:
            raise OSError(error, 'InitializeProcThreadAttributeList sizing failed')
        attributes = C.create_string_buffer(size.value)
        self.check('InitializeProcThreadAttributeList', attributes, 1, 0, C.byref(size))
        try:
            self.check('UpdateProcThreadAttribute', attributes, 0, 0x20002,
                       C.byref(inherited), C.sizeof(inherited), None, None)
            startup = STARTUPINFOEXW()
            startup.StartupInfo.cb = C.sizeof(startup)
            startup.StartupInfo.dwFlags = 0x100  # STARTF_USESTDHANDLES
            startup.StartupInfo.hStdInput = stdin
            startup.StartupInfo.hStdOutput = startup.StartupInfo.hStdError = out
            startup.lpAttributeList = C.cast(attributes, C.c_void_p)
            info = PROCESS_INFORMATION()
            cmdline = C.create_unicode_buffer(subprocess.list2cmdline(command))
            block = C.create_unicode_buffer(environment_block(env))
            self.check('CreateProcessW', command[0], cmdline, None, None, True, CREATE_FLAGS,
                       block, cwd, C.byref(startup), C.byref(info))
            own('process', info.hProcess); own('thread', info.hThread)
            return info
        finally:
            self.dll.DeleteProcThreadAttributeList(attributes)

    def assign(self, job, process): self.check('AssignProcessToJobObject', job, process)
    def member(self, job, process):
        result = BOOL(); self.check('IsProcessInJob', process, job, C.byref(result)); return bool(result.value)
    def resume(self, thread):
        count = self.dll.ResumeThread(thread)
        if count == 0xffffffff:
            code = C.get_last_error(); raise OSError(code, 'ResumeThread failed')
        if count != 1: raise LabError('unexpected suspend count; refusing unprotected execution')
    def exited(self, process):
        state = self.dll.WaitForSingleObject(process, 0)
        if state not in (0, 258):
            code = C.get_last_error(); raise OSError(code, 'WaitForSingleObject failed')
        return state == 0
    def exit_code(self, process):
        code = DWORD(); self.check('GetExitCodeProcess', process, C.byref(code)); return code.value
    def accounting(self, job):
        info = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
        self.check('QueryInformationJobObject', job, 1, C.byref(info), C.sizeof(info), None)
        return dict(active_processes=info.ActiveProcesses, total_processes=info.TotalProcesses,
                    limit_terminated_processes=info.TotalTerminatedProcesses)
    def terminate_job(self, job): self.check('TerminateJobObject', job, 1)
    def terminate_process(self, process): self.check('TerminateProcess', process, 1)
    def close(self, handle): self.check('CloseHandle', handle)


def run(command, env, log, timeout, *, config=None, observation=None, assessment=None,
        report=None, cwd=None, api=None):
    report = {} if report is None else report
    config = contract() if config is None else config
    if config != contract(config.get('maximum_job_commit_bytes')):
        raise LabError('Windows launcher contract changed or unsupported')
    if (not command or any(not isinstance(a, str) or '\0' in a for a in command) or
        not Path(command[0]).is_absolute() or len(subprocess.list2cmdline(command).encode('utf-16-le'))//2 >= 32767):
        raise LabError('invalid explicit Windows executable/command line')
    if type(timeout) not in (int, float) or not 0 < timeout <= 3600:
        raise LabError('invalid Windows supervision timeout')
    environment_block(env)
    limit, reason = select_commit_limit(config, observation or {}, assessment or {})
    api = NativeAPI() if api is None else api
    owned, process, job, assigned = [], None, None, False
    report.update(schema_version=1, platform='windows', method=config['method'], job_id=uuid.uuid4().hex,
        job_named=False, job_handle_inherited=False, config=config, commit_limit_bytes=limit,
        commit_limit_not_applied_reason=reason, security_sandbox=False, reservation=False,
        creation_flags=CREATE_FLAGS, associated_before_resume=False, resumed=False, pid=None, stage='create-job',
        primary_exit_code=None, active_processes=None, total_processes=None,
        peak_job_commit_bytes=None, sampled_peak_active_processes=0, termination_reason='setup',
        terminate_job_succeeded=None, tree_empty_confirmed=False, process_exit_confirmed=False,
        handle_closures=[], cleanup_errors=[], cleanup_complete=False)
    def own(name, handle):
        owned.append((name, handle)); return handle
    def account():
        data = api.accounting(job); report.update(data)
        report['sampled_peak_active_processes'] = max(report['sampled_peak_active_processes'], data['active_processes'])
        return data['active_processes']
    def reap():
        if process is not None and api.exited(process.hProcess):
            report['process_exit_confirmed'] = True
            if report['primary_exit_code'] is None:
                report['primary_exit_code'] = api.exit_code(process.hProcess)
                report['active_at_primary_exit'] = report['active_processes']
        return report['process_exit_confirmed']
    deadline = time.monotonic() + timeout
    error = None
    try:
        job = api.create_job(own)
        report['stage'] = 'configure-job'
        report['applied_limit_flags'] = api.configure(job, limit, config['active_process_limit'])
        report['stage'] = 'create-process-suspended'
        process = api.spawn_suspended(command, env, log, str(Path(cwd or Path.cwd()).resolve()), own)
        report['pid'] = process.dwProcessId
        report['stage'] = 'associate'
        api.assign(job, process.hProcess); assigned = True
        report['stage'] = 'verify-association'
        if not api.member(job, process.hProcess): raise LabError('owned Job association not confirmed')
        report['associated_before_resume'] = True
        if time.monotonic() >= deadline: raise subprocess.TimeoutExpired(command, timeout)
        report['stage'] = 'resume'
        api.resume(process.hThread); report['resumed'] = True
        report['stage'] = 'monitor'
        while True:
            active = account()
            if reap() and active == 0:
                report.update(tree_empty_confirmed=True, termination_reason='natural-exit')
                break
            if time.monotonic() >= deadline: raise subprocess.TimeoutExpired(command, timeout)
            time.sleep(min(0.02, max(0, deadline-time.monotonic())))
    except BaseException as exc:
        error = exc
        report['termination_reason'] = 'timeout' if isinstance(exc, subprocess.TimeoutExpired) else ('interrupted' if isinstance(exc, KeyboardInterrupt) else 'error')
        report['failure'] = f'{type(exc).__name__}: {exc}'
        report['failure_stage'] = report['stage']
        if isinstance(exc, OSError): report['winerror'] = getattr(exc, 'winerror', None) or exc.errno
    finally:
        # Handles registered during setup remain owned even if the setup call raises.
        if job is None:
            job = next((h for name, h in owned if name == 'job'), None)
        if process is None:
            h = next((h for name, h in owned if name == 'process'), None)
            if h is not None: process = PROCESS_INFORMATION(hProcess=h)
        try:
            if error is not None:
                if job is not None:
                    try:
                        api.terminate_job(job); report['terminate_job_succeeded'] = True
                    except BaseException as exc:
                        report['terminate_job_succeeded'] = False
                        report['cleanup_errors'].append(f'{type(exc).__name__}: {exc}')
                if process is not None and not assigned and not api.exited(process.hProcess):
                    api.terminate_process(process.hProcess)
                cleanup_deadline = time.monotonic() + config['cleanup_timeout_seconds']
                while True:
                    empty = job is None or account() == 0
                    done = process is None or reap()
                    if empty and done:
                        report['tree_empty_confirmed'] = True; break
                    if time.monotonic() >= cleanup_deadline: raise LabError('Job cleanup deadline exceeded')
                    time.sleep(0.01)
            if job is not None:
                report['peak_job_commit_bytes'] = api.limits(job).PeakJobMemoryUsed
        except BaseException as exc:
            report['cleanup_errors'].append(f'{type(exc).__name__}: {exc}')
        for name, handle in reversed(owned):
            try:
                api.close(handle); report['handle_closures'].append(dict(kind=name, closed=True))
            except BaseException as exc:
                report['handle_closures'].append(dict(kind=name, closed=False))
                report['cleanup_errors'].append(f'{type(exc).__name__}: {exc}')
        report['cleanup_complete'] = report['tree_empty_confirmed'] and not report['cleanup_errors']
        report['job_state'] = 'empty-confirmed' if report['tree_empty_confirmed'] else 'not-confirmed'
    if not report['cleanup_complete']:
        raise LabError('Windows tree/handle cleanup could not be confirmed') from error
    if error is not None: raise error
    return report['primary_exit_code']


def validate_report(report, config, request_sha256, operation_sha256, observation=None, assessment=None):
    if (not isinstance(report, dict) or not isinstance(report.get('handle_closures'), list) or
        any(not isinstance(item, dict) for item in report['handle_closures'])):
        raise LabError('malformed Windows launcher report')
    flags = KILL_ON_CLOSE | ACTIVE_PROCESS | (JOB_MEMORY if report.get('commit_limit_bytes') is not None else 0)
    if (type(report.get('schema_version')) is not int or report['schema_version'] != 1 or
        report.get('platform') != 'windows' or report.get('job_named') is not False or
        report.get('job_state') != 'empty-confirmed' or
        report.get('request_sha256') != request_sha256 or report.get('operation_sha256') != operation_sha256 or
        report.get('config') != config or report.get('method') != config['method'] or
        report.get('applied_limit_flags') != flags or report.get('creation_flags') != CREATE_FLAGS or
        report.get('associated_before_resume') is not True or report.get('resumed') is not True or
        report.get('job_handle_inherited') is not False or report.get('security_sandbox') is not False or
        report.get('tree_empty_confirmed') is not True or report.get('process_exit_confirmed') is not True or
        type(report.get('active_processes')) is not int or report['active_processes'] != 0 or report.get('cleanup_complete') is not True or
        report.get('cleanup_errors') != [] or report.get('termination_reason') != 'natural-exit' or
        type(report.get('primary_exit_code')) is not int or report['primary_exit_code'] != 0 or
        type(report.get('total_processes')) is not int or report['total_processes'] < 1 or
        {c.get('kind') for c in report.get('handle_closures', [])} != {'job', 'process', 'thread', 'stdio-input', 'stdio-output'} or
        any(c.get('closed') is not True for c in report['handle_closures'])):
        raise LabError('missing/incoherent Windows launcher report; no successful tree cleanup evidence')
    maximum = config['maximum_job_commit_bytes']
    applied = report.get('commit_limit_bytes')
    if applied is not None and (type(applied) is not int or maximum is None or not 0 < applied <= maximum):
        raise LabError('Windows launcher commit cap exceeds authorized ceiling')
    if applied is None and not report.get('commit_limit_not_applied_reason'):
        raise LabError('unexplained missing Windows commit limit')
    if observation is not None:
        expected, reason = select_commit_limit(config, observation, assessment)
        if applied != expected or report.get('commit_limit_not_applied_reason') != reason:
            raise LabError('Windows commit limit report differs from authorized formula')
