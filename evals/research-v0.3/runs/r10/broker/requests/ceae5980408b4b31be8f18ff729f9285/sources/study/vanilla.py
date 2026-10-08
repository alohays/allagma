"""Run all three scripts directly, without observation wrappers, under one broker job."""
import argparse
import subprocess
import sys
from common import ROOT, read, ref, write

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
args = parser.parse_args()
out = ROOT / args.output
out.mkdir(parents=True, exist_ok=False)
raw = read(ROOT / "evidence/raw-manifest.json")
results = []
for dataset in ("iris", "zoo", "wine"):
    script = ROOT / "work/capsule/code" / f"{dataset}_sample.py"
    command = [sys.executable, str(script)]
    result = subprocess.run(command, cwd=script.parent, capture_output=True, text=True, timeout=45)
    (out / f"{dataset}.stdout.txt").write_text(result.stdout)
    (out / f"{dataset}.stderr.txt").write_text(result.stderr)
    assert result.returncode == 0, result.stderr
    expected = next(r for r in raw["runs"] if r["dataset"] == dataset)
    assert result.stdout == (ROOT / expected["directory"] / "stdout.txt").read_text()
    results.append({"dataset": dataset, "argv": command, "cwd": script.parent.relative_to(ROOT).as_posix(),
        "stdout": ref(out / f"{dataset}.stdout.txt"), "stderr": ref(out / f"{dataset}.stderr.txt"),
        "exit_code": result.returncode, "exact_stdout_agreement": True})
write(out / "verification.json", {"status": "pass", "runs": results,
    "coverage": "Direct, uninstrumented execution of all three source scripts prints exactly the same four accuracy lines as canonical instrumented execution."})
print("All three direct script stdout streams exactly match canonical instrumented execution.")
