"""Research entries cannot silently become executable or license-approved."""
import copy
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from lia_lab.io import load, LabError
from lia_lab.model_backends import select_backend
from lia_lab.checkpoints import seal_snapshot

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load(ROOT / 'configs/model-candidates.yaml')
RECORDS = [c for c in CATALOG['candidates'] if c.get('family') == 'LFM3']
VALIDATOR = Draft202012Validator(load(ROOT / 'src/lia_lab/schemas/research-candidate.schema.json'))


def test_all_research_entries_and_distinct_formats():
    assert len(RECORDS) == 13
    assert len({c['model_id'] for c in RECORDS}) == 13
    for c in RECORDS:
        VALIDATOR.validate(c)
        r = c['research_contract']
        if r['format'] == 'GGUF':
            assert c['model_id'] == r['parent_model_id'] + '-GGUF'
            assert any(p['model_id'] == r['parent_model_id'] for p in RECORDS)
    assert not any(c['model_id'].endswith('Base-GGUF') for c in RECORDS)


@pytest.mark.parametrize('field,value', [('execution_allowed', True), ('license_review','approved'),
    ('individual_license_inspected',True), ('runtime_validation','PASS'), ('training_validation','PASS')])
def test_research_gates_require_deliberate_schema_change(field, value):
    c = copy.deepcopy(RECORDS[0]); c['research_contract'][field] = value
    assert list(VALIDATOR.iter_errors(c))


def test_decisions_cannot_be_labeled_conversation():
    c = copy.deepcopy(next(c for c in RECORDS if c['research_contract']['kind'] == 'decision'))
    c['research_contract']['output_modalities'] = ['text','speech']
    assert list(VALIDATOR.iter_errors(c))


@pytest.mark.parametrize('architecture,model_type', [('Lfm3ForCausalLM','lfm3'),
    ('Lfm3VlForConditionalGeneration','lfm3_vl'), ('Lfm3AudioForConditionalGeneration','lfm3_audio'),
    ('Lfm3OmniForConditionalGeneration','lfm3_omni'), ('D1Model','lfm3_vl'), ('D1Model','lfm3_omni')])
def test_unreviewed_architectures_remain_denied(architecture, model_type):
    with pytest.raises(LabError, match='unknown/mismatched'):
        select_backend({'model_type':model_type, 'architectures':[architecture]})


def test_liquid_license_not_accepted_by_sealer(tmp_path):
    with pytest.raises(LabError, match='reviewed Apache'):
        seal_snapshot(tmp_path, tmp_path/'unused.json', 'LiquidAI/LFM3-1.7B', 'a'*40,
                      'LFM Open License v1.0', 'LICENSE', 'fixture-not-approval')
    assert not (tmp_path/'unused.json').exists()
