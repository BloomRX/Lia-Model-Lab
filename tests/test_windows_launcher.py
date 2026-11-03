"""Simulated control flow, bindings and failure cleanup; not native Win32 proof."""
import copy
import sys
import subprocess
from types import SimpleNamespace
import pytest
from lia_lab import windows_launcher as w
from lia_lab.io import LabError


class FakeAPI:
    def __init__(self, fail=None, descendant=False):
        self.fail, self.descendant, self.alive, self.calls = fail, descendant, False, []
        self.handles, self.closed, self.polls = [], [], 0
        self.assigned, self.resumed = False, False
    def call(self, name):
        self.calls.append(name)
        if name == self.fail: raise OSError(5, name)
    def handle(self, own, name):
        h = len(self.handles)+100; self.handles.append(h); own(name, h); return h
    def create_job(self, own):
        self.call('CreateJobObjectW'); return self.handle(own, 'job')
    def configure(self, job, limit, count):
        self.call('SetInformationJobObject'); assert count == 16
        return w.KILL_ON_CLOSE | w.ACTIVE_PROCESS | (w.JOB_MEMORY if limit else 0)
    def spawn_suspended(self, command, env, log, cwd, own):
        self.handle(own, 'stdio-output'); self.handle(own, 'stdio-input')
        self.call('CreateProcessW')
        process = self.handle(own, 'process'); thread = self.handle(own, 'thread')
        self.alive = True
        return SimpleNamespace(hProcess=process, hThread=thread, dwProcessId=123)
    def assign(self, job, process): self.call('AssignProcessToJobObject'); self.assigned = True
    def member(self, job, process): self.call('IsProcessInJob'); return True
    def resume(self, thread): self.call('ResumeThread'); self.resumed = True
    def accounting(self, job):
        self.call('QueryInformationJobObject'); self.polls += 1
        if self.resumed:
            active = 1 if self.descendant and self.polls < 3 else 0
        else: active = int(self.alive and self.assigned)
        return dict(active_processes=active, total_processes=2, limit_terminated_processes=0)
    def exited(self, process): self.call('WaitForSingleObject'); return not self.alive or self.resumed
    def exit_code(self, process): self.call('GetExitCodeProcess'); return 0
    def limits(self, job): self.call('limits'); return SimpleNamespace(PeakJobMemoryUsed=1000)
    def terminate_job(self, job):
        self.call('TerminateJobObject')
        if self.assigned: self.alive = False
    def terminate_process(self, process): self.call('TerminateProcess'); self.alive = False
    def close(self, h): self.call('CloseHandle'); self.closed.append(h)


def run(api, **kwargs):
    return w.run([sys.executable, '-c', 'pass'], {'SYSTEMROOT':'test-only'}, None, 1, api=api, **kwargs)


def test_order_and_no_success_before_descendants_exit():
    api, report = FakeAPI(descendant=True), {}
    assert run(api, report=report) == 0
    names = ['CreateJobObjectW', 'SetInformationJobObject', 'CreateProcessW',
             'AssignProcessToJobObject', 'IsProcessInJob', 'ResumeThread']
    assert api.calls[:6] == names
    assert api.polls >= 3 and report['tree_empty_confirmed'] and report['cleanup_complete']
    assert report['active_at_primary_exit'] == 1
    assert set(api.handles) == set(api.closed)
    assert report['peak_job_commit_bytes'] == 1000 and not report['reservation']


@pytest.mark.parametrize('failure', ['CreateJobObjectW','SetInformationJobObject','CreateProcessW',
    'AssignProcessToJobObject','IsProcessInJob','ResumeThread','QueryInformationJobObject',
    'WaitForSingleObject','GetExitCodeProcess','limits','CloseHandle'])
def test_api_failures_close_all_registered_handles(failure):
    api, report = FakeAPI(failure), {}
    with pytest.raises((OSError, LabError)): run(api, report=report)
    if failure == 'CloseHandle':
        assert not report['cleanup_complete'] and report['cleanup_errors']
    else:
        assert set(api.handles) == set(api.closed)
    assert report['termination_reason'] in ('error', 'natural-exit')
    if failure in ('CreateJobObjectW','SetInformationJobObject','CreateProcessW','AssignProcessToJobObject','IsProcessInJob'):
        assert 'ResumeThread' not in api.calls
    if failure == 'AssignProcessToJobObject': assert 'TerminateProcess' in api.calls


