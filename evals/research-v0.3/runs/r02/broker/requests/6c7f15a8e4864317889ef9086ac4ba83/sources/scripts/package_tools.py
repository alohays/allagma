"""Broker-run package audit, revision sealing, and final hash verification."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".venv", "venv", "__pycache__", ".compute", ".tmp", ".git", ".pytest_cache"}
EXCLUDED_FILES = {".DS_Store", "artifact-manifest.json"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text())


def write(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def inventory():
    files = []
    for base, directories, names in os.walk(ROOT):
        directories[:] = sorted(d for d in directories if d not in EXCLUDED_DIRS)
        for name in sorted(names):
            if name in EXCLUDED_FILES or name.endswith((".pyc", ".pyo")):
                continue
            path = Path(base) / name
            assert path.is_file() and not path.is_symlink(), str(path)
            files.append({"path": path.relative_to(ROOT).as_posix(),
                          "size_bytes": path.stat().st_size, "sha256": sha(path)})
    return sorted(files, key=lambda entry: entry["path"])


def revision(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def resources():
    completed = []
    pending = []
    for path in sorted((ROOT / ".compute/requests").glob("*.json")):
        request = json.loads(path.read_text())
        response_path = ROOT / ".compute/responses" / (request["request_id"] + ".json")
        if not response_path.exists():
            pending.append({"request_id": request["request_id"], "category": request["category"],
                            "label": request["label"], "timeout_seconds": request["timeout_seconds"]})
            continue
        response = json.loads(response_path.read_text())
        result = response["result"]
        completed.append({"request_id": request["request_id"], "label": request["label"],
                          "category": request["category"], "marked_attempt": request["attempt"],
                          "requested_timeout_seconds": request["timeout_seconds"],
                          "injected_interruption": response.get("injected_interruption", False),
                          "status": result["status"], "exit_code": result["exit_code"],
                          "charged_seconds": result["charged_seconds"], "ended_at": result["ended_at"],
                          "peak_rss_bytes": result["peak_rss_bytes"],
                          "peak_storage_bytes": result["peak_storage_bytes"],
                          "response": response_path.relative_to(ROOT).as_posix()})
    completed.sort(key=lambda entry: entry["ended_at"])
    profile = read("inputs/RESOURCES.json")["profile"]
    totals = {category: sum(e["charged_seconds"] for e in completed if e["category"] == category)
              for category in ("setup", "compute")}
    attempts = sum(e["category"] == "compute" for e in completed + pending)
    assert attempts <= profile["attempt_limit"]
    for category in totals:
        assert totals[category] < profile["budgets_seconds"][category]
    assert all(e["peak_rss_bytes"] <= profile["rss_limit_bytes"] for e in completed)
    assert all(e["peak_storage_bytes"] <= profile["storage_limit_bytes"] for e in completed)
    assert all(e["requested_timeout_seconds"] <= profile["command_timeout_seconds"][e["category"]] for e in completed)
    return {"format": "culp-resource-ledger-v1", "observed_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Completed local-client receipts at collection time; the current request and later seal/verification charges are not yet completed and are listed separately when visible.",
            "charged_seconds_completed": totals, "compute_request_count_including_pending": attempts,
            "ceilings": profile, "completed_requests": completed, "pending_at_collection": pending,
            "model_usage": "Accounted by native controller, not measured by this package"}


def artifact_contract():
    submission = read("submission.json")
    assert submission["task_id"] == "core-culp" and submission["execution_status"] == "complete"
    for field in ("report", "manuscript", "review", "measurements", "protocol"):
        target = Path(submission[field])
        assert not target.is_absolute() and ".." not in target.parts
        assert (ROOT / target).is_file()
    for field in ("reproduce", "recompute"):
        item = submission[field]
        assert item["cwd"] == "."
        assert isinstance(item["argv"], list) and all(isinstance(arg, str) for arg in item["argv"])
        assert (ROOT / item["argv"][1]).is_file()
    task = (ROOT / "inputs/materials/task.txt").read_text()
    questions = ast.literal_eval(re.search(r"dict_keys\((\[.*?\])\)", task, re.DOTALL).group(1))
    report = read(submission["report"])
    assert list(report) == questions
    assert all(isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 100 for value in report.values())
    for path in ("analysis/final/report.json", "recomputed/report.json", "reproductions/validation/analysis/report.json"):
        assert report == read(path)
    verification = read("analysis/final/verification.json")
    assert verification["status"] == "passed"
    assert verification["same_environment_repeatability"]["all_dataset_arrays_graphs_predictions_stdout_equal"]
    assert verification["runner_sha256"] == sha(ROOT / "scripts/run_experiments.py")
    assert verification["recompute_sha256"] == sha(ROOT / "scripts/recompute.py")
    assert verification["protocol_sha256"] == sha(ROOT / "PROTOCOL.md")
    assert read("analysis/primary/verification.json")["recompute_sha256"] == sha(ROOT / "source/workflow-revisions/recompute-v1.py")
    assert read("recomputed/verification.json")["recompute_sha256"] == verification["recompute_sha256"]
    measurements = read(submission["measurements"])
    assert measurements == read("analysis/final/measurements.json")
    assert measurements["format"] == "research-measurements-v1"
    assert measurements["task_id"] == "core-culp" and measurements["protocol"] == "PROTOCOL.md"
    assert len(measurements["runs"]) == 12
    assert len({(entry["dataset"], entry["printed_label"]) for entry in measurements["runs"]}) == 12
    for entry in measurements["runs"]:
        for key in ("arrays", "dataset_arrays", "graph_arrays", "stdout", "broker_receipt"):
            assert (ROOT / entry[key]).is_file()
            assert not Path(entry[key]).is_absolute()
        assert entry["metrics"]["accuracy"] == entry["metrics"]["correct"] / entry["metrics"]["total"]
        assert entry["source_revision"] == verification["source_revision"]
        assert read(entry["broker_receipt"])["result"]["status"] == "completed"
    review = read("review.json")
    assert review["reviewed_source_revision"] == verification["source_revision"]
    for entry in review["checks"] + review["findings"]:
        assert entry["evidence"]
        for path in entry["evidence"]:
            assert (ROOT / path).is_file(), (entry["id"], path)
    direct = read("runs/direct-cli/verification.json")
    assert [entry["dataset"] for entry in direct] == ["iris", "zoo", "wine"]
    assert all(entry["returncode"] == 0 and entry["stdout_matches_instrumented_run"] and entry["stderr_empty"] for entry in direct)
    return {"status": "passed", "question_count": len(questions), "measurement_run_count": 12,
            "direct_script_count": len(direct), "source_revision": verification["source_revision"],
            "verified": ["submission paths and argv", "exact original question strings", "all published answer files equal",
                         "measurements reference numeric evidence verified by recomputation", "current checker and runner revisions",
                         "retained earlier checker revision", "review evidence links", "three direct CLI outputs"]}


def audit():
    contract = artifact_contract()
    expected_inputs = read("research-workspace.json")["common_inputs"]
    for relative, expected in expected_inputs.items():
        assert sha(ROOT / "inputs" / relative) == expected, relative
    profile = read("inputs/RESOURCES.json")["profile"]
    contents = inventory()
    assert all(row["size_bytes"] <= profile["file_limit_bytes"] for row in contents)
    for folder in ("scripts", "source/original/code", "source/adapted/code", "source/workflow-revisions"):
        for path in (ROOT / folder).rglob("*.py"):
            ast.parse(path.read_text(), filename=path.relative_to(ROOT).as_posix())
    for name in ("REPORT.md", "REPRODUCE.md", "PROTOCOL.md"):
        for target in re.findall(r"\]\(([^)]+)\)", (ROOT / name).read_text()):
            if target.startswith(("https://", "http://", "#")):
                continue
            target = target.split("#", 1)[0]
            # Manifest is produced by the following sealing request.
            assert target == "artifact-manifest.json" or (ROOT / target).exists(), (name, target)
    ledger = resources()
    scientific = [row for row in ledger["completed_requests"] if row["category"] == "compute"]
    interrupted = scientific[0]
    assert interrupted["marked_attempt"] and interrupted["injected_interruption"]
    assert interrupted["status"] == "timed_out" and interrupted["exit_code"] == -15
    assert read("runs/attempt01/execution.json")["datasets_completed"] == []
    assert all(row["status"] == "completed" for row in scientific[1:])
    contract.update(input_files_verified=len(expected_inputs), all_python_sources_parse=True,
                    local_manuscript_links_exist=True, interrupted_attempt_preserved=True,
                    completed_resource_totals=ledger["charged_seconds_completed"],
                    scope="Package contract and integrity checks plus references to prior scientific verification; no experiment execution.")
    write("evidence/package-audit.json", contract)
    print(json.dumps(contract, indent=2))


def seal():
    assert read("evidence/package-audit.json")["status"] == "passed"
    contract = artifact_contract()
    write("evidence/resource-ledger.json", resources())
    reviewed = [entry for entry in inventory() if entry["path"] != "review.json"]
    review = read("review.json")
    review["reviewed_artifact_revision"] = revision(reviewed)
    review["reviewed_artifacts"] = reviewed
    review["delivery_contract_audit"] = "evidence/package-audit.json"
    review["resource_ledger"] = "evidence/resource-ledger.json"
    write("review.json", review)
    entries = inventory()
    manifest = {"format": "sha256-artifact-manifest-v1", "task_id": "core-culp",
                "algorithm": "sha256", "artifact_revision": revision(entries),
                "revision_definition": "SHA-256 of json.dumps(files, sort_keys=True, separators=(',', ':')).encode()",
                "excluded_directory_names": sorted(EXCLUDED_DIRS),
                "excluded_file_names": sorted(EXCLUDED_FILES), "excluded_suffixes": [".pyc", ".pyo"],
                "self_exclusion_reason": "A manifest cannot contain its own cryptographic hash; final broker responses are transient .compute files.",
                "files": entries}
    write("artifact-manifest.json", manifest)
    print(json.dumps({"status": "sealed", "files": len(entries), "artifact_revision": manifest["artifact_revision"],
                      "reviewed_artifact_revision": review["reviewed_artifact_revision"],
                      "source_revision": contract["source_revision"]}, indent=2))


def verify():
    manifest = read("artifact-manifest.json")
    actual = inventory()
    assert actual == manifest["files"], "File inventory, bytes, or hashes differ from the sealed package"
    assert revision(actual) == manifest["artifact_revision"]
    review = read("review.json")
    reviewed = [entry for entry in actual if entry["path"] != "review.json"]
    assert reviewed == review["reviewed_artifacts"]
    assert revision(reviewed) == review["reviewed_artifact_revision"]
    assert artifact_contract()["status"] == "passed"
    ledger = resources()
    print(json.dumps({"status": "verified", "file_count": len(actual),
                      "artifact_revision": manifest["artifact_revision"],
                      "reviewed_artifact_revision": review["reviewed_artifact_revision"],
                      "completed_charged_seconds_at_final_check": ledger["charged_seconds_completed"],
                      "compute_requests_including_this_check": ledger["compute_request_count_including_pending"],
                      "scope": "All listed files, complete nonexcluded inventory, reviewed revision, artifact contract, and observed broker budgets. Scientific evidence was separately verified and retained."}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["audit", "seal", "verify"])
    operation = parser.parse_args().operation
    {"audit": audit, "seal": seal, "verify": verify}[operation]()
