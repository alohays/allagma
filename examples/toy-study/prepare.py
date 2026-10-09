#!/usr/bin/env python3
"""Prepare a prospective toy variant; scientific settings belong to this example."""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from allagma.bundles import default_intent, initialize
from allagma.files import AllagmaError, canonical, inventory, read_json, write_json


def prepare(destination, *, study_id="adapted-bias-study", bias=0.5, source=ROOT):
    """Only accept a new directory; never copy campaigns or frozen evidence."""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", study_id) or len(study_id) > 64:
        raise AllagmaError("Study ID must be a lowercase hyphenated name of at most 64 characters")
    if type(bias) not in (int, float) or not math.isfinite(bias) or abs(bias) > 1:
        raise AllagmaError("Bias must be finite and between -1 and 1 for this bounded example")
    destination, source = Path(destination).absolute(), Path(source).resolve()
    if destination.exists() or destination.is_symlink():
        raise AllagmaError("Preparation requires a new destination; existing files are never replaced")
    example = source / "examples/toy-study"
    protocol = read_json(example / "protocol.json")
    brief = read_json(example / "brief.json")
    originals = {name: value for name, value in inventory(example).items()
                 if name in {"protocol.json", "brief.json", "evidence-map.json"} or name.startswith("domain/")}
    protocol["revision"] = f"{study_id}-v1"
    protocol["hypothesis"] = f"Adding {bias} to the sample mean changes expected squared error by {bias ** 2} for zero-mean Rademacher data."
    for run in protocol["runs"]:
        run["input"]["bias"] = bias
    protocol["code"].append("adaptation.json")
    brief["study_id"] = study_id
    brief["question"] = f"How does adding {bias} change squared error when estimating a synthetic zero mean?"
    brief["motivation"] = "Prospectively adapt the existing known-answer toy; inspect the protocol before execution."
    brief["success_criteria"][-1] = "Any failures and retries remain traceable; preparation executes no attempts"
    # Input validation happens before creation. An unexpected filesystem/setup
    # failure leaves its partial destination for inspection, never erases it.
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copytree(example / "domain", destination / "domain", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(example / "evidence-map.json", destination / "evidence-map.json")
    shutil.copy2(source / "LICENSE", destination / "SOURCE-LICENSE.txt")
    write_json(destination / "brief.json", brief, immutable=True)
    write_json(destination / "protocol.json", protocol, immutable=True)
    write_json(destination / "adaptation.json", {
        "source": "Allagma examples/toy-study", "license": "MIT", "source_files": originals,
        "change": {"additive_bias": bias, "protocol_revision": protocol["revision"]},
        "preserved": "64 samples per seed, two known-answer pilots, 24 confirmation seeds, paired analysis and finite resource ceiling",
        "scope": "A new prospective workflow demonstration; no copied attempts, results or scientific novelty claim",
    }, immutable=True)
    intent = default_intent(study_id)
    intent["hosts"] = ["generic"]
    intent["request"] = {"budget": {"max_attempts": 28, "max_seconds": 60.0,
                                   "money_usd": 0.0, "per_attempt_seconds": 5.0}}
    lock = initialize(source, destination, intent=intent)
    return {"status": "prepared", "study_id": study_id, "bias": bias,
            "lock_id": lock["lock_id"], "protocol_revision": protocol["revision"],
            "next": "Inspect brief.json, protocol.json and adaptation.json, then start a new campaign.",
            "executed_attempts": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--id", default="adapted-bias-study")
    parser.add_argument("--bias", type=float, default=0.5)
    args = parser.parse_args()
    try:
        print(canonical(prepare(args.destination, study_id=args.id, bias=args.bias)).decode(), end="")
        return 0
    except (AllagmaError, OSError, ValueError) as exc:
        print(f"toy preparation: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
