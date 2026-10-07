"""Broker-owned execution of the native frozen Allagma campaign."""
import json
import os
from pathlib import Path
import sys

root = Path.cwd().resolve()
os.environ["TMPDIR"] = str(root / ".tmp")
lock = json.loads((root / "campaigns/core-culp/lock.yaml").read_text())
sys.path.insert(0, str(root / ".allagma/bundles" / lock["bundle_id"]))
from allagma.campaigns import run_campaign
state = run_campaign(root, "core-culp")
print(json.dumps(state, indent=2))
if state["execution_status"] in ["failed", "blocked", "budget_exhausted"]:
    raise SystemExit(1)
