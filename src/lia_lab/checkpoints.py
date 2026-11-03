"""Seal authorized LOCAL safetensors snapshots; never acquires weights or accepts terms."""
from pathlib import Path, PurePosixPath
import re
from safetensors import safe_open
from jsonschema import Draft202012Validator
from .io import LabError, atomic_json, digest, load

REV = re.compile(r'^[0-9a-f]{40}$')
# Only architecture contracts verified against TF 5.22.1 are executable.
from .model_backends import select_backend
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
        if not p.is_file() and not p.is_dir():
            raise LabError('snapshot special files forbidden: ' + p.name)
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
    if not isinstance(config, dict):
        raise LabError('invalid model config')
    if config.get('quantization_config'):
        raise LabError('prequantized safetensors require a separate reviewed loader; reference path is unquantized')
    select_backend(config)
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
    if len(weights) > 1 and 'model.safetensors.index.json' not in files:
        raise LabError('multiple weight files require an explicit shard index')
    if 'model.safetensors.index.json' in files:
        index = load(root / 'model.safetensors.index.json')
        if not isinstance(index, dict) or not isinstance(index.get('weight_map'), dict):
            raise LabError('invalid shard index mapping')
        weight_map = index['weight_map']
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
    atomic_json(output, result, overwrite=False)
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


def tensor_shapes(directory):
    """Headers only, no Torch; callers also verify the sealed inventory."""
    shapes = {}
    try:
        for path in sorted(Path(directory).rglob('*.safetensors')):
            with safe_open(path, framework='numpy') as handle:
                for name in handle.keys():
                    if name in shapes:
                        raise LabError('duplicate checkpoint parameter')
                    shapes[name] = tuple(handle.get_slice(name).get_shape())
    except Exception as exc:
        raise LabError('cannot establish checkpoint tensor shapes') from exc
    return shapes


def checkpoint_capacity(directory):
    """Config-derived verified parameter count, or None: never trust file count alone.

    Explicit dense Qwen3 and fixed-revision Qwen3.5 contracts only. This is parameter/load
    sizing, not a universal KV-cache/activation bound or real-runtime validation.
    """
    from .model_backends import qwen3_shapes
    from .qwen35_contract import shapes as qwen35_shapes, dtype_for
    import math
    config = load(Path(directory) / 'config.json')
    multimodal = config.get('model_type') == 'qwen3_5' if isinstance(config,dict) else False
    expected = qwen35_shapes(config) if multimodal else qwen3_shapes(config)
    if expected is None:
        return None
    if tensor_shapes(directory) != expected:
        raise LabError('checkpoint differs from explicit architecture parameter names/shapes')
    if multimodal:
        inventory = tensor_inventory(directory)
        if any(item['dtype'] != dtype_for(name) for name,item in inventory.items()):
            raise LabError('Qwen3.5 checkpoint dtype differs from explicit architecture contract')
        index = load(Path(directory)/'model.safetensors.index.json')
        if index.get('weight_map') != {k:v['shard'] for k,v in inventory.items()}:
            raise LabError('Qwen3.5 shard index differs from tensor inventory')
        expected_bytes = sum(math.prod(item['shape'])*(4 if item['dtype']=='F32' else 2) for item in inventory.values())
        if index.get('metadata',{}).get('total_size') != expected_bytes:
            raise LabError('Qwen3.5 shard index byte size mismatch')
    return sum(math.prod(shape) for shape in expected.values())


def tensor_inventory(directory):
    """Headers only: dtype, shape and shard; never materialize pretrained weights."""
    root=Path(directory); result={}
    try:
        for path in sorted(root.rglob('*.safetensors')):
            if path.is_symlink(): raise LabError('tensor shard symlink forbidden')
            with safe_open(path,framework='numpy') as handle:
                for name in handle.keys():
                    if name in result: raise LabError('duplicate checkpoint parameter')
                    tensor=handle.get_slice(name)
                    result[name]=dict(shape=tuple(tensor.get_shape()),dtype=tensor.get_dtype(),shard=path.relative_to(root).as_posix())
    except Exception as exc:
        raise LabError('cannot establish checkpoint tensor inventory') from exc
    return result
