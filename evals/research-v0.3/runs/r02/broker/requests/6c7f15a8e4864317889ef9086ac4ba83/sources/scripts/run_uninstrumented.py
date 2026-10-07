"""Direct sequential script execution to check that recording did not change stdout."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "runs/direct-cli"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=False)
    outcomes = []
    for dataset in ("iris", "zoo", "wine"):
        argv = [sys.executable, str(ROOT / "source/adapted/code" / (dataset + "_sample.py"))]
        result = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
        (OUTPUT / (dataset + "-stdout.txt")).write_text(result.stdout)
        (OUTPUT / (dataset + "-stderr.txt")).write_text(result.stderr)
        print(result.stdout, end="", flush=True)
        expected = (ROOT / "runs/attempt02" / dataset / "stdout.txt").read_text()
        outcome = {"dataset": dataset, "argv": argv, "returncode": result.returncode,
                   "stdout_matches_instrumented_run": result.stdout == expected,
                   "stderr_empty": result.stderr == ""}
        outcomes.append(outcome)
        (OUTPUT / "verification.json").write_text(json.dumps(outcomes, indent=2) + "\n")
        assert result.returncode == 0 and result.stdout == expected and result.stderr == "", outcome
    print("All three direct CLI outputs exactly match the recorded execution.", flush=True)


if __name__ == "__main__":
    main()
