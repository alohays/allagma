"""Broker-only differential check of ordinary script execution without profiling."""
import argparse
import json
import subprocess
import sys
from common import ROOT, ref, write_json

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    runs = []
    for dataset, attempt in [("iris", "iris-a02"), ("zoo", "zoo-a01"), ("wine", "wine-a01")]:
        script = ROOT / "source/adapted/code" / (dataset + "_sample.py")
        command = [sys.executable, str(script)]
        result = subprocess.run(command, cwd=script.parent, capture_output=True, text=True, check=False)
        stdout = out / (dataset + "-stdout.txt")
        stderr = out / (dataset + "-stderr.txt")
        stdout.write_text(result.stdout)
        stderr.write_text(result.stderr)
        expected = ROOT / "evidence/runs" / attempt / "stdout.txt"
        runs.append({"dataset": dataset, "command": command, "cwd": str(script.parent.relative_to(ROOT)),
                     "stdout": ref(stdout), "stderr": ref(stderr), "exit_code": result.returncode,
                     "source": ref(script), "expected": ref(expected),
                     "stdout_identical": result.stdout == expected.read_text()})
        assert result.returncode == 0 and result.stdout == expected.read_text()
    write_json(out / "check.json", {"passed": True, "runs": runs,
        "coverage": "Ordinary uninstrumented execution of each complete source script produces identical stdout to the captured run",
        "limitation": "Does not prove the absence of all possible instrumentation effects for other inputs"})
    print(json.dumps({"passed": True, "scripts": len(runs)}))
