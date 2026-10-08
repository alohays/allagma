"""Inspect actual toy evidence and adversarial references without repairing it."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from unittest.mock import patch

from allagma.cli import main
from allagma.demo import toy_workflow
from allagma.evidence import verify_evidence
from allagma.files import inventory, read_json, reference, write_json
from conformance.support import ROOT, WorkspaceTest


def claim(refs):
    return {"schema_version": "0.2", "record_type": "ClaimRecord", "claim_id": "C1",
            "text": "A fixture claim, not scientific qualification", "status": "inconclusive",
            "supporting": refs, "contradicting": [], "dependencies": [], "scope": "fixture",
            "limitations": ["Fixture only"], "supersedes": None}


class EvidenceVerification(WorkspaceTest):
    def test_complete_toy_references_are_checked_without_writes_or_execution(self):
        study = self.work / "study"
        expected = toy_workflow(ROOT, study)["audit"]["checked_references"]
        before = inventory(study)
        mtimes = {p: p.stat().st_mtime_ns for p in study.rglob("*")}
        with patch("subprocess.Popen", side_effect=AssertionError("execution")):
            result = verify_evidence(study, "campaigns/toy-v1/analyses/a001/paper/claims.json")
        self.assertEqual(result["status"], "pass", result["findings"])
        self.assertEqual(result["checked_references"], expected)
        self.assertEqual(expected, 521)
        self.assertEqual(inventory(study), before)
        self.assertEqual({p: p.stat().st_mtime_ns for p in study.rglob("*")}, mtimes)

    def test_nested_reference_lists_and_shared_references(self):
        write_json(self.work / "raw.json", {"measurement": 7})
        leaf = reference(self.work, self.work / "raw.json")
        write_json(self.work / "manifest.json", {"items": [leaf, leaf]})
        parent = reference(self.work, self.work / "manifest.json")
        write_json(self.work / "claims.json", [claim([parent]), claim([parent])])
        result = verify_evidence(self.work, "claims.json")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["checked_references"], 2)
        self.assertEqual(result["files_read"], 3)
        self.assertEqual(result["validated_records"], 2)

    def test_missing_changed_traversal_and_symlink_failures_are_collected(self):
        write_json(self.work / "raw.json", {"measurement": 7})
        original = reference(self.work, self.work / "raw.json")
        write_json(self.work / "raw.json", {"measurement": 9})
        (self.work / "alias.json").symlink_to(self.work / "raw.json")
        refs = [dict(original, path=path) for path in ("missing.json", "raw.json", "../outside.json", "alias.json")]
        write_json(self.work / "claims.json", claim(refs))
        result = verify_evidence(self.work, "claims.json")
        self.assertEqual(result["status"], "fail")
        self.assertEqual(len(result["findings"]), 4)
        self.assertEqual(result["checked_references"], 0)
        self.assertEqual([item["location"] for item in result["findings"]], [f"$.supporting[{i}]" for i in range(4)])

    def test_invalid_json_records_and_empty_roots_fail_closed(self):
        for index, text in enumerate(("[]", "{}", '{"record_type":"Unknown"}', '{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}')):
            path = self.work / f"bad-{index}.json"
            path.write_text(text)
            self.assertEqual(verify_evidence(self.work, path.name)["status"], "fail")
        write_json(self.work / "nested.json", {"record_type": "Unknown"})
        write_json(self.work / "claim.json", claim([reference(self.work, self.work / "nested.json")]))
        result = verify_evidence(self.work, "claim.json")
        self.assertEqual(result["findings"][0]["artifact"], "nested.json")

    def test_explicit_limits_fail_without_reading_past_the_ceiling(self):
        write_json(self.work / "raw.json", {"value": 42})
        write_json(self.work / "claim.json", claim([reference(self.work, self.work / "raw.json")]))
        for options in ({"max_files": 1}, {"max_bytes": 1}):
            result = verify_evidence(self.work, "claim.json", **options)
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["findings"][0]["code"], "inspection-limit")
            self.assertLessEqual(result["files_read"], options.get("max_files", 10000))
            self.assertLessEqual(result["bytes_read"], options.get("max_bytes", 256 * 1024 * 1024))

    def test_cli_failure_is_json_and_does_not_create_a_missing_study(self):
        output = StringIO()
        with redirect_stdout(output):
            code = main(["verify-evidence", "--study", str(self.work / "absent"), "--record", "claim.json"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["status"], "fail")
        self.assertFalse((self.work / "absent").exists())
        with redirect_stderr(StringIO()):
            self.assertEqual(main(["verify-evidence", "--study", str(self.work), "--record", "claim.json", "--max-files", "0"]), 2)
