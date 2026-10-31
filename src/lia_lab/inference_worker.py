"""Private subprocess entry point. No imports of Torch/Transformers until execution."""
import os
from pathlib import Path
import sys
import hashlib
import threading
import time
from .checkpoints import verify_snapshot
from .environment import dependencies, rss
from .containment import apply_limits
from .authorization import claim_worker
from .io import source_snapshot_hash
from .model_backends import select_backend, load_frontend, load_model, prepare_inputs, output_text, check_context, select_dtype, generation_options
from .inference_protocol import check_output
from .io import LabError, atomic_json, canonical, digest, load


class MemorySampler:
    def __init__(self):
        self.peak = None
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self):
        while not self.stop.is_set():
            value = rss()
            if value is not None:
                self.peak = max(self.peak or 0, value)
            self.stop.wait(0.05)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()


def torch_device(torch, requested, resident):
    if requested in {'cuda', 'rocm'}:
        hip = bool(torch.version.hip)
        if not torch.cuda.is_available() or hip != (requested == 'rocm'):
            raise LabError('requested CUDA/ROCm provider is not available in this torch build/device')
        free, total = torch.cuda.mem_get_info()
        if free < resident * 1.25 + 512 * 1024**2:
            raise LabError('GPU free memory below conservative inference envelope')
        return 'cuda:0', {'provider': requested, 'name': torch.cuda.get_device_name(0), 'total_bytes': total, 'free_before_bytes': free, 'torch_cuda_build': torch.version.cuda, 'torch_hip_build': torch.version.hip}
    if requested == 'mps':
        if not torch.backends.mps.is_available():
            raise LabError('MPS unavailable')
        return 'mps', {'provider': 'mps', 'vram_bytes': None}
    return 'cpu', {'provider': 'cpu', 'vram_bytes': None}


def validate_worker_grant(request):
    auth = request.get('authorization')
    if not isinstance(auth, dict):
        raise LabError('external worker grant required; offline env flags are not authorization')
    operation = auth['operation']
    args = operation['arguments']
    for key in ('snapshot', 'snapshot_manifest', 'device', 'dtype', 'repeats', 'max_tokens', 'context'):
        if request[key] != args[key]:
            raise LabError('worker request differs from authorized operation')
    if (operation['action'] != 'local-inference' or request['seed'] != 42 or
        request['snapshot_manifest_sha256'] != operation['snapshot_manifest_sha256'] or
        hashlib.sha256(canonical(request['suite']).encode()).hexdigest() != operation['suite_content_sha256'] or
        request['containment'] != operation['containment'] or
        source_snapshot_hash() != operation['source_snapshot_sha256']):
        raise LabError('worker binding mismatch')
    claim_worker(auth['store'], auth['id'], operation)


