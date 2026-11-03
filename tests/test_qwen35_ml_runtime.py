"""Opt-in local CPU runtime conformance. Synthetic weights / real metadata only.

No original pretrained weight loading or generation here; no operational grants.
Run only in the separately installed ML venv, with library offline mode.
"""
import os
from pathlib import Path
import pytest
if os.environ.get('LIA_TEST_ML_RUNTIME') != '1':
    pytest.skip('opt-in Windows CPU ML runtime; base/API CI must not install Torch',allow_module_level=True)
torch=pytest.importorskip('torch')
transformers=pytest.importorskip('transformers')
from lia_lab.model_backends import load_model, select_backend, prepare_inputs
from lia_lab.io import LabError, load
from lia_lab import qwen35_contract as q
from support_qwen35 import snapshot


def test_real_pinned_cpu_libraries_and_synthetic_full_state(tmp_path,monkeypatch):
    assert torch.__version__=='2.14.0+cpu' and torch.version.cuda is None and torch.version.hip is None
    assert transformers.__version__=='5.22.1'
    root=tmp_path/'tiny';c,shapes=snapshot(root,monkeypatch)
    # One authored nonzero BF16 scalar proves MTP values are read, not invented.
    import struct,json
    with (root/'model.safetensors').open('r+b') as stream:
        length=struct.unpack('<Q',stream.read(8))[0];header=json.loads(stream.read(length))
        stream.seek(8+length+header['mtp.fc.weight']['data_offsets'][0]);stream.write(b'\x80\x3f')
    model=load_model(transformers,root,select_backend(c),torch.float32)
    assert type(model).__name__=='Qwen3_5ForConditionalGeneration'
    assert type(model).__module__=='transformers.models.qwen3_5.modeling_qwen3_5'
    state=model.state_dict(keep_vars=True)
    assert state['lm_head.weight'] is state['model.language_model.embed_tokens.weight']
    assert {k:tuple(v.shape) for k,v in state.items() if k!='lm_head.weight'}==shapes
    assert all(p.dtype==torch.float32 for p in state.values())
    assert all(not p.requires_grad for p in model.mtp.parameters())
    assert state['mtp.fc.weight'].flatten()[0].item()==1.0
    assert model._lia_loading_audit['auxiliary_mtp_tensors_preserved']==15
    assert model._lia_loading_audit['mtp_generation_enabled'] is False


def test_real_parameter_identity_is_required_for_tied_alias(tmp_path,monkeypatch):
    root=tmp_path/'tiny';c,shapes=snapshot(root,monkeypatch)
    cfg=transformers.AutoConfig.from_pretrained(root,local_files_only=True,trust_remote_code=False)
    model=transformers.AutoModelForMultimodalLM.from_config(cfg,attn_implementation='eager')
    model.lm_head.weight=torch.nn.Parameter(model.model.language_model.embed_tokens.weight.clone())
    monkeypatch.setattr(transformers.AutoModelForMultimodalLM,'from_pretrained',lambda *a,**k:(model,
        dict(missing_keys=[],unexpected_keys=[],mismatched_keys=[],error_msgs=[])))
    with pytest.raises(LabError,match='materialized'):load_model(transformers,root,select_backend(c),torch.float32)


@pytest.fixture
def official_root():
    value=os.environ.get('LIA_QWEN35_SNAPSHOT')
    if not value:pytest.skip('requires an explicitly selected already-acquired official snapshot (metadata only)')
    root=Path(value)
    assert root.name==q.MODEL_REVISION
    return root


def test_real_offline_processor_and_native_template(official_root):
    frontend=transformers.AutoProcessor.from_pretrained(official_root,local_files_only=True,trust_remote_code=False)
    assert type(frontend).__name__=='Qwen3VLProcessor'
    assert type(frontend.tokenizer).__name__=='Qwen3_5Tokenizer'
    spec=select_backend(load(official_root/'config.json'))
    for case in load('configs/inference-suite.json')['cases']:
        inputs,template=prepare_inputs(spec,frontend,case)
        assert inputs['input_ids'].shape[0]==1 and inputs['input_ids'].shape[1]+128<=2048
        assert isinstance(template,str) and template


def test_real_full_config_meta_architecture_without_pretrained_allocation(official_root):
    raw=load(official_root/'config.json');expected=q.shapes(raw)
    cfg=transformers.AutoConfig.from_pretrained(official_root,local_files_only=True,trust_remote_code=False)
    assert cfg.vision_config.model_type=='qwen3_5_vision'  # official normalization of the legacy config label
    with torch.device('meta'):
        model=transformers.AutoModelForMultimodalLM.from_config(cfg,attn_implementation='eager')
    state=model.state_dict(keep_vars=True)
    assert all(p.device.type=='meta' for p in state.values())
    assert state['lm_head.weight'] is state['model.language_model.embed_tokens.weight']
    assert {k:tuple(v.shape) for k,v in state.items() if k!='lm_head.weight'}=={
        k:v for k,v in expected.items() if not k.startswith('mtp.')}
