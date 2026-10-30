"""Text/tool JSONL v1: strict validation, exact dedup and group-level splitting.

This is a bounded in-memory pilot factory, not a multimodal or production pipeline.
"""
import hashlib
import json
import random
import re
import unicodedata
from collections import defaultdict
from importlib.resources import files
from pathlib import Path
from jsonschema import Draft202012Validator
from .io import LabError, canonical, digest, json_loads, atomic_json

SCHEMA = json_loads(files("lia_lab").joinpath("schemas/example.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def validate_example(row):
    errors = sorted(VALIDATOR.iter_errors(row), key=lambda e: str(list(e.path)))
    if errors:
        raise LabError(errors[0].message)
    provenance, privacy = row["provenance"], row["privacy"]
    if provenance["license"].upper() in {"UNKNOWN", "PENDING", "PENDING_REVIEW"}:
        raise LabError("unreviewed license")
    if provenance["synthetic"] and not provenance.get("generator"):
        raise LabError("synthetic examples require generator provenance")
    if privacy["classification"] == "consented" and not privacy.get("consent_ref"):
        raise LabError("personal data requires consent reference (not consent document)")
    pending, seen = set(), set()
    messages = row["messages"]
    if messages[0]["role"] not in {"system", "user"}:
        raise LabError("conversation must start with system/user")
    for index, message in enumerate(messages):
        role = message["role"]
        if role == "system" and index != 0:
            raise LabError("system message only allowed at start")
        if not message.get("content") and not message.get("tool_calls"):
            raise LabError("message needs content or tool calls")
        if role != "assistant" and message.get("tool_calls"):
            raise LabError("only assistant can call tools")
        if role != "tool" and "tool_call_id" in message:
            raise LabError("only tool result can reference a call")
        if role == "tool":
            call_id = message.get("tool_call_id")
            if call_id not in pending:
                raise LabError("orphan/repeated tool result")
            pending.remove(call_id)
        elif pending:
            raise LabError("all tool results must arrive before next turn")
        for call in message.get("tool_calls", []):
            if call["id"] in seen:
                raise LabError("duplicate tool call id")
            seen.add(call["id"])
            pending.add(call["id"])
    if pending or messages[-1]["role"] != "assistant" or messages[-1].get("tool_calls"):
        raise LabError("trajectory must finish with assistant response after tool results")
    return row


def read_examples(path, max_bytes=16 * 1024 * 1024, max_rows=10000):
    path = Path(path)
    if path.stat().st_size > max_bytes:
        raise LabError("pilot input exceeds byte limit")
    rows, ids = [], set()
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                raise LabError(f"blank JSONL line {line_no}")
            if line_no > max_rows:
                raise LabError("pilot row limit exceeded")
            try:
                row = validate_example(json_loads(line))
            except (ValueError, KeyError) as exc:
                raise LabError(f"invalid example at line {line_no}: {exc}") from exc
            if row["id"] in ids:
                raise LabError("duplicate example id")
            ids.add(row["id"])
            rows.append(row)
    if not rows:
        raise LabError("empty dataset")
    return rows


def fingerprint(row):
    """Normalize natural-language whitespace, but preserve exact tool arguments."""
    messages = []
    for msg in row["messages"]:
        msg = dict(msg)
        if "content" in msg:
            msg["content"] = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", msg["content"])).strip()
        messages.append(msg)
    return hashlib.sha256(canonical(messages).encode()).hexdigest()


def prepare(rows, seed=42, ratios=(0.8, 0.1, 0.1)):
    if len(ratios) != 3 or any(x <= 0 for x in ratios) or abs(sum(ratios) - 1) > 1e-9:
        raise LabError("three positive split ratios must sum to 1")
    # Union groups linked by duplicate content BEFORE dedup; preserve full lineage.
    parent = {r["group_id"]: r["group_id"] for r in rows}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    first, kept, duplicate_ids = {}, [], []
    for row in sorted(rows, key=lambda r: r["id"]):
        validate_example(row)
        key = fingerprint(row)
        if key in first:
            original = first[key]
            a, b = find(original["group_id"]), find(row["group_id"])
            parent[max(a, b)] = min(a, b)
            duplicate_ids.append(row["id"])
        else:
            first[key] = row
            kept.append(row)
    groups = defaultdict(list)
    for row in kept:
        groups[find(row["group_id"])].append(row)
    keys = sorted(groups)
    if len(keys) < 3:
        raise LabError("need at least three independent groups after duplicate linkage")
    random.Random(seed).shuffle(keys)
    n = len(keys)
    train_n = min(n - 2, max(1, int(n * ratios[0])))
    val_n = min(n - train_n - 1, max(1, int(n * ratios[1])))
    assignments = [keys[:train_n], keys[train_n:train_n + val_n], keys[train_n + val_n:]]
    splits = {name: [r for k in ks for r in groups[k]]
              for name, ks in zip(("train", "validation", "test"), assignments)}
    return splits, {"removed_duplicate_ids": duplicate_ids, "group_counts": dict(zip(splits, map(len, assignments))),
                    "lineage": {k: find(k) for k in sorted(parent)}}


def build_dataset(source, output, seed=42):
    output = Path(output)
    if output.exists():
        raise LabError("output must not exist; use a new dataset version")
    source_hash = digest(source)
    rows = read_examples(source)
    if digest(source) != source_hash:
        raise LabError("source changed while preparing dataset")
    splits, report = prepare(rows, seed)
    # All validation occurs before writing. Incomplete outputs are never promoted.
    output.mkdir(parents=True)
    manifest = {"schema_version": 1, "status": "fixture-or-candidate-not-approved",
                "source_sha256": source_hash, "seed": seed, "dedup": "nfkc-whitespace-messages-v1",
                "report": report, "splits": {}}
    for name, examples in splits.items():
        path = output / f"{name}.jsonl"
        path.write_text("".join(canonical(r) + "\n" for r in examples), encoding="utf-8")
        manifest["splits"][name] = {"path": path.name, "sha256": digest(path), "count": len(examples)}
    atomic_json(output / "manifest.json", manifest)
    return manifest