@pytest.mark.parametrize('kind', ['timeout', 'interrupt'])
def test_abort_terminates_job_and_reaps(kind):
    api, report = FakeAPI(), {}
    def stop(job):
        if api.alive:
            if kind == 'interrupt': raise KeyboardInterrupt
            raise subprocess.TimeoutExpired('synthetic',1)
        return dict(active_processes=0, total_processes=2)
    api.accounting = stop
    with pytest.raises(KeyboardInterrupt if kind == 'interrupt' else subprocess.TimeoutExpired): run(api, report=report)
    assert report['terminate_job_succeeded'] and report['cleanup_complete']
    assert report['process_exit_confirmed'] and set(api.handles) == set(api.closed)


def test_cleanup_failure_cannot_claim_tree_gone():
    api, report = FakeAPI('TerminateJobObject'), {}
    def stop(job): raise subprocess.TimeoutExpired('synthetic',1)
    api.accounting = stop
    with pytest.raises(LabError, match='cleanup'): run(api, report=report)
    assert report['terminate_job_succeeded'] is False and not report['cleanup_complete']
    assert set(api.handles) == set(api.closed)


def test_commit_formula_uses_commit_and_approved_ceiling_only():
    config = w.contract(100)
    observation = dict(caller_commit_available_bytes=1000, system_commit_limit_bytes=2000,
        system_commit_used_bytes=1000, physical_available_bytes=1, process_working_set_bytes=999999)
    assert w.select_commit_limit(config, observation, {'effective_margin_percent':20}) == (100,None)
    observation['caller_commit_available_bytes'] = 110
    with pytest.raises(LabError, match='headroom'): w.select_commit_limit(config, observation, {'effective_margin_percent':20})
    del observation['system_commit_used_bytes']
    limit, reason = w.select_commit_limit(config, observation, {'effective_margin_percent':20})
    assert limit is None and reason


@pytest.mark.parametrize('maximum', [-1,0,True,2**63,float('nan'),'100'])
def test_invalid_commit_ceiling(maximum):
    with pytest.raises(LabError): w.contract(maximum)


@pytest.mark.parametrize('env', [{}, {'A':'x\0y'}, {'A=B':'c'}, {'A':'one','a':'two'}, {'':'value'}])
def test_invalid_environment(env):
    with pytest.raises(LabError): w.environment_block(env)


def test_environment_sorted_unicode_and_double_null():
    assert w.environment_block({'z':'fim','A':'ação'}) == 'A=ação\0z=fim\0\0'


@pytest.mark.parametrize('field,value', [('allow_breakaway',True), ('active_process_limit',100), ('version',2)])
def test_contract_mutation_blocks_before_creation(field,value):
    config=w.contract(); config[field]=value; api=FakeAPI()
    with pytest.raises(LabError): run(api, config=config)
    assert not api.calls


@pytest.mark.parametrize('field,value', [('request_sha256','wrong'),('operation_sha256','wrong'),
    ('associated_before_resume',False),('active_processes',1),('resumed',False),('cleanup_complete',False),
    ('job_handle_inherited',True),('primary_exit_code',1),('creation_flags',0),('applied_limit_flags',0),
    ('termination_reason','timeout'),('handle_closures',[])])
def test_report_binding_and_success_requires_empty_tree(field,value):
    report=dict(request_sha256='request', operation_sha256='operation')
    run(FakeAPI(), report=report)
    w.validate_report(report, w.contract(), 'request', 'operation')
    bad=copy.deepcopy(report); bad[field]=value
    with pytest.raises(LabError): w.validate_report(bad, w.contract(), 'request', 'operation')


def test_import_has_no_runtime_or_process_side_effect():
    code="import sys; import lia_lab.windows_launcher; assert 'torch' not in sys.modules; assert 'transformers' not in sys.modules"
    subprocess.run([sys.executable,'-c',code],check=True,timeout=10)


