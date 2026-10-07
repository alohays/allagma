"""Public entry point: fresh offline setup and all source execution via broker."""
import argparse
from pathlib import Path
import subprocess
import sys
import uuid

parser = argparse.ArgumentParser()
parser.add_argument("--id", default="r-" + uuid.uuid4().hex[:12])
parser.add_argument("--output")
args = parser.parse_args()
assert args.id and "/" not in args.id and "\\" not in args.id
environment = ".venv-" + args.id
output = args.output or "reproductions/" + args.id
root = Path.cwd().resolve()
setup = [sys.executable, "inputs/compute.py", "--category", "setup", "--label", "culp-fresh-environment-" + args.id,
         "--timeout", "90", "--", "python3", "scripts/setup_environment.py", environment, "evidence/setup/" + args.id]
subprocess.run(setup, check=True)
execution = [sys.executable, "inputs/compute.py", "--category", "compute", "--label", "culp-fresh-execution-" + args.id,
             "--timeout", "60", "--", str(root / environment / "bin/python"), "scripts/fresh_execute.py", output]
subprocess.run(execution, check=True)
print("Fresh reproduction retained in", output)
