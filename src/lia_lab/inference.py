"""Local process supervision with single-use operator grants. NOT a security sandbox."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import time
import hashlib
from .authorization import consume_grant, finalize_grant
from .checkpoints import verify_snapshot
from .containment import policy, supervise, launch_command
from .environment import doctor
from .experiments import ID
from .inference_protocol import validate_suite, validate_worker_results
from .io import LabError, atomic_json, digest, load, owned, roots, source_snapshot_hash, canonical, json_loads


def validate_options(device, dtype, repeats, max_tokens, context, timeout):
    if device not in {'cpu', 'cuda', 'rocm', 'mps'} or dtype not in {'float32', 'float16', 'bfloat16'}:
        raise LabError('unsupported device/dtype')
    if device == 'cpu' and dtype != 'float32':
        raise LabError('first CPU reference backend requires float32')
    for value, low, high in ((repeats, 2, 3), (max_tokens, 1, 512), (context, 128, 4096), (timeout, 1, 3600)):
        if type(value) is not int or not low <= value <= high:
            raise LabError('invalid inference budget')
    if max_tokens >= context:
        raise LabError('generation budget must be less than context limit')


def make_operation(snapshot, snapshot_manifest, suite_path, research_root, approved_root, run_id,
                   device='cpu', dtype='float32', repeats=2, max_tokens=128, context=2048,
                   timeout=600, containment='portable-process'):
    validate_options(device, dtype, repeats, max_tokens, context, timeout)
    if not ID.fullmatch(run_id):
        raise LabError('invalid run ID')
    root, approved = roots(research_root, approved_root)
    run = owned(root, 'experiments/' + run_id)
    snapshot = Path(snapshot).absolute()
    if run.is_relative_to(snapshot.resolve()) or snapshot.resolve().is_relative_to(run):
        raise LabError('experiment and snapshot storage overlap')
    manifest_hash = digest(snapshot_manifest)
    manifest = verify_snapshot(snapshot, snapshot_manifest)
    if digest(snapshot_manifest) != manifest_hash:
        raise LabError('manifest changed during preparation')
    if Path(suite_path).stat().st_size > 256 * 1024:
        raise LabError('suite exceeds 256 KiB budget')
    suite_bytes = Path(suite_path).read_bytes()
    suite = validate_suite(json_loads(suite_bytes.decode('utf-8')))
    settings = dict(snapshot=str(snapshot.resolve()), snapshot_manifest=str(Path(snapshot_manifest).resolve()),
        suite_path=str(Path(suite_path).resolve()), research_root=str(root), approved_root=str(approved),
        run_id=run_id, device=device, dtype=dtype, repeats=repeats, max_tokens=max_tokens,
        context=context, timeout=timeout, containment=containment)
    return {'schema_version': 1, 'action': 'local-inference', 'arguments': settings,
        'repository_root': subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip(),
        'snapshot': settings['snapshot'], 'research_root': str(root), 'approved_root': str(approved),
        'model_id': manifest['model_id'], 'revision': manifest['revision'], 'source': manifest['source'],
        'license': {**manifest['license'], 'sha256': manifest['files'][manifest['license']['file']]['sha256']},
        'snapshot_manifest_sha256': manifest_hash, 'suite_sha256': hashlib.sha256(suite_bytes).hexdigest(),
        'suite_content_sha256': hashlib.sha256(canonical(suite).encode()).hexdigest(),
        'source_snapshot_sha256': source_snapshot_hash(), 'snapshot_total_bytes': manifest['total_bytes'],
        'limits': {'max_output_tokens_per_request': max_tokens, 'max_requests': len(suite['cases'])*repeats,
                   'max_total_output_tokens': max_tokens*len(suite['cases'])*repeats,
                   'max_context_tokens': context, 'max_duration_seconds': timeout,
                   'max_external_cost': 0, 'cost_currency': 'USD', 'cost_scope': 'no-paid-services-not-an-energy-meter'},
        'containment': policy(containment, timeout, device),
        'disallowed_actions': ['download', 'training', 'publication', 'release']}


def operation_from_plan(plan):
    if not isinstance(plan, dict) or plan.get('action') != 'local-inference':
        raise LabError('not a local inference plan')
    operation = make_operation(**plan['arguments'])
    if operation != plan:
        raise LabError('plan stale/modified; regenerate and review exact inputs')
    return operation


def run_inference(snapshot, snapshot_manifest, suite_path, research_root, approved_root, run_id,
                  approval_store, approval_id, device='cpu', dtype='float32', repeats=2, max_tokens=128,
                  context=2048, timeout=600, containment='portable-process'):
    operation = make_operation(snapshot, snapshot_manifest, suite_path, research_root, approved_root,
        run_id, device, dtype, repeats, max_tokens, context, timeout, containment)
    root, _ = roots(research_root, approved_root)
    run = owned(root, 'experiments/' + run_id)
    if run.exists():
        raise FileExistsError('experiment already exists; approval not consumed')
    # Prepare/hash/inspect first; this is not model execution. Grant duration starts at atomic claim.
    manifest = load(snapshot_manifest)
    if digest(snapshot_manifest) != operation['snapshot_manifest_sha256']:
        raise LabError('authorized manifest changed')
    environment = doctor(root if root.exists() else '.')
    suite = validate_suite(load(suite_path))
    if hashlib.sha256(canonical(suite).encode()).hexdigest() != operation['suite_content_sha256']:
        raise LabError('authorized suite changed')
    checkout = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
    code_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    git_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True))
    lock_hash = digest(checkout / 'requirements.lock')
    receipt = consume_grant(approval_store, approval_id, operation)
    start = time.monotonic()
    deadline = start + min(timeout, receipt['expires_unix'] - receipt['consumed_at_unix'])
    # A failed/blocked execution burns the grant too. No refund or repeated implicit execution.
    try:
        run.mkdir(parents=True, exist_ok=False)
    except BaseException:
        finalize_grant(approval_store, approval_id, operation)
        raise
    record = {'schema_version': 2, 'kind': 'inference', 'status': 'started',
        'started_at_utc': datetime.now(timezone.utc).isoformat(), 'authorization_receipt': receipt,
        'operation': operation, 'evidence': 'no-checkpoint-inference-yet', 'inference_executed': False,
        'training_executed': False, 'release_approved': False, 'actual_cost': None, 'model_metrics': None,
        'environment': environment, 'run_id': run_id, 'code_commit': code_commit, 'git_dirty': git_dirty,
        'dependency_lock_sha256': lock_hash, 'source_snapshot_sha256': operation['source_snapshot_sha256'],
        'containment': operation['containment']}
    try:
        atomic_json(run / 'experiment.json', record)
    except BaseException:
        finalize_grant(approval_store, approval_id, operation)
        raise
    try:
        resident = manifest['stored_tensor_elements'] * (4 if dtype == 'float32' else 2)
        required = int(resident * 1.5) + 1024**3
        record['estimated_host_ram_bytes'] = required
        available = environment['ram']['available_bytes']
        blockers = []
        if available is None or available < required:
            blockers.append('host RAM unknown or below conservative loading envelope')
        if any(environment['dependencies'][n] is None for n in ('torch', 'transformers')):
            blockers.append('optional torch/transformers runtime is not installed')
        if blockers:
            record.update(status='blocked', blockers=blockers)
            return record
        request = {'snapshot': str(Path(snapshot).resolve()), 'snapshot_manifest': str(Path(snapshot_manifest).resolve()),
                   'snapshot_manifest_sha256': operation['snapshot_manifest_sha256'], 'suite': suite,
                   'device': device, 'dtype': dtype, 'repeats': repeats, 'max_tokens': max_tokens,
                   'context': context, 'seed': 42, 'containment': operation['containment'],
                   'authorization': {'store': str(Path(approval_store).resolve()), 'id':approval_id, 'operation':operation}}
        atomic_json(run / 'request.json', request)
        record['request_sha256'] = digest(run / 'request.json')
        atomic_json(run / 'experiment.json', record)
        allowed_env = {'PATH','HOME','USERPROFILE','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR',
                       'LD_LIBRARY_PATH','DYLD_LIBRARY_PATH','CUDA_VISIBLE_DEVICES','ROCR_VISIBLE_DEVICES',
                       'HIP_VISIBLE_DEVICES','LANG','LC_ALL'}
        env = {key: value for key, value in os.environ.items() if key in allowed_env}
        env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1',
                   HF_HUB_DISABLE_TELEMETRY='1', TOKENIZERS_PARALLELISM='false', DO_NOT_TRACK='1')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired('authorization deadline', timeout)
        with (run / 'worker.log').open('wb') as log:
            command = launch_command([sys.executable, '-m', 'lia_lab.inference_worker',
                str(run / 'request.json'), str(run / 'results.json')], operation['containment'])
            returncode = supervise(command, env, log, remaining)
        if returncode != 0:
            record.update(status='failed', failure=f'worker exit {returncode}; inspect local worker.log')
        else:
            results = load(run / 'results.json')
            if time.monotonic() > deadline:
                raise subprocess.TimeoutExpired('authorization deadline', timeout)
            validate_worker_results(results, request, record['request_sha256'], complete=True)
            record.update(status='completed-not-quality-approved', inference_executed=True,
                evidence='real-local-checkpoint-inference', results_sha256=digest(run / 'results.json'),
                model_metrics=results['metrics'], containment=results['containment'])
    except subprocess.TimeoutExpired:
        record.update(status='timed-out', failure='deadline exceeded; worker cleanup attempted')
    except KeyboardInterrupt:
        record.update(status='interrupted', failure='operator interrupted execution')
    except Exception as exc:
        record.update(status='failed', failure=f'{type(exc).__name__}: {exc}')
    finally:
        partial = run / 'results.json'
        if record['status'] != 'completed-not-quality-approved' and partial.is_file():
            try:
                data = load(partial)
                validate_worker_results(data, request, record['request_sha256'])
                count = data.get('successful_requests')
                completed = data.get('generation_calls_completed')
                if type(completed) is int and 0 < completed <= operation['limits']['max_requests'] and type(count) is int and 0 <= count <= completed:
                    record.update(inference_executed=True, evidence='partial-real-checkpoint-inference-not-completed',
                                  partial_requests=count, generation_calls_completed=completed, partial_results_sha256=digest(partial))
            except (ValueError, OSError, TypeError, AttributeError, UnboundLocalError):
                record['partial_results_unreadable_or_mismatched'] = True
        containment_file = run / 'containment.json'
        if containment_file.is_file():
            try:
                applied = load(containment_file)
                if applied.get('request_sha256') == record.get('request_sha256') and isinstance(applied.get('report'), dict):
                    record['containment'] = applied['report']
            except (ValueError, OSError, AttributeError):
                record['containment_report_invalid'] = True
        try:
            finalize_grant(approval_store, approval_id, operation)
        except LabError as exc:
            record.update(status='failed', authorization_finalization_error=str(exc))
        record['actual_duration_seconds'] = time.monotonic() - start
        atomic_json(run / 'experiment.json', record)
    return record
