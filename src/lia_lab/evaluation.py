"""Offline paired exact-match scorer. Does not run inference or judge persona."""
from .io import LabError, canonical


def compare(runs):
    if len(runs) < 2:
        raise LabError("need baseline and adapter runs")
    if len({r["variant"] for r in runs}) != len(runs):
        raise LabError("duplicate variant")
    if not {"base", "adapter"}.issubset({r["variant"] for r in runs}):
        raise LabError("base and adapter mandatory")
    reference = runs[0]
    for r in runs:
        if r["variant"] not in {"base", "adapter", "adapter-quantized"}:
            raise LabError("unknown variant")
        for key in ("dataset_sha256", "base_revision", "protocol"):
            if canonical(r[key]) != canonical(reference[key]):
                raise LabError(f"incomparable runs: {key}")
        if r["split"] != "test":
            raise LabError("comparison requires sealed test split")
        for key in ("model_artifact_sha256", "dataset_sha256"):
            from .experiments import SHA
            if not SHA.fullmatch(r[key]):
                raise LabError(f"invalid {key}")
        from .experiments import REV
        if not REV.fullmatch(r["base_revision"]):
            raise LabError("invalid revision")
        if not r.get("environment") or not r.get("evidence_ref"):
            raise LabError("environment and prediction provenance required")
        protocol = r["protocol"]
        required = {"template_sha256", "prompt_sha256", "tool_schema_sha256", "seed", "max_tokens", "context_limit", "sampling"}
        if set(protocol) != required:
            raise LabError("incomplete evaluation protocol")
        for key in ("template_sha256", "prompt_sha256", "tool_schema_sha256"):
            if not SHA.fullmatch(protocol[key]):
                raise LabError("invalid protocol hash")
        if type(protocol["seed"]) is not int or protocol["seed"] < 0:
            raise LabError("invalid protocol seed")
        for key in ("max_tokens", "context_limit"):
            if type(protocol[key]) is not int or protocol[key] <= 0:
                raise LabError("invalid context/output budget")
        if not isinstance(protocol["sampling"], dict) or not protocol["sampling"]:
            raise LabError("explicit sampling parameters required")
        rows = r["predictions"]
        ids = [p["id"] for p in rows]
        if not ids or len(ids) != len(set(ids)):
            raise LabError("empty/duplicate predictions")
        if any(not isinstance(p["prediction"], str) or not isinstance(p["expected"], str)
               or not p["capability"] for p in rows):
            raise LabError("invalid prediction/ground truth")
    expected = {p["id"]: (p["expected"], p["capability"]) for p in reference["predictions"]}
    scores = {}
    for r in runs:
        actual = {p["id"]: (p["expected"], p["capability"]) for p in r["predictions"]}
        if actual != expected:
            raise LabError("prediction IDs or ground truth differ")
        by_capability = {}
        for p in r["predictions"]:
            counts = by_capability.setdefault(p["capability"], {"correct": 0, "total": 0})
            counts["total"] += 1
            counts["correct"] += int(p["prediction"] == p["expected"])
        scores[r["variant"]] = {k: {**v, "exact_match": v["correct"] / v["total"]}
                                for k, v in by_capability.items()}
    regressions = []
    for variant, metrics in scores.items():
        if variant == "base":
            continue
        for cap, value in metrics.items():
            delta = value["exact_match"] - scores["base"][cap]["exact_match"]
            if delta < 0:
                regressions.append({"variant": variant, "capability": cap, "delta": delta})
    return {"status": "offline-scoring-not-model-validation", "metric": "exact-match-v1",
            "scores": scores, "regressions": regressions,
            "release_approved": False}
