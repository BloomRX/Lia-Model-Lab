"""Local CLI. Every operation is explicit; no network or training commands."""
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
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-data":
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
