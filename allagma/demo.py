"""Offline research walkthrough and bounded improvement example."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

from .bundles import default_intent, initialize, resolve_entry, source_revision
from .campaigns import analyze_campaign, audit_campaign, run_campaign, start_campaign
from .catalog import Catalog
from .contracts import validate_record
from .files import AllagmaError, canonical, read_json, reference, utcnow, write_json


def create_toy(source, destination, *, host="generic", roles=None, recipe="recipe/research", budget=None):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise AllagmaError("Toy destination must be empty; existing evidence is not replaced")
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("domain", "brief.json", "protocol.json", "evidence-map.json"):
        src = source / "examples/toy-study" / name
        if src.is_dir():
            shutil.copytree(src, destination / name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(src, destination / name)
    intent = default_intent("toy-bias-study")
    intent["recipe"] = recipe
    intent["roles"] = roles or {}
    intent["allow_experimental"] = bool(roles) or recipe != "recipe/research"
    intent["request"] = {"budget": budget or {"max_attempts": 28, "max_seconds": 60.0, "money_usd": 0.0, "per_attempt_seconds": 5.0}}
    initialize(source, destination, intent=intent)
    return destination


def toy_workflow(source, destination, *, host="generic", faults=True, roles=None, recipe="recipe/research"):
    study = create_toy(source, destination, host=host, roles=roles, recipe=recipe)
    start_campaign(study, "toy-v1")
    entry = resolve_entry(study, "context", "toy-v1")
    meta = read_json(Path(entry["path"]).parent / "module.yaml")
    example = read_json(Path(entry["path"]).parent / "example.json")
    example["context_id"] = "toy-v1-context"
    brief = read_json(study / "brief.json")
    example["records"].update({"question": brief["question"], "constraints": brief["constraints"],
                               "protocol": reference(study, study / "campaigns/toy-v1/protocol.json"),
                               "stop_rules": brief["stop_rules"],
                               "unresolved": ["No independent scientific review or real-model evaluation"],
                               "evidence": reference(study, study / "campaigns/toy-v1/materials/evidence-map.json")})
    handoff = study / "campaigns/toy-v1/context-input.json"
    write_json(handoff, example, immutable=True)
    context_path = study / "campaigns/toy-v1/context.json"
    subprocess.run([sys.executable, str(Path(entry["path"]).parent / "select.py"), str(handoff), str(context_path)], check=True)
    validate_record(read_json(context_path))
    if faults:
        failed = run_campaign(study, "toy-v1", fault={"run_id": "confirm-100", "mode": "failure"})
        if failed["execution_status"] != "failed":
            raise AllagmaError("Failure scenario did not execute as intended")
        interrupted = run_campaign(study, "toy-v1", fault={"run_id": "confirm-101", "mode": "interrupt"})
        if interrupted["execution_status"] != "paused":
            raise AllagmaError("Interruption scenario did not execute as intended")
    result = run_campaign(study, "toy-v1")
    if result["execution_status"] != "ready":
        raise AllagmaError(f"Toy campaign did not complete: {result}")
    analysis = analyze_campaign(study, "toy-v1")
    audit = audit_campaign(study, "toy-v1")
    if audit["verdict"] != "pass":
        raise AllagmaError(f"Toy audit failed: {audit}")
    owner = read_json(study / ".allagma/ownership.json")
    entry_path = owner["mapping"]["generic" if host == "generic" else f"{host}:{recipe}"]
    walkthrough = {"host": host, "scope": "Generic execution; native hosts are packaging/contract fixtures, not real-model smoke tests",
                   "entrypoint": entry_path, "native_hooks": False, "native_subagents": False,
                   "context_method": entry, "context": reference(study, context_path),
                   "analysis": analysis["analysis_id"], "audit": audit, "faults_demonstrated": faults,
                   "recorded_at": utcnow()}
    write_json(study / "walkthrough.json", walkthrough, immutable=True)
    return walkthrough


def compare_context(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise AllagmaError("Comparison directory already exists; preserve candidate history")
    output.mkdir(parents=True)
    catalog = Catalog(source)
    fixture_path = source / "evals/context-retention/cases.json"
    fixture = read_json(fixture_path)
    measurements = {}
    for module_id in ("context/full-record", "context/active-brief"):
        directory = catalog.directory(module_id)
        char_cost, recalls = 0, []
        for i, case in enumerate(fixture["cases"]):
            inputs = output / f"case-{i}.json"
            write_json(inputs, case, immutable=True)
            result_path = output / f"{module_id.split('/')[-1]}-{i}.json"
            subprocess.run([sys.executable, str(directory / "select.py"), str(inputs), str(result_path)], check=True)
            result = read_json(result_path)
            validate_record(result)
            recall = sum(key in result["content"] and result["content"][key] == case["records"][key] for key in case["required"]) / len(case["required"])
            recalls.append(recall)
            char_cost += len(canonical(result["content"]).decode())
        measurements[module_id] = {"required_recall": min(recalls), "character_cost": char_cost}
    baseline, candidate = measurements["context/full-record"], measurements["context/active-brief"]
    outcome = "adopt" if candidate["required_recall"] == 1 and candidate["character_cost"] < baseline["character_cost"] else "reject"
    proposal = {"target": "context selection", "hypothesis": "Focused context retains required fields with lower serialized character cost",
                "baseline": "context/full-record", "candidate": "context/active-brief", "source_revision": source_revision(source),
                "candidate_lineage": {"parent": "context/full-record", "change": "Select required and phase-relevant fields"}}
    write_json(output / "proposal.json", proposal, immutable=True)
    decision = {"schema_version": "0.2", "record_type": "ImprovementRecord", "improvement_id": output.name,
                "target": proposal["target"], "hypothesis": proposal["hypothesis"], "source_revision": proposal["source_revision"],
                "baseline": proposal["baseline"], "candidate": proposal["candidate"],
                "candidate_artifacts": [reference(output, output / "proposal.json")],
                "evaluation": "evaluation/context-retention", "controls": {"controller": "deterministic Python", "task_split": fixture["split"], "fixture_sha256": __import__('hashlib').sha256(fixture_path.read_bytes()).hexdigest(), "noise_band": 0, "resources": "same local process contract"},
                "outcome": outcome, "measurements": measurements, "cost": {"money_usd": 0, "model_tokens": 0, "complexity": "one selection helper, two thin entrypoints"},
                "user_intervention": 0, "reason": "Required-key retention and character cost determine this bounded decision.",
                "limitations": ["No model or scientific-quality evaluation; cannot generalize beyond the fixtures."],
                "release_decision": "Example decision only; no module lifecycle or default selection is changed automatically."}
    validate_record(decision)
    write_json(output / "decision.json", decision, immutable=True)
    return decision
