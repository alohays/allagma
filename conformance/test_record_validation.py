"""Public record admission must reject bad evidence without rewriting it."""
import copy
import json
import subprocess
import sys

from allagma.campaigns import run_campaign, start_campaign
from allagma.composition import select_context
from allagma.contracts import validate_record
from allagma.demo import create_toy
from allagma.files import AllagmaError, read_json, write_json
from conformance.support import ROOT, WorkspaceTest


class RecordValidation(WorkspaceTest):
    def cli(self, path):
        return subprocess.run(
            [sys.executable, "-B", "-m", "allagma", "validate-record", str(path)],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )

    def test_record_api_rejects_non_objects_and_invalid_type_identifiers(self):
        for value in (None, False, 7, "RunRecord", [], ["RunRecord"], {},
                      {"record_type": []}, {"record_type": {}},
                      {"record_type": None}, {"record_type": "Unknown"}):
            with self.subTest(value=value), self.assertRaises(AllagmaError):
                validate_record(value)

    def test_cli_rejects_malformed_records_without_tracebacks_or_writes(self):
        cases = (b"null", b"false", b"42", b'"RunRecord"', b"[]", b"{}",
                 b'{"record_type":[]}', b'{"record_type":{}}',
                 b'{"record_type":"Unknown"}', b'{"record_type":',
                 b'{"record_type":"ContextRecord","record_type":"ContextRecord"}',
                 b'{"value":NaN}', b'{"value":1e999}', b"\xff")
        path = self.work / "record with spaces.json"
        for data in cases:
            with self.subTest(data=data):
                path.write_bytes(data)
                before = path.stat().st_mtime_ns
                result = self.cli(path)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("allagma: "), result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(path.read_bytes(), data)
                self.assertEqual(path.stat().st_mtime_ns, before)
                self.assertEqual(list(self.work.iterdir()), [path])

    def test_cli_accepts_a_valid_record_and_preserves_missing_paths(self):
        fixture = read_json(ROOT / "methods/allagma-context-active-brief/example.json")
        path = self.work / "context.json"
        write_json(path, select_context(fixture, "context/active-brief"))
        before = path.read_bytes(), path.stat().st_mtime_ns
        result = self.cli(path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {"record_type": "ContextRecord", "status": "pass"})
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)
        result = self.cli(self.work / "absent" / "record.json")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.work / "absent").exists())

    def test_attempt_outcomes_require_consistent_timestamps_outputs_and_errors(self):
        study = create_toy(ROOT, self.work / "study")
        start_campaign(study, "record-contract")
        run_campaign(study, "record-contract", stop_after=1)
        original = read_json(next(study.glob("campaigns/*/runs/*/attempts/*/record.json")))
        self.assertEqual(original["status"], "succeeded")
        failure = {"kind": "fixture", "message": "Deliberate contract fixture"}
        for status in ("running", "succeeded", "failed", "interrupted"):
            valid = copy.deepcopy(original)
            valid.update(status=status, ended_at=None if status == "running" else original["ended_at"],
                         outputs=original["outputs"] if status == "succeeded" else [],
                         error=failure if status in ("failed", "interrupted") else None)
            with self.subTest(status=status):
                validate_record(valid)
                invalid = dict(valid, ended_at=original["ended_at"] if status == "running" else None)
                with self.assertRaisesRegex(AllagmaError, "timestamp"):
                    validate_record(invalid)
                if status in ("failed", "interrupted"):
                    with self.assertRaisesRegex(AllagmaError, "require an error"):
                        validate_record(dict(valid, error=None))
        for patch in ({"outputs": []}, {"error": failure}):
            with self.subTest(patch=patch), self.assertRaisesRegex(AllagmaError, "Successful attempts"):
                validate_record({**original, **patch})

    def test_supported_claim_cannot_omit_supporting_evidence(self):
        claim = {"schema_version": "0.2", "record_type": "ClaimRecord", "claim_id": "C1",
                 "text": "Fixture claim", "status": "inconclusive", "supporting": [],
                 "contradicting": [], "dependencies": [], "scope": "contract fixture",
                 "limitations": ["No scientific result"], "supersedes": None}
        validate_record(claim)
        claim["status"] = "supported"
        with self.assertRaisesRegex(AllagmaError, "require supporting evidence"):
            validate_record(claim)
        claim["supporting"] = [{"path": "raw.json", "sha256": "0" * 64,
                                "media_type": "application/json", "retention": "retain-with-study"}]
        validate_record(claim)  # Contract admission; verify-evidence checks the actual bytes.
