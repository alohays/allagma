"""Targeted executable checks for the selected offline adapter handoffs."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from .catalog import Catalog
from .contracts import validate_record
from .files import AllagmaError, file_hash, read_json, reference, write_json, write_text


def qualify_examples(root, roles, output, *, reference_root=None):
    from .campaigns import _run_helper
    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    reference_root = Path(reference_root).resolve() if reference_root else output
    catalog = Catalog(root)
    results = []
    context = catalog.directory(roles["context"])
    case = read_json(context / "example.json")
    write_json(output / "context-input.json", case, immutable=True)
    command = [sys.executable, str(context / "select.py"), str(output / "context-input.json"), str(output / "context.json")]
    _run_helper(command, output, timeout=15)
    produced = validate_record(read_json(output / "context.json"), root)
    if produced["method_id"] != roles["context"] or not all(produced["content"].get(key) == case["records"][key] for key in case["required"]):
        raise AllagmaError("Context example lost a required field or producer identity")
    results.append({"module": roles["context"], "status": "pass", "coverage": "Required fields retained, producer identity and ContextRecord schema",
                    "helper_sha256": file_hash(context / "select.py"), "output": reference(reference_root, output / "context.json")})
    write_text(output / "material.md", "# Qualification fixture\n", immutable=True)
    write_json(output / "evidence.json", {"fixture": True}, immutable=True)
    claim = {"schema_version": "0.2", "record_type": "ClaimRecord", "claim_id": "fixture",
             "text": "Fixture exists", "supporting": [reference(output, output / "evidence.json")],
             "contradicting": [], "dependencies": [], "scope": "adapter contract fixture",
             "limitations": ["No scientific inference"], "status": "supported", "supersedes": None}
    payload = {"study": str(output), "material": reference(output, output / "material.md"), "claims": [claim]}
    write_json(output / "review-input.json", payload, immutable=True)
    reviewer = catalog.directory(roles["reviewer"]) / "review.py"
    _run_helper([sys.executable, str(reviewer), str(output / "review-input.json"), str(output / "review.json")], output, timeout=15)
    if read_json(output / "review.json").get("verdict") != "pass":
        raise AllagmaError("Reviewer failed the valid-evidence handoff")
    payload["claims"][0]["supporting"][0]["sha256"] = "0" * 64
    write_json(output / "stale-review-input.json", payload, immutable=True)
    _run_helper([sys.executable, str(reviewer), str(output / "stale-review-input.json"), str(output / "stale-review.json")], output, timeout=15)
    if read_json(output / "stale-review.json").get("verdict") not in ("revise", "blocked"):
        raise AllagmaError("Reviewer accepted stale evidence")
    results.append({"module": roles["reviewer"], "status": "pass", "coverage": "Valid evidence accepted; stale digest rejected",
                    "helper_sha256": file_hash(reviewer), "output": reference(reference_root, output / "review.json"),
                    "negative_case": reference(reference_root, output / "stale-review.json")})
    write_json(output / "results.json", results, immutable=True)
    return results
