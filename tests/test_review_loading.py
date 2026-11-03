"""R2 doubles only: no Torch and no proof of real checkpoint compatibility."""
from support_environment import synthetic_ram
from copy import deepcopy
from types import SimpleNamespace
import math
import numpy as np
import pytest
from safetensors.numpy import save_file
from lia_lab.model_backends import load_model, select_backend, qwen3_shapes
from lia_lab.checkpoints import checkpoint_capacity
from lia_lab.io import LabError, load, atomic_json
from support_checkpoint import CONFIG, SHAPES


def stub(snapshot, report=None, mutate=None, tied=False):
    state = {name:SimpleNamespace(shape=shape) for name,shape in SHAPES.items()}
    if tied:
        cfg=load(snapshot[0]/'config.json');cfg['tie_word_embeddings']=True;atomic_json(snapshot[0]/'config.json',cfg)
        save_file({n:np.zeros(s,dtype=np.float32) for n,s in SHAPES.items() if n != 'lm_head.weight'}, snapshot[0]/'model.safetensors')
        state['lm_head.weight']=state['model.embed_tokens.weight']
    if mutate: mutate(state)
    model = type('Qwen3ForCausalLM',(),{'state_dict':lambda self,**kw:state,
            'config':SimpleNamespace(tie_word_embeddings=tied)})()
    calls=[]
    def loader(*args,**kwargs):
        calls.append(kwargs)
        return model, report if report is not None else dict(missing_keys=set(),unexpected_keys=set(),mismatched_keys=set(),error_msgs=[])
    tf=SimpleNamespace(AutoModelForCausalLM=SimpleNamespace(from_pretrained=loader))
    return tf,model,calls


def test_r2_complete_snapshot_and_report(snapshot):
    assert qwen3_shapes(CONFIG) == SHAPES  # independently handwritten expected map
    assert checkpoint_capacity(snapshot[0]) == sum(math.prod(s) for s in SHAPES.values())
    tf,model,calls=stub(snapshot)
    assert load_model(tf,snapshot[0],select_backend(CONFIG),'synthetic') is model
    assert calls[0]['output_loading_info'] is True and calls[0]['trust_remote_code'] is False


@pytest.mark.parametrize('field,value',[
    ('missing_keys',{'model.layers.0.self_attn.q_proj.weight'}),
    ('unexpected_keys',{'unrelated_tensor'}),
    ('mismatched_keys',{('model.norm.weight',(1,),(2,))}),
    ('error_msgs',['new parameter initialization failed']),
    ('conversion_errors',{'weight':'cannot convert'}),
    ('missing_keys',None),
])
def test_r2_loading_diagnostics_rejected(snapshot,field,value):
    report=dict(missing_keys=[],unexpected_keys=[],mismatched_keys=[],error_msgs=[]);report[field]=value
    tf,_,_=stub(snapshot,report)
    with pytest.raises(LabError):load_model(tf,snapshot[0],select_backend(CONFIG),'synthetic')


@pytest.mark.parametrize('change',['missing','unexpected','shape','unrelated'])
def test_r2_files_must_match_architecture_before_sizing(snapshot,change):
    tensors={name:np.zeros(shape,dtype=np.float32) for name,shape in SHAPES.items()}
    if change=='missing':tensors.pop('model.norm.weight')
    elif change=='unexpected':tensors['unrelated_tensor']=np.zeros((1,),dtype=np.float32)
    elif change=='shape':tensors['model.norm.weight']=np.zeros((3,),dtype=np.float32)
    else:tensors={'unrelated_tensor':np.zeros((1,),dtype=np.float32)}
    save_file(tensors,snapshot[0]/'model.safetensors')
    with pytest.raises(LabError,match='architecture'):checkpoint_capacity(snapshot[0])
    tf,_,_=stub(snapshot)
    with pytest.raises(LabError,match='materialized'):load_model(tf,snapshot[0],select_backend(CONFIG),'synthetic')


@pytest.mark.parametrize('change',['added-initialized','wrong-shape','absent-state'])
def test_r2_materialized_parameters_must_match_files_even_clean_report(snapshot,change):
    def mutate(state):
        if change=='added-initialized':state['randomly_initialized_weight']=SimpleNamespace(shape=(1,))
        elif change=='wrong-shape':state['model.norm.weight']=SimpleNamespace(shape=(3,))
        else:state.pop('model.norm.weight')
    tf,_,_=stub(snapshot,mutate=mutate)
    with pytest.raises(LabError,match='materialized'):load_model(tf,snapshot[0],select_backend(CONFIG),'synthetic')


@pytest.mark.parametrize('reported_missing',[[],['lm_head.weight']])
def test_r2_only_explicit_proven_qwen3_tied_alias_allowed(snapshot,reported_missing):
    report=dict(missing_keys=reported_missing,unexpected_keys=[],mismatched_keys=[],error_msgs=[])
    tf,model,_=stub(snapshot,report,tied=True)
    assert checkpoint_capacity(snapshot[0]) == sum(math.prod(s) for n,s in SHAPES.items() if n!='lm_head.weight')
    assert load_model(tf,snapshot[0],select_backend(CONFIG),'synthetic') is model


def test_r2_claimed_tie_without_parameter_identity_rejected(snapshot):
    tf,_,_=stub(snapshot,dict(missing_keys=['lm_head.weight'],unexpected_keys=[],mismatched_keys=[],error_msgs=[]),
                  tied=True,mutate=lambda state:state.update({'lm_head.weight':SimpleNamespace(shape=(3,2))}))
    with pytest.raises(LabError):load_model(tf,snapshot[0],select_backend(CONFIG),'synthetic')


@pytest.mark.parametrize('change',['missing-config','multimodal','bias','layers','bool-dimension'])
def test_r2_unknown_architecture_capacity_no_file_fallback(snapshot,change):
    cfg=deepcopy(CONFIG)
    if change=='missing-config':cfg.pop('head_dim')
    elif change=='multimodal':cfg={'model_type':'qwen3_5','architectures':['Qwen3_5ForConditionalGeneration']}
    elif change=='bias':cfg['attention_bias']=True
    elif change=='layers':cfg['num_hidden_layers']=1000000
    else:cfg['hidden_size']=True
    atomic_json(snapshot[0]/'config.json',cfg)
    assert checkpoint_capacity(snapshot[0]) is None


def test_r2_unknown_capacity_blocks_preflight(snapshot,tmp_path,monkeypatch):
    from lia_lab import inference
    from test_inference import run_fixture
    cfg=deepcopy(CONFIG);cfg.pop('head_dim');atomic_json(snapshot[0]/'config.json',cfg)
    # Reseal the intentionally unknown layout only as structural/operator fixture.
    from lia_lab.checkpoints import seal_snapshot
    snapshot[1].unlink()
    seal_snapshot(*snapshot,'fictional/fixture','a'*40,'Apache-2.0','LICENSE','FIXTURE-ONLY')
    env=inference.doctor();env['ram']['available_bytes']=10**12
    env['dependencies'].update(torch='stub-only',transformers='stub-only')
    monkeypatch.setattr(inference,'doctor',lambda _:synthetic_ram(env))
    monkeypatch.setattr(inference,'supervise',lambda *a:pytest.fail('unknown sizing launched worker'))
    result=run_fixture(snapshot,tmp_path)
    assert result['status']=='blocked' and result['estimated_host_ram_bytes'] is None
    assert any('capacity unknown' in b for b in result['blockers'])
