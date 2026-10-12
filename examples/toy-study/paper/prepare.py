#!/usr/bin/env python3
"""Prepare an unreviewed publication of the completed default toy, offline."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

EXAMPLE = Path(__file__).resolve().parent
sys.path.insert(0, str(EXAMPLE.parents[2]))

from allagma import papers, references
from allagma.bundles import verify_study
from allagma.campaigns import audit_evidence
from allagma.files import AllagmaError, confined, file_hash, read_json, utcnow, write_json
from allagma.references import require


def prepare(study, revision, authors):
    study = Path(study).resolve()
    require(bool(references.ID.fullmatch(revision)), "Use a portable publication revision such as toy-paper-r1")
    destination = confined(study, f"publications/{revision}")
    require(not destination.exists(), "Preserve this publication; choose a new revision")
    papers.author_tex({"authors": authors})
    verify_study(study)
    campaign = study / "campaigns/toy-v1"
    protocol = read_json(campaign / "protocol.json")
    require(protocol == read_json(EXAMPLE.parent / "protocol.json"),
            "This example supports the default toy protocol only; write a separate paper for an adapted study")
    analysis = read_json(campaign / "analyses/a001/record.json")
    require(analysis["configuration"]["partial"] is False, "Complete the toy before preparing its paper")
    audit = read_json(campaign / "latest-audit.json")
    require(audit.get("verdict") == "pass" and not audit.get("findings"), "The toy needs a passing retained audit")
    claims = read_json(campaign / "analyses/a001/paper/claims.json")
    # Read-only traversal: retain the existing audit and never rerun a campaign.
    audit_evidence(study, [analysis, claims, audit])
    summary = read_json(campaign / "analyses/a001/outputs/summary.json")
    require(summary["replicates"] == 24 and summary["samples_per_replicate"] == 64
            and summary["bias"] == .25 and summary["counterexample_seeds"],
            "Expected the complete default toy results, including counterexamples")
    require([c["claim_id"] for c in claims] == ["C1", "C2", "C3"], "Expected the default toy claim ledger")

    config = read_json(EXAMPLE / "paper.example.json")
    prefix = destination.relative_to(study).as_posix()
    config.update(authors=authors, date=utcnow()[:10], references=f"{prefix}/references")
    config["sections"] = {name: f"{prefix}/sections/{name}.tex" for name in papers.SECTIONS}
    for source in config["evidence"].values():
        source["sha256"] = file_hash(confined(study, source["path"]))
    config["claims"][0]["status"] = claims[0]["status"]
    config["claims"][1]["status"] = "negative" if claims[1]["status"] == "contradicted" else "inconclusive"
    literature = read_json(EXAMPLE / "reference-map.json")
    references.validate_map(literature, require_review=True)
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copytree(EXAMPLE / "sections", destination / "sections")
    write_json(destination / "references/map.json", literature, immutable=True)
    references.refresh(destination / "references", require_review=True)
    write_json(destination / "paper.json", config, immutable=True)
    review_input = {"reviewer": "", "reviewed_content_sha256": papers.review_fingerprint(study, config),
                    "scientific": {"verdict": "pending", "scope": "", "observations": []},
                    "humanizer": {"verdict": "pending", "scope": "", "observations": []}}
    write_json(destination / "review-input.json", review_input, immutable=True)
    return {"status": "prepared-unreviewed", "configuration": f"{prefix}/paper.json",
            "reviewed_content_sha256": review_input["reviewed_content_sha256"],
            "scope": "Retained toy results only; scientific and prose review are still required"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--authors", type=Path, required=True, help="Explicit attribution JSON; no identity is inferred")
    args = parser.parse_args()
    try:
        result = prepare(args.study, args.revision, read_json(args.authors))
    except (AllagmaError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"{exc}\n")
    import json
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
