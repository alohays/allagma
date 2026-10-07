"""Local evaluation controller. It never supplies scientific follow-up guidance."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from allagma import bundles, resources
from allagma.files import file_hash, inventory, read_json, utcnow, write_json


def load_adapter(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


native = load_adapter("native_capture", "adapters/codex/session.py")
local = load_adapter("local_broker", "adapters/local-process/broker.py")
CODEX = Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex")
BASE = ROOT/"evals/research-v0.3"


def prepare_core(label, condition):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,59}", label):
        raise ValueError("Invalid run label")
    workspace = ROOT/"work/v03-development"/label/"candidate"
    record = BASE/"development/sessions"/label
    if workspace.exists() or record.exists():
        raise ValueError("Use a new run label; previous work is preserved")
    inputs = workspace/"inputs"
    inputs.mkdir(parents=True)
    source = ROOT/"studies/core-culp/reference"
    for name in ("code", "data", "metadata"):
        shutil.copytree(source/name, inputs/"capsule-6460826"/name)
    # Match the upstream hard task's source exclusions. Reference outputs,
    # environment and reproduction instructions never enter the workspace.
    (inputs/"capsule-6460826/code/run.sh").unlink()
    task = read_json(source/"controller-task.json")
    prompts = read_json(source/"upstream-prompts.json")
    task_text = prompts["codeocean_hard"].replace("{task_prompt}", task["task_prompt"]).replace("{json_fields}", str(task["results"][0].keys()))
    (inputs/"task.txt").write_text(task_text+"\n")
    shutil.copyfile(BASE/"briefs/core-culp.md", inputs/"BRIEF.md")
    shutil.copyfile(BASE/"COMPUTE.md", inputs/"COMPUTE.md")
    shutil.copyfile(ROOT/"adapters/local-process/compute_client.py", inputs/"compute.py")
    shutil.copytree(ROOT/"work/v03-development/wheelhouse-core", inputs/"wheels")
    ledger = BASE/"development/resource-ledger"
    policy = resources._policy(ledger)
    remaining = resources.summary(ledger)
    write_json(inputs/"RESOURCES.json", {"phase": "development", "profile": policy["profile"],
        "remaining_seconds_at_start": remaining["remaining_seconds"],
        "remaining_compute_requests_at_start": remaining["attempt_limit"]-remaining["attempts"],
        "native_session_timeout_seconds": 1800, "hardware": "Local Apple M4 Pro, 14 CPU cores, 20 GPU cores, 48 GB unified memory",
        "python": sys.version.split()[0], "network": False,
        "note": "This development run shares the already adopted development envelope; no ceiling is expanded."})
    (inputs/"SOURCES.md").write_text("# Sources\n\nCORE-Bench public training capsule `capsule-6460826`, CULP.\n\n"
        "Benchmark: https://github.com/siegelz/core-bench at e32a2980e72fe6eb04ee04eb749458f570625663.\n"
        f"Capsule DOI: {task['capsule_doi']}.\n\n"
        "The original science and scoring are retained. This locally adapted evaluation supplies an offline wheelhouse and adds evidence/review requirements; it is not an official leaderboard run.\n")
    readonly = [inputs]
    workflow = None
    if condition == "allagma":
        intent = bundles.default_intent(label)
        intent["hosts"] = ["codex"]
        intent["request"] = {"budget": {"max_attempts": 8, "max_seconds": 300,
            "per_attempt_seconds": 90, "money_usd": 0}}
        workflow = bundles.initialize(ROOT, workspace, study_id=label, intent=intent)
        readonly += [workspace/".allagma/bundles", workspace/".agents"]
    record.mkdir(parents=True)
    control_files = ["evals/research-v0.3/controller.py", "adapters/codex/session.py",
                     "adapters/local-process/broker.py", "adapters/local-process/compute_client.py",
                     "allagma/resources.py", "allagma/files.py"]
    for name in control_files:
        target = record/"controller-source"/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, target)
    write_json(record/"inputs.json", {"prepared_at": utcnow(), "task": "core-culp", "condition": condition,
        "workspace": str(workspace), "ledger": str(ledger), "readonly": [str(p) for p in readonly],
        "common_inputs": inventory(inputs), "workflow_lock": workflow,
        "controller_sha256": file_hash(__file__), "control_files": {name:file_hash(ROOT/name) for name in control_files},
        "phase": "development"}, immutable=True)
    prompt = ("Complete the research task in inputs/BRIEF.md using inputs/task.txt, inputs/SOURCES.md, inputs/RESOURCES.json and inputs/COMPUTE.md. "
              "Work autonomously through planning, implementation, actual execution, recovery, critique, reporting and verification. "
              "Read all four files before acting. Keep all work inside this workspace and all computation within the supplied local broker. "
              "The provided files are the full initial brief; no task-specific follow-up guidance is planned. Deliver the requested artifacts and an honest completion assessment.\n")
    if condition == "allagma":
        prompt += "Use the installed Allagma research workflow and native skills. Read ALLAGMA.md, resolve the selected recipe and methods through the exact study/campaign lock, and preserve the generated bundle.\n"
    (record/"initial-prompt.txt").write_text(prompt)
    return record


def launch(record):
    record = Path(record).resolve()
    prepared = read_json(record/"inputs.json")
    workspace = Path(prepared["workspace"])
    if inventory(workspace/"inputs") != prepared["common_inputs"]:
        raise ValueError("Prepared common inputs changed")
    for name, expected in prepared.get("control_files", {}).items():
        if file_hash(ROOT/name) != expected:
            raise ValueError("Prepared controller code changed: "+name)
    broker = local.Broker(workspace, prepared["ledger"], record/"broker",
        readonly=prepared["readonly"], protected=[ROOT], interrupt_first_attempt=True)
    result = native.capture(codex=CODEX, workspace=workspace, record=record/"native",
        runtime=workspace.parent/"runtime", prompt=(record/"initial-prompt.txt").read_text(), timeout=1800,
        config=Path.home()/".codex/config.toml", auth=Path.home()/".codex/auth.json",
        blocked=[ROOT, Path.home()/".codex", Path.home()/".agents", Path.home()/"Documents/vault"],
        readonly=prepared["readonly"], on_tick=broker.poll)
    write_json(record/"controller-outcome.json", {"native_status": result["status"],
        "inputs_unchanged": inventory(workspace/"inputs")==prepared["common_inputs"],
        "submission_exists": (workspace/"submission.json").exists(),
        "task_completion": "unscored", "subsequent_coordinator_messages": 0}, immutable=True)
    print(json.dumps({"record": str(record), "native_status": result["status"], "thread_ids": result["thread_ids"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["prepare-core", "launch"])
    parser.add_argument("--label")
    parser.add_argument("--condition", choices=["plain", "allagma"])
    parser.add_argument("--record", type=Path)
    args = parser.parse_args()
    if args.operation == "prepare-core":
        print(prepare_core(args.label, args.condition))
    else:
        launch(args.record)
