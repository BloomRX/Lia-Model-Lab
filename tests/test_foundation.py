import copy
import json
from pathlib import Path
import numpy as np
import pytest
from safetensors.numpy import save_file
from lia_lab.io import LabError, load, json_loads, canonical, digest, roots, owned, atomic_json
from lia_lab.datasets import validate_example, read_examples, prepare, build_dataset
from lia_lab.experiments import validate_plan, register_plan, verify_dataset, verify_resume, inspect_adapter, export_adapter
from lia_lab.evaluation import compare
from lia_lab.cli import main


def example(i=0, group=None):
    return {"schema_version": 1, "id": f"fixture-{i}", "group_id": group or f"conversation-{i}",
            "language": "pt-BR", "capabilities": ["conversation"],
            "provenance": {"source": "original-test-fixture", "revision": "v1", "license": "CC0-1.0",
                           "rights_reviewed": True, "synthetic": True, "generator": "handwritten-test"},
            "privacy": {"classification": "fictional", "reviewed": True},
            "messages": [{"role": "user", "content": f"Qual o número de teste {i}?"},
                         {"role": "assistant", "content": str(i)}]}


def plan():
    return {"schema_version": 1, "experiment_id": "fixture-plan", "status": "planned",
            "base": {"model_id": "fictional/test", "revision": "a"*40, "tokenizer_revision": "a"*40,
                     "weights_sha256": "b"*64, "chat_template_sha256": "c"*64, "license_review_ref": "fixture-only"},
            "dataset_manifest": "dataset/manifest.json", "seed": 42,
            "training": {"method": "sft", "adapter": "qlora", "rank": 8, "alpha": 16,
                         "max_seq_length": 512, "microbatch": 1, "gradient_accumulation": 4,
                         "max_steps": 10, "save_steps": 5, "learning_rate": 0.0001,
                         "compute_dtype": "bfloat16", "target_modules": ["q_proj"],
                         "quantization": "nf4-double-quant"},
            "environment": {"python": "3.11.2", "dependencies": {"peft": "0.18.0", "transformers": "5.0.0", "torch": "2.9.0", "trl": "0.25.0"},
                            "hardware": "fixture-no-gpu", "backend": "cpu", "driver": "none"},
            "budget": {"max_hours": 0, "max_cost": 0, "currency": "BRL"}, "authorization_ref": None}


def write_rows(path, rows):
    path.write_text("".join(canonical(r)+"\n" for r in rows))


@pytest.mark.parametrize("value", ['{"a":1,"a":2}', '{"x":NaN}'])
def test_strict_json(value):
    with pytest.raises(ValueError): json_loads(value)


def test_yaml_duplicate(tmp_path):
    p=tmp_path/'x.yaml'; p.write_text('a: 1\na: 2\n')
    with pytest.raises(ValueError): load(p)


@pytest.mark.parametrize("mutate", [
    lambda r: r.update(extra=True),
    lambda r: r['provenance'].update(license='PENDING'),
    lambda r: r['provenance'].pop('generator'),
    lambda r: r['privacy'].update(classification='consented'),
    lambda r: r['messages'].append({'role':'tool','content':'x','tool_call_id':'absent'}),
    lambda r: r['messages'][-1].update(tool_calls=[{'id':'a','name':'x','arguments':{}}]),
])
def test_bad_examples(mutate):
    r=example(); mutate(r)
    with pytest.raises(ValueError): validate_example(r)


def test_tool_trajectory():
    r=example(); r['messages']=[r['messages'][0], {'role':'assistant','tool_calls':[{'id':'1','name':'inventory','arguments':{}}]},
        {'role':'tool','tool_call_id':'1','content':'3'}, {'role':'assistant','content':'Há três unidades.'}]
    assert validate_example(r)==r
    r['messages'].insert(2,{'role':'assistant','content':'Não esperei.'})
    with pytest.raises(ValueError): validate_example(r)


def test_dedup_linkage_and_determinism():
    rows=[example(i) for i in range(12)]
    dup=copy.deepcopy(rows[0]); dup.update(id='duplicate', group_id=rows[1]['group_id']); rows.append(dup)
    splits, report=prepare(rows)
    assert report['removed_duplicate_ids'] and sum(map(len,splits.values()))==12
    assert report['lineage']['conversation-0']==report['lineage']['conversation-1']
    assert prepare(list(reversed(rows)))==(splits,report)
    seen=set()
    for values in splits.values():
        groups={report['lineage'][r['group_id']] for r in values}; assert not seen&groups; seen|=groups


