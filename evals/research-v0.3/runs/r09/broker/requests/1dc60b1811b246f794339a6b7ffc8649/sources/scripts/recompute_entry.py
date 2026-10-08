"""Portable broker-only recomputation, with minimal offline setup if needed."""
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
    parser.add_argument("--output")
    args = parser.parse_args()
    out = ROOT / (args.output or ("recomputed/" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]))
    out = out.resolve()
    assert out.is_relative_to(ROOT)
    out.mkdir(parents=True, exist_ok=False)

    def broker(category, label, timeout, command):
        argv = [sys.executable, "inputs/compute.py", "--category", category, "--label", label,
                "--timeout", str(timeout), "--", *command]
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        (out / (label + "-client-stdout.txt")).write_text(result.stdout)
        (out / (label + "-client-stderr.txt")).write_text(result.stderr)
        print(result.stdout, end="", flush=True)
        print(result.stderr, end="", file=sys.stderr, flush=True)
        response, _ = json.JSONDecoder().raw_decode(result.stdout.lstrip())
        request_id = response["request_id"]
        if response.get("status") == "observation_timeout":
            raise RuntimeError(f"Observation timeout; inspect request {request_id}; no retry was submitted")
        archive = out / "broker" / request_id
        archive.mkdir(parents=True)
        for source, name in [(ROOT / ".compute/requests" / (request_id + ".json"), "request.json"),
                             (ROOT / ".compute/responses" / (request_id + ".json"), "response.json"),
                             (ROOT / ".compute/responses" / (request_id + "-stdout.txt"), "stdout.txt"),
                             (ROOT / ".compute/responses" / (request_id + "-stderr.txt"), "stderr.txt")]:
            if source.exists():
                shutil.copyfile(source, archive / name)
        if response["result"]["status"] != "completed" or result.returncode != 0:
            raise RuntimeError(f"Broker job failed; retained request {request_id}")

    python = ROOT / ".venv/bin/python"
    if not python.exists():
        environment = out / ".venv"
        broker("setup", "recompute-venv", 60, [sys.executable, "-m", "venv", str(environment)])
        python = environment / "bin/python"
        broker("setup", "recompute-numpy", 60, [str(python), "-m", "pip", "install", "--no-cache-dir",
               "--no-index", "--find-links", "inputs/materials/wheels", "numpy==1.26.4"])
    broker("compute", "submission-recompute", 30, [str(python), "scripts/recompute.py",
           "--output", str((out / "analysis").relative_to(ROOT)), "--compare-report", "report.json"])
    print(f"Recomputed from retained evidence only: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
