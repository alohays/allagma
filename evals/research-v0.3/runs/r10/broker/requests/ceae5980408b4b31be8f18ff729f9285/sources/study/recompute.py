"""Public retained-data recomputation command; delegates all numerical work."""
import argparse
from datetime import datetime, timezone
import subprocess
import sys
from common import ROOT

parser = argparse.ArgumentParser()
parser.add_argument("--id", default=None)
args = parser.parse_args()
identity = args.id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
assert identity and all(ch.isalnum() or ch in "-_" for ch in identity)
label = "recompute-" + identity
subprocess.run([sys.executable, "study/broker_run.py", "--category", "compute", "--label", label,
    "--timeout", "30", "--", str(ROOT / ".venv/bin/python"), "study/analyze.py", "--manifest", "evidence/raw-manifest.json",
    "--output", "recomputations/" + identity, "--compare", "analysis/main"], cwd=ROOT, check=True)
