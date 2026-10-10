#!/usr/bin/env python3
"""New publication tables from frozen r07 outputs; never train or edit r07."""
from __future__ import annotations

import argparse
import itertools
import math
from pathlib import Path
import shutil
import statistics
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from allagma.files import file_hash, read_json, write_bytes, write_json

HERE = Path(__file__).resolve().parent
BASE = "694f13c1b923ff8e8a58442dd203baf613f76205"
SELECTED = {"summary.json": "analysis/summary.json", "seed-level.json": "analysis/seed-level.json",
            "measurements.json": "analysis/measurements.json", "protocol.md": "PROTOCOL.md",
            "main-figure.pdf": "analysis/main-figure.pdf", "license.txt": "LICENSE-AI-SCIENTIST"}


def retain(package):
    index_path = ROOT / "evals/research-v0.3/runs/r07/package/package-index.json"
    index = read_json(index_path)
    selected = {}
    for target, original in SELECTED.items():
        source = Path(package) / original
        metadata = index["files"][original]
        if file_hash(source) != metadata["sha256"] or source.stat().st_size != metadata["bytes"]:
            raise ValueError(f"Retained package input differs from the frozen index: {original}")
        write_bytes(HERE / "science" / target, source.read_bytes(), immutable=True)
        selected[target] = {"original_path": original, **metadata}
    write_json(HERE / "science/source-manifest.json", {
        "format": "allagma-publication-source-selection-v1", "source_run": "r07",
        "source_revision": BASE, "source_index_sha256": file_hash(index_path),
        "source_index_url": f"https://github.com/alohays/allagma/blob/{BASE}/evals/research-v0.3/runs/r07/package/package-index.json",
        "files": selected, "scope": "Exact selected outputs from a completed study; no new training or historical edits"}, immutable=True)


