"""Offline architecture evidence: synthetic tiny tensors, never real model loading."""
from copy import deepcopy
import math
import pytest
from lia_lab import qwen35_contract as q
from lia_lab.checkpoints import checkpoint_capacity, tensor_inventory
from lia_lab.io import atomic_json, load, LabError
from support_qwen35 import official_config, snapshot, write_zero_shard, write_index


def test_official_fixed_config_equations_cover_text_vision_mtp():
    shapes=q.shapes(official_config())
    assert shapes is not None and len(shapes)==488
    assert sum(math.prod(s) for s in shapes.values())==873438784
    assert sum(math.prod(s) for n,s in shapes.items() if n.startswith('mtp.'))==20452864
    assert len([n for n in shapes if n.startswith('model.visual.')])==153
    assert len([n for n in shapes if q.dtype_for(n)=='F32'])==36
    assert shapes['model.language_model.layers.3.self_attn.q_proj.weight']==(4096,1024)
    assert shapes['model.visual.patch_embed.proj.weight']==(768,3,2,16,16)


@pytest.mark.parametrize('change',['no-vision','wrong-model','wrong-class','extra','dtype','bias','layers','tie','missing'])
def test_unrecognized_configuration_is_not_given_file_sizing(change):
    c=official_config()
    if change=='no-vision':c.pop('vision_config')
    elif change=='wrong-model':c['model_type']='qwen3_5_text'
    elif change=='wrong-class':c['architectures']=['Unknown']
    elif change=='extra':c['auto_map']={'AutoModel':'remote.Code'}
    elif change=='dtype':c['text_config']['dtype']='float32'
    elif change=='bias':c['text_config']['attention_bias']=True
    elif change=='layers':c['text_config']['num_hidden_layers']=True
    elif change=='tie':c['tie_word_embeddings']=False
    else:c['text_config'].pop('linear_key_head_dim')
    assert q.shapes(c) is None


def test_tiny_shape_dtype_and_index_contract(tmp_path,monkeypatch):
    root=tmp_path/'tiny';c,shapes=snapshot(root,monkeypatch)
    assert checkpoint_capacity(root)==sum(math.prod(s) for s in shapes.values())
    assert tensor_inventory(root)['mtp.fc.weight']['dtype']=='BF16'
    assert shapes['model.language_model.layers.0.linear_attn.conv1d.weight']==(6,1,2)
    assert shapes['model.visual.merger.linear_fc2.weight']==(8,4)


@pytest.mark.parametrize('change',['missing','unexpected','shape','dtype','duplicate','index','index-size','unknown-mtp'])
def test_corrupt_snapshot_rejected_before_runtime(tmp_path,monkeypatch,change):
    root=tmp_path/'tiny';c,shapes=snapshot(root,monkeypatch);changed=deepcopy(shapes);dtypes={}
    if change=='missing':changed.pop('model.visual.pos_embed.weight')
    elif change=='unexpected':changed['unknown.weight']=(1,)
    elif change=='unknown-mtp':changed['mtp.unknown.weight']=(1,)
    elif change=='shape':changed['mtp.fc.weight']=(1,1)
    elif change=='dtype':dtypes['mtp.fc.weight']='F32'
    elif change=='duplicate':write_zero_shard(root/'duplicate.safetensors',{'mtp.fc.weight':shapes['mtp.fc.weight']})
    elif change=='index':
        index=load(root/'model.safetensors.index.json');index['weight_map']['mtp.fc.weight']='missing.safetensors';atomic_json(root/'model.safetensors.index.json',index)
    elif change=='index-size':
        index=load(root/'model.safetensors.index.json');index['metadata']['total_size']+=1;atomic_json(root/'model.safetensors.index.json',index)
    if change in {'missing','unexpected','unknown-mtp','shape','dtype'}:
        write_zero_shard(root/'model.safetensors',changed,dtypes)
    with pytest.raises(LabError):checkpoint_capacity(root)


def test_runtime_fingerprint_is_bound_without_importing_torch(snapshot,tmp_path,monkeypatch):
    from lia_lab.inference import make_operation
    from lia_lab import inference_worker as worker
    op=make_operation(*snapshot,'configs/inference-suite.json',tmp_path/'r',tmp_path/'a','fixture')
    r={k:op['arguments'][k] for k in ('snapshot','snapshot_manifest','device','dtype','repeats','max_tokens','context')}
    r.update(seed=42,snapshot_manifest_sha256=op['snapshot_manifest_sha256'],suite=load('configs/inference-suite.json'),
        containment=op['containment'],memory_policy=op['memory_policy'],authorization={'operation':op,'store':'unused','id':'unused'})
    monkeypatch.setattr(worker,'fingerprint',lambda:{'different':'runtime'})
    monkeypatch.setattr(worker,'claim_worker',lambda *a:pytest.fail('changed runtime reached grant'))
    with pytest.raises(LabError,match='binding'):worker.validate_worker_grant(r)


def test_sealed_synthetic_payload_tamper_rejected(tmp_path,monkeypatch):
    from lia_lab.checkpoints import seal_snapshot,verify_snapshot
    root=tmp_path/'tiny';snapshot(root,monkeypatch)
    manifest=tmp_path/'fixture-manifest.json'
    seal_snapshot(root,manifest,'fictional/qwen35-shape-fixture','a'*40,'Apache-2.0','LICENSE','TEST-SYNTHETIC-NOT-A-REAL-REVIEW')
    assert verify_snapshot(root,manifest)['release_approved'] is False
    path=root/'model.safetensors';data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data)
    with pytest.raises(LabError,match='mismatch'):verify_snapshot(root,manifest)


@pytest.mark.parametrize('template',[None,{}, {'tool_use':'named-only'},' '])
def test_processor_native_default_template_required(template):
    from types import SimpleNamespace
    from lia_lab.model_backends import select_backend,native_chat_template
    with pytest.raises(LabError,match='template'):
        native_chat_template(select_backend(official_config()),SimpleNamespace(chat_template=template))
