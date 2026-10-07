"""Invoke the supplied broker client and retain its permanent request/response evidence.

This is orchestration/bookkeeping only. Scientific programs remain broker children.
"""
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def archive_all():
    destination = ROOT / "evidence/broker"
    destination.mkdir(parents=True, exist_ok=True)
    for request_path in sorted((ROOT / ".compute/requests").glob("*.json")):
        request = json.loads(request_path.read_text())
        request_id = request["request_id"]
        folder = destination / request_id
        folder.mkdir(exist_ok=True)
        shutil.copyfile(request_path, folder / "request.json")
        for suffix, name in ((".json", "response.json"), ("-stdout.txt", "stdout.txt"), ("-stderr.txt", "stderr.txt")):
            source = ROOT / ".compute/responses" / (request_id + suffix)
            if source.exists():
                shutil.copyfile(source, folder / name)


def run(arguments):
    result = subprocess.run([sys.executable, "inputs/compute.py", *arguments], cwd=ROOT,
                            text=True, capture_output=True)
    archive_all()
    try:
        response, _ = json.JSONDecoder().raw_decode(result.stdout)
        folder = ROOT / "evidence/broker" / response["request_id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "client-stdout.txt").write_text(result.stdout)
        (folder / "client-stderr.txt").write_text(result.stderr)
    except (ValueError, KeyError):
        response = {"status": "client_failure", "returncode": result.returncode}
    print(result.stdout, end="", flush=True)
    print(result.stderr, end="", file=sys.stderr, flush=True)
    return response, result.returncode


if __name__ == "__main__":
    if sys.argv[1:] == ["--archive-only"]:
        archive_all()
    else:
        _, returncode = run(sys.argv[1:])
        raise SystemExit(returncode)
