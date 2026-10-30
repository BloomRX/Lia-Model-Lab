"""Strict serialization, bounded path ownership and atomic publication."""
import hashlib
import json
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


def json_loads(text):
    return json.loads(text, object_pairs_hook=_unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(LabError(f"nonfinite {x}")))


class StrictLoader(yaml.SafeLoader):
    pass


def _yaml_mapping(loader, node):
    return _unique((loader.construct_object(k), loader.construct_object(v)) for k, v in node.value)


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _yaml_mapping)


def load(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return yaml.load(text, Loader=StrictLoader) if path.suffix in {".yaml", ".yml"} else json_loads(text)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
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