def test_small_and_bad_ratios():
    with pytest.raises(ValueError): prepare([example(0),example(1)])
    with pytest.raises(ValueError): prepare([example(i) for i in range(4)],ratios=(1,0,0))


def test_factory_and_tampering(tmp_path):
    source=tmp_path/'input.jsonl'; write_rows(source,[example(i) for i in range(12)])
    out=tmp_path/'dataset'; m=build_dataset(source,out)
    assert verify_dataset(out/'manifest.json')==m
    with pytest.raises(ValueError): build_dataset(source,out)
    with (out/'test.jsonl').open('a') as f: f.write('\n')
    with pytest.raises(ValueError): verify_dataset(out/'manifest.json')


def test_jsonl_limits_duplicates(tmp_path):
    p=tmp_path/'x.jsonl'; write_rows(p,[example(),example()])
    with pytest.raises(ValueError): read_examples(p)
    with pytest.raises(ValueError): read_examples(p,max_bytes=1)
    p.write_text('')
    with pytest.raises(ValueError): read_examples(p)


@pytest.mark.parametrize('bad', ['../escape','/etc/passwd'])
def test_paths(tmp_path,bad):
    with pytest.raises(ValueError): owned(tmp_path,bad)
    with pytest.raises(ValueError): roots(tmp_path,tmp_path/'approved')


@pytest.mark.parametrize('mutate', [
    lambda c:c['base'].update(revision='main'), lambda c:c['training'].update(rank=0),
    lambda c:c['training'].update(quantization='gguf'), lambda c:c['environment'].update(backend='vulkan'),
    lambda c:c['budget'].update(max_cost=-1), lambda c:c.update(status='completed'),
])
def test_plan_rejects(mutate):
    c=plan(); mutate(c)
    with pytest.raises(ValueError): validate_plan(c)


def test_register_plan(tmp_path):
    source=tmp_path/'input.jsonl'; write_rows(source,[example(i) for i in range(10)])
    build_dataset(source,tmp_path/'dataset')
    config=tmp_path/'plan.json'; atomic_json(config,plan())
    record=register_plan(config,tmp_path/'research',tmp_path/'approved')
    assert not record['training_executed'] and record['status']=='planned'
    with pytest.raises(ValueError): register_plan(config,tmp_path/'research',tmp_path/'approved')


def prediction(variant):
    return {'variant':variant,'split':'test','dataset_sha256':'d'*64,'base_revision':'a'*40,
        'model_artifact_sha256':'b'*64,'protocol':{'template_sha256':'c'*64,'prompt_sha256':'e'*64,'tool_schema_sha256':'f'*64,'seed':42,'max_tokens':64,'context_limit':512,'sampling':{'temperature':0}},
        'environment':{'engine':'fixture'},'evidence_ref':'synthetic-not-inference',
        'predictions':[{'id':'1','capability':'tools','expected':'ok','prediction':'ok'},
                       {'id':'2','capability':'ptbr','expected':'sim','prediction':'sim'}]}


def test_comparison_does_not_hide_regression():
    base, adapter=prediction('base'),prediction('adapter'); adapter['predictions'][0]['prediction']='wrong'
    report=compare([base,adapter,prediction('adapter-quantized')])
    assert report['regressions'][0]['capability']=='tools' and not report['release_approved']


@pytest.mark.parametrize('mutate', [lambda r:r.update(dataset_sha256='e'*64),
    lambda r:r['predictions'].pop(), lambda r:r['predictions'].append(r['predictions'][0]),
    lambda r:r.update(split='train'),lambda r:r.update(protocol={'seed':123})])
def test_comparison_rejects(mutate):
    adapter=prediction('adapter'); mutate(adapter)
    with pytest.raises(ValueError): compare([prediction('base'),adapter])


def adapter_fixture(path):
    path.mkdir()
    atomic_json(path/'adapter_config.json',{'peft_type':'LORA','r':2,'target_modules':['q_proj'],'base_model_name_or_path':'fixture/base'})
    atomic_json(path/'provenance.json',{'base_model_id':'fixture/base','base_revision':'a'*40,'base_weights_sha256':'b'*64})
    save_file({'base.q_proj.lora_A.weight':np.zeros((2,4),dtype=np.float32),
               'base.q_proj.lora_B.weight':np.zeros((4,2),dtype=np.float32)},str(path/'adapter_model.safetensors'))


