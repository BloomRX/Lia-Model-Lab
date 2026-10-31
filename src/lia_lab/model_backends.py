"""Explicit TF 5.22.1 architecture contracts; registry/API checks do NOT validate weights."""
from dataclasses import dataclass
from .io import LabError


@dataclass(frozen=True)
class Backend:
    model_type: str
    architecture: str
    model_auto: str
    frontend_auto: str
    frontend_class: str
    multimodal: bool


BACKENDS = {
    'qwen3_5': Backend('qwen3_5', 'Qwen3_5ForConditionalGeneration', 'AutoModelForImageTextToText', 'AutoProcessor', 'Qwen3VLProcessor', True),
    'qwen3': Backend('qwen3', 'Qwen3ForCausalLM', 'AutoModelForCausalLM', 'AutoTokenizer', 'Qwen2Tokenizer', False),
}


def select_backend(config):
    if not isinstance(config, dict) or not isinstance(config.get('model_type'), str):
        raise LabError('invalid model config/type')
    spec = BACKENDS.get(config.get('model_type'))
    if spec is None or config.get('architectures') != [spec.architecture]:
        raise LabError('unknown/mismatched architecture; no generic loading fallback')
    if config.get('quantization_config') or config.get('auto_map'):
        raise LabError('quantized/custom-code architecture not approved by reference loader')
    if spec.multimodal and (not isinstance(config.get('text_config'), dict) or config['text_config'].get('model_type') != 'qwen3_5_text' or
                            not isinstance(config.get('vision_config'), dict)):
        raise LabError('full Qwen3.5 multimodal config required; text-only export is a different architecture')
    return spec


def load_frontend(transformers, snapshot, spec):
    frontend = getattr(transformers, spec.frontend_auto).from_pretrained(snapshot,
                local_files_only=True, trust_remote_code=False)
    if type(frontend).__name__ != spec.frontend_class:
        raise LabError('unexpected tokenizer/processor class; review exact checkpoint config')
    return frontend


def load_model(transformers, snapshot, spec, dtype):
    model = getattr(transformers, spec.model_auto).from_pretrained(snapshot, dtype=dtype,
        local_files_only=True, trust_remote_code=False, use_safetensors=True,
        attn_implementation='eager', use_kernels=False)
    if type(model).__name__ != spec.architecture:
        raise LabError('AutoModel registry returned an unexpected concrete architecture')
    return model


def prepare_inputs(spec, frontend, case):
    """Native processor for full VLM even for text. No image/video is loaded here."""
    import copy
    messages = copy.deepcopy(case['messages'])
    if spec.multimodal:
        for message in messages:
            message['content'] = [{'type': 'text', 'text': message['content']}]
    template = frontend.get_chat_template(tools=case.get('tools'))
    kwargs = dict(tools=case.get('tools'), chat_template=template, add_generation_prompt=True,
                  enable_thinking=False)
    if spec.multimodal:
        inputs = frontend.apply_chat_template(messages, tokenize=True, return_dict=True, return_tensors='pt',
                                              truncation=False, padding=False, **kwargs)
    else:
        prompt = frontend.apply_chat_template(messages, tokenize=False, **kwargs)
        inputs = frontend(prompt, add_special_tokens=False, return_tensors='pt', truncation=False, padding=False)
    return inputs, template


def output_text(generated, input_count, tokenizer, eos, max_tokens):
    ids = generated[0, input_count:].tolist()
    if len(ids) > max_tokens:
        raise LabError('backend exceeded authorized generation budget')
    eos = eos if isinstance(eos, list) else [eos]
    text_ids = ids[:-1] if ids and ids[-1] in eos else ids
    text = tokenizer.decode(text_ids, skip_special_tokens=False)
    if not text.strip():
        raise LabError('empty response; not a successful request')
    return ids, text


def check_context(shape, config, requested, max_tokens):
    if len(shape) != 2 or shape[0] != 1 or type(shape[-1]) is not int or shape[-1] < 1:
        raise LabError('one nonempty conversation per request required')
    declared = getattr(config, 'max_position_embeddings', None) or getattr(getattr(config, 'text_config', None), 'max_position_embeddings', None)
    effective = min(requested, declared) if type(declared) is int else requested
    if shape[-1] + max_tokens > effective:
        raise LabError('prompt plus generation exceeds context; no silent truncation')
    return shape[-1]


def select_dtype(torch, device, name):
    if name not in {'float32', 'float16', 'bfloat16'} or (device == 'cpu' and name != 'float32'):
        raise LabError('unsupported reference dtype/device')
    if device.startswith('cuda') and name == 'bfloat16' and not torch.cuda.is_bf16_supported():
        raise LabError('BF16 not supported by selected torch/device')
    return getattr(torch, name)


def generation_options(tokenizer, max_tokens):
    """Do not inherit return-shape/minimum-length defaults from a generation_config."""
    return dict(max_new_tokens=max_tokens, min_new_tokens=0, min_length=0, do_sample=False,
        num_beams=1, num_return_sequences=1, use_cache=True, return_dict_in_generate=False,
        output_scores=False, output_logits=False, output_attentions=False, output_hidden_states=False,
        pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id)
