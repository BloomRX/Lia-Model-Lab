"""Original engineering prompts and conservative validators, not a quality benchmark."""
import json
from .io import LabError, json_loads


def validate_suite(suite):
    if not isinstance(suite, dict) or suite.get('schema_version') != 1 or suite.get('evidence') != 'original-public-engineering-cases-not-training-data':
        raise LabError('invalid inference suite')
    cases = suite.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= 20:
        raise LabError('suite size/type')
    seen = set()
    for case in cases:
        if not isinstance(case, dict):
            raise LabError('suite case must be an object')
        for key in ('id', 'capability'):
            if not isinstance(case.get(key), str) or not case[key].strip() or len(case[key]) > 80:
                raise LabError('case identity/capability required and bounded')
        if case['id'] in seen:
            raise LabError('suite duplicate IDs')
        seen.add(case['id'])
        if case.get('check') not in {'exact', 'json', 'human', 'tool'}:
            raise LabError('unsupported check')
        messages = case.get('messages')
        if not isinstance(messages, list) or not 1 <= len(messages) <= 64:
            raise LabError('expected 1..64 suite messages')
        for message in messages:
            if (not isinstance(message, dict) or message.get('role') not in {'system', 'user', 'assistant'} or
                    not isinstance(message.get('content'), str) or not message['content'].strip() or len(message['content']) > 4000):
                raise LabError('invalid or unbounded message')
        if messages[-1]['role'] != 'user':
            raise LabError('suite must end with user request')
        if case['check'] == 'exact' and not isinstance(case.get('expected'), str):
            raise LabError('exact check requires expected output')
        if case['check'] == 'json' and not isinstance(case.get('expected_json'), dict):
            raise LabError('JSON check requires expected object')
        if case['check'] == 'tool':
            from .training_prep import validate_tool_schema, validate_tool_arguments
            tools, call = case.get('tools'), case.get('expected_call')
            if not isinstance(tools, list) or not tools or not isinstance(call, dict):
                raise LabError('tool schema and expected call required')
            schemas = {}
            for tool in tools:
                fn = tool.get('function') if isinstance(tool, dict) and tool.get('type') == 'function' else None
                if (not isinstance(fn, dict) or not isinstance(fn.get('name'), str) or not fn['name'] or
                        fn['name'] in schemas or not isinstance(fn.get('parameters'), dict)):
                    raise LabError('unique explicit function schemas required')
                validate_tool_schema(fn['parameters'])
                schemas[fn['name']] = fn['parameters']
            name = call.get('name')
            if not isinstance(name, str) or name not in schemas or not isinstance(call.get('arguments'), dict):
                raise LabError('expected tool call must match a declared function')
            validate_tool_arguments(schemas[name], call['arguments'])
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


def validate_worker_results(data, request, request_hash, complete=False):
    """Structural/protocol validation, NOT a signature proving the origin of local results."""
    import math
    if not isinstance(data, dict) or data.get('schema_version') != 2:
        raise LabError('invalid worker result schema')
    if data.get('evidence') != 'real-local-checkpoint-inference' or data.get('request_sha256') != request_hash:
        raise LabError('worker result binding mismatch')
    operation = request['authorization']['operation']
    if data.get('model_id') != operation['model_id'] or data.get('revision') != operation['revision']:
        raise LabError('worker result model mismatch')
    responses = data.get('responses')
    count, calls = data.get('successful_requests'), data.get('generation_calls_completed')
    expected = [(case, repeat) for repeat in range(request['repeats']) for case in request['suite']['cases']]
    if (type(count) is not int or type(calls) is not int or not isinstance(responses,list) or
            len(responses) != count or not 0 <= count <= calls <= len(expected)):
        raise LabError('invalid result counts')
    for response, (case, repeat) in zip(responses, expected):
        if (not isinstance(response, dict) or type(response.get('repeat')) is not int or response.get('id') != case['id'] or response.get('repeat') != repeat or
                response.get('capability') != case['capability'] or not isinstance(response.get('text'),str) or not response['text'].strip()):
            raise LabError('worker response order/identity/empty text mismatch')
        input_tokens = response.get('input_tokens')
        if type(input_tokens) is not int or not 1 <= input_tokens < request['context']:
            raise LabError('invalid input token budget')
        tokens=response.get('output_tokens_including_eos')
        if type(tokens) is not int or not 1 <= tokens <= request['max_tokens'] or input_tokens + tokens > request['context']:
            raise LabError('invalid result token budget')
        for key in ('generation_seconds_including_prefill','generation_process_cpu_seconds'):
            value=response.get(key)
            if type(value) not in (int,float) or not math.isfinite(value) or value < 0:
                raise LabError('invalid generation metric')
    if complete and (data.get('completed') is not True or count != len(expected) or calls != count or not isinstance(data.get('metrics'),dict)):
        raise LabError('incomplete worker results')
    if complete:
        metrics = data['metrics']
        for key in ('runtime_import_seconds', 'frontend_load_seconds', 'weights_load_and_device_transfer_seconds'):
            value = metrics.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise LabError('missing/invalid load metric')
        for key in ('prefill_seconds', 'ttft_seconds', 'decode_only_tokens_per_second'):
            if key not in metrics or metrics[key] is not None:
                raise LabError('unmeasured reference metrics must remain null')
        if type(metrics.get('total_requests')) is not int or metrics['total_requests'] != count:
            raise LabError('metric request count mismatch')
        containment = data.get('containment')
        if not isinstance(containment, dict) or containment.get('profile') != request['containment']['profile']:
            raise LabError('missing/mismatched containment report')
    return data
