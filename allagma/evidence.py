"""Bounded, read-only inspection of declared artifact references; no study code."""
from __future__ import annotations

import hashlib
from pathlib import Path
import stat

from .contracts import ROOT, validate, validate_record
from .files import AllagmaError, confined, parse_json, read_json


class InspectionLimit(AllagmaError):
    pass


def verify_evidence(study, record, *, max_files=10000, max_bytes=256 * 1024 * 1024):
    """Start from one record or a nonempty list, then follow declared JSON refs.

    Study-relative paths are never executed or imported. No mutation lock is
    created: callers should inspect a quiescent copy, not a live campaign.
    """
    if type(max_files) is not int or max_files < 1 or type(max_bytes) is not int or max_bytes < 1:
        raise AllagmaError("Inspection limits must be positive integers")
    study = Path(study).resolve()
    findings, seen = [], set()
    counts = {"files_read": 0, "bytes_read": 0, "checked_references": 0, "validated_records": 0}
    ref_schema = read_json(ROOT / "contracts/ClaimRecord.schema.json")["properties"]["supporting"]["items"]
    entry_hash = None

    def finding(code, origin, location, detail):
        findings.append({"code": code, "artifact": origin, "location": location,
                         "detail": str(detail).replace(str(study), "<study>")})

    def read(relative, *, expected=None, json_content=False):
        path = confined(study, relative)
        before = path.stat()
        if not stat.S_ISREG(before.st_mode):
            raise AllagmaError(f"Not a regular evidence file: {relative}")
        if counts["files_read"] >= max_files or before.st_size > max_bytes - counts["bytes_read"]:
            raise InspectionLimit("Inspection limit reached; rerun with an explicitly larger --max-files or --max-bytes after reviewing package size")
        checksum, chunks = hashlib.sha256(), []
        counts["files_read"] += 1
        with path.open("rb") as stream:
            remaining = before.st_size
            while remaining:
                chunk = stream.read(min(65536, remaining))
                if not chunk:
                    raise AllagmaError(f"Evidence changed while reading: {relative}")
                remaining -= len(chunk)
                counts["bytes_read"] += len(chunk)
                checksum.update(chunk)
                if json_content:
                    chunks.append(chunk)
        after = path.stat()
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise AllagmaError(f"Evidence changed while reading: {relative}")
        actual = checksum.hexdigest()
        if expected is not None and expected != actual:
            raise AllagmaError(f"Digest mismatch: {relative}; expected {expected}, found {actual}")
        value = parse_json(b"".join(chunks).decode("utf-8")) if json_content else None
        return actual, value

    try:
        entry_hash, root = read(record, json_content=True)
        roots = root if isinstance(root, list) else [root]
        if not roots or any(not isinstance(item, dict) or "record_type" not in item for item in roots):
            raise AllagmaError("Entry must be an Allagma record or a nonempty list of records")
        pending = [(root, record, "$")]
        while pending:
            value, origin, location = pending.pop()
            if isinstance(value, dict):
                if "record_type" in value:
                    try:
                        validate_record(value)
                        counts["validated_records"] += 1
                    except (AllagmaError, ValueError, TypeError, KeyError) as exc:
                        finding("invalid-record", origin, location, exc)
                # Generic transport manifests can contain path/hash metadata
                # without declaring an ArtifactRef. Record schemas catch
                # incomplete references in typed fields; untyped hash maps
                # remain outside this inspector's declared graph coverage.
                if {"path", "sha256", "media_type", "retention"} <= value.keys():
                    try:
                        validate(value, ref_schema)
                        identity = (value["path"], value["sha256"], value["media_type"])
                        if identity in seen:
                            continue
                        seen.add(identity)
                        is_json = value["media_type"] == "application/json"
                        _, child = read(value["path"], expected=value["sha256"], json_content=is_json)
                        counts["checked_references"] += 1
                        if is_json:
                            pending.append((child, value["path"], "$"))
                    except InspectionLimit:
                        raise
                    except (AllagmaError, OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
                        finding("invalid-reference", origin, location, exc)
                else:
                    pending.extend((child, origin, f"{location}.{key}") for key, child in reversed(list(value.items())))
            elif isinstance(value, list):
                pending.extend((child, origin, f"{location}[{index}]") for index, child in reversed(list(enumerate(value))))
    except InspectionLimit as exc:
        finding("inspection-limit", record, "$", exc)
    except (AllagmaError, OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        finding("invalid-entry", record, "$", exc)

    return {"verification_version": 1, "status": "fail" if findings else "pass",
            "entry": record, "entry_sha256": entry_hash, **counts, "findings": findings,
            "limits": {"max_files": max_files, "max_bytes": max_bytes},
            "coverage": "Record contracts and declared transitive artifact digests; application/json references are traversed.",
            "limitations": ["The entry digest is computed, not authenticated against an independent trusted source.",
                            "No campaign completeness, lock freshness, scientific correctness, recomputation or native-host qualification check.",
                            "Unreferenced files and undeclared hash maps are outside coverage. Inspect a quiescent copy; this is not an atomic snapshot.",
                            "No study code is executed and no study files or reviews are written."]}