def derive():
    manifest = read_json(HERE / "science/source-manifest.json")
    for name, expected in manifest["files"].items():
        if file_hash(HERE / "science" / name) != expected["sha256"]:
            raise ValueError(f"Publication source changed: {name}")
    summary = read_json(HERE / "science/summary.json")
    states = read_json(HERE / "science/seed-level.json")
    measurements = read_json(HERE / "science/measurements.json")["runs"]
    lookup = {(r["dataset"], r["seed"], r["schedule"], r["updates"], r["variant"]): r for r in states}
    checked = 0

    def outcome(row, seed, policy, updates, family):
        state = lookup[row["dataset"], seed, policy, updates, row["variant"]]
        if family == "coverage":
            return state[row["metric"]]
        value = state["sw1"]
        if family == "effects":
            value -= lookup[row["dataset"], seed, policy, updates, "raw"]["sw1"]
        return value

    def same(a, b):
        if not math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-12):
            raise ValueError(f"Publication reanalysis disagrees: {a} != {b}")

    for family in ("effects", "absolute_sw1", "coverage"):
        for row in summary[family]:
            values = []
            for seed in row["seeds"] if "seeds" in row else sorted({s["seed"] for s in states if s["dataset"] == row["dataset"]}):
                def y(policy, updates):
                    return outcome(row, seed, policy, updates, family)
                contrast = row.get("contrast", "cell")
                if contrast == "cell":
                    value = y(row["schedule"], row["updates"])
                elif contrast == "schedule_cosine_minus_constant":
                    value = y("cosine", row["updates"]) - y("constant", row["updates"])
                elif contrast == "duration_10000_minus_5000":
                    value = y(row["schedule"], 10000) - y(row["schedule"], 5000)
                elif contrast == "interaction":
                    value = (y("cosine", 10000) - y("constant", 10000)) - (y("cosine", 5000) - y("constant", 5000))
                else:
                    raise ValueError("Unknown frozen contrast")
                values.append(value)
            if len(values) != row["n"]:
                raise ValueError("Independent seed count changed")
            for observed, expected in zip(values, row["values"], strict=True):
                same(observed, expected)
            mean, sd = statistics.mean(values), statistics.stdev(values)
            se = sd / math.sqrt(len(values))
            same(mean, row["mean"]); same(sd, row["sd"]); same(se, row["se"])
            # Frozen protocol: n=4, Student t 0.975 quantile with 3 df.
            same(mean - 3.182446305284263 * se, row["ci95"][0])
            same(mean + 3.182446305284263 * se, row["ci95"][1])
            p = sum(abs(statistics.mean(a*b for a,b in zip(values, signs))) >= abs(mean)-1e-14
                    for signs in itertools.product((-1, 1), repeat=len(values))) / 2 ** len(values)
            same(p, row["sign_flip_p"])
            for i, expected in enumerate(row["leave_one_out_means"]):
                same(statistics.mean(values[:i] + values[i+1:]), expected)
            checked += 1
    groups = {name: [r for r in summary["effects"] if r["contrast"] == contrast] for name, contrast in {
        "cells": "cell", "schedule": "schedule_cosine_minus_constant",
        "duration": "duration_10000_minus_5000", "interaction": "interaction"}.items()}
    for rows in groups.values():
        for row in rows:
            row["decay"] = "0.99" if row["variant"] == "ema099" else "0.999"
            row["negative_seeds"] = sum(value < 0 for value in row["values"])
    raw = [r for r in summary["absolute_sw1"] if r["contrast"] == "cell" and r["variant"] == "raw"]
    raw_lookup = {(r["dataset"],r["schedule"],r["updates"]):r["mean"] for r in raw}
    counts = {"cells": len(measurements), "states": len(states),
        "independent_seeds_per_dataset": summary["independent_seeds_per_dataset"],
        "trajectories": len({r["attempt_id"] for r in measurements}),
        "training_updates": sum(max(r["updates"] for r in measurements if r["attempt_id"] == aid)
                                for aid in {r["attempt_id"] for r in measurements}),
        "ema_cells": len(groups["cells"]), "negative_cell_means": sum(r["mean"] < 0 for r in groups["cells"]),
        "cell_intervals_below_zero": sum(r["ci95"][1] < 0 for r in groups["cells"]),
        "schedule_contrasts": len(groups["schedule"]), "positive_schedule_means": sum(r["mean"] > 0 for r in groups["schedule"]),
        "schedule_intervals_above_zero": sum(r["ci95"][0] > 0 for r in groups["schedule"]),
        "duration_contrasts": len(groups["duration"]), "duration_intervals_containing_zero": sum(r["ci95"][0] <= 0 <= r["ci95"][1] for r in groups["duration"]),
        "interactions": len(groups["interaction"]), "interaction_intervals_containing_zero": sum(r["ci95"][0] <= 0 <= r["ci95"][1] for r in groups["interaction"]),
        "raw_comparisons": len(raw_lookup)//2, "raw_cosine_better": sum(raw_lookup[d,"cosine",n] < raw_lookup[d,"constant",n] for d,n in {(d,n) for d,_,n in raw_lookup}),
        "gmm_states": sum(r["dataset"] == "gmm8" for r in states),
        "gmm_all_modes": sum(r["dataset"] == "gmm8" and r["covered_modes"] == 8 for r in states),
        "summaries_checked": checked}
    result = {"format": "ema-publication-values-v1", "counts": counts, **groups,
              "absolute_cells": [r for r in summary["absolute_sw1"] if r["contrast"] == "cell"],
              "source_manifest_sha256": file_hash(HERE / "science/source-manifest.json"),
              "scope": "Recalculated frozen summaries from retained seed-level measurements; no new training or metric extraction"}
    write_json(HERE / "science/publication-values.json", result)
    write_json(HERE / "science/recomputation.json", {"status": "pass", "summaries_checked": checked,
        "source_manifest_sha256": result["source_manifest_sha256"], "publication_values_sha256": file_hash(HERE / "science/publication-values.json"),
        "checks": ["source file hashes", "all per-seed contrasts", "means, SDs and SEs", "95% t intervals",
                   "exact sign-flip p-values", "leave-one-seed-out means"], "scope": result["scope"]})
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retained-package", type=Path)
    args = parser.parse_args()
    if args.retained_package:
        retain(args.retained_package)
    print(derive())
