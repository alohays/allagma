"""Validate the deliberately small JSON Schema vocabulary used by this release.

Schemas are also standard draft-2020-12 documents for independent validators.
Unknown validation keywords fail closed instead of silently weakening a schema.
"""
from __future__ import annotations

from datetime import datetime
import math
from pathlib import Path
import re

from .files import AllagmaError, read_json

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = {"$schema", "$id", "$defs", "$ref", "title", "description", "type",
             "properties", "required", "additionalProperties", "items", "enum",
             "const", "minimum", "maximum", "minLength", "maxLength", "pattern",
             "minItems", "maxItems", "uniqueItems", "anyOf", "oneOf", "format"}


def _equal(a, b):
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_equal(a[key], b[key]) for key in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    return a == b


def _finite(value):
    return isinstance(value, int) or math.isfinite(value)


def validate(value, schema, path="$", *, root=None):
    root = schema if root is None else root
    if schema is True:
        return
    if schema is False:
        raise AllagmaError(f"{path}: prohibited value")
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise AllagmaError(f"Unsupported schema keywords: {sorted(unknown)}")
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            raise AllagmaError(f"Only internal schema references are supported: {ref}")
        validate(value, root["$defs"][ref.split("/")[-1]], path, root=root)
    for keyword in ("anyOf", "oneOf"):
        if keyword in schema:
            matches = 0
            for option in schema[keyword]:
                try:
                    validate(value, option, path, root=root)
                    matches += 1
                except AllagmaError:
                    pass
            if matches == 0 or (keyword == "oneOf" and matches != 1):
                raise AllagmaError(f"{path}: failed {keyword}")
    types = {"object": isinstance(value, dict), "array": isinstance(value, list),
             "string": isinstance(value, str), "null": value is None,
             "boolean": isinstance(value, bool),
             "integer": (isinstance(value, int) and not isinstance(value, bool)) or
                        (isinstance(value, float) and math.isfinite(value) and value.is_integer()),
             "number": isinstance(value, (int, float)) and not isinstance(value, bool)
                       and _finite(value)}
    if "type" in schema:
        allowed = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(types.get(t, False) for t in allowed):
            raise AllagmaError(f"{path}: expected {allowed}, got {type(value).__name__}")
    if "const" in schema and not _equal(value, schema["const"]):
        raise AllagmaError(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and not any(_equal(value, option) for option in schema["enum"]):
        raise AllagmaError(f"{path}: expected one of {schema['enum']}")
    if isinstance(value, dict):
        missing = set(schema.get("required", [])) - value.keys()
        if missing:
            raise AllagmaError(f"{path}: missing {sorted(missing)}")
        properties = schema.get("properties", {})
        for key, child in value.items():
            sub = properties.get(key, schema.get("additionalProperties", True))
            validate(child, sub, f"{path}.{key}", root=root)
    if isinstance(value, list):
        for i, child in enumerate(value):
            validate(child, schema.get("items", True), f"{path}[{i}]", root=root)
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", math.inf):
            raise AllagmaError(f"{path}: invalid array length")
        if schema.get("uniqueItems") and any(_equal(v, w) for i, v in enumerate(value) for w in value[:i]):
            raise AllagmaError(f"{path}: duplicate array items")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", math.inf):
            raise AllagmaError(f"{path}: invalid string length")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise AllagmaError(f"{path}: invalid string format")
        if schema.get("format") == "date-time":
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)", value):
                    raise ValueError("expected RFC 3339 timestamp")
                parsed = datetime.fromisoformat(value.upper().replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ValueError("timezone missing")
            except ValueError as exc:
                raise AllagmaError(f"{path}: expected timestamp with timezone") from exc
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not _finite(value) or value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            raise AllagmaError(f"{path}: number outside bounds")


def validate_record(record, root=ROOT):
    if not isinstance(record, dict):
        raise AllagmaError("Expected an Allagma record object")
    kind = record.get("record_type")
    if not isinstance(kind, str) or kind not in {"StudySpec", "ExperimentSpec", "RunRecord", "AnalysisRecord",
                    "ClaimRecord", "ReviewRecord", "ImprovementRecord", "ContextRecord"}:
        raise AllagmaError(f"Unknown record type: {kind}")
    validate(record, read_json(Path(root) / "contracts" / f"{kind}.schema.json"))
    if kind == "RunRecord":
        if (record["status"] == "running") != (record["ended_at"] is None):
            raise AllagmaError("Running attempts have no end timestamp; terminal attempts must have one")
        if record["status"] == "succeeded" and (record["error"] is not None or not record["outputs"]):
            raise AllagmaError("Successful attempts require outputs and no error")
        if record["status"] in ("failed", "interrupted") and record["error"] is None:
            raise AllagmaError("Failed/interrupted attempts require an error")
    if kind == "ClaimRecord" and record["status"] == "supported" and not record["supporting"]:
        raise AllagmaError("Supported claims require supporting evidence")
    return record
