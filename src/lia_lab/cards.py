"""Generate review drafts from verified local metadata, never invent approval."""
from pathlib import Path
from .experiments import verify_dataset, inspect_adapter
from .io import LabError, digest


def write_card(kind, source, output):
    output = Path(output)
    if output.exists():
        raise LabError("card output exists; review/update explicitly")
    if kind == "dataset":
        manifest = verify_dataset(source)
        text = "# Dataset card — draft for review\n\nStatus: DRAFT / NOT APPROVED FOR TRAINING OR PUBLICATION\n\n"
        text += f"Manifest SHA-256: `{digest(source)}`\n\nSeed: {manifest['seed']}\n\n"
        text += "| Split | Examples | SHA-256 |\n|---|---:|---|\n"
        for name, entry in manifest["splits"].items():
            text += f"| {name} | {entry['count']} | {entry['sha256']} |\n"
        text += "\nSource/license/rights/consent review, curator, purpose, retention, deletion and publication: PENDING HUMAN REVIEW.\n"
        text += "Exact dedup/group isolation verified structurally; no semantic dedup, privacy or legal certification.\n"
    elif kind == "model":
        report = inspect_adapter(source)
        text = "# Model card — local adapter draft\n\nStatus: STRUCTURAL ONLY / NOT RUNTIME VALIDATED / NO RELEASE APPROVAL\n\n"
        text += f"Base ID: `{report['base']['base_model_id']}`\n\nBase revision: `{report['base']['base_revision']}`\n\n"
        text += "| Artifact | SHA-256 |\n|---|---|\n"
        for name, sha in report["files"].items():
            text += f"| {name} | {sha} |\n"
        text += "\nTraining/data lineage, license/notices, evaluation base/adapter/quantized, intended uses, limitations and runtime compatibility: PENDING REVIEW.\n"
    else:
        raise LabError("unknown card kind")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: never silently overwrite a curator's existing card.
    with output.open("x", encoding="utf-8") as stream:
        stream.write(text)
    return {"status": "draft-not-approved", "sha256": digest(output)}
