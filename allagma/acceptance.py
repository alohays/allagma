"""Executable I1–I5 acceptance evidence, with retained artifacts and scope."""
from __future__ import annotations

from copy import deepcopy
import io
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import unittest

from . import bundles as b
from .campaigns import analyze_campaign, audit_campaign, run_campaign, start_campaign
from .catalog import Catalog
from .demo import compare_context, create_toy, toy_workflow
from .files import (AllagmaError, digest, file_hash, inventory, read_json, reference,
                    utcnow, write_bytes, write_json, write_text)
from .migrations import plan_migration, apply_migration, rollback_migration


def require(condition, message):
    if not condition:
        raise AllagmaError("Acceptance failed: " + message)


def expected_error(call, text):
    try:
        call()
    except AllagmaError as exc:
        require(text in str(exc), f"Expected {text!r}; observed {str(exc)!r}")
        return {"expected_error": str(exc), "status": "pass"}
    raise AllagmaError("Acceptance failed: expected an error containing " + text)


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.cases.append({"test": test.id(), "status": "pass"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.cases.append({"test": test.id(), "status": "fail"})

    def addError(self, test, err):
        super().addError(test, err)
        self.cases.append({"test": test.id(), "status": "error"})


def _version(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else "version probe unavailable"
    except (OSError, subprocess.TimeoutExpired):
        return "not installed / version probe unavailable"


def _copy_source(source, output):
    for name in b.source_inventory(source):
        write_bytes(output / name, (source / name).read_bytes())
    shutil.copytree(source / "examples/toy-study", output / "examples/toy-study",
                    ignore=shutil.ignore_patterns("__pycache__", "evidence", "results"))


def _adopt(source, study):
    plan = b.plan_update(source, study)
    b.reconcile_update(study, plan["id"])
    b.validate_update(study, plan["id"])
    b.adopt_update(study, plan["id"])
    return plan


def version_scenario(source, output):
    """Exercise actual updates, coexistence, retirement, old resume and rollback."""
    output.mkdir(parents=True)
    central = output / "central"
    _copy_source(source, central)
    study = create_toy(central, output / "study")
    start_campaign(study, "old-campaign")
    run_campaign(study, "old-campaign", stop_after=2)
    original = b.verify_study(study)
    original_entry = b.resolve_entry(study, "context", "old-campaign")
    code = inventory(study / "domain")
    path = central / "methods/allagma-context-active-brief/SKILL.md"
    path.write_text(path.read_text() + "\nClarification in the synthetic update fixture.\n")
    require(b.resolve_entry(study, "context", "old-campaign") == original_entry, "central edits leaked into an old campaign")
    checks = {"central_isolation": {"status": "pass", "entry": original_entry}, "check": b.check_update(central, study)}
    write_json(study / "overrides/settings.json", {"context_chars": 900})
    checks["intent_freshness"] = expected_error(lambda: b.verify_study(study), "Configuration changed")
    # Deprecate in a fixture release, keep both choices in a subsequent compatible
    # release, then retire. These labels are not published Allagma releases.
    active_path = central / "methods/allagma-context-active-brief/module.yaml"
    active = read_json(active_path)
    active["lifecycle"] = "deprecated"
    active["replacement"] = {"id": "context/full-record", "migration": "Select the full-record method; the artifact contracts are unchanged",
                             "earliest_retirement": "0.3.0", "reason": "Synthetic lifecycle acceptance example"}
    write_json(active_path, active)
    full_path = central / "methods/allagma-context-full-record/module.yaml"
    full = read_json(full_path); full["lifecycle"] = "stable"; write_json(full_path, full)
    for recipe_path in (central / "recipes").glob("*/recipe.json"):
        recipe = read_json(recipe_path); recipe["roles"]["context"] = "context/full-record"; write_json(recipe_path, recipe)
    release = read_json(central / "release.json")
    release.update(release="0.2.1", release_tag="v0.2.1")
    write_json(central / "release.json", release)
    first = _adopt(central, study)
    write_json(output / "deprecation.json", {"release": release, "old": active, "replacement": full}, immutable=True)
    release.update(release="0.2.2", release_tag="v0.2.2"); write_json(central / "release.json", release)
    selected_old = read_json(study / "allagma.yaml")
    selected_old["roles"]["context"] = "context/active-brief"
    coexistence = Catalog(central).resolve(selected_old)
    require({"context/active-brief", "context/full-record"} <= set(coexistence["modules"]), "replacement coexistence failed")
    write_json(output / "coexistence.json", {"release": release, "resolution": coexistence}, immutable=True)
    _adopt(central, study)
    release.update(release="0.3.0", release_tag="v0.3.0"); write_json(central / "release.json", release)
    active["lifecycle"] = "retired"; write_json(active_path, active)
    retirement = _adopt(central, study)
    latest = b.verify_study(study)
    require("context/active-brief" not in latest["modules"], "retired method entered new selection")
    require(b.resolve_entry(study, "context", "old-campaign") == original_entry, "retirement changed old routing")
    require(run_campaign(study, "old-campaign", stop_after=1)["execution_status"] == "paused", "historical resume failed")
    require(inventory(study / "domain") == code, "update changed study-owned science")
    require(read_json(study / "overrides/settings.json") == {"context_chars": 900}, "update overwrote overrides")
    checks["retirement_resume"] = {"status": "pass", "active_bundle": latest["bundle_id"], "old_bundle": original["bundle_id"], "update": retirement["id"]}
    rolled_back = b.rollback(study, first["id"])
    require(b.verify_study(study)["lock_id"] == original["lock_id"], "rollback failed to restore the exact lock")
    require(read_json(study / "overrides/settings.json") == {}, "rollback failed to restore configuration")
    require(b.bundle_path(study, latest).exists(), "rollback deleted historical content")
    checks["rollback"] = {"status": "pass", **rolled_back}
    entrypoint = study / "ALLAGMA.md"
    before = entrypoint.read_text(); entrypoint.write_text(before + "\nA local generated-file edit.\n")
    checks["generated_conflict"] = expected_error(lambda: b.plan_update(central, study), "Locally edited generated file")
    entrypoint.write_text(before)
    release["contracts"] = ["99.0"]; write_json(central / "release.json", release)
    incompatible = b.plan_update(central, study)
    checks["contract_mismatch"] = expected_error(lambda: b.reconcile_update(study, incompatible["id"]), "Contract migration required")
    release["contracts"] = ["0.2"]; write_json(central / "release.json", release)
    baseline = read_json(study / ".allagma/scaffold-baseline.json")
    lock_before = file_hash(study / ".allagma/lock.yaml")
    migration = {"from": "1", "to": "2", "answers": baseline["answers"], "reason": "Add a separate study log",
                 "files": {"STUDY-LOG.md": "# Study log\n\nRecord protocol amendments here.\n"}}
    plan = plan_migration(study, migration)
    apply_migration(study, plan["id"])
    require(file_hash(study / ".allagma/lock.yaml") == lock_before, "scaffold migration changed the method lock")
    rollback_migration(study, plan["id"])
    require(not (study / "STUDY-LOG.md").exists(), "inverse migration did not restore the baseline")
    (study / "README.md").write_text("# User research notes\n")
    migration["files"] = {"README.md": "# Different template\n"}
    conflict = plan_migration(study, migration)
    checks["scaffold_conflict"] = expected_error(lambda: apply_migration(study, conflict["id"]), "Unresolved three-way conflicts")
    require((study / "README.md").read_text() == "# User research notes\n", "scaffold conflict erased local work")
    checks["scaffold_inverse"] = {"status": "pass", "migration": plan["id"], "method_lock_unchanged": True}
    result = {"status": "pass", "scope": "Synthetic release and migration fixtures", "checks": checks}
    write_json(output / "scenario.json", result, immutable=True)
    return result


def run_acceptance(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise AllagmaError("Acceptance output already exists; use a fresh directory to preserve evidence")
    output.mkdir(parents=True)
    report = {"schema_version": "0.2", "status": "running", "started_at": utcnow(),
              "release": "0.2.0", "source_revision": b.source_revision(source),
              "source_inventory": b.source_inventory(source), "conformance_inventory": inventory(source / "conformance"),
              "environment": {"python": platform.python_version(), "platform": platform.platform(), "timezone_for_reporting": "Asia/Seoul",
                              "codex_version_probe": _version(["codex", "--version"]), "claude_version_probe": _version(["claude", "--version"])},
              "milestones": {}, "limitations": ["Native Codex and Claude Code activation/model quality are not claimed; tests cover packaging and shared contracts.",
                                                   "The toy is a synthetic known-answer study, not scientific novelty or an LLM capability improvement."]}
    try:
        Catalog(source).check()
        contributor_paths = ["CONTRIBUTING.md", "GOVERNANCE.md", "CODE_OF_CONDUCT.md", "LICENSE",
                             "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "docs/module-authoring.md",
                             ".github/CODEOWNERS", ".github/PULL_REQUEST_TEMPLATE.md",
                             ".github/ISSUE_TEMPLATE/bug_report.yml", ".github/ISSUE_TEMPLATE/module_proposal.yml",
                             ".github/workflows/conformance.yml"]
        for name in contributor_paths:
            require((source / name).is_file() and (source / name).stat().st_size > 0, "missing contributor material " + name)
        report["contributor_materials"] = {name: file_hash(source / name) for name in contributor_paths}
        stream = io.StringIO()
        suite = unittest.defaultTestLoader.discover(str(source / "conformance"), top_level_dir=str(source))
        result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=EvidenceResult).run(suite)
        write_text(output / "conformance.log", stream.getvalue(), immutable=True)
        tests = {"tests_run": result.testsRun, "successful": result.wasSuccessful(), "skipped": len(result.skipped), "cases": result.cases}
        write_json(output / "conformance.json", tests, immutable=True)
        require(result.wasSuccessful() and not result.skipped, "conformance suite did not pass without skips")
        report["conformance"] = {"tests_run": result.testsRun, "result": reference(output, output / "conformance.json"), "log": reference(output, output / "conformance.log")}
        report["milestones"]["I3"] = {"status": "pass", "evidence": ["conformance.json", "conformance.log"],
                                      "checks": ["one-module authoring and targeted check", "capability/contract guards", "offline contributor workflow"]}
        walks, locks, values = {}, {}, {}
        for host in b.HOSTS:
            walks[host] = toy_workflow(source, output / host, host=host)
            locks[host] = b.verify_study(output / host)
            values[host] = read_json(output / host / "campaigns/toy-v1/analyses/a001/outputs/summary.json")
        require(len({lock["bundle_id"] for lock in locks.values()}) == 1, "host paths did not use the same bundle")
        require(all(values[host] == values["generic"] for host in b.HOSTS), "host handoffs disagreed on scientific output")
        report["milestones"]["I1"] = {"status": "pass", "shared_bundle": locks["generic"]["bundle_id"],
                                      "evidence": [f"{host}/walkthrough.json" for host in b.HOSTS],
                                      "native_hooks": False, "native_subagents": False, "same_numerical_output": True,
                                      "host_scope": "Real generic execution; native entrypoint registration/routing contract fixtures"}
        replacements = [("context-replacement", {"context": "context/full-record"}, "recipe/research"),
                        ("reviewer-replacement", {"reviewer": "reviewer/trace"}, "recipe/research"),
                        ("recipe-replacement", {}, "recipe/replication")]
        replacement_evidence = []
        for name, roles, recipe in replacements:
            walk = toy_workflow(source, output / name, faults=False, roles=roles, recipe=recipe)
            lock = b.verify_study(output / name)
            common = locks["generic"]["modules"].keys() & lock["modules"].keys()
            require(all(locks["generic"]["modules"][key]["revision"] == lock["modules"][key]["revision"] for key in common), "replacement rewrote shared modules")
            require(walk["audit"]["verdict"] == "pass", "replacement walkthrough failed")
            replacement_evidence.append({"case": name, "evidence": f"{name}/walkthrough.json", "unchanged_shared_modules": len(common)})
        adopted = compare_context(source, output / "comparison")
        rejected = compare_context(source, output / "comparison-rejected", baseline_id="context/active-brief", candidate_id="context/full-record")
        require(adopted["outcome"] == "adopt" and rejected["outcome"] == "reject", "comparison decisions did not match the measured fixture costs")
        unavailable = output / "unevaluated-source"
        _copy_source(source, unavailable)
        (unavailable / "methods/allagma-context-active-brief/select.py").write_text('raise RuntimeError("Unavailable fixture backend")\n')
        unevaluated = compare_context(unavailable, output / "comparison-unevaluated")
        require(unevaluated["outcome"] == "not evaluated", "environmental failure was treated as a measured rejection")
        report["milestones"]["I2"] = {"status": "pass", "replacements": replacement_evidence, "comparisons": ["comparison/decision.json", "comparison-rejected/decision.json", "comparison-unevaluated/decision.json"]}
        version_scenario(source, output / "versioning")
        report["milestones"]["I4"] = {"status": "pass", "evidence": ["versioning/scenario.json"],
                                      "checks": ["central/profile isolation", "explicit update stages", "generated-file conflicts", "contract mismatch", "coexistence and retirement", "old campaign resume", "complete rollback", "separate scaffold migration and inverse"]}
        limited = create_toy(source, output / "partial-study", budget={"max_attempts": 4, "max_seconds": 30, "money_usd": 0, "per_attempt_seconds": 5})
        start_campaign(limited, "limited")
        stopped = run_campaign(limited, "limited")
        require(stopped["execution_status"] == "budget_exhausted", "budget case did not stop")
        analyze_campaign(limited, "limited", allow_partial=True)
        partial = audit_campaign(limited, "limited")
        require(partial["verdict"] == "pass" and read_json(limited / "campaigns/limited/state.json")["execution_status"] == "partial", "partial evidence was mislabeled complete")
        attempts = [read_json(path) for path in (output / "generic/campaigns/toy-v1").glob("runs/*/attempts/*/record.json")]
        counts = {status: sum(item["status"] == status for item in attempts) for status in ("succeeded", "failed", "interrupted")}
        require(counts == {"succeeded": 26, "failed": 1, "interrupted": 1}, "toy attempt evidence is incomplete")
        report["milestones"]["I5"] = {"status": "pass", "attempts": counts, "confirmation_replicates": values["generic"]["replicates"],
                                      "evidence": ["generic/campaigns/toy-v1/analyses/a001/raw-manifest.json", "generic/campaigns/toy-v1/analyses/a001/record.json", "generic/campaigns/toy-v1/analyses/a001/paper/claims.json", "generic/campaigns/toy-v1/analyses/a001/paper/manuscript.md", "generic/campaigns/toy-v1/latest-audit.json", "partial-study/campaigns/limited/latest-audit.json"],
                                      "audit": walks["generic"]["audit"], "scientific_summary": values["generic"]}
        require(set(report["milestones"]) == {"I1", "I2", "I3", "I4", "I5"}, "milestone coverage is incomplete")
        require(b.source_revision(source) == report["source_revision"], "source changed during acceptance")
        require(inventory(source / "conformance") == report["conformance_inventory"], "conformance checks changed during acceptance")
        require(all(file_hash(source / name) == expected for name, expected in report["contributor_materials"].items()), "contributor materials changed during acceptance")
        report["status"] = "pass"
        report["completed_at"] = utcnow()
        write_json(output / "acceptance.json", report, immutable=True)
        write_text(output / "README.md", "# Allagma v0.2 acceptance\n\nAll I1–I5 checks passed. See acceptance.json for exact source, checks, artifacts and limits.\n\n"
                   "The full toy manuscript is in `generic/campaigns/toy-v1/analyses/a001/paper/manuscript.md`.\n"
                   "Native host paths are contract fixtures; no real-model qualification is claimed.\n", immutable=True)
        return {"status": "pass", "milestones": {key: value["status"] for key, value in sorted(report["milestones"].items())},
                "tests_run": result.testsRun, "report": str(output / "acceptance.json"),
                "manuscript": str(output / "generic/campaigns/toy-v1/analyses/a001/paper/manuscript.md"), "source_revision": report["source_revision"]}
    except Exception as exc:
        report["status"] = "fail"; report["error"] = str(exc); report["completed_at"] = utcnow()
        write_json(output / "acceptance.json", report, immutable=True)
        raise
