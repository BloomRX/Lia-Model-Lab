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
    'qwen3_5': Backend('qwen3_5', 'Qwen3_5ForConditionalGeneration', 'AutoModelForMultimodalLM', 'AutoProcessor', 'Qwen3VLProcessor', True),
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


def architecture_contract(config):
    import hashlib
    from .io import canonical
    spec=select_backend(config)
    return dict(model_type=spec.model_type,concrete_class=spec.architecture,model_auto=spec.model_auto,
        frontend_auto=spec.frontend_auto,frontend_class=spec.frontend_class,
        canonical_config_sha256=hashlib.sha256(canonical(config).encode()).hexdigest(),
        tensor_contract='qwen35-fixed-0.8b-v1' if spec.multimodal else 'qwen3-dense-v1',
        auxiliary_policy='verified-frozen-mtp-storage-no-mtp-generation-v1' if spec.multimodal else 'none')


def native_chat_template(spec, frontend, tools=None):
    if spec.multimodal:
        # ProcessorMixin.apply_chat_template selects its own chat_template/default;
        # it has no tokenizer-style get_chat_template in Transformers 5.22.1.
        template=getattr(frontend,'chat_template',None)
        if isinstance(template,dict):template=template.get('default')
    else:
        template=frontend.get_chat_template(tools=tools)
    if not isinstance(template,str) or not template.strip():
        raise LabError('native frontend chat template missing/ambiguous')
    return template


def qwen3_shapes(config):
    """Narrow explicit dense-Qwen3 layout; missing/other variants -> unknown.

    No default dimensions inferred from a library that might change. Qwen3.5
    uses its separate fixed-configuration contract, never file-sized fallback.
    """
    if not isinstance(config, dict) or config.get('model_type') != 'qwen3' or config.get('architectures') != ['Qwen3ForCausalLM']:
        return None
    fields = ('hidden_size', 'vocab_size', 'intermediate_size', 'num_hidden_layers',
              'num_attention_heads', 'num_key_value_heads', 'head_dim')
    if any(type(config.get(k)) is not int or not 0 < config[k] <= 10000000 for k in fields):
        return None
    if (config['num_hidden_layers'] > 256 or config['num_key_value_heads'] > config['num_attention_heads'] or
        config['num_attention_heads'] % config['num_key_value_heads'] or
        config.get('attention_bias') is not False or config.get('mlp_bias', False) is not False or
        type(config.get('tie_word_embeddings')) is not bool):
        return None
    h, v, mid, layers, heads, kv, d = (config[k] for k in fields)
    shapes = {'model.embed_tokens.weight': (v, h), 'model.norm.weight': (h,)}
    if not config['tie_word_embeddings']:
        shapes['lm_head.weight'] = (v, h)
    for i in range(layers):
        prefix = f'model.layers.{i}.'
        shapes.update({prefix + key: shape for key, shape in {
            'self_attn.q_proj.weight': (heads * d, h),
            'self_attn.k_proj.weight': (kv * d, h), 'self_attn.v_proj.weight': (kv * d, h),
            'self_attn.o_proj.weight': (h, heads * d),
            'self_attn.q_norm.weight': (d,), 'self_attn.k_norm.weight': (d,),
            'input_layernorm.weight': (h,), 'post_attention_layernorm.weight': (h,),
            'mlp.gate_proj.weight': (mid, h), 'mlp.up_proj.weight': (mid, h),
            'mlp.down_proj.weight': (h, mid)}.items()})
    return shapes


def load_model(transformers, snapshot, spec, dtype):
    if spec.model_type == 'qwen3_5':
        from .checkpoints import checkpoint_capacity
        if checkpoint_capacity(snapshot) is None:
            raise LabError('Qwen3.5 configuration is outside the implemented profile')
    loaded = getattr(transformers, spec.model_auto).from_pretrained(snapshot, dtype=dtype,
        local_files_only=True, trust_remote_code=False, use_safetensors=True,
        attn_implementation='eager', use_kernels=False, output_loading_info=True)
    if not isinstance(loaded, tuple) or len(loaded) != 2:
        raise LabError('backend did not return model and loading report')
    model, report = loaded
    if type(model).__name__ != spec.architecture or not isinstance(report, dict):
        raise LabError('unexpected concrete architecture or missing loading report')
    # No blanket ignored keys. Only the proven, canonical tied output alias
    # may be absent from serialization/report; no naming conversions are allowed.
    from .checkpoints import tensor_shapes
    shapes = tensor_shapes(snapshot)
    state = model.state_dict(keep_vars=True)
    embedding = 'model.language_model.embed_tokens.weight' if spec.model_type == 'qwen3_5' else 'model.embed_tokens.weight'
    tied = (spec.model_type in {'qwen3','qwen3_5'} and getattr(model.config, 'tie_word_embeddings', False) is True and
            embedding in shapes and 'lm_head.weight' not in shapes and embedding in state and 'lm_head.weight' in state and
            state['lm_head.weight'] is state[embedding])
    allowed = {'lm_head.weight'} if tied else set()
    for key in ('missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs'):
        types = (list, tuple) if key == 'error_msgs' else (list, tuple, set)
        if key not in report or not isinstance(report[key], types):
            raise LabError('missing/malformed loading report field: ' + key)
        value = report[key]
        if key == 'missing_keys' and isinstance(value, (list, tuple, set)):
            if any(not isinstance(k, str) for k in value):
                raise LabError('invalid missing parameter names')
            value = set(value) - allowed
        if value:
            raise LabError('checkpoint loading rejected: ' + key)
    # Reject any other nonempty diagnostics, rather than ignore future API errors.
    if any(value for key, value in report.items() if key not in
           {'missing_keys', 'unexpected_keys', 'mismatched_keys', 'error_msgs'}):
        raise LabError('unreviewed loading report diagnostics')
    actual = {name: tuple(tensor.shape) for name, tensor in state.items() if name not in allowed}
    auxiliary_count = 0
    if spec.model_type == 'qwen3_5':
        core = {k:v for k,v in shapes.items() if not k.startswith('mtp.')}
        if actual != core:
            raise LabError('materialized Qwen3.5 core does not match checkpoint parameter names/shapes')
        from .qwen35_auxiliary import restore
        auxiliary_count = restore(model, snapshot, shapes, dtype)
        actual = {name: tuple(tensor.shape) for name,tensor in model.state_dict(keep_vars=True).items() if name not in allowed}
    if actual != shapes:
        raise LabError('materialized architecture does not match checkpoint parameter names/shapes')
    model._lia_loading_audit = dict(concrete_class=type(model).__name__, serialized_tensors=len(shapes),
        tied_aliases=sorted(allowed), auxiliary_mtp_tensors_preserved=auxiliary_count, mtp_generation_enabled=False,
        state_shapes_match=True, native_loading_report={k:list(v) for k,v in report.items()})
    return model


def prepare_inputs(spec, frontend, case):
    """Native processor for full VLM even for text. No image/video is loaded here."""
    import copy
    messages = copy.deepcopy(case['messages'])
    if spec.multimodal:
        for message in messages:
            message['content'] = [{'type': 'text', 'text': message['content']}]
    template = native_chat_template(spec,frontend,case.get('tools'))
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
