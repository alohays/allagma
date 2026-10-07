"""Fresh offline environment, all original experiments, recovery, and recomputation."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from broker import run

ROOT = Path(__file__).resolve().parents[1]


def required(arguments):
    response, code = run(arguments)
    if code != 0 or response.get("result", {}).get("status") != "completed":
        raise SystemExit("Broker request did not complete; retained evidence must be inspected before continuation.")
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reproductions/" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=False)
    if sys.version_info[:2] != (3, 11):
        raise SystemExit("The supplied offline wheels require Python 3.11 on Apple Silicon macOS.")
    if not (ROOT / "source/provenance.json").exists():
        required(["--category", "setup", "--label", "fresh-prepare-sources", "--timeout", "15", "--",
                  "python3", "scripts/prepare_sources.py"])
    environment = output / "venv"
    python = str(environment / "bin/python")
    required(["--category", "setup", "--label", "fresh-environment", "--timeout", "60", "--",
              "python3", "-m", "venv", str(environment)])
    required(["--category", "setup", "--label", "fresh-offline-dependencies", "--timeout", "90", "--",
              python, "-m", "pip", "install", "--no-cache-dir", "--no-index", "--find-links",
              "inputs/materials/wheels", "-r", "requirements.lock"])
    first_run = args.output + "/runs/attempt01"
    response, code = run(["--category", "compute", "--label", "fresh-all-three-scripts", "--timeout", "90", "--attempt", "--",
                          python, "scripts/run_experiments.py", "--output", first_run])
    selected = first_run
    # Only a final authoritative injected-interruption receipt enables this retry.
    # An observation timeout is neither final nor retriable here.
    if code != 0:
        if response.get("injected_interruption") and response.get("result", {}).get("status") in ("timed_out", "interrupted", "terminated"):
            selected = args.output + "/runs/attempt02"
            response = required(["--category", "compute", "--label", "fresh-interruption-recovery", "--timeout", "90", "--",
                                 python, "scripts/run_experiments.py", "--output", selected])
        else:
            raise SystemExit("Fresh execution did not complete; preserve and inspect the authoritative broker outcome.")
    arguments = ["--category", "compute", "--label", "fresh-evidence-verification", "--timeout", "30", "--",
                 python, "scripts/recompute.py", "--run", selected, "--output", args.output + "/analysis"]
    if (ROOT / "report.json").exists():
        arguments += ["--expected", "report.json"]
    required(arguments)
    summary = {"status": "completed", "selected_run": selected,
               "experiment_request_id": response["request_id"],
               "analysis": args.output + "/analysis", "fresh_environment": str(environment.relative_to(ROOT))}
    (output / "reproduction.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
