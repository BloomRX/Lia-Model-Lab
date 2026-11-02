"""Synthetic producer stubs test only supervisor protocol/status transitions; NO inference."""
import copy
import json
import subprocess
import pytest
from lia_lab import inference
from lia_lab.io import atomic_json,load,digest
from lia_lab.environment import doctor
from lia_lab.authorization import claim_worker
from support_authorization import fixture_grant


@pytest.fixture
def run_setup(snapshot,tmp_path,monkeypatch):
    args=dict(snapshot=snapshot[0],snapshot_manifest=snapshot[1],suite_path='configs/inference-suite.json',
        research_root=tmp_path/'research',approved_root=tmp_path/'approved',run_id='synthetic-protocol-only')
    op=inference.make_operation(**args)
    store,grant=fixture_grant(tmp_path/'operator/grants.db',op)
    env=doctor();env['dependencies'].update(torch='FAKE-PREFLIGHT',transformers='FAKE-PREFLIGHT');env['ram']['available_bytes']=10**12
    monkeypatch.setattr(inference,'doctor',lambda _:env)
    return dict(**args,approval_store=store,approval_id=grant),tmp_path/'research/experiments/synthetic-protocol-only'


def result_fixture(request,request_hash,n,completed=False):
    # Explicitly fabricated metrics, used only in temp unit-test files.
    responses=[]
    for repeat in range(request['repeats']):
        for c in request['suite']['cases']:
            responses.append(dict(id=c['id'],repeat=repeat,capability=c['capability'],text='SYNTHETIC',
                input_tokens=1,output_tokens_including_eos=1,generation_seconds_including_prefill=0.01,generation_process_cpu_seconds=0.01))
    op=request['authorization']['operation']
    return dict(schema_version=2,completed=completed,evidence='real-local-checkpoint-inference',
        request_sha256=request_hash,model_id=op['model_id'],revision=op['revision'],
        successful_requests=n,generation_calls_completed=n,responses=responses[:n],metrics={'SYNTHETIC':True,'runtime_import_seconds':0.01,'frontend_load_seconds':0.01,
        'weights_load_and_device_transfer_seconds':0.01,'prefill_seconds':None,'ttft_seconds':None,
        'decode_only_tokens_per_second':None,'total_requests':n},containment=request['containment'])


@pytest.mark.parametrize('mode',['completed','incomplete','failed-partial','timeout-partial','interrupted-partial','corrupt-list','corrupt-json','wrong-hash','empty','wrong-model','wrong-order'])
def test_result_state_machine_is_structural_only(run_setup,monkeypatch,mode):
    args,path=run_setup
    def producer(command,env,log,timeout):
        request_file=path/'request.json';r=load(request_file)
        claim_worker(r['authorization']['store'],r['authorization']['id'],r['authorization']['operation'])
        n=len(r['suite']['cases'])*r['repeats'] if mode=='completed' else 1
        data=result_fixture(r,digest(request_file),n,completed=mode=='completed')
        if mode=='wrong-hash':data['request_sha256']='0'*64
        if mode=='wrong-model':data['model_id']='other/model'
        if mode=='empty':data['responses'][0]['text']=''
        if mode=='wrong-order':data['responses'][0]['repeat']=3
        if mode=='corrupt-list':data=[]
        atomic_json(path/'results.json',data)
        if mode=='corrupt-json':(path/'results.json').write_text('broken')
        if mode=='timeout-partial':raise subprocess.TimeoutExpired('fake',1)
        if mode=='interrupted-partial':raise KeyboardInterrupt
        return 1 if mode=='failed-partial' else 0
    monkeypatch.setattr(inference,'supervise',producer)
    record=inference.run_inference(**args)
    if mode=='completed':assert record['status']=='completed-not-quality-approved'
    elif mode=='timeout-partial':assert record['status']=='timed-out'
    elif mode=='interrupted-partial':assert record['status']=='interrupted'
    else:assert record['status']=='failed'
    if mode in {'failed-partial','timeout-partial','interrupted-partial','incomplete'}:
        assert record['partial_requests']==1 and record['evidence'].startswith('partial-')
    elif mode!='completed':assert record['inference_executed'] is False
    assert record['release_approved'] is False
    with pytest.raises(FileExistsError):inference.run_inference(**args)
