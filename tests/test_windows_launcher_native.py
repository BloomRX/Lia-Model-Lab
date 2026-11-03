"""Native Windows x64, real disposable child trees, no ML or stress allocation."""
import ctypes as C
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
from lia_lab import windows_launcher as w
from lia_lab.io import LabError

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='native Windows x64 launcher only')


def wait_file(path):
    deadline=time.monotonic()+5
    while not path.exists():
        assert time.monotonic()<deadline, 'disposable child did not start'
        time.sleep(0.01)
    return json.loads(path.read_text(encoding='utf-8'))


def open_child(api, pid):
    f=api.dll.OpenProcess; f.argtypes=[w.DWORD,w.BOOL,w.DWORD]; f.restype=w.HANDLE
    return api.check('OpenProcess', 0x100000 | 0x1000, False, pid)


class ObserveAPI(w.NativeAPI):
    def __init__(self, marker):
        super().__init__(); self.marker=marker; self.before_resume=False
        self.child_handle=None; self.child_in_owned_job=False; self.closed=[]
    def spawn_suspended(self,*args):
        self.info=super().spawn_suspended(*args)
        return self.info
    def assign(self,job,process):
        self.job=job
        return super().assign(job,process)
    def resume(self,thread):
        assert not self.marker.exists(), 'Python ran before assignment'
        assert self.member(self.job,self.info.hProcess)
        self.before_resume=True
        return super().resume(thread)
    def accounting(self,job):
        if self.marker.exists() and self.child_handle is None:
            data=json.loads(self.marker.read_text(encoding='utf-8'))
            if 'child_pid' in data:
                self.child_handle=open_child(self,data['child_pid'])
                self.child_in_owned_job=self.member(job,self.child_handle)
        return super().accounting(job)
    def close(self,handle):
        super().close(handle); self.closed.append(handle)
    def release_observer(self):
        if self.child_handle is not None:
            super().close(self.child_handle); self.child_handle=None


def tree_code(marker, child_seconds, root_seconds=0):
    return f"""
import os,sys,subprocess,json,time
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep({child_seconds})'])
with open({str(marker)!r},'w',encoding='utf-8') as f:
    json.dump(dict(primary_pid=os.getpid(),child_pid=child.pid),f)
print('worker-stdout',flush=True)
print('worker-stderr',file=sys.stderr,flush=True)
time.sleep({root_seconds})
"""


def invoke(tmp_path, code, timeout=5, api=None, report=None, **kwargs):
    with (tmp_path/'worker.log').open('wb') as log:
        return w.run([sys.executable,'-c',code],dict(os.environ),log,timeout,api=api,report=report,**kwargs)


def test_native_abi_and_commit_readback(tmp_path):
    assert C.sizeof(w.STARTUPINFOW)==104 and C.sizeof(w.STARTUPINFOEXW)==112
    assert C.sizeof(w.PROCESS_INFORMATION)==24
    assert C.sizeof(w.JOBOBJECT_BASIC_ACCOUNTING_INFORMATION)==48
    report={}
    observation=dict(caller_commit_available_bytes=2**30,system_commit_limit_bytes=2**31,system_commit_used_bytes=2**30)
    assert invoke(tmp_path,'print("native")',report=report,config=w.contract(256*1024**2),
        observation=observation,assessment={'effective_margin_percent':20})==0
    assert report['commit_limit_bytes']==256*1024**2
    assert report['applied_limit_flags']==w.KILL_ON_CLOSE|w.ACTIVE_PROCESS|w.JOB_MEMORY
    assert report['peak_job_commit_bytes']>0 and report['cleanup_complete']


def test_native_suspended_association_and_descendant_natural_exit(tmp_path):
    marker=tmp_path/'started.json'; api=ObserveAPI(marker); report={}
    start=time.monotonic()
    try:
        assert invoke(tmp_path,tree_code(marker,0.6),api=api,report=report)==0
        assert time.monotonic()-start>=0.6
        assert api.before_resume and api.child_in_owned_job
        assert report['associated_before_resume'] and report['total_processes']>=2
        assert report['active_at_primary_exit']>=1
        assert report['active_processes']==0 and report['tree_empty_confirmed']
        assert api.exited(api.child_handle)
        text=(tmp_path/'worker.log').read_text(encoding='utf-8')
        assert 'worker-stdout' in text and 'worker-stderr' in text
    finally: api.release_observer()


def test_native_timeout_kills_entire_tree(tmp_path):
    marker=tmp_path/'started.json'; api=ObserveAPI(marker); report={}
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            invoke(tmp_path,tree_code(marker,60,60),timeout=2,api=api,report=report)
        assert api.child_in_owned_job and api.exited(api.child_handle)
        assert report['termination_reason']=='timeout' and report['terminate_job_succeeded']
        assert report['cleanup_complete'] and report['active_processes']==0
        assert all(h['closed'] for h in report['handle_closures'])
    finally: api.release_observer()


def test_native_last_job_handle_close_kills_tree(tmp_path):
    api=w.NativeAPI(); owned=[]; job=None; child=None
    def own(name,handle): owned.append((name,handle)); return handle
    marker=tmp_path/'started.json'
    with (tmp_path/'worker.log').open('wb') as log:
        try:
            job=api.create_job(own); api.configure(job,256*1024**2,16)
            info=api.spawn_suspended([sys.executable,'-c',tree_code(marker,60,60)],dict(os.environ),log,str(tmp_path),own)
            api.assign(job,info.hProcess); assert api.member(job,info.hProcess); api.resume(info.hThread)
            data=wait_file(marker); child=open_child(api,data['child_pid'])
            assert api.member(job,child)
            api.close(job); owned=[(n,h) for n,h in owned if n!='job']; job=None
            deadline=time.monotonic()+5
            while not (api.exited(info.hProcess) and api.exited(child)):
                assert time.monotonic()<deadline
                time.sleep(0.01)
        finally:
            if job is not None: api.terminate_job(job)
            if child is not None: api.close(child)
            for _,h in reversed(owned): api.close(h)


