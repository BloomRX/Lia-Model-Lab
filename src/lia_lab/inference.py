"""Authorized local inference supervisor; isolated, bounded worker and durable failures."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time
from .checkpoints import verify_snapshot
from .environment import doctor
from .experiments import ID
from .inference_protocol import validate_suite
from .io import LabError, atomic_json, digest, load, owned, roots, source_snapshot_hash


def validate_options(device, dtype, repeats, max_tokens, context, timeout):
    if device not in {'cpu', 'cuda', 'rocm', 'mps'} or dtype not in {'float32', 'float16', 'bfloat16'}:
        raise LabError('unsupported device/dtype')
    if device == 'cpu' and dtype != 'float32':
        raise LabError('first CPU reference backend requires float32; quantized CPU uses a separate future backend')
    for value, low, high in ((repeats, 2, 3), (max_tokens, 1, 512), (context, 128, 4096), (timeout, 1, 3600)):
        if type(value) is not int or not low <= value <= high:
            raise LabError('invalid inference budget')
    if max_tokens >= context:
        raise LabError('generation budget must be less than context limit')


def run_inference(snapshot, snapshot_manifest, suite_path, research_root, approved_root, run_id,
                  approval_ref, device='cpu', dtype='float32', repeats=2, max_tokens=128,
                  context=2048, timeout=600):
    validate_options(device, dtype, repeats, max_tokens, context, timeout)
    if not ID.fullmatch(run_id) or not approval_ref or approval_ref.startswith('PENDING'):
        raise LabError('run ID and explicit execution approval reference required')
    root, _ = roots(research_root, approved_root)
    # Never write logs/results into the selected checkpoint or its parent tree.
    snapshot = Path(snapshot).absolute()
    run = owned(root, 'experiments/' + run_id)
    if run.resolve().is_relative_to(snapshot.resolve()) or snapshot.resolve().is_relative_to(run.resolve()):
        raise LabError('experiment and snapshot storage overlap')
    run.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    record = {'schema_version': 1, 'kind': 'inference', 'status': 'started',
              'started_at_utc': datetime.now(timezone.utc).isoformat(), 'approval_ref': approval_ref,
              'evidence': 'no-checkpoint-inference-yet', 'inference_executed': False,
              'training_executed': False, 'release_approved': False, 'actual_cost': None,
              'model_metrics': None, 'environment': doctor(root), 'run_id': run_id}
    atomic_json(run / 'experiment.json', record)
    try:
        manifest = verify_snapshot(snapshot, snapshot_manifest)
        if Path(suite_path).stat().st_size > 256 * 1024:
            raise LabError('suite exceeds 256 KiB budget')
        suite = validate_suite(load(suite_path))
        record.update(model_id=manifest['model_id'], base_revision=manifest['revision'],
                      snapshot_manifest_sha256=digest(snapshot_manifest), suite_sha256=digest(suite_path))
        checkout = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
        record['code_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        record['git_dirty'] = bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True))
        record['dependency_lock_sha256'] = digest(checkout / 'requirements.lock')
        record['source_snapshot_sha256'] = source_snapshot_hash()
        resident = manifest['stored_tensor_elements'] * (4 if dtype == 'float32' else 2)
        required = int(resident * 1.5) + 1024 ** 3
        record['estimated_host_ram_bytes'] = required
        available = record['environment']['ram']['available_bytes']
        blockers = []
        if available is None or available < required:
            blockers.append('host RAM unknown or below conservative loading envelope')
        if any(record['environment']['dependencies'][name] is None for name in ('torch', 'transformers')):
            blockers.append('optional torch/transformers runtime is not installed')
        if blockers:
            record.update(status='blocked', blockers=blockers)
            return record
        request = {'snapshot': str(snapshot.resolve()), 'snapshot_manifest': str(Path(snapshot_manifest).resolve()),
                   'suite': suite, 'device': device, 'dtype': dtype, 'repeats': repeats,
                   'max_tokens': max_tokens, 'context': context, 'seed': 42}
        atomic_json(run / 'request.json', request)
        record['request_sha256'] = digest(run / 'request.json')
        atomic_json(run / 'experiment.json', record)
        env = dict(os.environ)
        env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1',
                   HF_HUB_DISABLE_TELEMETRY='1', TOKENIZERS_PARALLELISM='false', DO_NOT_TRACK='1')
        # stdout is progress-free; errors remain local. timeout kills the worker, never promotes results.
        with (run / 'worker.log').open('wb') as log:
            result = subprocess.run([sys.executable, '-m', 'lia_lab.inference_worker',
                                     str(run / 'request.json'), str(run / 'results.json')],
                                    env=env, stdout=log, stderr=log, timeout=timeout, check=False)
        if result.returncode != 0:
            record.update(status='failed', failure=f'worker exit {result.returncode}; inspect local worker.log')
        else:
            results = load(run / 'results.json')
            if results.get('evidence') != 'real-local-checkpoint-inference' or results.get('successful_requests', 0) != len(suite['cases']) * repeats:
                raise LabError('incomplete worker result; not approved')
            record.update(status='completed-not-quality-approved', inference_executed=True,
                          evidence='real-local-checkpoint-inference', results_sha256=digest(run / 'results.json'),
                          model_metrics=results['metrics'])
    except subprocess.TimeoutExpired:
        record.update(status='failed', failure='worker timeout; subprocess killed; partial outputs are not proof')
    except Exception as exc:
        record.update(status='failed', failure=f'{type(exc).__name__}: {exc}')
    except KeyboardInterrupt:
        record.update(status='failed', failure='operator interrupted execution; results incomplete')
    finally:
        partial = run / 'results.json'
        if record['status'] != 'completed-not-quality-approved' and partial.is_file():
            try:
                data = load(partial)
                if data.get('evidence') == 'real-local-checkpoint-inference' and data.get('successful_requests', 0) > 0:
                    record.update(inference_executed=True, evidence='partial-real-checkpoint-inference-not-completed',
                                  partial_requests=data['successful_requests'], partial_results_sha256=digest(partial))
            except (ValueError, OSError):
                record['partial_results_unreadable'] = True
        record['actual_duration_seconds'] = time.perf_counter() - start
        atomic_json(run / 'experiment.json', record)
    return record