def test_adapter_export(tmp_path):
    source=tmp_path/'source'; adapter_fixture(source)
    report=export_adapter(source,tmp_path/'export')
    assert inspect_adapter(tmp_path/'export')==report
    with pytest.raises(ValueError): export_adapter(source,tmp_path/'export')
    (source/'adapter_model.safetensors').write_bytes(b'broken')
    with pytest.raises(ValueError): inspect_adapter(source)


def test_adapter_unpaired(tmp_path):
    source=tmp_path/'source';adapter_fixture(source)
    save_file({'x.lora_A.weight':np.zeros((2,4),dtype=np.float32)},str(source/'adapter_model.safetensors'))
    with pytest.raises(ValueError):inspect_adapter(source)


def test_resume_metadata(tmp_path):
    record={'config_sha256':'a'*64,'dataset_manifest_sha256':'b'*64,'code_commit':'c'*40,'source_snapshot_sha256':'d'*64,'dependency_lock_sha256':'e'*64}
    atomic_json(tmp_path/'record.json',record)
    ckpt={**record,'files':{}}
    for n in ('adapter','optimizer','scheduler','rng'):
        p=tmp_path/(n+'.txt');p.write_text('fixture only');ckpt['files'][n]={'path':p.name,'sha256':digest(p)}
    atomic_json(tmp_path/'checkpoint.json',ckpt)
    assert verify_resume(tmp_path/'record.json',tmp_path/'checkpoint.json')['resumed'] is False
    (tmp_path/'rng.txt').write_text('tampered')
    with pytest.raises(ValueError):verify_resume(tmp_path/'record.json',tmp_path/'checkpoint.json')


def test_cli(tmp_path,capsys):
    source=tmp_path/'input.jsonl';write_rows(source,[example(i) for i in range(8)])
    assert main(['validate-data',str(source)])==0
    assert main(['build-data',str(source),str(tmp_path/'out')])==0
    assert main(['verify-data',str(tmp_path/'out/manifest.json')])==0
    assert main(['validate-data',str(tmp_path/'missing')])==2


def test_cards_are_unapproved_and_no_overwrite(tmp_path):
    from lia_lab.cards import write_card
    source=tmp_path/'input.jsonl';write_rows(source,[example(i) for i in range(8)])
    build_dataset(source,tmp_path/'dataset')
    result=write_card('dataset',tmp_path/'dataset/manifest.json',tmp_path/'dataset-card.md')
    assert result['status']=='draft-not-approved'
    assert 'PENDING HUMAN REVIEW' in (tmp_path/'dataset-card.md').read_text()
    with pytest.raises(ValueError):write_card('dataset',tmp_path/'dataset/manifest.json',tmp_path/'dataset-card.md')
    adapter_fixture(tmp_path/'adapter')
    write_card('model',tmp_path/'adapter',tmp_path/'model-card.md')
    assert 'NOT RUNTIME VALIDATED' in (tmp_path/'model-card.md').read_text()


def test_symlink_escape_adapter(tmp_path):
    source=tmp_path/'source';adapter_fixture(source)
    outside=tmp_path/'outside.json';outside.write_text('{}')
    (source/'provenance.json').unlink();(source/'provenance.json').symlink_to(outside)
    with pytest.raises(ValueError):inspect_adapter(source)


@pytest.mark.parametrize('value',[float('nan'),float('inf')])
def test_nonfinite_budget(value):
    c=plan();c['budget']['max_cost']=value
    with pytest.raises(ValueError):validate_plan(c)


def test_incomplete_protocol_rejected():
    base, adapter=prediction('base'),prediction('adapter')
    base['protocol']={};adapter['protocol']={}
    with pytest.raises(ValueError,match='incomplete'):compare([base,adapter])


def test_adapter_revision_mismatch(tmp_path):
    p=tmp_path/'adapter';adapter_fixture(p)
    cfg=load(p/'adapter_config.json');cfg['revision']='c'*40
    atomic_json(p/'adapter_config.json',cfg)
    with pytest.raises(ValueError,match='revision mismatch'):inspect_adapter(p)


def test_template_cli_rejection_without_download(tmp_path,capsys):
    assert main(['register-plan','configs/sft-pilot.template.yaml','--research-root',str(tmp_path/'research'),
                 '--approved-root',str(tmp_path/'approved')])==2
    assert not (tmp_path/'research').exists()
