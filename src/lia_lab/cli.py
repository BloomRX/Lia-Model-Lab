"""Explicit local tooling. No downloader, paid API or training command."""
import argparse
import json
import sys
from pathlib import Path
from .datasets import build_dataset, read_examples
from .experiments import register_plan, verify_dataset, verify_resume, inspect_adapter, export_adapter
from .evaluation import compare
from .cards import write_card
from .io import LabError, atomic_json, load


def main(argv=None):
    parser = argparse.ArgumentParser(prog="lia-lab")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("validate-data"); p.add_argument("input")
    p = commands.add_parser("build-data"); p.add_argument("input"); p.add_argument("output"); p.add_argument("--seed", type=int, default=42)
    p = commands.add_parser("verify-data"); p.add_argument("manifest")
    p = commands.add_parser("register-plan"); p.add_argument("config"); p.add_argument("--research-root", required=True); p.add_argument("--approved-root", required=True)
    p = commands.add_parser("verify-resume"); p.add_argument("record"); p.add_argument("checkpoint_manifest")
    p = commands.add_parser("compare"); p.add_argument("runs", nargs="+"); p.add_argument("--output", required=True)
    p = commands.add_parser("inspect-adapter"); p.add_argument("directory")
    p = commands.add_parser("export-adapter"); p.add_argument("source"); p.add_argument("destination")
    p = commands.add_parser("write-card"); p.add_argument("kind", choices=["dataset", "model"]); p.add_argument("source"); p.add_argument("output")
    p = commands.add_parser("doctor"); p.add_argument("--storage", default=".")
    p = commands.add_parser("seal-model")
    p.add_argument("directory"); p.add_argument("output")
    for name in ("model-id", "revision", "license-id", "license-file", "license-review-ref"):
        p.add_argument("--" + name, required=True)
    for command in ("plan-inference", "infer-local"):
        p = commands.add_parser(command)
        for name in ("snapshot", "snapshot-manifest", "suite", "research-root", "approved-root", "run-id"):
            p.add_argument("--" + name, required=True)
        if command == "infer-local":
            p.add_argument("--approval-store", required=True); p.add_argument("--approval-id", required=True)
        else:
            p.add_argument("--output", required=True)
        p.add_argument("--device", choices=["cpu", "cuda", "rocm", "mps"], default="cpu")
        p.add_argument("--dtype", choices=["float32", "float16", "bfloat16"], default="float32")
        p.add_argument("--containment", choices=["portable-process", "linux-rlimit", "linux-netns-rlimit"], required=True)
        for name, default in (("repeats",2),("max-tokens",128),("context",2048),("timeout",600)):
            p.add_argument("--" + name, type=int, default=default)
    p = commands.add_parser("approve-inference")
    p.add_argument("plan"); p.add_argument("--store", required=True); p.add_argument("--ttl", type=int, default=900)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            from .environment import doctor
            result = doctor(args.storage)
        elif args.command == "seal-model":
            from .checkpoints import seal_snapshot
            result = seal_snapshot(args.directory, args.output, args.model_id, args.revision,
                                   args.license_id, args.license_file, args.license_review_ref)
        elif args.command == "approve-inference":
            from .authorization import confirm_plan
            result = confirm_plan(args.plan, args.store, args.ttl)
        elif args.command in {"infer-local", "plan-inference"}:
            from .inference import run_inference, make_operation
            options = dict(snapshot=args.snapshot, snapshot_manifest=args.snapshot_manifest, suite_path=args.suite,
                research_root=args.research_root, approved_root=args.approved_root, run_id=args.run_id,
                device=args.device, dtype=args.dtype, repeats=args.repeats, max_tokens=args.max_tokens,
                context=args.context, timeout=args.timeout, containment=args.containment)
            if args.command == "plan-inference":
                if Path(args.output).exists():
                    raise LabError("plan output already exists")
                result = make_operation(**options); atomic_json(args.output, result)
            else:
                result = run_inference(**options, approval_store=args.approval_store, approval_id=args.approval_id)
                print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
                return 0 if result["status"] == "completed-not-quality-approved" else 2
        elif args.command == "validate-data":
            result = {"validated_examples": len(read_examples(args.input))}
        elif args.command == "build-data":
            result = build_dataset(args.input, args.output, args.seed)
        elif args.command == "verify-data":
            result = verify_dataset(args.manifest)
        elif args.command == "register-plan":
            result = register_plan(args.config, args.research_root, args.approved_root)
        elif args.command == "verify-resume":
            result = verify_resume(args.record, args.checkpoint_manifest)
        elif args.command == "compare":
            if Path(args.output).exists():
                raise LabError("comparison output already exists")
            result = compare([load(p) for p in args.runs]); atomic_json(args.output, result)
        elif args.command == "write-card":
            result = write_card(args.kind, args.source, args.output)
        elif args.command == "inspect-adapter":
            result = inspect_adapter(args.directory)
        else:
            result = export_adapter(args.source, args.destination)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
