#!/usr/bin/env python3
"""Retain the reader's toy-paper judgments in a new review/config revision.

This records supplied judgments; it neither conducts nor approves a review.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from allagma import papers, references
from allagma.files import AllagmaError, confined, file_hash, read_json, utcnow, write_json
from allagma.references import nonempty, require


def record_review(study, publication, configuration, revision, judgments):
    study = Path(study).resolve()
    require(all(references.ID.fullmatch(value) for value in (publication, revision)), "Use portable publication/review IDs")
    directory = confined(study, f"publications/{publication}")
    config = deepcopy(read_json(confined(directory, configuration)))
    fingerprint = papers.review_fingerprint(study, config)
    require(judgments.get("reviewed_content_sha256") == fingerprint,
            "Review input is stale; inspect the changed manuscript and record new judgments at its current fingerprint")
    require(nonempty(judgments.get("reviewer")), "Name the actual reviewer or explicitly describe a self-review")
    for kind in ("scientific", "humanizer"):
        judgment = judgments.get(kind, {})
        require(judgment.get("verdict") == "accept" and nonempty(judgment.get("scope"))
                and isinstance(judgment.get("observations"), list) and judgment["observations"]
                and all(map(nonempty, judgment["observations"])),
                f"Supply an actual accepted {kind} review with scope and observations; a check is not a review")
    destination = confined(directory, f"reviews/{revision}")
    require(not destination.exists(), "Preserve the old review; choose a new review revision")
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination / "input.json", judgments, immutable=True)
    old_reviews = deepcopy(config.get("review", {}))
    old_evidence = deepcopy(config["evidence"])
    for item in old_reviews.values():
        config["evidence"].pop(item.get("record"), None)
    config["review"] = {}
    for kind in ("scientific", "humanizer"):
        path = destination / f"{kind}.json"
        record = {"format": "allagma-paper-review-v1", "kind": kind,
                  "reviewer": judgments["reviewer"], "reviewed_at": utcnow(),
                  "reviewed_content_sha256": fingerprint,
                  **{key: judgments[kind][key] for key in ("verdict", "scope", "observations")}}
        if kind in old_reviews:
            record["supersedes"] = old_evidence[old_reviews[kind]["record"]]
        write_json(path, record, immutable=True)
        key = f"{kind}-review"
        config["evidence"][key] = {"path": path.relative_to(study).as_posix(), "sha256": file_hash(path)}
        config["review"][kind] = {"status": "complete", "scope": judgments[kind]["scope"], "record": key}
    papers.validate(study, config)
    write_json(destination / "paper.json", config, immutable=True)
    return {"status": "recorded", "configuration": (destination / "paper.json").relative_to(study).as_posix(),
            "reviewed_content_sha256": fingerprint,
            "scope": "Supplied reviewer judgments plus deterministic integrity checks; no independent peer review"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--publication", required=True)
    parser.add_argument("--config", default="paper.json", help="Path relative to the publication directory")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = record_review(args.study, args.publication, args.config, args.revision, read_json(args.input))
    except (AllagmaError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
