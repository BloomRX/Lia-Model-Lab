"""Private subprocess entry point. No imports of Torch/Transformers until execution."""
import os
from pathlib import Path
import sys
import hashlib
import threading
import time
from .checkpoints import verify_snapshot
from .environment import dependencies, rss
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


def execute(request, output):
    if os.environ.get('HF_HUB_OFFLINE') != '1':
        raise LabError('worker must be launched by authorized offline supervisor')
    manifest = verify_snapshot(request['snapshot'], request['snapshot_manifest'])
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForImageTextToText
    dtype = getattr(torch, request['dtype'])
    device, hardware = torch_device(torch, request['device'], manifest['stored_tensor_elements'] * (4 if request['dtype'] == 'float32' else 2))
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
    common = {'local_files_only': True, 'trust_remote_code': False}
    with MemorySampler() as sampler:
        load_start = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(snapshot, **common)
        if not tokenizer.chat_template:
            raise LabError('checkpoint has no native chat template; do not invent one')
        config = load(Path(snapshot) / 'config.json')
        cls = AutoModelForImageTextToText if config['model_type'] in {'qwen3_5', 'gemma4'} else AutoModelForCausalLM
        model = cls.from_pretrained(snapshot, dtype=dtype, use_safetensors=True, attn_implementation='eager', **common)
        model.to(device).eval()
        sync()
        loading = time.perf_counter() - load_start
        rss_loaded = rss()
        responses = []
        result = {'schema_version': 1, 'evidence': 'real-local-checkpoint-inference',
                  'model_id': manifest['model_id'], 'revision': manifest['revision'],
                  'default_template_sha256': hashlib.sha256(tokenizer.get_chat_template().encode()).hexdigest(),
                  'generation_config': model.generation_config.to_dict(),
                  'sft_readiness': {'peft_probe_executed': False, 'assistant_mask_verified': False,
                      'linear_modules_observed_not_approved_targets': {n: list(m.weight.shape) for n, m in model.named_modules() if isinstance(m, torch.nn.Linear)}},
                  'backend': 'transformers-local', 'dependencies': dependencies(), 'hardware': hardware,
                  'seed': request['seed'], 'determinism': 'greedy; cross-device bitwise equality not guaranteed',
                  'successful_requests': 0, 'responses': responses,
                  'metrics': {'load_seconds': loading, 'rss_after_load_bytes': rss_loaded,
                              'ttft_seconds': None, 'decode_only_tokens_per_second': None}}
        for repeat in range(request['repeats']):
            for case in request['suite']['cases']:
                template = tokenizer.get_chat_template(tools=case.get('tools'))
                prompt = tokenizer.apply_chat_template(case['messages'], tools=case.get('tools'), chat_template=template,
                           tokenize=False, add_generation_prompt=True, enable_thinking=False)
                inputs = tokenizer(prompt, add_special_tokens=False, return_tensors='pt').to(device)
                count = inputs['input_ids'].shape[-1]
                if count + request['max_tokens'] > request['context']:
                    raise LabError('prompt plus generation exceeds context; no silent truncation')
                sync()
                started, cpu_started = time.perf_counter(), time.process_time()
                with torch.inference_mode():
                    generated = model.generate(**inputs, max_new_tokens=request['max_tokens'], do_sample=False,
                                num_beams=1, use_cache=True, pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id)
                sync()
                elapsed = time.perf_counter() - started
                ids = generated[0, count:].tolist()
                eos = model.generation_config.eos_token_id
                eos = eos if isinstance(eos, list) else [eos]
                text_ids = ids[:-1] if ids and ids[-1] in eos else ids
                text = tokenizer.decode(text_ids, skip_special_tokens=False)
                response = {'id': case['id'], 'repeat': repeat, 'capability': case['capability'],
                            'input_tokens': count, 'output_tokens_including_eos': len(ids), 'text': text,
                            'template_sha256': hashlib.sha256(template.encode()).hexdigest(),
                            'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                            'tool_schema_sha256': hashlib.sha256(canonical(case.get('tools', [])).encode()).hexdigest(),
                            'generation_seconds_including_prefill': elapsed,
                            'output_tokens_per_generation_second': len(ids) / elapsed if elapsed > 0 else None,
                            'process_cpu_seconds': time.process_time() - cpu_started, 'rss_after_bytes': rss(),
                            'budget_exhausted': len(ids) >= request['max_tokens'],
                            'check': check_output(case, text)}
                responses.append(response)
                result['successful_requests'] += 1
                atomic_json(output, result)  # partial result survives crash, never considered completed by supervisor
        result['metrics'].update(sampled_peak_rss_bytes=sampler.peak,
              gpu_peak_allocated_bytes=torch.cuda.max_memory_allocated() if device.startswith('cuda') else None,
              gpu_peak_reserved_bytes=torch.cuda.max_memory_reserved() if device.startswith('cuda') else None,
              total_requests=len(responses), all_responses_nonempty=all(bool(r['text'].strip()) for r in responses),
              automatic_checks_passed=sum(r['check']['passed'] is True for r in responses),
              automatic_checks_failed=sum(r['check']['passed'] is False for r in responses),
              human_reviews_pending=sum(r['check']['passed'] is None for r in responses))
        result['metrics']['repeat_text_consistency'] = {c['id']: len({r['text'] for r in responses if r['id'] == c['id']}) == 1 for c in request['suite']['cases']}
        # Detect on-disk mutation during execution, not merely at startup.
        verify_snapshot(snapshot, request['snapshot_manifest'])
        atomic_json(output, result)


if __name__ == '__main__':
    execute(load(sys.argv[1]), sys.argv[2])
