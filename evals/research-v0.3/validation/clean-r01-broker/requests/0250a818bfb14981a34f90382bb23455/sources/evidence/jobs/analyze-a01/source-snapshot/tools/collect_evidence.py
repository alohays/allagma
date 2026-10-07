"""Construct portable records/manifests from existing receipts; no scientific work."""
import argparse
import json
from pathlib import Path
from common import ROOT, now, ref, sha, write_json

CAMPAIGN = ROOT / "campaigns/culp-reproduction"

def collect_history():
    attempts = []
    # Include initial setup clients that ran before the study-owned bridge existed.
    for directory in sorted((ROOT / "evidence/setup").iterdir()):
        if not directory.is_dir():
            continue
        for file in directory.glob("*.json"):
            value = json.loads(file.read_text())
            if "result" not in value or "request_id" not in value:
                continue
            request = json.loads((directory / "request.json").read_text()) if (directory / "request.json").exists() else {}
            attempts.append({"identity": "initial-" + directory.name, "category": "setup", "request": request,
                             "receipt": ref(file), "result": value["result"], "request_id": value["request_id"]})
    job_roots = [ROOT / "evidence/jobs", ROOT / "reproduction/verified/jobs"]
    for jobroot in job_roots:
        if not jobroot.exists():
            continue
        for directory in sorted(jobroot.iterdir()):
            response_path = directory / "client-result.json"
            if not response_path.exists():
                continue
            response = json.loads(response_path.read_text())
            before = json.loads((directory / "before.json").read_text())
            item = {"identity": before["identity"], "category": before["category"],
                    "started_at": before["started_at"], "command": before["command"], "cwd": before["cwd"],
                    "receipt": ref(response_path), "prelaunch": ref(directory / "before.json"),
                    "request_id": response["request_id"], "result": response.get("result"),
                    "injected_interruption": response.get("injected_interruption", False)}
            attempts.append(item)
            name = before["identity"]
            if name in ["pilot-a01", "iris-a01", "iris-a02", "zoo-a01", "wine-a01"]:
                dataset = name.split("-")[0]
                out = ROOT / ("evidence/pilot/a01" if dataset == "pilot" else "evidence/runs/" + name)
                output_refs = [ref(p) for p in sorted(out.rglob("*")) if p.is_file()] if out.exists() else []
                output_refs += [ref(response_path), ref(directory / "client-stdout.txt"), ref(directory / "client-stderr.txt")]
                result = response["result"]
                status = "succeeded" if result["status"] == "completed" else "interrupted" if response["injected_interruption"] else "failed"
                rr = {"schema_version": "0.2", "record_type": "RunRecord", "run_id": dataset,
                    "attempt_id": name, "attempt_number": int(name[-2:]), "campaign_id": "culp-reproduction",
                    "experiment_id": dataset, "started_at": before["started_at"], "ended_at": result["ended_at"],
                    "inputs": [ref(CAMPAIGN / "runs" / dataset / "parameters.json"), ref(CAMPAIGN / "protocol.json"), ref(directory / "before.json")],
                    "outputs": output_refs, "environment": {"metadata": ref(ROOT / "evidence/setup/environment.json"),
                        "receipt": ref(response_path), "model_accounting": "Native model use external; local scientific worker tokens are zero"},
                    "model_revision": None, "data_revision": sha(ROOT / "evidence/provenance.json"),
                    "usage": {"wall_seconds": result["charged_seconds"], "money_usd": 0, "tokens": 0},
                    "status": status, "error": None if status == "succeeded" else {"kind": "controller_injected_interruption" if response["injected_interruption"] else result["status"],
                        "message": "Authoritative status preserved as " + result["status"] + "; see original receipt. New attempt required."},
                    "protocol_revision": "culp-v1", "bundle_id": "b-9a39b70665ba909edb8abc13",
                    "split": "pilot" if dataset == "pilot" else "confirmation", "command": before["command"], "exit_code": result["exit_code"]}
                target = CAMPAIGN / "runs" / dataset / "attempts" / name / "record.json"
                if target.exists():
                    assert json.loads(target.read_text()) == rr, "Never overwrite an attempt"
                else:
                    write_json(target, rr)
    totals = {category: sum(a["result"]["charged_seconds"] for a in attempts if a["category"] == category and a.get("result")) for category in ["setup", "compute"]}
    write_json(ROOT / "evidence/attempt-history.json", {"attempts": attempts, "known_charge_seconds": totals,
        "compute_requests": sum(a["category"] == "compute" for a in attempts),
        "scope": "Copied broker outcomes available in the delivered workspace; controller retains authoritative accounting. Final verification receipt may be newer than this table.",
        "recovery": {"interrupted": "iris-a01", "successful_retry": "iris-a02", "scientific_changes": "none",
                     "original_status": "timed_out", "injected_interruption": True}})

def raw_manifest():
    runs, files = [], []
    for dataset, attempt in [("iris", "iris-a02"), ("zoo", "zoo-a01"), ("wine", "wine-a01")]:
        path = ROOT / "evidence/runs" / attempt / "raw.json"
        raw = json.loads(path.read_text())
        record = CAMPAIGN / "runs" / dataset / "attempts" / attempt / "record.json"
        assert json.loads(record.read_text())["status"] == "succeeded"
        runs.append({"dataset": dataset, "attempt_id": attempt, "raw": ref(path), "run_record": ref(record)})
        files.extend([ref(path), ref(record), raw["script"], raw["dataset_arrays"], raw["stdout"], raw["stderr"]])
        files.extend(c["arrays"] for c in raw["calls"])
    files += [ref(CAMPAIGN / "protocol.json"), ref(ROOT / "evidence/provenance.json")]
    value = {"format": "culp-raw-manifest-v1", "runs": runs,
             "files": list({f["path"]: f for f in files}.values()),
             "exclusions": [{"attempt_id": "pilot-a01", "reason": "Synthetic qualification, no task answers"},
                            {"attempt_id": "iris-a01", "reason": "Injected interruption, authoritative timed_out; incomplete outputs not eligible"}]}
    dest = ROOT / "evidence/raw-manifest.json"
    if dest.exists():
        assert json.loads(dest.read_text()) == value, "Raw manifest is immutable"
    else:
        write_json(dest, value)
    runs = [{"dataset": e["dataset"], "seed": 42, "phase": "confirmation", "device": "cpu", "attempt_id": e["attempt_id"],
             "raw": e["raw"]["path"], "source_revision": sha(ROOT / "evidence/provenance.json"),
             "arrays": json.loads((ROOT/e["raw"]["path"]).read_text())["dataset_arrays"]["path"],
             "calls": [{"printed_label": c["printed_label"], "actual_predictor": c["actual_predictor"], "arrays": c["arrays"]["path"]}
                       for c in json.loads((ROOT/e["raw"]["path"]).read_text())["calls"]]} for e in value["runs"]]
    write_json(ROOT / "measurements.json", {"format": "research-measurements-v1", "task_id": "core-culp",
        "protocol": "campaigns/culp-reproduction/protocol.json", "runs": runs,
        "extension": "CULP-specific retained dataset/split arrays and per-call prediction/label/graph/score NPZ files; all load with allow_pickle=False. Supplied MEASUREMENTS.md specifies no CULP-specific fields."})

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw", action="store_true")
    args = p.parse_args()
    collect_history()
    if args.raw:
        raw_manifest()
