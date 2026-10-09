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
    res = sub.add_parser("resource", help="Supervise finite study-owned local process budgets")
    res.add_argument("operation", choices=["init", "run", "status", "recover"])
    res.add_argument("--ledger", type=Path, required=True)
    res.add_argument("--profile", type=Path)
    res.add_argument("--workdir", type=Path)
    res.add_argument("--label")
    res.add_argument("--category", default="compute")
    res.add_argument("--timeout", type=float)
    res.add_argument("--attempt", action="store_true")
    res.epilog = "For run, put the supervised command after --."
    research = sub.add_parser("research", help="Prepare a reusable brief/material/resource workspace or explicitly run its native workflow")
    research.add_argument("operation", choices=["prepare", "run", "status"])
    research.add_argument("--source", type=Path, default=ROOT)
    research.add_argument("--study", type=Path, required=True)
    research.add_argument("--control", type=Path, required=True)
    research.add_argument("--brief", type=Path)
    research.add_argument("--materials", type=Path)
    research.add_argument("--profile", type=Path)
    research.add_argument("--references", type=Path, help="Critical reference dossier to freeze into preparation inputs")
    research.add_argument("--reference-cache", type=Path, help="Verified cache for selected execution assets")
    research.add_argument("--paper-config", type=Path, help="Optional paper request with researcher-supplied attribution")
    research.add_argument("--id", default="study")
    research.add_argument("--session", default="session-001")
    research.add_argument("--codex", type=Path)
    research.add_argument("--timeout", type=float)
    research.add_argument("--config", type=Path, default=Path.home()/".codex/config.toml")
    research.add_argument("--auth", type=Path, default=Path.home()/".codex/auth.json")
    research.add_argument("--interrupt-first-attempt", action="store_true")
    research.add_argument("--baseline", action="store_true", help="Evaluation control: common infrastructure without Allagma methods")
    refs = sub.add_parser("reference", help="Maintain an offline critical literature map and frozen reading inputs")
    refs.add_argument("operation", choices=["init", "add", "check", "index", "snapshot", "cache-init", "acquire", "verify-cache", "policy", "quarantine"])
    refs.add_argument("--directory", type=Path, required=True)
    refs.add_argument("--question", default="")
    refs.add_argument("--mode", choices=["online", "offline", "provided-only"], default="provided-only")
    refs.add_argument("--record", type=Path)
    refs.add_argument("--destination", type=Path)
    refs.add_argument("--require-review", action="store_true")
    refs.add_argument("--cache", type=Path, default=Path.cwd() / ".allagma-reference-cache")
    refs.add_argument("--online", action="store_true", help="Explicitly allow acquisition HTTP requests outside scientific workers")
    refs.add_argument("--provided", type=Path, help="Local-only JSON mapping of asset IDs to supplied file paths")
    refs.add_argument("--policy", type=Path)
    refs.add_argument("--approval", type=Path)
    refs.add_argument("--asset-id")
    paper = sub.add_parser("paper", help="Validate or build an optional evidence-linked arXiv paper; never submit")
    paper.add_argument("operation", choices=["init", "check", "build"])
    paper.add_argument("--study", type=Path, required=True)
    paper.add_argument("--config", type=Path, help="Defaults to STUDY/paper.json")
    paper.add_argument("--title")
    paper.add_argument("--authors", type=Path, help="Researcher-supplied attribution JSON")
    paper.add_argument("--destination", type=Path)
    paper.add_argument("--engine", choices=["pdflatex", "xelatex"], default="pdflatex")
    paper.add_argument("--timeout", type=int, default=60)
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    command_argv = []
    parser_argv = argv
    if argv[:2] == ["resource", "run"] and "--" in argv:
        boundary = argv.index("--")
        parser_argv, command_argv = argv[:boundary], argv[boundary+1:]
    args = parser().parse_args(parser_argv)
    try:
        if args.command == "research" and args.operation == "run" and read_json(args.control/"prepared.json").get("workflow_enabled",True):
            root = bundles.bundle_path(args.study, bundles.verify_study(args.study))
            if root.resolve() != ROOT:
                return subprocess.run([sys.executable, str(root/"tools/allagma.py"), *argv]).returncode
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
        elif args.command == "resource":
            from . import resources
            if args.operation == "init":
                if not args.profile or not args.workdir:
                    raise AllagmaError("Resource initialization requires --profile and --workdir")
                result = resources.initialize(args.ledger, read_json(args.profile), args.workdir)
            elif args.operation == "run":
                if not args.label or args.timeout is None:
                    raise AllagmaError("Resource execution requires --label and --timeout")
                result = resources.execute(args.ledger, command_argv, label=args.label,
                    category=args.category, timeout=args.timeout, attempt=args.attempt, workdir=args.workdir)
            elif args.operation == "recover":
                result = resources.recover(args.ledger)
            else:
                result = resources.summary(args.ledger)
        elif args.command == "paper":
            from . import papers
            configuration = args.config or args.study / "paper.json"
            if args.operation == "init":
                if not args.authors or not args.title:
                    raise AllagmaError("Paper initialization requires --title and researcher-supplied --authors")
                result = papers.initialize(args.study, configuration, title=args.title, authors=read_json(args.authors))
            elif args.operation == "check":
                checked = papers.validate(args.study, read_json(configuration))
                result = {key: checked[key] for key in ("status", "scope")}
                if checked["status"] == "pass":
                    result.update(citations=checked["citations"], claims=list(checked["claims"]), values=list(checked["values"]))
            else:
                if not args.destination:
                    raise AllagmaError("Paper build requires a new --destination")
                from .research import _load
                adapter = _load("allagma_arxiv_output", ROOT / "adapters/arxiv/package.py")
                result = adapter.build(args.study, read_json(configuration), args.destination,
                                       engine=args.engine, timeout=args.timeout)
        elif args.command == "reference":
            from . import references
            if args.operation in ("cache-init", "acquire", "verify-cache", "policy", "quarantine"):
                from .research import _load
                adapter_path = ROOT / "adapters/reference-assets/acquire.py"
                if not adapter_path.exists():
                    raise AllagmaError("This bundle does not include the optional reference acquisition adapter")
                adapter = _load("allagma_reference_acquisition", adapter_path)
                if args.operation == "cache-init":
                    result = adapter.initialize(args.cache, policy=read_json(args.policy) if args.policy else None)
                elif args.operation == "acquire":
                    result = adapter.acquire(args.cache, read_json(args.directory / "assets.json"), args.directory,
                        online=args.online, provided=read_json(args.provided) if args.provided else None,
                        approvals=read_json(args.approval) if args.approval else None)
                elif args.operation == "policy":
                    if not args.policy:
                        raise AllagmaError("Policy adoption requires --policy")
                    result = adapter.adopt_policy(args.cache, read_json(args.policy),
                        approval=read_json(args.approval) if args.approval else None)
                elif args.operation == "quarantine":
                    if not args.asset_id:
                        raise AllagmaError("Quarantine requires --asset-id")
                    result = adapter.quarantine(args.cache, read_json(args.directory / "retrieval.json"), args.asset_id)
                else:
                    result = adapter.verify(args.cache, read_json(args.directory / "retrieval.json"))
            elif args.operation == "init":
                result = references.initialize(args.directory, question=args.question, mode=args.mode)
            elif args.operation == "add":
                if not args.record:
                    raise AllagmaError("Adding a reference requires --record")
                value = references.add_record(read_json(args.directory / "map.json"), read_json(args.record), directory=args.directory)
                write_json(args.directory / "map.json", value)
                result = references.refresh(args.directory)
            elif args.operation == "snapshot":
                if not args.destination:
                    raise AllagmaError("A reference snapshot requires --destination")
                result = references.snapshot(args.directory, args.destination, require_review=args.require_review)
            else:
                result = references.refresh(args.directory, require_review=args.require_review)
        elif args.command == "research":
            from . import research
            if args.operation == "prepare":
                if not all((args.brief,args.materials,args.profile)):
                    raise AllagmaError("Research preparation requires --brief, --materials and --profile")
                result = research.prepare(args.source,args.study,args.control,brief=args.brief,materials=args.materials,
                                          profile=read_json(args.profile),study_id=args.id,install_workflow=not args.baseline,
                                          reference_directory=args.references,reference_cache=args.reference_cache,
                                          paper_configuration=read_json(args.paper_config) if args.paper_config else None)
            elif args.operation == "run":
                if args.codex is None or args.timeout is None:
                    raise AllagmaError("Native execution requires explicit --codex and --timeout")
                result = research.run(args.study,args.control,codex=args.codex,timeout=args.timeout,session_id=args.session,
                    config=args.config,auth=args.auth,interrupt_first_attempt=args.interrupt_first_attempt)
            else:
                result = research.status(args.study,args.control)
        else:
            from .acceptance import run_acceptance
            result = run_acceptance(ROOT, args.output)
        print(canonical(result).decode(), end="")
        if args.command == "resource" and args.operation == "run" and result["status"] != "completed":
            return 1
        if args.command == "research" and args.operation == "run" and result["status"] != "completed":
            return 1
        if args.command == "reference" and args.operation == "acquire" and any(a["status"] != "available" for a in result["assets"]):
            return 1
        if isinstance(result, dict) and (result.get("verdict") in ("revise", "blocked") or result.get("execution_status") in ("failed", "blocked", "budget_exhausted", "needs_revision")):
            return 1
        return 0
    except (AllagmaError, OSError, KeyError, ValueError) as exc:
        print(f"allagma: {exc}", file=sys.stderr)
        return 2
