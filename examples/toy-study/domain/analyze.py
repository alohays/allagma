"""Study-owned paired MSE analysis; all numbers come from raw observations."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys


def analyze(study, manifest, output):
    rows = []
    for ref in manifest["raw"]:
        path = study / ref["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != ref["sha256"]:
            raise ValueError("Raw digest mismatch")
        raw = json.loads(path.read_text())
        if raw["control"] != "random":
            raise ValueError("Pilot/control output leaked into confirmation")
        estimate = math.fsum(raw["samples"]) / len(raw["samples"])
        mean_error = (estimate - raw["target"]) ** 2
        biased_error = (estimate + raw["bias"] - raw["target"]) ** 2
        rows.append({"seed": raw["seed"], "n": raw["n"], "mean_estimate": estimate,
                     "mean_squared_error": mean_error, "biased_squared_error": biased_error,
                     "paired_difference": biased_error - mean_error})
    rows.sort(key=lambda row: row["seed"])
    if len(rows) < 2 or len({row["seed"] for row in rows}) != len(rows):
        raise ValueError("Need independent distinct seeds for uncertainty")
    differences = [row["paired_difference"] for row in rows]
    delta = statistics.mean(differences)
    se = statistics.stdev(differences) / math.sqrt(len(rows))
    summary = {"replicates": len(rows), "samples_per_replicate": rows[0]["n"],
               "mean_mse": statistics.mean(row["mean_squared_error"] for row in rows),
               "biased_mse": statistics.mean(row["biased_squared_error"] for row in rows),
               "difference": delta, "standard_error": se, "ci95_normal": [delta - 1.96 * se, delta + 1.96 * se],
               "counterexample_seeds": [row["seed"] for row in rows if row["paired_difference"] <= 0],
               "method": "paired differences across seeds; normal approximation, 1.96 standard errors"}
    output.mkdir(parents=True, exist_ok=False)
    (output / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n")
    with (output / "per-seed.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    analyze(Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3]))
