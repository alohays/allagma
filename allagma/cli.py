"""Command-line entrypoint; executing a campaign dispatches to its pinned helper."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from . import __version__
from . import bundles, campaigns, migrations
from .catalog import Catalog
from .contracts import validate_record
from .demo import compare_context, toy_workflow
from .files import AllagmaError, canonical, read_json, write_json

ROOT = Path(__file__).resolve().parents[1]


def parser():
    p = argparse.ArgumentParser(prog="allagma", description="Portable methods, exact study locks and traceable evidence")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Check all modules, or only one module's contract")
    check.add_argument("--source", type=Path, default=ROOT)
    check.add_argument("--module")
    init = sub.add_parser("init", help="Initialize a study while preserving user-owned files")
    init.add_argument("--source", type=Path, default=ROOT)
    init.add_argument("--study", type=Path, required=True)
    init.add_argument("--id", default="study")
    init.add_argument("--intent", type=Path)
    entry = sub.add_parser("entry", help="Resolve a canonical method from a study or campaign lock")
    entry.add_argument("--study", type=Path, required=True)
    entry.add_argument("--campaign")
    entry.add_argument("--module")
    verify = sub.add_parser("verify", help="Verify the study lock, content and intent freshness")
    verify.add_argument("--study", type=Path, required=True)
    val = sub.add_parser("validate-record")
    val.add_argument("path", type=Path)
    toy = sub.add_parser("toy", help="Run a complete offline toy study with failure and interruption")
    toy.add_argument("--source", type=Path, default=ROOT)
    toy.add_argument("--destination", type=Path, required=True)
    toy.add_argument("--host", choices=bundles.HOSTS, default="generic")
    toy.add_argument("--no-faults", action="store_true")
    toy.add_argument("--context")
    toy.add_argument("--reviewer")
    toy.add_argument("--recipe", default="recipe/research")
    compare = sub.add_parser("compare", help="Run the bounded context-method comparison")
    compare.add_argument("--source", type=Path, default=ROOT)
    compare.add_argument("--output", type=Path, required=True)
    compare.add_argument("--baseline", default="context/full-record")
    compare.add_argument("--candidate", default="context/active-brief")
    camp = sub.add_parser("campaign")
    camp.add_argument("operation", choices=["start", "run", "analyze", "audit", "status"])
    camp.add_argument("--study", type=Path, required=True)
    camp.add_argument("--campaign", required=True)
    camp.add_argument("--analysis-id")
    camp.add_argument("--allow-partial", action="store_true")
    camp.add_argument("--stop-after", type=int)
    camp.add_argument("--fault-run")
    camp.add_argument("--fault-mode", choices=["failure", "interrupt"])
    camp.add_argument("--crash-after-start", action="store_true", help=argparse.SUPPRESS)
    update = sub.add_parser("update")
    update.add_argument("operation", choices=["check", "plan", "reconcile", "validate", "adopt", "rollback", "recover"])
    update.add_argument("--study", type=Path, required=True)
    update.add_argument("--source", type=Path, default=ROOT)
    update.add_argument("--id")
    migration = sub.add_parser("migrate")
    migration.add_argument("operation", choices=["plan", "apply", "rollback", "recover"])
    migration.add_argument("--study", type=Path, required=True)
    migration.add_argument("--spec", type=Path)
    migration.add_argument("--id")
    accept = sub.add_parser("acceptance", help="Generate I1–I5 evidence and a machine-readable report")
    accept.add_argument("--output", type=Path, default=ROOT / "build/acceptance")
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = parser().parse_args(argv)
    try:
        if args.command == "campaign" and args.operation in ("start", "run", "analyze", "audit"):
            if args.operation == "start":
                lock = bundles.verify_study(args.study)
            else:
                directory = campaigns.campaign_path(args.study, args.campaign)
                lock = bundles.verify_lock(args.study, read_json(directory / "lock.yaml"))
            root = bundles.bundle_path(args.study, lock)
            if root.resolve() != ROOT:
                return subprocess.run([sys.executable, str(root / "tools/allagma.py"), *argv]).returncode
        if args.command == "check":
            result = {"checked": Catalog(args.source).check(args.module), "status": "pass"}
        elif args.command == "init":
            result = bundles.initialize(args.source, args.study, study_id=args.id, intent=read_json(args.intent) if args.intent else None)
        elif args.command == "entry":
            result = bundles.resolve_entry(args.study, args.module, args.campaign)
        elif args.command == "verify":
            lock = bundles.verify_study(args.study)
            bundles.check_ownership(args.study)
            result = {"status": "pass", "bundle_id": lock["bundle_id"], "lock_id": lock["lock_id"]}
        elif args.command == "validate-record":
            result = {"status": "pass", "record_type": validate_record(read_json(args.path))["record_type"]}
        elif args.command == "toy":
            roles = {key: value for key, value in {"context": args.context, "reviewer": args.reviewer}.items() if value}
            result = toy_workflow(args.source, args.destination, host=args.host, faults=not args.no_faults, roles=roles, recipe=args.recipe)
        elif args.command == "compare":
            result = compare_context(args.source, args.output, baseline_id=args.baseline, candidate_id=args.candidate)
        elif args.command == "campaign":
            if args.operation == "start":
                result = campaigns.start_campaign(args.study, args.campaign)
            elif args.operation == "run":
                if bool(args.fault_run) != bool(args.fault_mode):
                    raise AllagmaError("Fault injection requires both --fault-run and --fault-mode")
                result = campaigns.run_campaign(args.study, args.campaign,
                    fault={"run_id": args.fault_run, "mode": args.fault_mode} if args.fault_run else None,
                    stop_after=args.stop_after, crash_after_start=args.crash_after_start)
            elif args.operation == "analyze":
                result = campaigns.analyze_campaign(args.study, args.campaign, analysis_id=args.analysis_id or "a001", allow_partial=args.allow_partial)
            elif args.operation == "audit":
                result = campaigns.audit_campaign(args.study, args.campaign, analysis_id=args.analysis_id)
            else:
                result = read_json(campaigns.campaign_path(args.study, args.campaign) / "state.json")
        elif args.command == "update":
            if args.operation in ("check", "plan"):
                result = getattr(bundles, args.operation + "_update")(args.source, args.study)
            elif args.operation == "recover":
                result = bundles.recover_update(args.study)
            else:
                if not args.id:
                    raise AllagmaError("This update operation requires --id")
                fn = bundles.rollback if args.operation == "rollback" else getattr(bundles, args.operation + "_update")
                result = fn(args.study, args.id)
        elif args.command == "migrate":
            if args.operation == "plan":
                if not args.spec:
                    raise AllagmaError("Migration plan requires --spec")
                result = migrations.plan_migration(args.study, read_json(args.spec))
            else:
                if not args.id:
                    raise AllagmaError("Migration operation requires --id")
                result = getattr(migrations, args.operation + "_migration")(args.study, args.id)
        else:
            from .acceptance import run_acceptance
            result = run_acceptance(ROOT, args.output)
        print(canonical(result).decode(), end="")
        if isinstance(result, dict) and (result.get("verdict") == "revise" or result.get("execution_status") in ("failed", "budget_exhausted", "needs_revision")):
            return 1
        return 0
    except (AllagmaError, OSError, KeyError, ValueError) as exc:
        print(f"allagma: {exc}", file=sys.stderr)
        return 2
