"""Offline environment setup; invoke only through inputs/compute.py (setup)."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import venv

parser = argparse.ArgumentParser()
parser.add_argument("environment")
parser.add_argument("evidence")
args = parser.parse_args()
root = Path.cwd().resolve()
environment = (root / args.environment).resolve()
evidence = root / args.evidence
assert environment.is_relative_to(root) and not environment.exists()
evidence.mkdir(parents=True, exist_ok=True)
venv.EnvBuilder(with_pip=True).create(environment)
python = str(environment / "bin/python")
command = [python, "-m", "pip", "install", "--no-index", "--no-cache-dir",
           "--find-links", str(root / "inputs/wheels"), "-r", str(root / "requirements.lock.txt")]
(evidence / "install-command.json").write_text(json.dumps(command, indent=2) + "\n")
subprocess.run(command, check=True)
freeze = subprocess.check_output([python, "-m", "pip", "freeze", "--all"], text=True)
(evidence / "pip-freeze.txt").write_text(freeze)
subprocess.run([python, "-m", "pip", "check"], check=True)
print(freeze, end="")
