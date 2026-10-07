"""Fresh setup and full execution via the common broker; no direct science."""
import argparse
import json
from pathlib import Path
import sys
from common import ROOT, ref, write_json
from broker_job import invoke

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="reproduction/fresh")
    p.add_argument("--env", default=".venv-reproduce")
    args = p.parse_args()
    output = ROOT / args.output
    env = ROOT / args.env
    if output.exists() or env.exists():
        raise SystemExit("Choose new --output and --env paths; prior attempts are immutable")
    for path in [output, env]:
        path.resolve().relative_to(ROOT)
    output.mkdir(parents=True)
    history = args.output + "/jobs"
    def job(name, category, timeout, cmd, marked=False):
        result = invoke(name, category, timeout, cmd, marked, history)
        if result["result"]["status"] != "completed":
            raise RuntimeError(f"{name} did not complete; preserve its evidence and inspect before retrying")
    job("fresh-venv", "setup", 60, ["python3.11", "-m", "venv", str(env)])
    py = str(env / "bin/python")
    job("fresh-packages", "setup", 120, [py, "-m", "pip", "install", "--no-cache-dir", "--no-index",
        "--find-links", "inputs/materials/wheels", "-r", "requirements.lock.txt"])
    job("fresh-environment", "setup", 15, [py, "tools/environment.py", args.output + "/environment.json"])
    job("fresh-pilot", "compute", 90, [py, "tools/pilot.py", "--out", args.output + "/pilot"])
    runs = []
    for dataset in ["iris", "zoo", "wine"]:
        # Run one scientific process at a time; controller interruption is recorded
        # and retried only after an authoritative terminal outcome.
        attempt = 1
        while True:
            location = args.output + f"/{dataset}-a{attempt:02d}"
            result = invoke(f"fresh-{dataset}-a{attempt:02d}", "compute", 60,
                [py, "tools/run_capsule.py", "--dataset", dataset, "--out", location],
                marked=(dataset == "iris" and attempt == 1), history=history)
            if result["result"]["status"] == "completed":
                runs.append({"dataset": dataset, "raw": ref(ROOT / location / "raw.json"),
                             "attempt_id": f"fresh-{dataset}-a{attempt:02d}"})
                break
            if not result.get("injected_interruption") or attempt != 1:
                raise RuntimeError("Unsuccessful scientific job retained; no unsupported automatic retry")
            attempt += 1
    files = []
    for run in runs:
        raw = json.loads((ROOT / run["raw"]["path"]).read_text())
        files.extend([run["raw"], raw["script"], raw["dataset_arrays"], raw["stdout"], raw["stderr"]])
        files.extend(c["arrays"] for c in raw["calls"])
    manifest = {"format": "culp-raw-manifest-v1", "runs": runs,
                "files": list({f["path"]: f for f in files}.values()),
                "exclusions": ["Synthetic pilot", "Any authoritatively interrupted attempt"]}
    path = output / "raw-manifest.json"
    write_json(path, manifest)
    job("fresh-analysis", "compute", 30, [py, "tools/analyze.py", "--manifest", str(path.relative_to(ROOT)),
                                          "--out", args.output + "/analysis"])
    job("fresh-graph-audit", "compute", 30, [py, "tools/audit_science.py", "--manifest", str(path.relative_to(ROOT)),
        "--out", args.output + "/graph-audit.json"])
    # This comparison is file bookkeeping, not recomputation of science.
    original = json.loads((ROOT / "report.json").read_text())
    fresh = json.loads((output / "analysis/report.json").read_text())
    write_json(output / "agreement.json", {"answers_identical": original == fresh,
        "scope": "Six requested rounded percentages in a fresh environment; no historical reference outputs available"})
    assert original == fresh
    print("Fresh environment, all three source scripts, retained-data analysis and graph audit completed.")

if __name__ == "__main__":
    main()
