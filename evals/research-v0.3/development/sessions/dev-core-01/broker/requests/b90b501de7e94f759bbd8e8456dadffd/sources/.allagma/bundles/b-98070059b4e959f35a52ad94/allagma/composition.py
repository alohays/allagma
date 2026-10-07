"""Executable, bounded examples of replaceable context and reviewer contracts."""
from __future__ import annotations

import argparse
from pathlib import Path
from .contracts import validate_record
from .files import AllagmaError, canonical, read_json, verify_reference, write_json


def select_context(payload, method_id, *, strategy=None):
    strategy = strategy or method_id
    required = payload["required"]
    records = payload["records"]
    if not set(required) <= records.keys():
        raise AllagmaError("Required context records are missing")
    if strategy == "context/full-record":
        selected = list(records)
    elif strategy == "context/active-brief":
        selected = list(dict.fromkeys([*required, *payload.get("relevant", [])]))
        if not set(selected) <= records.keys():
            raise AllagmaError("Relevant context records are missing")
    else:
        raise AllagmaError(f"Unknown context strategy: {method_id}")
    content = {key: records[key] for key in selected}
    limitations = []
    if len(canonical(content).decode()) > payload.get("max_chars", 12000):
        limitations.append("Context exceeds the requested size; required evidence was retained.")
    return {"schema_version": "0.2", "record_type": "ContextRecord", "context_id": payload["context_id"],
            "method_id": method_id, "required": required, "selected": selected,
            "omitted": [key for key in records if key not in selected], "content": content,
            "limitations": limitations}


def review(payload, strict):
    study = Path(payload["study"])
    findings = []
    try:
        verify_reference(study, payload["material"])
        for claim in payload["claims"]:
            validate_record(claim)
            for evidence in [*claim["supporting"], *claim["contradicting"]]:
                verify_reference(study, evidence)
            if strict:
                for evidence in claim["dependencies"]:
                    verify_reference(study, evidence)
            if claim["status"] == "stale":
                findings.append(f"Stale claim: {claim['claim_id']}")
    except AllagmaError as exc:
        findings.append(str(exc))
    return {"verdict": "revise" if findings else "pass", "findings": findings,
            "coverage": "Schema, material and direct evidence digests" +
                        ("; dependency digests" if strict else "") +
                        ". No independent assessment of scientific validity."}


def context_main(method_id):
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    manifest = Path(sys.argv[0]).resolve().parent / "module.yaml"
    producer = read_json(manifest)["id"] if manifest.exists() else method_id
    value = select_context(read_json(args.input), producer, strategy=method_id)
    validate_record(value)
    write_json(args.output, value, immutable=True)


def review_main(strict=False):
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    write_json(args.output, review(read_json(args.input), strict), immutable=True)
