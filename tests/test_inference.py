"""Offline contracts only: tiny zero tensors are NOT a language model checkpoint."""
import copy
import json
import subprocess
from pathlib import Path
import numpy as np
import pytest
from safetensors.numpy import save_file
from lia_lab.checkpoints import seal_snapshot, verify_snapshot
from lia_lab.environment import doctor
from lia_lab.inference import run_inference, validate_options
from lia_lab.inference_protocol import validate_suite, check_output
from lia_lab.io import LabError, atomic_json, load
from lia_lab.training_prep import hf_messages, render_sft_example
from lia_lab.cli import main




def test_environment_is_weight_free():
    report = doctor()
    assert report['gpu_runtime_verified'] is False
    assert report['ram']['total_bytes'] is None or report['ram']['total_bytes'] > 0
    assert report['disk_free_bytes'] >= 0


def test_snapshot_inventory(snapshot):
    directory, manifest = snapshot
    result = verify_snapshot(directory, manifest)
    assert result['stored_tensor_elements'] == 6
    assert result['release_approved'] is False
    assert 'attestation' in result['evidence']


@pytest.mark.parametrize('change', ['weight', 'extra', 'missing', 'license', 'revision', 'manifest-size'])
def test_snapshot_tamper(snapshot, change):
    directory, manifest = snapshot
    if change == 'weight':
        (directory / 'model.safetensors').write_bytes(b'corrupt')
    elif change == 'extra':
        (directory / 'custom.py').write_text('raise Exception("must never execute")')
    elif change == 'missing':
        (directory / 'config.json').unlink()
    elif change == 'license':
        data = load(manifest); data['license']['id'] = 'unknown'; atomic_json(manifest, data)
    elif change == 'revision':
        data = load(manifest); data['revision'] = 'main'; atomic_json(manifest, data)
    else:
        data = load(manifest); data['total_bytes'] += 1; atomic_json(manifest, data)
    with pytest.raises(Exception):
        verify_snapshot(directory, manifest)


def test_symlink_rejected(snapshot, tmp_path):
    directory, manifest = snapshot
    (directory / 'external.txt').symlink_to(manifest)
    with pytest.raises(LabError, match='symlink'):
        verify_snapshot(directory, manifest)


def test_root_symlink_rejected(snapshot, tmp_path):
    directory, manifest = snapshot
    link = tmp_path / 'linked'; link.symlink_to(directory, target_is_directory=True)
    with pytest.raises(LabError, match='symlink'):
        seal_snapshot(link, tmp_path / 'new.json', 'fictional/fixture', 'a'*40, 'Apache-2.0', 'LICENSE', 'test')


def test_bad_shard_index(snapshot):
    directory, manifest = snapshot
    atomic_json(directory / 'model.safetensors.index.json', {'weight_map': {'other': 'model.safetensors'}})
    with pytest.raises(LabError, match='index'):
        verify_snapshot(directory, manifest)


@pytest.mark.parametrize('revision,license_id,ref', [('main','Apache-2.0','test'),('a'*40,'restrictive','test'),('a'*40,'Apache-2.0','PENDING')])
def test_seal_review_gate(snapshot, tmp_path, revision, license_id, ref):
    with pytest.raises(LabError):
        seal_snapshot(snapshot[0], tmp_path / 'bad.json', 'fictional/fixture', revision, license_id, 'LICENSE', ref)


def test_no_overwrite(snapshot):
    directory, manifest = snapshot
    with pytest.raises(LabError, match='new'):
        seal_snapshot(directory, manifest, 'fictional/fixture', 'a'*40, 'Apache-2.0', 'LICENSE', 'test')


def test_suite_and_output_contract():
    suite = validate_suite(load('configs/inference-suite.json'))
    assert len(suite['cases']) == 5
    assert check_output(suite['cases'][0], 'texto')['passed'] is None
    assert check_output(suite['cases'][1], 'PONTE-47')['passed'] is True
    assert check_output(suite['cases'][1], 'PONTE-47 extra')['passed'] is False
    assert check_output(suite['cases'][2], '{"livros":7,"cidade":"Recife"}')['passed'] is True
    assert check_output(suite['cases'][2], '```json\n{}\n```')['passed'] is False
    call = '<tool_call>{"name":"consultar_estante","arguments":{"codigo":"LIV-27"}}</tool_call>'
    assert check_output(suite['cases'][4], call)['passed'] is True
    assert check_output(suite['cases'][4], call+call)['passed'] is False
    assert check_output(suite['cases'][4], 'I executed a tool')['passed'] is False


@pytest.mark.parametrize('change', ['duplicate', 'unknown-check', 'size', 'role'])
def test_invalid_suite(change):
    suite = load('configs/inference-suite.json')
    if change == 'duplicate': suite['cases'].append(suite['cases'][0])
    if change == 'unknown-check': suite['cases'][0]['check'] = 'execute-shell'
    if change == 'size': suite['cases'][0]['messages'][0]['content'] = 'x'*4001
    if change == 'role': suite['cases'][0]['messages'][-1]['role'] = 'tool'
    with pytest.raises(LabError): validate_suite(suite)


