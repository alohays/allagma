#!/usr/bin/env python3
"""Independently audit the complete toy using exact rational arithmetic.

No Allagma helper or study runner/evaluator/analyzer/writer is imported. This
checks the declared toy only; it is not a general scientific-validity checker.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def audit(study, campaign="toy-v1"):
    study = Path(study).resolve()
    directory = study / "campaigns" / campaign
    analysis = directory / "analyses/a001"
    seen = set()

    def verify(ref):
        path = study / ref["path"]
        require(path.resolve().is_relative_to(study), "Reference escapes study")
        require(not path.is_symlink(), "Evidence is a symlink")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == ref["sha256"], f"Digest changed: {ref['path']}")
        seen.add((ref["path"], ref["sha256"]))
        return path

    protocol = read(directory / "protocol.json")
    planned = {run["id"]: run for run in protocol["runs"]}
    records = {path.relative_to(study).as_posix(): read(path)
               for path in directory.glob("runs/*/attempts/*/record.json")}
    counts = Counter(record["status"] for record in records.values())
    require(counts == {"succeeded": 26, "failed": 1, "interrupted": 1}, "Unexpected complete-toy attempt counts")
    require({r["run_id"] for r in records.values() if r["status"] == "succeeded"} == planned.keys(), "Missing successful planned run")
    manifest = read(analysis / "raw-manifest.json")
    require({ref["path"] for ref in manifest["runs"]} == records.keys(), "Attempt omitted from analysis manifest")
    for ref in manifest["runs"]:
        verify(ref)
    eligible = {}
    for name, record in records.items():
        require(record["run_id"] in planned, "Run absent from frozen plan")
        plan = planned[record["run_id"]]
        require(record["split"] == plan["split"], "Run split changed")
        for ref in record["inputs"] + record["outputs"]:
            verify(ref)
        if record["status"] == "succeeded":
            inputs = read(study / name.replace("record.json", "input.json"))
            require(inputs == plan["input"] and "fault" not in inputs, "Successful science used changed/fault inputs")
            require(record["run_id"] not in eligible, "Duplicate successful run")
            raw_ref = next(ref for ref in record["outputs"] if ref["path"].endswith("/raw.json"))
            if plan["split"] == "confirmation":
                eligible[record["run_id"]] = raw_ref
    require({ref["path"] for ref in manifest["raw"]} == {ref["path"] for ref in eligible.values()}, "Raw manifest contains ineligible data")
    require(len(manifest["raw"]) == 24, "Incomplete confirmation plan")
    require(len(manifest["exclusions"]) == 4, "Pilots/faults were not excluded")
    rows = {}
    for ref in manifest["raw"]:
        raw = read(verify(ref))
        require(raw["n"] == 64 and len(raw["samples"]) == 64, "Incorrect sample count")
        require(raw["control"] == "random" and set(raw["samples"]) <= {-1, 1}, "Not Rademacher confirmation data")
        require(raw["target"] == 0 and Q(str(raw["bias"])) == Q(1, 4), "Toy estimand changed")
        mean = sum(Q(int(x)) for x in raw["samples"]) / 64
        plain, biased = mean ** 2, (mean + Q(1, 4)) ** 2
        require(float(mean) == raw["mean_estimate"] and float(mean + Q(1, 4)) == raw["biased_estimate"], "Estimator arithmetic differs")
        rows[raw["seed"]] = (mean, plain, biased, biased - plain)
    require(set(rows) == set(range(100, 124)), "Confirmation seeds changed or duplicated")
    count = len(rows)
    plain = sum(row[1] for row in rows.values()) / count
    biased = sum(row[2] for row in rows.values()) / count
    difference = biased - plain
    variance = sum((row[3] - difference) ** 2 for row in rows.values()) / (count - 1)
    se = math.sqrt(float(variance / count))
    interval = [float(difference) - 1.96 * se, float(difference) + 1.96 * se]
    counterexamples = sorted(seed for seed, row in rows.items() if row[3] <= 0)
    expected = {"mean_mse": float(plain), "biased_mse": float(biased), "difference": float(difference), "standard_error": se}
    summary = read(analysis / "outputs/summary.json")
    for key, value in expected.items():
        require(math.isclose(value, summary[key], rel_tol=1e-13, abs_tol=1e-15), f"Independent arithmetic differs: {key}")
    require(summary["counterexample_seeds"] == counterexamples, "Counterexamples differ")
    require(all(math.isclose(a, b, rel_tol=1e-13, abs_tol=1e-15) for a, b in zip(summary["ci95_normal"], interval)), "Interval differs")
    with (analysis / "outputs/per-seed.csv").open() as stream:
        table = list(csv.DictReader(stream))
    require(len(table) == count, "Per-seed table has wrong row count")
    for row in table:
        for key, expected_value in zip(("mean_estimate", "mean_squared_error", "biased_squared_error", "paired_difference"), rows[int(row["seed"])]):
            require(Q(row[key]) == expected_value, f"Per-seed table differs: {row['seed']} {key}")
    claims = read(analysis / "paper/claims.json")
    require([claim["status"] for claim in claims] == ["supported", "contradicted"], "Claim classifications differ")
    require(interval[0] > 0 and counterexamples, "Claim directions lack numerical evidence")
    paper = (analysis / "paper/manuscript.md").read_text()
    require(all(f"{value:.8f}" in paper for value in (float(plain), float(biased), float(difference), *interval)), "Manuscript numbers differ")
    # Independently enumerate the binomial distribution of the count of +1s.
    exact_plain = sum(Q(math.comb(64, k), 2 ** 64) * Q(2*k - 64, 64) ** 2 for k in range(65))
    exact_biased = sum(Q(math.comb(64, k), 2 ** 64) * (Q(2*k - 64, 64) + Q(1, 4)) ** 2 for k in range(65))
    require(exact_plain == Q(1, 64) and exact_biased - exact_plain == Q(1, 16), "Known-answer expectation differs")
    return {"status": "pass", "checked_at": datetime.now(timezone.utc).isoformat(),
            "attempts": dict(counts), "confirmation_replicates": count, "distinct_direct_references": len(seen),
            "exact_observed": {"mean_mse": str(plain), "biased_mse": str(biased), "difference": str(difference)},
            "scientific_summary": {**expected, "ci95_normal": interval, "counterexample_seeds": counterexamples},
            "enumerated_population_mse": {"mean": str(exact_plain), "biased": str(exact_biased)},
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "coverage": "Separate rational arithmetic and binomial enumeration; complete-toy eligibility, reference digests, CSV, claims and manuscript numbers. No Allagma or study helper imports."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--campaign", default="toy-v1")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.study, args.campaign)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result, indent=2))
