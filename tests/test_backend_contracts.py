"""Mock backend contract tests; NOT proof that Qwen weights load or generate."""
from types import SimpleNamespace
import pytest
from lia_lab.model_backends import select_backend, load_frontend, load_model, prepare_inputs, output_text
from lia_lab.io import LabError


def config(kind):
    if kind=='qwen3':return {'model_type':kind,'architectures':['Qwen3ForCausalLM']}
    return {'model_type':kind,'architectures':['Qwen3_5ForConditionalGeneration'],
            'text_config':{'model_type':'qwen3_5_text'},'vision_config':{}}


@pytest.mark.parametrize('kind,model,front,concrete',[('qwen3','AutoModelForCausalLM','AutoTokenizer','Qwen3ForCausalLM'),('qwen3_5','AutoModelForImageTextToText','AutoProcessor','Qwen3_5ForConditionalGeneration')])
def test_explicit_backend_and_from_pretrained(kind,model,front,concrete):
    spec=select_backend(config(kind));calls=[]
    assert spec.model_auto==model and spec.frontend_auto==front
    def load_front(*a,**kw):
        calls.append(('front',a,kw));return type(spec.frontend_class,(),{})()
    def load_weights(*a,**kw):
        calls.append(('weights',a,kw));return type(concrete,(),{})()
    tf=SimpleNamespace(**{front:SimpleNamespace(from_pretrained=load_front),model:SimpleNamespace(from_pretrained=load_weights)})
    load_frontend(tf,'/local-only',spec);load_model(tf,'/local-only',spec,'synthetic-dtype')
    assert calls[0][2]=={'local_files_only':True,'trust_remote_code':False}
    assert calls[1][2]=={'local_files_only':True,'trust_remote_code':False,'dtype':'synthetic-dtype',
        'use_safetensors':True,'attn_implementation':'eager','use_kernels':False}


@pytest.mark.parametrize('cfg',[{}, {'model_type':'gemma4','architectures':['Gemma4ForConditionalGeneration']},
 {'model_type':'qwen3','architectures':['Wrong']}, {'model_type':'qwen3_5_text','architectures':['Qwen3_5ForCausalLM']},
 {'model_type':'qwen3_5','architectures':['Qwen3_5ForConditionalGeneration']},
 {**config('qwen3'),'auto_map':{'x':'remote.Code'}}])
def test_unknown_or_changed_architecture_fails(cfg):
    with pytest.raises(LabError):select_backend(cfg)


def test_unexpected_auto_registry_result():
    spec=select_backend(config('qwen3'))
    tf=SimpleNamespace(AutoModelForCausalLM=SimpleNamespace(from_pretrained=lambda *a,**k:object()),
                       AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a,**k:object()))
    with pytest.raises(LabError):load_model(tf,'local',spec,'dtype')
    with pytest.raises(LabError):load_frontend(tf,'local',spec)


@pytest.mark.parametrize('kind',['qwen3','qwen3_5'])
def test_native_template_and_explicit_no_truncation(kind):
    spec=select_backend(config(kind));calls=[]
    class Frontend:
        def get_chat_template(self,**kw):return 'reviewed-native-template'
        def apply_chat_template(self,messages,**kwargs):
            calls.append(('template',messages,kwargs));return {'input_ids':'synthetic'} if spec.multimodal else 'rendered'
        def __call__(self,prompt,**kwargs):calls.append(('encode',prompt,kwargs));return {'input_ids':'synthetic'}
    case={'messages':[{'role':'user','content':'texto apenas'}],'tools':[{'type':'function','function':{'name':'never-execute'}}]}
    inputs,template=prepare_inputs(spec,Frontend(),case)
    assert template=='reviewed-native-template' and inputs['input_ids']=='synthetic'
    assert calls[0][2]['enable_thinking'] is False
    assert calls[0][2]['add_generation_prompt'] is True
    assert calls[-1][2]['truncation'] is False
    if spec.multimodal:
        assert calls[0][1][0]['content']==[{'type':'text','text':'texto apenas'}]
        assert calls[0][2]['tokenize'] is True and calls[0][2]['return_dict'] is True
    else:assert calls[-1][2]['add_special_tokens'] is False
    assert case['messages'][0]['content']=='texto apenas'  # not mutated


class Generated:
    def __init__(self,ids):self.ids=ids
    def __getitem__(self,key):return SimpleNamespace(tolist=lambda:self.ids[key[1]])


def test_output_split_eos_and_no_tool_execution():
    seen=[]
    decoder=SimpleNamespace(decode=lambda ids,**kw:seen.append(ids) or '<tool_call>{"name":"fictional"}</tool_call>')
    ids,text=output_text(Generated([10,11,20,21,99]),2,decoder,[99],3)
    assert ids==[20,21,99] and seen==[[20,21]]
    assert '<tool_call>' in text  # opaque text only; no executor exists


@pytest.mark.parametrize('ids,text,max_tokens',[([1,2],'',2),([1,2],'  ',2),([1,2,3],'text',2)])
def test_empty_and_over_budget_outputs_fail(ids,text,max_tokens):
    with pytest.raises(LabError):output_text(Generated(ids),0,SimpleNamespace(decode=lambda *a,**k:text),99,max_tokens)


def test_context_and_generation_bounds():
    from lia_lab.model_backends import check_context
    cfg=SimpleNamespace(text_config=SimpleNamespace(max_position_embeddings=100))
    assert check_context((1,90),cfg,128,10)==90
    for shape,maximum in [((1,91),10),((1,101),1),((2,10),10),((1,0),1),((1,20),90)]:
        with pytest.raises(LabError):check_context(shape,cfg,100,maximum)


def test_dtype_selection_is_explicit():
    from lia_lab.model_backends import select_dtype
    torch=SimpleNamespace(float32='f32',float16='f16',bfloat16='bf16',cuda=SimpleNamespace(is_bf16_supported=lambda:False))
    assert select_dtype(torch,'cpu','float32')=='f32'
    assert select_dtype(torch,'cuda:0','float16')=='f16'
    with pytest.raises(LabError):select_dtype(torch,'cuda:0','bfloat16')
    with pytest.raises(LabError):select_dtype(torch,'cpu','float16')


def test_generation_defaults_cannot_expand_request_shape_or_budget():
    from lia_lab.model_backends import generation_options
    kwargs=generation_options(SimpleNamespace(pad_token_id=0,eos_token_id=99),16)
    assert kwargs['pad_token_id']==0 and kwargs['max_new_tokens']==16
    assert kwargs['min_new_tokens']==0 and kwargs['num_return_sequences']==1
    assert kwargs['return_dict_in_generate'] is False and kwargs['output_logits'] is False
    assert kwargs['do_sample'] is False
