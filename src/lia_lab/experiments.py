"""Reproducible plans and local adapter packaging. Never starts training."""
import importlib.metadata
import math
import platform
import re
import shutil
import subprocess
from pathlib import Path
from .datasets import read_examples, fingerprint
from .io import LabError, atomic_json, canonical, digest, load, owned, roots, source_snapshot_hash

SHA = re.compile(r"^[a-f0-9]{64}$")
REV = re.compile(r"^[a-f0-9]{40}$")
ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$")


def verify_dataset(path):
    path = Path(path)
    manifest = load(path)
    if manifest.get("schema_version") != 1:
        raise LabError("unsupported dataset manifest schema")
    if set(manifest["splits"]) != {"train", "validation", "test"}:
        raise LabError("all three splits required")
    groups, contents, ids = set(), set(), set()
    for name, entry in manifest["splits"].items():
        file = owned(path.parent, entry["path"])
        if digest(file) != entry["sha256"]:
            raise LabError(f"split hash mismatch: {name}")
        rows = read_examples(file)
        if len(rows) != entry["count"]:
            raise LabError("split count mismatch")
        current_groups = {manifest["report"]["lineage"][r["group_id"]] for r in rows}
        current_contents = {fingerprint(r) for r in rows}
        current_ids = {r["id"] for r in rows}
        if groups & current_groups or contents & current_contents or ids & current_ids:
            raise LabError("cross-split leakage")
        groups |= current_groups
        contents |= current_contents
        ids |= current_ids
    return manifest


def validate_plan(config):
    if "PENDING" in canonical(config):
        raise LabError("planning placeholders must be resolved before registration")
    required = {"schema_version", "experiment_id", "status", "base", "dataset_manifest", "seed",
                "training", "environment", "budget", "authorization_ref"}
    if set(config) != required or config["schema_version"] != 1 or config["status"] != "planned":
        raise LabError("invalid plan fields/version/status")
    if not ID.fullmatch(config["experiment_id"]):
        raise LabError("invalid experiment id")
    base = config["base"]
    for field in ("revision", "tokenizer_revision"):
        if not REV.fullmatch(base.get(field, "")):
            raise LabError(f"base {field} must be immutable 40-hex revision")
    for field in ("weights_sha256", "chat_template_sha256"):
        if not SHA.fullmatch(base.get(field, "")):
            raise LabError(f"base {field} required")
    if not base.get("model_id") or not base.get("license_review_ref"):
        raise LabError("base identity/license review required")
    if type(config["seed"]) is not int or config["seed"] < 0:
        raise LabError("seed must be nonnegative integer")
    t = config["training"]
    if t.get("method") != "sft" or t.get("adapter") not in {"lora", "qlora"}:
        raise LabError("only SFT LoRA/QLoRA supported by planning contract")
    for field in ("rank", "alpha", "max_seq_length", "microbatch", "gradient_accumulation", "max_steps", "save_steps"):
        if type(t.get(field)) is not int or t[field] <= 0:
            raise LabError(f"positive integer required: {field}")
    if not isinstance(t.get("learning_rate"), (int, float)) or not 0 < t["learning_rate"] < 1:
        raise LabError("invalid learning rate")
    if not t.get("target_modules") or not all(isinstance(x, str) and x for x in t["target_modules"]):
        raise LabError("explicit inspected target modules required")
    if t.get("compute_dtype") not in {"bfloat16", "float16"}:
        raise LabError("invalid compute dtype")
    if t["adapter"] == "qlora" and t.get("quantization") != "nf4-double-quant":
        raise LabError("QLoRA requires explicit NF4 double quant contract")
    if t["adapter"] == "lora" and t.get("quantization") != "none":
        raise LabError("LoRA reference is not quantized")
    env = config["environment"]
    for key in ("python", "dependencies", "hardware", "backend", "driver"):
        if not env.get(key):
            raise LabError(f"planned environment missing {key}")
    if env["backend"] not in {"cpu", "cuda", "rocm"}:
        raise LabError("training backend unproven; Vulkan is inference-only here")
    if not isinstance(env["dependencies"], dict) or not {"torch", "transformers", "peft", "trl"}.issubset(env["dependencies"]) or not all(
        isinstance(v, str) and re.fullmatch(r"\d+\.\d+\.\d+", v) for v in env["dependencies"].values()
    ):
        raise LabError("dependency versions must be exact x.y.z")
    for key in ("max_hours", "max_cost"):
        value = config["budget"].get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise LabError("explicit nonnegative budget required")
    if not config["budget"].get("currency"):
        raise LabError("budget currency required")
    # authorization_ref may be null: a valid plan still authorizes NOTHING.
    return config


