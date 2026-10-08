"""Public full-reproduction command. Orchestration only; no scientific imports.

Every setup/experiment/analysis child is submitted to inputs/compute.py via the
study-owned recording wrapper. Run from workspace root, never inside a broker job.
"""
import argparse
from datetime import datetime, timezone
import subprocess
import sys
from common import ROOT, read, ref, tree_manifest, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", default=None)
    args = parser.parse_args()
    identity = args.id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    assert identity and all(ch.isalnum() or ch in "-_" for ch in identity)
    prefix = "reproduction-" + identity
    destination = ROOT / "reproductions" / identity
    destination.mkdir(parents=True, exist_ok=False)
    environment = ROOT / (".venv-" + prefix)
    if environment.exists():
        raise SystemExit("Fresh environment path already exists; choose another ID")
    def run(category, suffix, timeout, command):
        subprocess.run([sys.executable, "study/broker_run.py", "--category", category,
            "--label", prefix + "-" + suffix, "--timeout", str(timeout), "--", *map(str, command)],
            cwd=ROOT, check=True)
    run("setup", "environment", 60, [sys.executable, "-m", "venv", environment])
    python = environment / "bin/python"
    run("setup", "packages", 90, [python, "-m", "pip", "install", "--no-cache-dir", "--no-index",
        "--find-links", ROOT / "inputs/materials/wheels", "-r", ROOT / "requirements-lock.txt"])
    run("setup", "dependency-check", 20, [python, "-m", "pip", "check"])
    runs = []
    files = []
    for dataset in ("iris", "zoo", "wine"):
        path = destination / "raw" / dataset
        run("compute", dataset, 120 if dataset == "iris" else 60,
            [python, "study/runner.py", "--dataset", dataset, "--output", path.relative_to(ROOT)])
        runs.append({"dataset": dataset, "directory": path.relative_to(ROOT).as_posix(),
                     "attempt_id": prefix + "-" + dataset})
        files += list(path.rglob("*"))
    manifest = destination / "raw-manifest.json"
    write(manifest, {"format": "culp-raw-manifest-v1", "runs": runs, "files": tree_manifest(files), "exclusions": []})
    analysis = destination / "analysis"
    run("compute", "analysis", 30, [python, "study/analyze.py", "--manifest", manifest.relative_to(ROOT),
                                     "--output", analysis.relative_to(ROOT)])
    run("compute", "comparison", 20, [python, "study/compare_reproduction.py", "--analysis", analysis.relative_to(ROOT),
                                       "--output", (destination / "comparison.json").relative_to(ROOT)])
    write(destination / "complete.json", {"status": "complete", "environment": environment.relative_to(ROOT).as_posix(),
        "raw_manifest": ref(manifest), "comparison": ref(destination / "comparison.json"),
        "coverage": "Fresh setup, all three required source scripts, retained-data analysis and comparison against the delivered original answers"})
    print("Completed full reproduction in " + destination.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
