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
from allagma.campaigns import _check_materials, audit_evidence
from allagma.contracts import validate_record
from allagma.files import (AllagmaError, canonical, confined, file_hash, read_json,
                          utcnow, verify_reference, write_json)
from allagma.references import require


def verify_retained_audit(study, campaign, analysis, claims):
    """Bind the selected claim ledger to its retained passing review, read-only."""
    audit = read_json(campaign / "latest-audit.json")
    require(isinstance(audit, dict) and audit.get("verdict") == "pass"
            and audit.get("findings") == [], "The toy needs a passing retained audit")
    source = audit.get("review")
    require(isinstance(source, dict) and isinstance(source.get("path"), str)
            and isinstance(source.get("sha256"), str), "The retained audit needs a review reference")
    review_path = verify_reference(study, source)
    selected = campaign / "analyses/a001"
    require(review_path.name == "record.json" and review_path.parent.parent == selected / "reviews",
            "Retained audit must cover the selected a001 analysis")
    receipt = read_json(confined(study, review_path.with_name("audit.json").relative_to(study).as_posix()))
    require(canonical(receipt) == canonical(audit), "Latest audit differs from its retained audit receipt")
    review = validate_record(read_json(review_path))
    require(review["record_type"] == "ReviewRecord" and review["verdict"] == "pass"
            and review["findings"] == [] and review["review_id"] == review_path.parent.name,
            "The retained review must record a passing audit")
    require(verify_reference(study, review["material"]) == selected / "paper/manuscript.md",
            "Retained audit must cover the selected a001 analysis")
    input_name = review_path.with_name("input.json").relative_to(study).as_posix()
    inputs = [item for item in review["trace"] if item["path"] == input_name]
    require(len(inputs) == 1, "The retained review needs its original audit input")
    reviewed = read_json(verify_reference(study, inputs[0]))
    require(isinstance(reviewed, dict) and reviewed.get("material") == review["material"],
            "Retained audit input does not identify the reviewed manuscript")
    require(canonical(reviewed.get("claims")) == canonical(claims),
            "Claims differ from the retained audit input; preserve the evidence and investigate")
    _check_materials(study, campaign)
    # Traversal verifies descendants; the comparison above binds the claim root.
    audit_evidence(study, [analysis, claims, review])


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
    analysis = validate_record(read_json(campaign / "analyses/a001/record.json"))
    require(analysis["configuration"]["partial"] is False, "Complete the toy before preparing its paper")
    claims = read_json(campaign / "analyses/a001/paper/claims.json")
    require(isinstance(claims, list) and claims, "Expected the default toy claim ledger")
    for claim in claims:
        validate_record(claim)
    verify_retained_audit(study, campaign, analysis, claims)
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
