#!/usr/bin/env python3
"""Verify/update the complete source package; never include artifacts or caches."""
import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lia_lab.io import LabError, load, json_loads, atomic_json
from jsonschema import Draft202012Validator

ROOT_FILES = {".gitignore", "README.md", "AGENTS.md", "pyproject.toml", "requirements.lock", "requirements-api.lock"}
TREES = ("docs", "configs", "templates", "src", "tests", "scripts", ".agents", ".codex", ".github")
EXTENSIONS = {".md", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".py", ".txt"}


def package_paths(root=ROOT):
    paths = [root / n for n in ROOT_FILES if (root / n).is_file()]
    for tree in TREES:
        paths += [p for p in (root / tree).rglob("*") if p.is_file()
                  and p.suffix in EXTENSIONS and not any(
                      x == "__pycache__" or x.endswith(".egg-info") for x in p.parts)
                  and p.relative_to(root).as_posix() not in {".codex/config.toml", ".codex/config.local.toml"}]
    for p in paths:
        if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
            raise LabError(f"package symlink: {p}")
    return sorted(set(paths))


def manifest(root=ROOT):
    return {"package": "Lia Model Lab", "version": "0.4.0", "status": "inference-infrastructure-not-model-release",
            "manifest_scope": "All maintained source/documentation/config/fixture/skill/agent files; excludes itself, Git, caches, installed metadata and ML artifacts.",
            "files": [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size,
                       "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in package_paths(root)]}


def validate(root=ROOT, check_manifest=True):
    paths = package_paths(root)
    counts = {"json": 0, "yaml": 0, "toml": 0, "links": 0, "skills": 0, "agents": 0}
    # Retired source name is constructed to avoid keeping a literal reference to it.
    retired = "Lia_" + "Model_" + "Blueprint.md"
    for p in paths:
        text = p.read_text(encoding="utf-8")
        if retired in text or re.search(r"^(<<<<<<< |=======\s*$|>>>>>>> )", text, re.M):
            raise LabError(f"retired reference/conflict marker in {p}")
        if p.suffix in {".json", ".yaml", ".yml"}:
            data = load(p)
            counts["json" if p.suffix == ".json" else "yaml"] += 1
            if p.name.endswith(".schema.json"):
                Draft202012Validator.check_schema(data)
        elif p.suffix == ".jsonl":
            for line in text.splitlines(): json_loads(line)
        elif p.suffix == ".toml":
            tomllib.loads(text); counts["toml"] += 1
        if p.suffix == ".md":
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in link or link.startswith(("#", "mailto:")): continue
                target = link.split("#", 1)[0]
                if target and not (p.parent / target).exists():
                    raise LabError(f"broken link {p.relative_to(root)}: {link}")
                counts["links"] += 1
        if p.name == "SKILL.md":
            if not text.startswith("---\n"):
                raise LabError("missing skill frontmatter")
            import yaml
            from lia_lab.io import StrictLoader
            front = yaml.load(text.split("---", 2)[1], Loader=StrictLoader)
            if front.get("name") != p.parent.name or not front.get("description"):
                raise LabError(f"invalid skill identity {p}")
            for section in ("## Procedimento", "## Saída e ownership", "## Critério de conclusão", "## Limites"):
                if section not in text: raise LabError(f"incomplete skill: {p}")
            counts["skills"] += 1
        if p.parent == root / ".codex/agents":
            agent = tomllib.loads(text)
            if agent.get("name") != p.stem or not agent.get("description") or not agent.get("developer_instructions"):
                raise LabError(f"invalid agent profile: {p}")
            if "Read only" not in agent["developer_instructions"]:
                raise LabError("reviewers must be read-only by instruction")
            references = re.findall(r"\.agents/skills/[a-z-]+/SKILL\.md", text)
            if not references: raise LabError("profile has no explicit skill")
            for ref in references:
                if not (root / ref).is_file(): raise LabError(f"missing profile skill: {ref}")
            counts["agents"] += 1
    catalog = load(root / "configs/model-candidates.yaml")
    lfm = [c for c in catalog["candidates"] if c.get("family") == "LFM3"]
    schema = load(root / "src/lia_lab/schemas/research-candidate.schema.json")
    expected = {"LiquidAI/" + name for name in (
        "LFM3-1.7B", "LFM3-1.7B-Base", "LFM3-VL-2B", "LFM3-Audio-2B", "LFM3-Omni-2B", "d1-2B", "d1-Omni-2B")}
    expected |= {name + "-GGUF" for name in expected if not name.endswith("-Base")}
    if len(lfm) != 13 or {c["model_id"] for c in lfm} != expected:
        raise LabError("LFM3 research registry missing/duplicate/unconfirmed identity")
    for candidate in lfm:
        errors = list(Draft202012Validator(schema).iter_errors(candidate))
        if errors:
            raise LabError("invalid LFM3 research contract: " + errors[0].message)
    if counts["skills"] != 9 or counts["agents"] != 7:
        raise LabError("unexpected skills/agents registry; update ownership contract deliberately")
    if check_manifest and load(root / "PACKAGE-MANIFEST.json") != manifest(root):
        raise LabError("manifest coverage/hash mismatch; regenerate after final edits")
    return {"status": "PASS", "scope": "repository-integrity-not-ML", "files": len(paths), **counts}


def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write_manifest:
            validate(check_manifest=False)
            atomic_json(ROOT / "PACKAGE-MANIFEST.json", manifest())
        print(json.dumps(validate(), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 1


if __name__ == "__main__": sys.exit(main())