def register_plan(config_path, research_root, approved_root):
    root, _ = roots(research_root, approved_root)
    config = validate_plan(load(config_path))
    dataset_path = (Path(config_path).parent / config["dataset_manifest"]).resolve()
    verify_dataset(dataset_path)
    run = owned(root, "experiments/" + config["experiment_id"])
    if run.exists():
        raise LabError("experiment id already registered; no overwrite")
    try:
        code_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except subprocess.CalledProcessError:
        raise LabError("registration requires a git checkout") from None
    checkout = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    source_hash = source_snapshot_hash()
    git_dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True))
    record = {"schema_version": 1, "status": "planned", "training_executed": False,
              "git_dirty": git_dirty, "source_snapshot_sha256": source_hash,
              "dependency_lock_sha256": digest(checkout / "requirements.lock"),
              "config": config, "config_sha256": digest(config_path),
              "dataset_manifest_sha256": digest(dataset_path), "code_commit": code_commit,
              "observed_planner_environment": {"python": platform.python_version(), "os": platform.platform(),
                  "dependencies": {p: importlib.metadata.version(p) for p in ("PyYAML", "jsonschema", "safetensors", "numpy")}},
              "resume": {"checkpoint": None, "optimizer": None, "scheduler": None, "rng": None},
              "actual_duration_seconds": None, "actual_cost": None}
    atomic_json(run / "experiment.json", record)
    return record


def verify_resume(record_path, checkpoint_manifest):
    record, checkpoint = load(record_path), load(checkpoint_manifest)
    if checkpoint["config_sha256"] != record["config_sha256"]:
        raise LabError("cannot resume with changed config")
    if checkpoint["dataset_manifest_sha256"] != record["dataset_manifest_sha256"]:
        raise LabError("cannot resume with changed data")
    for key in ("code_commit", "source_snapshot_sha256", "dependency_lock_sha256"):
        if checkpoint.get(key) != record.get(key) or key not in checkpoint:
            raise LabError("cannot resume with changed or missing source/environment identity")
    if set(checkpoint["files"]) != {"adapter", "optimizer", "scheduler", "rng"}:
        raise LabError("resume requires adapter/optimizer/scheduler/RNG")
    for entry in checkpoint["files"].values():
        if digest(owned(Path(checkpoint_manifest).parent, entry["path"])) != entry["sha256"]:
            raise LabError("resume artifact hash mismatch")
    return {"status": "verified-metadata-only", "resumed": False}


def inspect_adapter(directory):
    """PEFT config + local safetensors validation; no pickle/code execution."""
    from safetensors import safe_open
    directory = Path(directory).resolve()
    for name in ("adapter_config.json", "provenance.json", "adapter_model.safetensors"):
        owned(directory, name)
    cfg = load(directory / "adapter_config.json")
    if cfg.get("peft_type") != "LORA" or not cfg.get("target_modules") or type(cfg.get("r")) is not int or cfg["r"] <= 0:
        raise LabError("invalid LoRA adapter config")
    provenance = load(directory / "provenance.json")
    if not REV.fullmatch(provenance.get("base_revision", "")):
        raise LabError("adapter requires immutable base revision")
    if cfg.get("revision") is not None and cfg["revision"] != provenance["base_revision"]:
        raise LabError("adapter config/provenance revision mismatch")
    if cfg.get("base_model_name_or_path") != provenance.get("base_model_id"):
        raise LabError("base identity mismatch")
    if not SHA.fullmatch(provenance.get("base_weights_sha256", "")):
        raise LabError("base weights hash required")
    weights = owned(directory, "adapter_model.safetensors")
    # Ensure metadata files also do not escape via symlinks.
    for name in ("adapter_config.json", "provenance.json"):
        owned(directory, name)
    try:
        with safe_open(weights, framework="numpy") as f:
            keys = list(f.keys())
            if not keys or any(not ("lora_A" in k or "lora_B" in k) for k in keys):
                raise LabError("unsupported adapter tensors")
            # Validate paired rank dimensions without loading full tensors.
            for k in keys:
                partner = k.replace("lora_A", "lora_B") if "lora_A" in k else k.replace("lora_B", "lora_A")
                if partner not in keys:
                    raise LabError("unpaired LoRA matrices")
                shape = f.get_slice(k).get_shape()
                if len(shape) != 2 or shape[0 if "lora_A" in k else 1] != cfg["r"]:
                    raise LabError("adapter rank mismatch")
    except LabError:
        raise
    except Exception as exc:
        raise LabError("invalid safetensors artifact") from exc
    return {"status": "structural-only-not-runtime-validated", "base": provenance,
            "files": {n: digest(directory / n) for n in
                      ("adapter_config.json", "adapter_model.safetensors", "provenance.json")}}


def export_adapter(source, destination):
    report = inspect_adapter(source)
    destination = Path(destination)
    if destination.exists():
        raise LabError("export destination exists")
    if destination.resolve().is_relative_to(Path(source).resolve()):
        raise LabError("export destination overlaps source")
    destination.mkdir(parents=True)
    for name, expected in report["files"].items():
        shutil.copyfile(Path(source) / name, destination / name)
        if digest(destination / name) != expected:
            raise LabError("export integrity mismatch; do not promote")
    atomic_json(destination / "export-manifest.json", report)
    return report
