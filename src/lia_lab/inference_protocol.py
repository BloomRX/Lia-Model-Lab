"""Original engineering prompts and conservative validators, not a quality benchmark."""
import json
from .io import LabError, json_loads


def validate_suite(suite):
    if suite.get('schema_version') != 1 or suite.get('evidence') != 'original-public-engineering-cases-not-training-data':
        raise LabError('invalid inference suite')
    cases = suite['cases']
    if not 1 <= len(cases) <= 20 or len({c['id'] for c in cases}) != len(cases):
        raise LabError('suite size/duplicate IDs')
    for case in cases:
        if case['check'] not in {'exact', 'json', 'human', 'tool'}:
            raise LabError('unsupported check')
        if not case['messages'] or case['messages'][-1]['role'] != 'user':
            raise LabError('suite must end with user request')
        for message in case['messages']:
            if message['role'] not in {'system', 'user', 'assistant'} or not isinstance(message['content'], str) or len(message['content']) > 4000:
                raise LabError('invalid or unbounded message')
        if case['check'] == 'exact' and not isinstance(case.get('expected'), str):
            raise LabError('exact check requires expected output')
        if case['check'] == 'json' and not isinstance(case.get('expected_json'), dict):
            raise LabError('JSON check requires expected object')
        if case['check'] == 'tool' and not case.get('tools'):
            raise LabError('tool schema required')
    return suite


def check_output(case, text):
    """Never run tools. Parse only the explicitly supported Qwen tool-call envelope."""
    if case['check'] == 'human':
        return {'status': 'human-review-required', 'passed': None}
    if case['check'] == 'exact':
        return {'status': 'automatic-exact', 'passed': text.strip() == case['expected']}
    if case['check'] == 'json':
        try:
            value = json_loads(text)
            passed = value == case['expected_json']
        except (ValueError, TypeError):
            passed = False
        return {'status': 'automatic-json-object', 'passed': passed}
    try:
        start, end = text.index('<tool_call>') + len('<tool_call>'), text.index('</tool_call>')
        call = json_loads(text[start:end].strip())
        passed = call == case['expected_call'] and text.count('<tool_call>') == 1
        return {'status': 'qwen-envelope-only-no-tool-execution', 'passed': passed}
    except (ValueError, KeyError, TypeError):
        return {'status': 'unparsed-or-incorrect-tool-call-review-raw-output', 'passed': False}
