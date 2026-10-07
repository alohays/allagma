#!/usr/bin/env python3
"""Compare the bounded validator with an independent schema implementation."""
import argparse
from copy import deepcopy
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from allagma.contracts import validate
from allagma.files import AllagmaError, read_json, utcnow, write_json


def records(value):
    if isinstance(value, dict):
        if isinstance(value.get("record_type"), str):
            yield value
        for child in value.values():
            yield from records(child)
    elif isinstance(value, list):
        for child in value:
            yield from records(child)


def audit(evidence):
    import jsonschema
    formats = jsonschema.FormatChecker()
    if "date-time" not in formats.checkers:
        raise RuntimeError("Install tools/requirements-validation.txt for independent timestamp checks")
    schemas = {p.stem.removesuffix(".schema"): read_json(p) for p in (ROOT / "contracts").glob("*.schema.json")}
    fixtures = {}
    for path in sorted(evidence.rglob("*.json")):
        for record in records(read_json(path)):
            fixtures.setdefault(record["record_type"], record)
    if schemas.keys() - fixtures.keys():
        raise RuntimeError("Evidence does not exercise every record type")
    mismatches, count = [], 0

    def compare(kind, label, value, schema):
        nonlocal count
        expected = jsonschema.Draft202012Validator(schema, format_checker=formats).is_valid(value)
        try:
            validate(value, schema)
            actual = True
        except AllagmaError:
            actual = False
        count += 1
        if expected != actual:
            mismatches.append({"record": kind, "case": label, "independent_valid": expected, "builtin_valid": actual})

    for kind, schema in sorted(schemas.items()):
        fixture = fixtures[kind]
        compare(kind, "original", fixture, schema)
        compare(kind, "unknown property", {**fixture, "unexpected": True}, schema)
        for key in schema["required"]:
            changed = deepcopy(fixture)
            del changed[key]
            compare(kind, f"missing {key}", changed, schema)
        for key in schema["properties"]:
            for value in (None, False, True, -1, 0, 1, 1.5, "", "arbitrary", [], {}, [None]):
                compare(kind, f"{key}={value!r}", {**fixture, key: value}, schema)
    for value in ("2026-10-07T12:00:00Z", "2026-10-07T12:00:00.123+09:00",
                  "2026-10-07 12:00:00Z", "2026-10-07T12:00Z", "2026-W41-3T12:00:00Z",
                  "2026-10-07T12:00:00+01:60", "2026-02-30T12:00:00Z"):
        compare("date-time", value, value, {"type": "string", "format": "date-time"})
    return {"status": "pass" if not mismatches else "fail", "checked_at": utcnow(),
            "jsonschema_version": importlib.metadata.version("jsonschema"),
            "rfc3339_validator_version": importlib.metadata.version("rfc3339-validator"),
            "schemas": len(schemas), "cases": count, "mismatches": mismatches,
            "coverage": "All record types: valid instances, missing required fields, unknown properties, field-type/boundary mutations, independent RFC 3339 timestamps. Semantic cross-record constraints are covered separately."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.evidence)
    write_json(args.output, result, immutable=True)
    print(json.dumps(result, indent=2))
    raise SystemExit(result["status"] != "pass")