@pytest.mark.parametrize('options', [('cpu','float16',2,128,2048,600),('cuda','float32',1,128,2048,600),('cpu','float32',2,512,128,600),('cpu','float32',2,128,2048,0)])
def test_invalid_budgets(options):
    with pytest.raises(LabError): validate_options(*options)


def run_fixture(snapshot, tmp_path, run_id='unit-fixture', **options):
    from lia_lab.inference import make_operation
    from support_authorization import fixture_grant
    args = dict(snapshot=snapshot[0], snapshot_manifest=snapshot[1], suite_path='configs/inference-suite.json',
        research_root=tmp_path/'research', approved_root=tmp_path/'approved', run_id=run_id, **options)
    if (tmp_path/'research/experiments'/run_id).exists():
        return run_inference(**args, approval_store=tmp_path/'operator/grants.db', approval_id='used-fixture')
    operation = make_operation(**args)
    store, grant_id = fixture_grant(tmp_path/'operator/grants.db', operation)
    return run_inference(**args, approval_store=store, approval_id=grant_id)


def test_uninstalled_runtime_blocks_and_records(snapshot, tmp_path, monkeypatch):
    from lia_lab import inference
    real = doctor()
    real['dependencies']['torch'] = None
    monkeypatch.setattr(inference, 'doctor', lambda _: real)
    result = run_fixture(snapshot, tmp_path)
    assert result['status'] == 'blocked' and result['inference_executed'] is False
    assert result['model_metrics'] is None
    assert result['actual_duration_seconds'] >= 0
    assert load(tmp_path/'research/experiments/unit-fixture/experiment.json')['status'] == 'blocked'
    assert not (tmp_path/'approved').exists()
    with pytest.raises(FileExistsError): run_fixture(snapshot, tmp_path)


def test_snapshot_failure_is_recorded(snapshot, tmp_path):
    (snapshot[0]/'model.safetensors').write_bytes(b'invalid')
    with pytest.raises(LabError): run_fixture(snapshot, tmp_path)
    assert not (tmp_path/'research').exists()


def test_memory_block(snapshot, tmp_path, monkeypatch):
    from lia_lab import inference
    real = doctor(); real['ram']['available_bytes'] = 1
    monkeypatch.setattr(inference, 'doctor', lambda _: real)
    result = run_fixture(snapshot, tmp_path)
    assert any('RAM' in b for b in result['blockers'])


def test_timeout_never_promotes(snapshot, tmp_path, monkeypatch):
    from lia_lab import inference
    real = doctor(); real['ram']['available_bytes'] = 10**12
    real['dependencies'].update(torch='synthetic-version', transformers='synthetic-version')
    monkeypatch.setattr(inference, 'doctor', lambda _: real)
    def timeout(command, env, log, duration):
        assert env['HF_HUB_OFFLINE'] == '1'
        assert 0 < duration <= 1
        raise subprocess.TimeoutExpired('synthetic-unit-test', duration)
    monkeypatch.setattr(inference, 'supervise', timeout)
    result = run_fixture(snapshot, tmp_path, timeout=1)
    assert result['status'] == 'timed-out' and result['inference_executed'] is False
    assert 'deadline' in result['failure']
    assert result['model_metrics'] is None


def test_roots_and_approval(snapshot, tmp_path):
    with pytest.raises(LabError):
        run_inference(*snapshot, 'configs/inference-suite.json', tmp_path, tmp_path/'application', 'fixture',tmp_path/'operator/grants.db','test')
    with pytest.raises(LabError):
        run_inference(*snapshot, 'configs/inference-suite.json', tmp_path/'r', tmp_path/'a', 'fixture',tmp_path/'operator/grants.db','PENDING')


class SyntheticTokenizer:
    """Mask-contract unit fixture. Does not implement a real tokenizer/template."""
    chat_template = '{% generation %}synthetic{% endgeneration %}'
    def apply_chat_template(self, *args, **kwargs):
        assert kwargs['return_assistant_tokens_mask'] is True
        assert kwargs['truncation'] is False
        messages=args[0]
        return {'input_ids':list(range(1,len(messages)*2+1)), 'assistant_masks':[v for m in messages for v in ([1,1] if m['role']=='assistant' else [0,0])]}


def test_sft_mask_contract():
    row = {'messages': [{'role':'user','content':'a'}, {'role':'assistant','content':'b'}]}
    result = render_sft_example(row, SyntheticTokenizer())
    assert result['labels'] == [-100, -100, 3, 4]
    tokenizer = SyntheticTokenizer(); tokenizer.chat_template = 'native without spans'
    tokenizer.apply_chat_template=lambda *a, **k: {'input_ids':[1,2,3,4],'assistant_masks':[0,0,0,0]}
    with pytest.raises(LabError, match='empty'): render_sft_example(row, tokenizer)


