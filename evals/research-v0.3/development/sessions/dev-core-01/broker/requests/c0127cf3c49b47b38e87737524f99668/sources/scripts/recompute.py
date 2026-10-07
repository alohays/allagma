"""Public entry point: one broker request; raw evidence only, no scientific rerun."""
import subprocess
import sys
import uuid

output = "recomputations/a-" + uuid.uuid4().hex[:12]
command = [sys.executable, "inputs/compute.py", "--category", "compute", "--label", "culp-raw-only-recompute",
           "--timeout", "15", "--", "python3", "scripts/analyze.py", ".", "analysis/raw-manifest.json", output]
raise SystemExit(subprocess.run(command).returncode)