def test_worker_rejects_altered_launcher_before_grant_claim(snapshot,tmp_path,monkeypatch):
    from lia_lab.inference import make_operation
    from lia_lab import inference_worker as worker
    from lia_lab.io import load
    op=make_operation(*snapshot,'configs/inference-suite.json',tmp_path/'r',tmp_path/'a','fixture')
    r={k:op['arguments'][k] for k in ('snapshot','snapshot_manifest','device','dtype','repeats','max_tokens','context')}
    r.update(seed=42,snapshot_manifest_sha256=op['snapshot_manifest_sha256'],suite=load('configs/inference-suite.json'),
        containment=copy.deepcopy(op['containment']),memory_policy=op['memory_policy'],
        authorization=dict(operation=op,store='unused',id='unused'))
    r['containment']['windows_launcher']=w.contract(123)
    monkeypatch.setattr(worker,'claim_worker',lambda *a:pytest.fail('changed launcher reached claim'))
    with pytest.raises(LabError,match='binding'): worker.validate_worker_grant(r)


@pytest.mark.parametrize('mode',['missing','wrong-binding','active-descendant','cleanup-failed','association-denied'])
def test_pipeline_never_promotes_bad_launcher_report(snapshot,tmp_path,monkeypatch,mode):
    from lia_lab import inference
    from lia_lab.io import atomic_json, load, digest
    from lia_lab.memory_resources import loading_envelope
    from support_authorization import fixture_grant
    from support_environment import synthetic_launcher
    from test_supervisor_results import result_fixture
    from test_windows_memory import observation
    original_policy=inference.policy
    ceiling=loading_envelope(inference.checkpoint_capacity(snapshot[0]),'float32',load(snapshot[1])['total_bytes'])
    monkeypatch.setattr(inference,'policy',lambda *a:{**original_policy(*a),'windows_launcher':w.contract(ceiling)})
    env=inference.doctor();env['memory']=observation();env['dependencies'].update(torch='FAKE',transformers='FAKE')
    monkeypatch.setattr(inference,'doctor',lambda _:env)
    args=dict(snapshot=snapshot[0],snapshot_manifest=snapshot[1],suite_path='configs/inference-suite.json',
        research_root=tmp_path/'r',approved_root=tmp_path/'a',run_id='synthetic-launcher-protocol')
    op=inference.make_operation(**args)
    store,grant=fixture_grant(tmp_path/'operator/grants.db',op)
    def producer(command,env,log,timeout,**kwargs):
        context=kwargs['windows'];synthetic_launcher(context)
        if mode=='association-denied':
            context['report'].update(resumed=False,associated_before_resume=False,failure_stage='associate',
                failure='AssignProcessToJobObject: synthetic access denied',winerror=5)
            raise OSError(5,'synthetic association denied')
        request=load(command[-2]);request['_request_sha256']=digest(command[-2])
        from lia_lab.inference_worker import memory_preflight
        monkeypatch.setattr('lia_lab.inference_worker.observe',lambda:copy.deepcopy(request['memory_supervisor']))
        memory_preflight(request,command[-1],load(request['snapshot_manifest']))
        n=len(request['suite']['cases'])*request['repeats']
        atomic_json(command[-1],result_fixture(request,digest(command[-2]),n,completed=True))
        report=context['report']
        # A forged file cannot replace the supervisor's in-memory receipt.
        atomic_json(Path(command[-1]).parent/'windows-launcher.json',copy.deepcopy(report))
        if mode=='missing': report.clear()
        if mode=='wrong-binding': report['request_sha256']='wrong'
        if mode=='active-descendant': report['active_processes']=1
        if mode=='cleanup-failed': report['cleanup_complete']=False
        return 0
    from pathlib import Path
    monkeypatch.setattr(inference,'supervise',producer)
    result=inference.run_inference(**args,approval_store=store,approval_id=grant)
    assert result['status']==('blocked' if mode=='association-denied' else 'failed')
    if mode=='cleanup-failed': assert 'cleanup not confirmed' in result['failure']
