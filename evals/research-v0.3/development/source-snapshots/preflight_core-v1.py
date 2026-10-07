"""Controller-only compatibility check; never supplied to evaluated agents."""
import ast
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Dict


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path.cwd()
    original = root / "capsules/capsule-6460826"
    destination = root / "culp-preflight"
    destination.mkdir(exist_ok=False)
    for name in ("code", "data", "metadata"):
        shutil.copytree(original/name, destination/name)
    modifications = []
    for name in ("wine_sample.py", "zoo_sample.py"):
        path = destination/"code"/name
        source = path.read_text()
        changed = source.replace("'/data/", "'../data/")
        assert source != changed
        path.write_text(changed)
        modifications.append({"file": name, "original_sha256": sha(original/"code"/name),
                              "adapted_sha256": sha(path), "change": "Absolute container /data path becomes capsule-relative ../data; no algorithm or parameters changed"})
    answers, runs = {}, []
    environment = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}
    for name in ("iris_sample.py", "zoo_sample.py", "wine_sample.py"):
        result = subprocess.run([sys.executable, name], cwd=destination/"code",
                                env=environment, text=True, capture_output=True, timeout=30)
        (destination/(name+".stdout.txt")).write_text(result.stdout)
        (destination/(name+".stderr.txt")).write_text(result.stderr)
        runs.append({"script": name, "exit_code": result.returncode,
                     "stdout_sha256": sha(destination/(name+".stdout.txt"))})
        print(result.stdout, end="", flush=True)
        if result.returncode:
            print(result.stderr, file=sys.stderr)
            raise SystemExit(result.returncode)
        for dataset, lp, accuracy in re.findall(r"Prediction Accuracy for (\w+) Dataset \(λ=(\w+)\) = ([0-9.]+)%", result.stdout):
            answers[(dataset, lp)] = float(accuracy)
    task = next(item for item in json.loads((root/"core-bench/benchmark/dataset/core_train.json").read_text())
                if item["capsule_id"] == "capsule-6460826")
    report = {}
    for question in task["results"][0]:
        dataset = next(key for key in ("Iris", "Zoo", "Wine") if key in question)
        lp = "CN" if " CN " in question else "AA"
        report[question] = answers[(dataset, lp)]
    # Execute the exact upstream scoring function, with only its required imports.
    # No numerical tolerance, reference answer or algorithm changes are permitted.
    import numpy as np
    from scipy.stats import t
    scorer_source = root/"core-bench/benchmark/evaluations.py"
    tree = ast.parse(scorer_source.read_text())
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "eval_result_json")
    namespace = {"np": np, "math": math, "t": t, "Dict": Dict}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(scorer_source), "exec"), namespace)
    score = namespace["eval_result_json"](task["results"], copy.deepcopy(report))
    outcome = {"capsule_id": task["capsule_id"], "task_prompt": task["task_prompt"],
        "original_tar_sha256": sha(root/"capsules/capsule-6460826.tar.gz"),
        "upstream_scorer_sha256": sha(scorer_source), "scorer": "exact upstream eval_result_json AST; original references",
        "modifications": modifications, "runs": runs, "report": report, "score": score,
        "status": "pass" if score["correct_written_answers"] == score["total_written_questions"] == 6 else "fail",
        "scope": "Native Mac CPU compatibility with path-only changes and isolated updated dependencies; not a full CORE-Bench run",
        "source_caveat": "Iris and Zoo source scripts loop over labels but always call link_predictor='CS'; retained exactly for source-task fidelity"}
    (destination/"preflight.json").write_text(json.dumps(outcome, indent=2)+"\n")
    print(json.dumps(outcome, indent=2))
    raise SystemExit(0 if outcome["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
