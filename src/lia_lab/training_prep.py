"""Assistant-only loss contract. No weights, optimizer or trainer is created here."""
from copy import deepcopy
from .io import LabError


def hf_messages(example, tools=None):
    """Translate canonical tool calls explicitly; do not concatenate chat strings."""
    messages = deepcopy(example['messages'])
    names = {tool['function']['name'] for tool in tools or []}
    calls = {}
    for message in messages:
        if 'tool_calls' in message:
            converted = []
            for call in message['tool_calls']:
                if call['name'] not in names:
                    raise LabError('training tool call requires matching explicit tool schema')
                calls[call['id']] = call['name']
                converted.append({'id': call['id'], 'type': 'function',
                                  'function': {'name': call['name'], 'arguments': call['arguments']}})
            message['tool_calls'] = converted
        if message['role'] == 'tool':
            if message.get('tool_call_id') not in calls:
                raise LabError('orphan tool result')
            message['name'] = calls[message['tool_call_id']]
    return messages


def render_sft_example(example, tokenizer, max_length=2048, tools=None):
    if type(max_length) is not int or not 16 <= max_length <= 4096:
        raise LabError('invalid SFT sequence budget')
    if not isinstance(tokenizer.chat_template, str) or '{% generation' not in tokenizer.chat_template:
        raise LabError('reviewed generation-span template required; native template may need an audited training variant')
    encoded = tokenizer.apply_chat_template(hf_messages(example, tools), tools=tools, tokenize=True,
                add_generation_prompt=False, return_dict=True, return_assistant_tokens_mask=True,
                truncation=False, padding=False)
    ids, mask = encoded['input_ids'], encoded.get('assistant_masks')
    if not isinstance(ids, list) or not ids or any(type(x) is not int or x < 0 for x in ids):
        raise LabError('expected one unbatched sequence of valid token IDs')
    if len(ids) > max_length:
        raise LabError('SFT example too long; curate explicitly, never silently truncate tool trajectory')
    if not isinstance(mask, list) or len(mask) != len(ids) or any(x not in (0, 1) for x in mask) or not any(mask) or all(mask):
        raise LabError('invalid or empty assistant-only mask; refuse full-prompt loss')
    return {'input_ids': ids, 'attention_mask': [1] * len(ids),
            'labels': [token if train else -100 for token, train in zip(ids, mask)],
            'trainable_tokens': sum(mask), 'evidence': 'rendered-only-not-trained'}


def assert_no_suite_overlap(examples, suite):
    """Exact normalized user-prompt leakage gate; NOT semantic decontamination."""
    import unicodedata
    def norm(text):
        return ' '.join(unicodedata.normalize('NFKC', text).split())
    holdout = {norm(m['content']) for c in suite['cases'] for m in c['messages'] if m['role'] == 'user'}
    for example in examples:
        if any(norm(m.get('content', '')) in holdout for m in example['messages'] if m['role'] == 'user'):
            raise LabError('engineering evaluation prompt leaked into training data')
    return {'status': 'exact-prompt-overlap-not-found', 'semantic_decontamination': False}