def execute(request, output):
    if os.environ.get('HF_HUB_OFFLINE') != '1':
        raise LabError('library offline mode required; this is not authorization or OS network isolation')
    validate_worker_grant(request)
    containment = apply_limits(request['containment'])
    atomic_json(Path(output).parent / 'containment.json', {'request_sha256':request.get('_request_sha256'), 'report':containment})
    if digest(request['snapshot_manifest']) != request['snapshot_manifest_sha256']:
        raise LabError('authorized manifest changed')
    manifest = verify_snapshot(request['snapshot'], request['snapshot_manifest'])
    import_started = time.perf_counter()
    import torch
    import transformers
    if transformers.__version__ != '5.22.1':
        raise LabError('reference API requires Transformers 5.22.1')
    runtime_import_seconds = time.perf_counter() - import_started
    device, hardware = torch_device(torch, request['device'], manifest['stored_tensor_elements'] * (4 if request['dtype'] == 'float32' else 2))
    dtype = select_dtype(torch, device, request['dtype'])
    torch.manual_seed(request['seed'])
    if device.startswith('cuda'):
        torch.cuda.manual_seed_all(request['seed'])
        torch.cuda.reset_peak_memory_stats()
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    def sync():
        if device.startswith('cuda'):
            torch.cuda.synchronize()
        elif device == 'mps':
            torch.mps.synchronize()
    snapshot = request['snapshot']
    with MemorySampler() as sampler:
        config = load(Path(snapshot) / 'config.json')
        spec = select_backend(config)
        frontend_started = time.perf_counter()
        frontend = load_frontend(transformers, snapshot, spec)
        frontend_load_seconds = time.perf_counter() - frontend_started
        tokenizer = frontend.tokenizer if spec.multimodal else frontend
        frontend.get_chat_template()  # fail safely if missing/ambiguous
        weights_started = time.perf_counter()
        model = load_model(transformers, snapshot, spec, dtype)
        model.to(device).eval()
        sync()
        weights_load_seconds = time.perf_counter() - weights_started
        rss_loaded = rss()
        responses = []
        result = {'schema_version': 2, 'completed': False, 'containment': containment,
                  'request_sha256': request['_request_sha256'], 'evidence': 'real-local-checkpoint-inference',
                  'model_id': manifest['model_id'], 'revision': manifest['revision'],
                  'default_template_sha256': hashlib.sha256(frontend.get_chat_template().encode()).hexdigest(),
                  'generation_config': model.generation_config.to_dict(),
                  'sft_readiness': {'peft_probe_executed': False, 'assistant_mask_verified': False,
                      'linear_modules_observed_not_approved_targets': {n: list(m.weight.shape) for n, m in model.named_modules() if isinstance(m, torch.nn.Linear)}},
                  'backend': 'transformers-local', 'dependencies': dependencies(), 'hardware': hardware,
                  'seed': request['seed'], 'determinism': 'greedy; cross-device bitwise equality not guaranteed',
                  'successful_requests': 0, 'generation_calls_completed': 0, 'responses': responses,
                  'metrics': {'runtime_import_seconds': runtime_import_seconds,
                              'frontend_load_seconds': frontend_load_seconds, 'weights_load_and_device_transfer_seconds': weights_load_seconds,
                              'process_rss_after_load_bytes': rss_loaded, 'prefill_seconds': None,
                              'ttft_seconds': None, 'decode_only_tokens_per_second': None}}
        atomic_json(output, result)
        for repeat in range(request['repeats']):
            for case in request['suite']['cases']:
                inputs, template = prepare_inputs(spec, frontend, case)
                inputs = inputs.to(device)
                count = check_context(tuple(inputs['input_ids'].shape), model.config, request['context'], request['max_tokens'])
                sync()
                started, cpu_started = time.perf_counter(), time.process_time()
                with torch.inference_mode():
                    generated = model.generate(**inputs, **generation_options(tokenizer, request['max_tokens']))
                sync()
                elapsed = time.perf_counter() - started
                cpu_seconds = time.process_time() - cpu_started
                result['generation_calls_completed'] += 1
                result['last_generation_seconds_including_prefill'] = elapsed
                atomic_json(output, result)
                ids, text = output_text(generated, count, tokenizer, model.generation_config.eos_token_id, request['max_tokens'])
                response = {'id': case['id'], 'repeat': repeat, 'capability': case['capability'],
                            'input_tokens': count, 'output_tokens_including_eos': len(ids), 'text': text,
                            'template_sha256': hashlib.sha256(template.encode()).hexdigest(),
                            'input_ids_sha256': hashlib.sha256(canonical(inputs['input_ids'].tolist()).encode()).hexdigest(),
                            'tool_schema_sha256': hashlib.sha256(canonical(case.get('tools', [])).encode()).hexdigest(),
                            'generation_seconds_including_prefill': elapsed,
                            'output_tokens_per_second_including_prefill': len(ids) / elapsed if elapsed > 0 else None,
                            'generation_process_cpu_seconds': cpu_seconds, 'process_rss_after_bytes': rss(),
                            'budget_exhausted': len(ids) >= request['max_tokens'],
                            'check': check_output(case, text)}
                responses.append(response)
                result['successful_requests'] += 1
                atomic_json(output, result)  # partial result survives crash, never considered completed by supervisor
        result['metrics'].update(process_sampled_peak_rss_bytes=sampler.peak,
              torch_gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated() if device.startswith('cuda') else None,
              torch_gpu_peak_reserved_bytes=torch.cuda.max_memory_reserved() if device.startswith('cuda') else None,
              total_requests=len(responses), all_responses_nonempty=all(bool(r['text'].strip()) for r in responses),
              automatic_checks_passed=sum(r['check']['passed'] is True for r in responses),
              automatic_checks_failed=sum(r['check']['passed'] is False for r in responses),
              human_reviews_pending=sum(r['check']['passed'] is None for r in responses))
        result['metrics']['repeat_text_consistency'] = {c['id']: len({r['text'] for r in responses if r['id'] == c['id']}) == 1 for c in request['suite']['cases']}
        # Detect on-disk mutation during execution, not merely at startup.
        verify_snapshot(snapshot, request['snapshot_manifest'])
        if digest(request['snapshot_manifest']) != request['snapshot_manifest_sha256']:
            raise LabError('authorized manifest changed during execution')
        result['completed'] = True
        atomic_json(output, result)


if __name__ == '__main__':
    request = load(sys.argv[1])
    request['_request_sha256'] = digest(sys.argv[1])
    execute(request, sys.argv[2])
