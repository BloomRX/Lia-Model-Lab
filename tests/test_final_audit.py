"""Regressions for concrete final-audit findings; synthetic files, no model execution."""
import copy
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import os
import numpy as np
import pytest
from safetensors.numpy import save_file
from lia_lab.io import LabError, atomic_json, load
from lia_lab import experiments, environment
from lia_lab.datasets import build_dataset
from lia_lab.checkpoints import files_at
from lia_lab.model_backends import select_backend
from lia_lab.inference_protocol import validate_suite, validate_worker_results
from test_foundation import plan, example, write_rows
from test_supervisor_results import result_fixture


def make_plan(tmp_path):
    source=tmp_path/'source.jsonl';write_rows(source,[example(i) for i in range(10)])
    build_dataset(source,tmp_path/'dataset')
    config=tmp_path/'plan.json';atomic_json(config,plan())
    return config


def test_concurrent_plan_reserves_id_once(tmp_path, monkeypatch):
    config=make_plan(tmp_path);barrier=Barrier(2)
    def fingerprint():
        barrier.wait(timeout=10)
        return 'a'*64
    monkeypatch.setattr(experiments,'source_snapshot_hash',fingerprint)
    def register(_):
        try:
            return experiments.register_plan(config,tmp_path/'research',tmp_path/'approved')['status']
        except LabError:
            return 'rejected'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(register,range(2)))==['planned','rejected']
    assert load(tmp_path/'research/experiments/fixture-plan/experiment.json')['status']=='planned'


def test_exclusive_atomic_publication(tmp_path):
    path=tmp_path/'artifact.json'
    def publish(i):
        try:
            atomic_json(path,{'producer':i},overwrite=False)
            return i
        except FileExistsError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        winners=[i for i in pool.map(publish,range(2)) if i is not None]
    assert len(winners)==1 and load(path)=={'producer':winners[0]}
    assert len(list(tmp_path.iterdir()))==1


def test_exclusive_publication_does_not_follow_dangling_symlink(tmp_path):
    target=tmp_path/'target.json';link=tmp_path/'link.json';link.symlink_to(target)
    with pytest.raises(FileExistsError):atomic_json(link,{},overwrite=False)
    assert link.is_symlink() and not target.exists()


def test_registration_rejects_input_change(tmp_path,monkeypatch):
    config=make_plan(tmp_path)
    real=experiments.verify_dataset
    def mutate(path):
        result=real(path);value=load(config);value['seed']=123;atomic_json(config,value)
        return result
    monkeypatch.setattr(experiments,'verify_dataset',mutate)
    with pytest.raises(LabError,match='changed'):experiments.register_plan(config,tmp_path/'research',tmp_path/'approved')
    assert not (tmp_path/'research').exists()


def test_dataset_verification_rechecks_bytes(tmp_path,monkeypatch):
    config=make_plan(tmp_path);real=experiments.read_examples
    def mutate(path):
        rows=real(path);path.write_text(path.read_text()+'\n');return rows
    monkeypatch.setattr(experiments,'read_examples',mutate)
    with pytest.raises(LabError,match='changed'):experiments.verify_dataset(tmp_path/'dataset/manifest.json')


def test_plan_target_modules_must_be_a_list():
    p=plan();p['training']['target_modules']='q_proj'
    with pytest.raises(LabError):experiments.validate_plan(p)


def test_multi_weight_snapshot_requires_index(snapshot):
    save_file({'other':np.zeros((1,),dtype=np.float32)},str(snapshot[0]/'other.safetensors'))
    with pytest.raises(LabError,match='shard index'):files_at(snapshot[0])


def test_special_file_snapshot_rejected(snapshot):
    if not hasattr(os,'mkfifo'):pytest.skip('POSIX FIFO unavailable')
    os.mkfifo(snapshot[0]/'pipe.txt')
    with pytest.raises(LabError,match='special files'):files_at(snapshot[0])


@pytest.mark.parametrize('config',[[],{'model_type':[]},{'model_type':'qwen3_5','architectures':['Qwen3_5ForConditionalGeneration'],'text_config':None}])
def test_malformed_model_config_fails_closed(config):
    with pytest.raises(LabError):select_backend(config)


