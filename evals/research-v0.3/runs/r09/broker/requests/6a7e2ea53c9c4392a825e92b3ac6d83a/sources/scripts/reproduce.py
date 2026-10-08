"""Fresh-environment orchestration. All setup and scientific work uses the broker."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="New workspace-relative directory; default is unique")
    args = parser.parse_args()
    relative = args.output or ("reproduction/" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8])
    out = (ROOT / relative).resolve()
    assert out.is_relative_to(ROOT), "Output must remain in this workspace"
    out.mkdir(parents=True, exist_ok=False)
    (out / "commands").mkdir()
    environment = out / ".venv"
    python = str(environment / "bin/python")
    history = []

    def relative_path(path):
        return str(path.relative_to(ROOT))

    def run(category, label, timeout, argv, marked=False):
        command = [sys.executable, "inputs/compute.py", "--category", category,
                   "--label", label, "--timeout", str(timeout)]
        if marked:
            command.append("--attempt")
        command += ["--", *argv]
        print("BROKER:", json.dumps(command), flush=True)
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        number = len(history) + 1
        log = out / "commands" / f"{number:02d}-{label}"
        log.with_suffix(".stdout.txt").write_text(result.stdout)
        log.with_suffix(".stderr.txt").write_text(result.stderr)
        try:
            response, _ = json.JSONDecoder().raw_decode(result.stdout.lstrip())
        except ValueError:
            raise RuntimeError(f"No parseable broker response; retained client logs at {log}")
        request_id = response["request_id"]
        entry = {"command": command, "request_id": request_id, "label": label,
                 "category": category, "client_exit_code": result.returncode}
        history.append(entry)
        (out / "history.json").write_text(json.dumps(history, indent=2) + "\n")
        if response.get("status") == "observation_timeout":
            (out / "pending-request.json").write_text(json.dumps(response, indent=2) + "\n")
            raise RuntimeError(f"Observation timeout for {request_id}; no retry submitted. Inspect this same request's response before further work.")
        archive = out / "broker" / request_id
        archive.mkdir(parents=True)
        for source, dest in [(ROOT / ".compute/requests" / (request_id + ".json"), "request.json"),
                             (ROOT / ".compute/responses" / (request_id + ".json"), "response.json"),
                             (ROOT / ".compute/responses" / (request_id + "-stdout.txt"), "stdout.txt"),
                             (ROOT / ".compute/responses" / (request_id + "-stderr.txt"), "stderr.txt")]:
            if source.exists():
                shutil.copyfile(source, archive / dest)
        entry["receipt"] = relative_path(archive / "response.json")
        entry["result"] = response.get("result")
        entry["injected_interruption"] = response.get("injected_interruption", False)
        (out / "history.json").write_text(json.dumps(history, indent=2) + "\n")
        print(json.dumps({"label": label, "request_id": request_id, "result": response.get("result")}), flush=True)
        return entry

    def require_completed(entry):
        if entry["result"]["status"] != "completed" or entry["result"]["exit_code"] != 0:
            raise RuntimeError(f"Broker job failed; preserved history and no blind retry: {entry['request_id']}")

    try:
        subprocess.run([sys.executable, "scripts/freeze_sources.py"], cwd=ROOT, check=True)
        require_completed(run("setup", "fresh-venv", 60, [sys.executable, "-m", "venv", str(environment)]))
        require_completed(run("setup", "fresh-offline-packages", 90,
                              [python, "-m", "pip", "install", "--no-cache-dir", "--no-index",
                               "--find-links", "inputs/materials/wheels", "-r", "requirements.lock"]))
        require_completed(run("setup", "fresh-environment-record", 15,
                              [python, "scripts/environment.py", relative_path(out / "environment.json")]))
        index = {"format": "culp-run-index-v1", "interrupted": None, "runs": []}
        for dataset in ["iris", "zoo", "wine"]:
            directory = out / (dataset + "-attempt-01")
            record = run("compute", "fresh-" + dataset, 60,
                         [python, "scripts/run_capture.py", dataset, "--output", relative_path(directory)],
                         marked=dataset == "iris")
            if record["injected_interruption"]:
                index["interrupted"] = {"directory": relative_path(directory),
                                         "attempt_id": record["request_id"], "receipt": record["receipt"]}
                directory = out / (dataset + "-attempt-02-recovery")
                record = run("compute", "fresh-" + dataset + "-recovery", 60,
                             [python, "scripts/run_capture.py", dataset, "--output", relative_path(directory)])
            require_completed(record)
            index["runs"].append({"dataset": dataset, "directory": relative_path(directory),
                                  "attempt_id": record["request_id"], "receipt": record["receipt"]})
            (out / "run-index.json").write_text(json.dumps(index, indent=2) + "\n")
        direct = out / "direct"
        record = run("compute", "fresh-direct-validation", 30,
                     [python, "scripts/run_direct.py", "--output", relative_path(direct)])
        require_completed(record)
        index["direct"] = {"directory": relative_path(direct), "attempt_id": record["request_id"], "receipt": record["receipt"]}
        (out / "run-index.json").write_text(json.dumps(index, indent=2) + "\n")
        record = run("compute", "fresh-evidence-recomputation", 30,
                     [python, "scripts/recompute.py", "--index", relative_path(out / "run-index.json"),
                      "--output", relative_path(out / "analysis"), "--compare-report", "report.json"])
        require_completed(record)
        (out / "completion.json").write_text(json.dumps({"status": "complete", "fresh_environment": relative_path(environment),
            "report": relative_path(out / "analysis/report.json"), "all_six_answers_match_submission": True,
            "verification": relative_path(out / "analysis/verification.json")}, indent=2) + "\n")
        print(f"Fresh reproduction completed; artifacts: {relative_path(out)}", flush=True)
    except BaseException as error:
        (out / "failure.json").write_text(json.dumps({"status": "failed", "error": repr(error)}, indent=2) + "\n")
        raise


if __name__ == "__main__":
    main()