@pytest.mark.parametrize('name', ['CreateJobObjectW','SetInformationJobObject','CreateProcessW',
    'AssignProcessToJobObject','ResumeThread'])
def test_native_setup_failure_no_python_instruction_or_handle_leak(tmp_path,monkeypatch,name):
    api=w.NativeAPI(); marker=tmp_path/'should-not-exist'; report={}
    count=api.dll.GetProcessHandleCount; count.argtypes=[w.HANDLE,C.POINTER(w.DWORD)]; count.restype=w.BOOL
    def handles():
        n=w.DWORD(); api.check('GetProcessHandleCount',api.dll.GetCurrentProcess(),C.byref(n)); return n.value
    baseline=handles()
    def denied(*args): C.set_last_error(5); return 0xffffffff if name=='ResumeThread' else 0
    monkeypatch.setattr(api.dll,name,denied)
    with pytest.raises(OSError):
        invoke(tmp_path,f'from pathlib import Path; Path({str(marker)!r}).touch()',api=api,report=report)
    assert not marker.exists() and report['cleanup_complete']
    assert all(h['closed'] for h in report['handle_closures'])
    assert handles()<=baseline+1
    assert not report['resumed']


def test_native_interrupt_terminates_tree(tmp_path):
    marker=tmp_path/'started.json'; report={}
    class InterruptedAPI(ObserveAPI):
        interrupted=False
        def accounting(self,job):
            data=super().accounting(job)
            if self.child_in_owned_job and not self.interrupted:
                self.interrupted=True; raise KeyboardInterrupt
            return data
    api=InterruptedAPI(marker)
    try:
        with pytest.raises(KeyboardInterrupt): invoke(tmp_path,tree_code(marker,60,60),api=api,report=report)
        assert report['termination_reason']=='interrupted' and report['cleanup_complete']
        assert api.exited(api.child_handle)
    finally: api.release_observer()


def test_native_unicode_quoting_cwd_filtered_env_exit_code(tmp_path):
    cwd=tmp_path/'diretório com espaço'; cwd.mkdir(); report={}
    code='import sys,os,json;print(json.dumps(dict(args=sys.argv[1:],cwd=os.getcwd(),env=dict(os.environ)),ensure_ascii=False));sys.exit(7)'
    env={'SYSTEMROOT':os.environ['SYSTEMROOT'],'LIA_TEST_UNICODE':'ação'}
    args=['space value','"quoted"','trailing slash\\','']
    with (tmp_path/'worker.log').open('wb') as log:
        rc=w.run([sys.executable,'-X','utf8','-c',code,*args],env,log,5,cwd=cwd,report=report)
    assert rc==7 and report['primary_exit_code']==7 and report['cleanup_complete']
    data=json.loads((tmp_path/'worker.log').read_text(encoding='utf-8'))
    assert data['args']==args and Path(data['cwd'])==cwd
    assert data['env']['LIA_TEST_UNICODE']=='ação'
    assert 'USERPROFILE' not in data['env'] and 'PATH' not in data['env']


def test_native_nested_owned_jobs_preserve_both_controls(tmp_path):
    inner_report=tmp_path/'inner.json'
    code=f"""
import sys,os,json
from lia_lab.windows_launcher import run
r={{}}
with open({str(tmp_path/'inner.log')!r},'wb') as log:
    assert run([sys.executable,'-c','print(123)'],dict(os.environ),log,5,report=r)==0
with open({str(inner_report)!r},'w',encoding='utf-8') as f: json.dump(r,f)
"""
    report={}
    assert invoke(tmp_path,code,report=report)==0
    inner=json.loads(inner_report.read_text(encoding='utf-8'))
    assert inner['associated_before_resume'] and inner['cleanup_complete']
    assert report['total_processes']>=2
    assert report['cleanup_complete']


def test_native_handle_whitelist_does_not_inherit_unrelated_event(tmp_path):
    api=w.NativeAPI(); f=api.dll.CreateEventW
    f.argtypes=[C.c_void_p,w.BOOL,w.BOOL,C.c_wchar_p]; f.restype=w.HANDLE
    event=api.check('CreateEventW',None,False,False,None)
    try:
        api.check('SetHandleInformation',event,1,1)
        code=f"""
import ctypes as C
k=C.WinDLL('kernel32',use_last_error=True)
k.SetEvent.argtypes=[C.c_void_p];k.SetEvent.restype=C.c_int
signaled=k.SetEvent({event})
print('SetEvent-result',signaled)
"""
        assert invoke(tmp_path,code,api=api)==0
        # Handle values are process-local and may be reused for a different
        # child object. Observe the original parent's event, not child errno.
        assert api.dll.WaitForSingleObject(event,0)==258  # WAIT_TIMEOUT
        # Positive control: unrestricted inheritance must signal that same
        # parent event. This detects a broken probe or inert child code.
        subprocess.run([sys.executable,'-c',code+'\nassert signaled\n'],
            close_fds=False,creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=10,check=True,capture_output=True)
        assert api.dll.WaitForSingleObject(event,0)==0  # WAIT_OBJECT_0
    finally: api.close(event)
