"""Native HF generation masks with per-turn validation. No trainer or weights."""
from copy import deepcopy
from jsonschema import Draft202012Validator
from .io import LabError



def validate_tool_schema(schema):
    """Only in-document references: schema validation must never fetch files/URLs."""
    if not isinstance(schema, dict):
        raise LabError('explicit object tool schema required')
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {'$ref', '$dynamicRef', '$recursiveRef'} and (not isinstance(child, str) or not child.startswith('#')):
                    raise LabError('external tool schema references forbidden')
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(schema)
    from jsonschema.exceptions import SchemaError
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise LabError('invalid tool parameter schema') from exc


def validate_tool_arguments(schema, arguments):
    validate_tool_schema(schema)
    from referencing.exceptions import Unresolvable
    try:
        errors = list(Draft202012Validator(schema).iter_errors(arguments))
    except Unresolvable as exc:
        raise LabError('unresolvable local tool schema reference') from exc
    if errors:
        raise LabError('tool arguments do not match schema')


def hf_messages(example, tools=None):
    messages = deepcopy(example['messages'])
    if not messages or len(messages) > 64:
        raise LabError('expected 1..64 messages')
    schemas = {}
    for tool in tools or []:
        if tool.get('type') != 'function':
            raise LabError('function tool schema required')
        function = tool['function']
        name, schema = function['name'], function.get('parameters')
        if name in schemas or not isinstance(schema, dict):
            raise LabError('unique explicit tool schemas required')
        validate_tool_schema(schema)
        schemas[name] = schema
    calls, pending = {}, set()
    for message in messages:
        role = message['role']
        if role not in {'system', 'user', 'assistant', 'tool'}:
            raise LabError('unknown message role')
        if pending and role != 'tool':
            raise LabError('all tool results must precede continuation')
        if role != 'assistant' and 'tool_calls' in message:
            raise LabError('only assistant may call tools')
        if 'tool_calls' in message:
            if not message['tool_calls']:
                raise LabError('empty tool_calls')
            converted = []
            for call in message['tool_calls']:
                name, call_id = call['name'], call['id']
                if name not in schemas:
                    raise LabError('training tool call requires matching explicit tool schema')
                if call_id in calls or not isinstance(call['arguments'], dict):
                    raise LabError('duplicate tool call ID/invalid arguments')
                validate_tool_arguments(schemas[name], call['arguments'])
                calls[call_id] = name
                pending.add(call_id)
                converted.append({'id': call_id, 'type': 'function',
                                  'function': {'name': name, 'arguments': call['arguments']}})
            message['tool_calls'] = converted
            message.setdefault('content', None)
        elif not isinstance(message.get('content'), str) or not message['content']:
            raise LabError('nonempty message content required')
        if role == 'tool':
            call_id = message.get('tool_call_id')
            if call_id not in pending:
                raise LabError('orphan/repeated tool result')
            message['name'] = calls[call_id]
            pending.remove(call_id)
    if pending:
        raise LabError('missing tool results')
    if not any(m['role'] == 'assistant' for m in messages):
        raise LabError('no assistant training turn')
    return messages


def _encode(tokenizer, messages, tools):
    encoded = tokenizer.apply_chat_template(messages, tools=tools, tokenize=True,
        add_generation_prompt=False, return_dict=True, return_assistant_tokens_mask=True,
        truncation=False, padding=False)
    ids, mask = encoded['input_ids'], encoded.get('assistant_masks')
    # ProcessorMixin returns a batch even for one conversation; never flatten multiple samples.
    if isinstance(ids, list) and len(ids) == 1 and isinstance(ids[0], list):
        if not isinstance(mask, list) or len(mask) != 1 or not isinstance(mask[0], list):
            raise LabError('invalid processor batch mask')
        ids, mask = ids[0], mask[0]
    if not isinstance(ids, list) or not ids or any(type(x) is not int or x < 0 for x in ids):
        raise LabError('expected one unbatched sequence of valid token IDs')
    if (not isinstance(mask, list) or len(mask) != len(ids) or
            any(type(x) is not int or x not in (0, 1) for x in mask)):
        raise LabError('invalid native assistant_masks')
    return ids, mask


def render_sft_example(example, tokenizer, max_length=2048, tools=None):
    if type(max_length) is not int or not 16 <= max_length <= 4096:
        raise LabError('invalid SFT sequence budget')
    # Do not infer correctness from a literal Jinja tag. Validate returned native masks per turn.
    messages = hf_messages(example, tools)
    ids, mask = _encode(tokenizer, messages, tools)
    if len(ids) > max_length:
        raise LabError('SFT example too long; no silent truncation')
    if not any(mask) or all(mask):
        raise LabError('empty/full-prompt assistant mask')
    previous = 0
    for i, message in enumerate(messages):
        prefix_ids, prefix_mask = _encode(tokenizer, messages[:i+1], tools)
        end = len(prefix_ids)
        if end <= previous or prefix_ids != ids[:end] or prefix_mask != mask[:end]:
            raise LabError('template/tokenization not prefix-stable; audit a training variant before use')
        segment = mask[previous:end]
        if (message['role'] == 'assistant') != any(segment):
            raise LabError('native generation spans must cover every assistant turn and no user/tool/system turn')
        previous = end
    return {'input_ids': ids, 'attention_mask': [1]*len(ids),
            'labels': [token if train else -100 for token, train in zip(ids, mask)],
            'trainable_tokens': sum(mask), 'evidence': 'native-masks-and-turn-checks-not-weight-compatibility'}


def assert_no_suite_overlap(examples, suite):
    """Exact normalized substring leakage gate, NOT semantic decontamination."""
    import unicodedata
    def norm(text):
        return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())
    holdout = {norm(m['content']) for c in suite['cases'] for m in c['messages']
               if m['role'] == 'user' and isinstance(m.get('content'), str) and norm(m['content'])}
    for example in examples:
        for message in example['messages']:
            text = norm(message.get('content') or '')
            if any(prompt in text for prompt in holdout):
                raise LabError('engineering evaluation prompt leaked into training data')
    return {'status': 'normalized-exact-substring-overlap-not-found', 'semantic_decontamination': False}
