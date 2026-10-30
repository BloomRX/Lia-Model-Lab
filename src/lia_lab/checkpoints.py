"""Seal authorized LOCAL safetensors snapshots; never acquires weights or accepts terms."""
from pathlib import Path, PurePosixPath
import re
from safetensors import safe_open
from jsonschema import Draft202012Validator
from .io import LabError, atomic_json, digest, load

REV = re.compile(r'^[0-9a-f]{40}$')
MODEL_TYPES = {'qwen2', 'qwen3', 'qwen3_5', 'gemma4'}
SAFE_SUFFIXES = {'.json', '.safetensors', '.txt', '.md', '.jinja', '.model'}


def validate_snapshot_manifest(manifest):
    schema = load(Path(__file__).parent / 'schemas/model-snapshot.schema.json')
    errors = list(Draft202012Validator(schema).iter_errors(manifest))
    if errors:
        raise LabError('invalid snapshot manifest schema: ' + errors[0].message)


def files_at(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise LabError('snapshot must be a real directory, not a symlink')
    files = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise LabError('snapshot symlinks forbidden; materialize an authorized standalone snapshot')
        if p.is_file():
            if p.suffix not in SAFE_SUFFIXES and p.name not in {'LICENSE', 'NOTICE'}:
                raise LabError('snapshot contains unsupported file: ' + p.name)
            files[p.relative_to(root).as_posix()] = {'bytes': p.stat().st_size, 'sha256': digest(p)}
    if 'config.json' not in files or 'tokenizer_config.json' not in files:
        raise LabError('config and tokenizer config required')
    weights = [n for n in files if n.endswith('.safetensors')]
    if not weights:
        raise LabError('local safetensors weights required; pickle/GGUF not this backend')
    config = load(root / 'config.json')
    if config.get('quantization_config'):
        raise LabError('prequantized safetensors require a separate reviewed loader; reference path is unquantized')
    if config.get('model_type') not in MODEL_TYPES:
        raise LabError('unsupported model_type; add and test an explicit backend mapping')
    # Read real headers without allocating model tensors.
    params = 0
    keys = set()
    tensor_shards = {}
    for name in weights:
        try:
            handle = safe_open(root / name, framework='numpy')
        except Exception as exc:
            raise LabError('invalid local safetensors header: ' + name) from exc
        with handle:
            for key in handle.keys():
                if key in keys:
                    raise LabError('duplicate tensor across shards')
                keys.add(key)
                tensor_shards[key] = name
                shape = handle.get_slice(key).get_shape()
                count = 1
                for size in shape:
                    count *= size
                params += count
    if 'model.safetensors.index.json' in files:
        weight_map = load(root / 'model.safetensors.index.json')['weight_map']
        if weight_map != tensor_shards or set(weight_map.values()) != set(weights):
            raise LabError('shard index coverage mismatch')
        for name in weight_map.values():
            if str(PurePosixPath(name)) != name or '..' in PurePosixPath(name).parts:
                raise LabError('invalid shard name')
    return files, params


def seal_snapshot(directory, output, model_id, revision, license_id, license_file, review_ref):
    if not REV.fullmatch(revision) or not re.fullmatch(r'[\w.-]+/[\w.-]+', model_id):
        raise LabError('exact model ID and immutable 40-hex upstream revision required')
    if license_id != 'Apache-2.0' or not review_ref or review_ref.startswith('PENDING'):
        raise LabError('pilot allowlist requires reviewed Apache-2.0 and human authorization reference')
    if Path(directory).is_symlink():
        raise LabError("snapshot root symlink forbidden")
    directory, output = Path(directory).resolve(), Path(output)
    if output.resolve().is_relative_to(directory) or output.exists():
        raise LabError('manifest must be new and outside snapshot')
    files, params = files_at(directory)
    if license_file not in files:
        raise LabError('reviewed license must be an included local file')
    result = {'schema_version': 1, 'model_id': model_id, 'revision': revision,
              'source': f'https://huggingface.co/{model_id}/tree/{revision}',
              'license': {'id': license_id, 'file': license_file, 'review_ref': review_ref},
              'files': files, 'stored_tensor_elements': params, 'total_bytes': sum(x['bytes'] for x in files.values()),
              'evidence': 'local-integrity-and-operator-attestation-not-upstream-authenticity',
              'release_approved': False}
    validate_snapshot_manifest(result)
    atomic_json(output, result)
    return result


def verify_snapshot(directory, manifest_path):
    manifest = load(manifest_path)
    validate_snapshot_manifest(manifest)
    if manifest.get('schema_version') != 1 or not REV.fullmatch(manifest.get('revision', '')):
        raise LabError('invalid snapshot manifest revision/schema')
    if manifest.get('source') != f'https://huggingface.co/{manifest["model_id"]}/tree/{manifest["revision"]}':
        raise LabError('snapshot origin mismatch')
    if manifest['license']['id'] != 'Apache-2.0' or not manifest['license']['review_ref']:
        raise LabError('license review absent')
    files, params = files_at(Path(directory))
    if manifest['files'] != files or manifest['stored_tensor_elements'] != params or manifest['total_bytes'] != sum(x['bytes'] for x in files.values()):
        raise LabError('snapshot inventory/hash/size mismatch')
    if manifest['license']['file'] not in files:
        raise LabError('license file missing')
    return manifest