def test_invalid_sft_masks():
    row = {'messages': [{'role':'user','content':'a'}, {'role':'assistant','content':'b'}]}
    for mask in ([], [0,0,0], [1,1,1], [0,2,1], [0,1]):
        tokenizer = SyntheticTokenizer()
        tokenizer.apply_chat_template = lambda *a, **k: {'input_ids':[1,2,3],'assistant_masks':mask}
        with pytest.raises(LabError): render_sft_example(row, tokenizer)


def test_tool_translation():
    row = {'messages': [{'role':'assistant','tool_calls':[{'id':'a','name':'lookup','arguments':{'id':7}}]},
                        {'role':'tool','tool_call_id':'a','content':'fictional'}]}
    with pytest.raises(LabError, match='schema'): hf_messages(row)
    converted = hf_messages(row,[{'type':'function','function':{'name':'lookup','parameters':{'type':'object','properties':{'id':{'type':'integer'}},'required':['id']}}}])
    assert converted[0]['tool_calls'][0]['function']['arguments'] == {'id':7}
    assert converted[1]['name'] == 'lookup'
    assert row['messages'][0]['tool_calls'][0]['name'] == 'lookup'  # no mutation


def test_cli_doctor(capsys):
    assert main(['doctor']) == 0
    assert json.loads(capsys.readouterr().out)['evidence'] == 'observed-environment-not-inference'


def test_evaluation_prompt_leakage():
    from lia_lab.training_prep import assert_no_suite_overlap
    suite = load('configs/inference-suite.json')
    examples = [{'messages': [{'role':'user','content':'original unrelated training prompt'}]}]
    assert assert_no_suite_overlap(examples, suite)['semantic_decontamination'] is False
    examples[0]['messages'][0]['content'] = suite['cases'][1]['messages'][0]['content'].replace(' ', '  ')
    with pytest.raises(LabError, match='leaked'): assert_no_suite_overlap(examples, suite)


def test_json_duplicate_keys_are_not_a_pass():
    case = load('configs/inference-suite.json')['cases'][2]
    assert check_output(case, '{"livros":0,"livros":7,"cidade":"Recife"}')['passed'] is False


def test_prequantized_model_is_not_silently_loaded(snapshot):
    directory, manifest = snapshot
    atomic_json(directory / 'config.json', {'model_type':'qwen3','quantization_config':{'quant_method':'bitsandbytes'}})
    with pytest.raises(LabError, match='prequantized'): verify_snapshot(directory, manifest)


def test_private_worker_rejects_missing_external_grant(snapshot, tmp_path):
    import os, sys
    # Only run this dependency-negative test when Torch really is absent; never instantiate a fake giant config.
    if doctor()['dependencies']['torch'] is not None:
        pytest.skip('requires actually missing optional Torch runtime')
    request = tmp_path/'request.json'
    from lia_lab.containment import policy
    from lia_lab.io import digest
    atomic_json(request, {'snapshot':str(snapshot[0]), 'snapshot_manifest':str(snapshot[1]),
        'snapshot_manifest_sha256':digest(snapshot[1]), 'containment':policy('portable-process',10,'cpu')})
    output = tmp_path/'results.json'
    env = dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    result = subprocess.run([sys.executable,'-m','lia_lab.inference_worker',str(request),str(output)],
                            capture_output=True, text=True, env=env, timeout=10)
    assert result.returncode != 0 and 'external worker grant required' in result.stderr
    assert not output.exists()


@pytest.mark.parametrize('field,value', [('release_approved',True),('stored_tensor_elements',True),('revision','main')])
def test_snapshot_schema_cannot_promote_or_invent_types(snapshot, field, value):
    data = load(snapshot[1]); data[field] = value; atomic_json(snapshot[1],data)
    with pytest.raises(LabError, match='schema'): verify_snapshot(*snapshot)


def test_actual_worker_missing_torch_with_fixture_grant(snapshot,tmp_path,monkeypatch):
    from lia_lab import inference
    if doctor()['dependencies']['torch'] is not None:
        pytest.skip('negative test requires actually missing Torch')
    report=doctor();report['dependencies'].update(torch='synthetic-preflight-only',transformers='synthetic-preflight-only')
    report['ram']['available_bytes']=10**12
    monkeypatch.setattr(inference,'doctor',lambda _:report)
    result=run_fixture(snapshot,tmp_path)
    assert result['status']=='failed' and result['inference_executed'] is False
    log=(tmp_path/'research/experiments/unit-fixture/worker.log').read_text()
    assert "No module named 'torch'" in log
    assert result['containment']['security_sandbox'] is False
