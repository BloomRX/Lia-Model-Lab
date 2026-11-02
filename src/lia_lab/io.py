"""Strict serialization, bounded path ownership and atomic publication."""
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
import yaml


class LabError(ValueError):
    """Invalid input; no artifact should be promoted."""


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LabError(f"duplicate key: {key}")
        result[key] = value
    return result


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise LabError('nonfinite numeric literal')
    return value


def json_loads(text):
    return json.loads(text, object_pairs_hook=_unique, parse_float=_finite_float,
                      parse_constant=lambda x: (_ for _ in ()).throw(LabError(f"nonfinite {x}")))


class StrictLoader(yaml.SafeLoader):
    pass


def _yaml_mapping(loader, node):
    return _unique((loader.construct_object(k), loader.construct_object(v)) for k, v in node.value)


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _yaml_mapping)


def _yaml_float(loader, node):
    value = yaml.SafeLoader.construct_yaml_float(loader, node)
    if not math.isfinite(value):
        raise LabError('nonfinite YAML number')
    return value


StrictLoader.add_constructor('tag:yaml.org,2002:float', _yaml_float)


def load(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        return yaml.load(text, Loader=StrictLoader) if path.suffix in {".yaml", ".yml"} else json_loads(text)
    except yaml.YAMLError as exc:
        raise LabError('invalid YAML: ' + str(path)) from exc


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def atomic_json(path, value, *, overwrite=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        if overwrite:
            os.replace(tmp, path)
        else:
            # Publish only a fully written file; link is atomic and refuses existing
            # paths (including symlinks). No check-then-replace race for new artifacts.
            os.link(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def owned(root, name):
    root = Path(root).resolve()
    target = (root / name).resolve()
    if not target.is_relative_to(root) or target == root:
        raise LabError("path must remain inside owned root")
    return target


def roots(research_root, approved_root):
    research, approved = Path(research_root).resolve(), Path(approved_root).resolve()
    if research.is_relative_to(approved) or approved.is_relative_to(research):
        raise LabError("research and application-approved storage must be disjoint")
    return research, approved


def source_snapshot_hash():
    """Fingerprint executing package source and schemas, including uncommitted edits."""
    module = Path(__file__).resolve().parent
    paths = sorted([*module.rglob('*.py'), *module.joinpath('schemas').glob('*.json')])
    return hashlib.sha256(canonical({p.relative_to(module).as_posix(): digest(p) for p in paths}).encode()).hexdigest()
