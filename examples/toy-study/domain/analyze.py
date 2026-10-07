"""Study-owned paired MSE analysis; all numbers come from raw observations."""
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys


def figure(rows, average):
    """Deterministic SVG primitives keep this small example dependency-free."""
    differences = [row["paired_difference"] for row in rows]
    lower, upper = min(0, min(differences)) - 0.025, max(0, max(differences)) + 0.025
    left, right, top, bottom = 110, 790, 90, 570
    x = lambda value: left + (value - lower) / (upper - lower) * (right - left)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 640" role="img" aria-labelledby="title description">',
             '<title id="title">Paired squared-error differences by confirmation seed</title>',
             '<desc id="description">Positive differences favor the sample mean. The dashed line is the across-seed mean; the solid vertical line is zero.</desc>',
             '<rect width="840" height="640" fill="white"/>',
             '<g font-family="sans-serif" fill="#172b3a">',
             '<text x="30" y="32" font-size="20">Paired squared-error differences</text>',
             '<text x="30" y="56" font-size="13">One dot per confirmation seed; dashed line: mean difference</text>',
             '<text x="30" y="80" font-size="12">Seed</text>']
    for tick in range(6):
        value = lower + (upper - lower) * tick / 5
        position = x(value)
        parts += [f'<line x1="{position:.3f}" x2="{position:.3f}" y1="{top}" y2="{bottom}" stroke="#e2e8ee"/>',
                  f'<text x="{position:.3f}" y="596" text-anchor="middle" font-size="12">{value:.3f}</text>']
    parts += [f'<line x1="{x(0):.3f}" x2="{x(0):.3f}" y1="{top}" y2="{bottom}" stroke="#526777"/>',
              f'<line x1="{x(average):.3f}" x2="{x(average):.3f}" y1="{top}" y2="{bottom}" stroke="#172b3a" stroke-dasharray="5 4"/>']
    for index, row in enumerate(rows):
        y = top + 10 + index * (bottom - top - 20) / max(1, len(rows) - 1)
        value = row["paired_difference"]
        color = "#0072b2" if value > 0 else "#c45100"
        parts += [f'<text x="85" y="{y + 4:.3f}" text-anchor="end" font-size="12">{row["seed"]}</text>',
                  f'<circle data-seed="{row["seed"]}" data-difference="{value:.17g}" cx="{x(value):.3f}" cy="{y:.3f}" r="4" fill="{color}"/>']
    parts += ['<text x="450" y="625" text-anchor="middle" font-size="13">Squared error: biased estimator − sample mean</text>', '</g></svg>']
    return "\n".join(parts) + "\n"


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
    sensitivity = [{"omitted_seed": row["seed"], "mean_difference": statistics.mean(
        other["paired_difference"] for other in rows if other["seed"] != row["seed"])} for row in rows]
    summary = {"replicates": len(rows), "samples_per_replicate": rows[0]["n"],
               "mean_mse": statistics.mean(row["mean_squared_error"] for row in rows),
               "biased_mse": statistics.mean(row["biased_squared_error"] for row in rows),
               "difference": delta, "standard_error": se, "ci95_normal": [delta - 1.96 * se, delta + 1.96 * se],
               "counterexample_seeds": [row["seed"] for row in rows if row["paired_difference"] <= 0],
               "leave_one_seed_out": {"replicates": len(sensitivity),
                                      "minimum_difference": min(row["mean_difference"] for row in sensitivity),
                                      "maximum_difference": max(row["mean_difference"] for row in sensitivity),
                                      "positive_count": sum(row["mean_difference"] > 0 for row in sensitivity)},
               "method": "paired differences across seeds; normal approximation, 1.96 standard errors"}
    output.mkdir(parents=True, exist_ok=False)
    (output / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2, allow_nan=False) + "\n")
    with (output / "per-seed.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (output / "leave-one-seed-out.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["omitted_seed", "mean_difference"])
        writer.writeheader()
        writer.writerows(sensitivity)
    (output / "paired-differences.svg").write_text(figure(rows, delta))


if __name__ == "__main__":
    analyze(Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()), Path(sys.argv[3]))
