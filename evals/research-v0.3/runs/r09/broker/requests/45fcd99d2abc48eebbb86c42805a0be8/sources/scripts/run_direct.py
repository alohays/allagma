"""Direct uninstrumented runpy execution of all three adapted source scripts."""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(ROOT / "source/adapted/code"))
    completed = []
    for dataset in ["iris", "zoo", "wine"]:
        script = ROOT / "source/adapted/code" / (dataset + "_sample.py")
        with (out / (dataset + "-stdout.txt")).open("x") as stdout, (out / (dataset + "-stderr.txt")).open("x") as stderr:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                runpy.run_path(str(script), run_name="__main__")
        completed.append({"dataset": dataset, "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
                          "status": "completed"})
        (out / "run.json").write_text(json.dumps({"execution": "uninstrumented runpy.run_path", "runs": completed}, indent=2) + "\n")
        print((out / (dataset + "-stdout.txt")).read_text(), end="", flush=True)


if __name__ == "__main__":
    main()
