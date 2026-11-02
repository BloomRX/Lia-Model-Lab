"""Actual lightweight HF 5.22.1 APIs with an ORIGINAL local WordLevel tokenizer.
NOT Qwen tokenizer files, model weights, native Qwen templates or inference.
Run in the isolated requirements-api.lock environment; base suite explicitly skips this module.
"""
import importlib.metadata
import pytest
transformers=pytest.importorskip('transformers',reason='lightweight HF API job uses requirements-api.lock; no Torch/weights')
from tokenizers import Tokenizer,models,pre_tokenizers
from transformers import PreTrainedTokenizerFast,AutoConfig
from transformers.models.auto.modeling_auto import MODEL_FOR_CAUSAL_LM_MAPPING_NAMES,MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING_NAMES
from transformers.models.auto.processing_auto import PROCESSOR_MAPPING_NAMES
from transformers.models.auto.tokenization_auto import TOKENIZER_MAPPING_NAMES
from lia_lab.training_prep import render_sft_example
from lia_lab.io import LabError


@pytest.fixture
def local_tokenizer():
    backend=Tokenizer(models.WordLevel({'[UNK]':0,'user':1,'assistant':2,'system':3,'tool':4,
        'oi':5,'resposta':6,'fim':7,'consulta':8},unk_token='[UNK]'))
    backend.pre_tokenizer=pre_tokenizers.Whitespace()
    tokenizer=PreTrainedTokenizerFast(tokenizer_object=backend,unk_token='[UNK]')
    # Authored here. generation spans cover assistant body/tool calls AND turn terminator.
    tokenizer.chat_template="""{% for m in messages %}{{ m.role }} {% if m.role == 'assistant' %}{% generation %}{{ m.content or '' }}{% if m.tool_calls is defined %}{{ m.tool_calls | tojson }}{% endif %} fim{% endgeneration %} {% else %}{{ m.content }} fim {% endif %}{% endfor %}"""
    return tokenizer


def test_real_version_no_torch_and_auto_registries():
    assert transformers.__version__=='5.22.1'
    with pytest.raises(importlib.metadata.PackageNotFoundError):importlib.metadata.version('torch')
    assert AutoConfig.for_model('qwen3_5').text_config.model_type=='qwen3_5_text'
    assert AutoConfig.for_model('qwen3').model_type=='qwen3'
    assert MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING_NAMES['qwen3_5']=='Qwen3_5ForConditionalGeneration'
    assert MODEL_FOR_CAUSAL_LM_MAPPING_NAMES['qwen3']=='Qwen3ForCausalLM'
    assert PROCESSOR_MAPPING_NAMES['qwen3_5']=='Qwen3VLProcessor'
    assert TOKENIZER_MAPPING_NAMES['qwen3']=='Qwen2Tokenizer'


def test_actual_api_mask_field_and_turn_end(local_tokenizer):
    row={'messages':[{'role':'user','content':'oi'},{'role':'assistant','content':'resposta'}]}
    encoded=local_tokenizer.apply_chat_template(row['messages'],return_dict=True,return_assistant_tokens_mask=True)
    assert 'assistant_masks' in encoded and encoded['assistant_masks']==[0,0,0,0,1,1]
    rendered=render_sft_example(row,local_tokenizer)
    assert rendered['labels']==[-100,-100,-100,-100,6,7]


def test_real_api_multiturn_and_tool_roundtrip(local_tokenizer):
    row={'messages':[{'role':'system','content':'oi'},{'role':'user','content':'oi'},
        {'role':'assistant','tool_calls':[{'id':'c1','name':'consulta','arguments':{'id':7}}]},
        {'role':'tool','tool_call_id':'c1','content':'resposta'},
        {'role':'assistant','content':'resposta'},{'role':'user','content':'oi'},{'role':'assistant','content':'resposta'}]}
    tools=[{'type':'function','function':{'name':'consulta','parameters':{'type':'object','properties':{'id':{'type':'integer'}},'required':['id']}}}]
    result=render_sft_example(row,local_tokenizer,tools=tools)
    assert result['trainable_tokens']>6
    assert -100 in result['labels'] and result['labels'][-1]==7


@pytest.mark.parametrize('template',[
 "{% for m in messages %}{{m.role}} {{m.content}} fim {% endfor %}",
 "{% generation %}{% for m in messages %}{{m.role}} {{m.content}} fim {% endfor %}{% endgeneration %}",
 "{% for m in messages %}{% if m.role=='user' %}{% generation %}{{m.content}}{% endgeneration %}{% else %}{{m.content}}{% endif %} fim {% endfor %}"])
def test_real_jinja_incorrect_generation_scopes_rejected(local_tokenizer,template):
    local_tokenizer.chat_template=template
    row={'messages':[{'role':'user','content':'oi'},{'role':'assistant','content':'resposta'}]}
    with pytest.raises(LabError):render_sft_example(row,local_tokenizer)


def test_real_api_long_sequence_is_not_truncated(local_tokenizer):
    row={'messages':[{'role':'user','content':'oi '*40},{'role':'assistant','content':'resposta'}]}
    with pytest.raises(LabError,match='long'):render_sft_example(row,local_tokenizer,max_length=16)


def test_real_api_trailing_whitespace_span_failure_is_not_silenced(local_tokenizer):
    # TF5.22.1 char_to_token at whitespace end can mask later user/tool tokens.
    local_tokenizer.chat_template=local_tokenizer.chat_template.replace('fim{% endgeneration %} ', 'fim {% endgeneration %}')
    row={'messages':[{'role':'user','content':'oi'},{'role':'assistant','content':'resposta'},
                     {'role':'user','content':'oi'},{'role':'assistant','content':'resposta'}]}
    with pytest.raises(LabError):render_sft_example(row,local_tokenizer)