def test_unknown_cgroup_layout_does_not_report_host_ram(tmp_path,monkeypatch):
    info=tmp_path/'meminfo';info.write_text('MemAvailable: 1000000 kB\nMemTotal: 2000000 kB\n')
    monkeypatch.setattr(environment,'Path',lambda path:info if path=='/proc/meminfo' else tmp_path/'absent')
    assert environment.memory()=={'total_bytes':None,'available_bytes':None}


@pytest.mark.parametrize('change',['not-object','case-type','capability','messages','expected-call','tool-schema'])
def test_malformed_suites_rejected_before_grant(change):
    suite=load('configs/inference-suite.json')
    if change=='not-object':suite=[]
    elif change=='case-type':suite['cases'][0]=[]
    elif change=='capability':suite['cases'][0].pop('capability')
    elif change=='messages':suite['cases'][0]['messages']=[]
    elif change=='expected-call':suite['cases'][-1].pop('expected_call')
    else:suite['cases'][-1]['tools'][0]['function']['parameters']={'type':'not-a-type'}
    with pytest.raises(LabError):validate_suite(suite)


@pytest.mark.parametrize('change',['metrics','nonfinite','ttft','count','containment','input','repeat','response-type'])
def test_completed_result_contract_rejects_incomplete_metrics(change):
    request={'repeats':2,'max_tokens':16,'context':128,'suite':load('configs/inference-suite.json'),
             'authorization':{'operation':{'model_id':'fictional/test','revision':'a'*40}},'containment':{'profile':'portable-process'}}
    data=result_fixture(request,'b'*64,10,True)
    if change=='metrics':data['metrics'].pop('runtime_import_seconds')
    elif change=='nonfinite':data['metrics']['frontend_load_seconds']=float('inf')
    elif change=='ttft':data['metrics']['ttft_seconds']=0.1
    elif change=='count':data['metrics']['total_requests']=True
    elif change=='containment':data['containment']={}
    elif change=='input':data['responses'][0]['input_tokens']=128
    elif change=='repeat':data['responses'][0]['repeat']=False
    else:data['responses'][0]=[]
    with pytest.raises(LabError):validate_worker_results(data,request,'b'*64,True)


@pytest.mark.parametrize('text',['{"value":1e999}','{"value":-1e999}'])
def test_json_overflow_is_not_finite(text):
    from lia_lab.io import json_loads
    with pytest.raises(LabError):json_loads(text)


@pytest.mark.parametrize('text',['value: .inf','value: .nan','value: [broken'])
def test_invalid_yaml_is_a_controlled_input_error(tmp_path,text):
    p=tmp_path/'input.yaml';p.write_text(text)
    with pytest.raises(LabError):load(p)


def test_snapshot_array_config_rejected(snapshot):
    atomic_json(snapshot[0]/'config.json',[])
    with pytest.raises(LabError):files_at(snapshot[0])


@pytest.mark.parametrize('reference',['https://untrusted.invalid/schema.json','file:///etc/passwd'])
@pytest.mark.parametrize('consumer',['suite','training'])
def test_tool_schemas_never_fetch_external_references(reference,consumer):
    from lia_lab.training_prep import hf_messages
    suite=load('configs/inference-suite.json')
    tool=suite['cases'][-1]['tools'][0]
    tool['function']['parameters']={'$ref':reference}
    with pytest.raises(LabError,match='external tool schema'):
        if consumer=='suite':validate_suite(suite)
        else:hf_messages({'messages':[{'role':'user','content':'fixture'},{'role':'assistant','content':'fixture'}]},[tool])


def test_local_schema_references_remain_supported():
    from lia_lab.training_prep import validate_tool_arguments
    validate_tool_arguments({'$defs':{'arg':{'type':'integer'}},'$ref':'#/$defs/arg'},1)
    with pytest.raises(LabError,match='local tool schema'):
        validate_tool_arguments({'$ref':'#/$defs/missing'},1)
