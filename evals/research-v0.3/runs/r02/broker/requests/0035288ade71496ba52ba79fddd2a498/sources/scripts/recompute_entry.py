"""Broker entry point for regenerating answers from retained evidence only."""
from pathlib import Path
import sys
from broker import run

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    python = ROOT / ".venv/bin/python"
    if not python.exists():
        raise SystemExit("Create the pinned .venv as documented in REPRODUCE.md before recomputation.")
    _, code = run(["--category", "compute", "--label", "retained-evidence-recompute", "--timeout", "30", "--",
                   str(python), "scripts/recompute.py", "--run", "runs/attempt02",
                   "--compare-run", "reproductions/validation/runs/attempt01",
                   "--output", "recomputed", "--expected", "report.json"])
    sys.exit(code)
