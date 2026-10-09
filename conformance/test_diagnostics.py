"""Prerequisite reports must not launch hosts or mutate the inspected study."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
import subprocess
import sys
from unittest.mock import patch

from allagma import bundles
from allagma.cli import main
from allagma.diagnostics import diagnose
from allagma.files import inventory, read_json, write_json
from conformance.support import ROOT, WorkspaceTest


class Diagnostics(WorkspaceTest):
    def test_offline_needs_neither_native_tools_nor_subprocesses(self):
        with patch("shutil.which", side_effect=AssertionError("host lookup")), \
             patch("subprocess.Popen", side_effect=AssertionError("execution")):
            result = diagnose(ROOT)
        self.assertEqual(result["status"], "pass")
        self.assertEqual({item["id"] for item in result["checks"]}, {"python", "platform", "catalog", "toy-resources"})

    def test_incomplete_source_reports_independent_failures_and_remedies(self):
        source = self.source_copy()
        (source / "methods/allagma-context-active-brief/select.py").unlink()
        (source / "examples/toy-study/domain/runner.py").unlink()
        result = diagnose(source)
        failed = [item for item in result["checks"] if item["status"] == "fail"]
        self.assertEqual({item["id"] for item in failed}, {"catalog", "toy-resources"})
        self.assertTrue(all(item["remedy"] for item in failed))
        self.assertNotIn(str(self.work), str(result))

    def test_missing_source_and_study_are_not_created(self):
        result = diagnose(self.work / "absent-source", study=self.work / "absent-study")
        self.assertEqual(result["status"], "fail")
        self.assertEqual(list(self.work.iterdir()), [])

    def test_study_checks_preserve_bytes_and_mtimes_even_on_failure(self):
        study = self.work / "study"
        bundles.initialize(ROOT, study)
        self.assertEqual(diagnose(ROOT, study=study)["status"], "pass")
        write_json(study / "overrides/settings.json", {"language": "French"})
        (study / "ALLAGMA.md").write_text("user-owned edit\n")
        before = inventory(study)
        mtimes = {p: p.stat().st_mtime_ns for p in study.rglob("*")}
        result = diagnose(ROOT, study=study)
        self.assertEqual({item["id"] for item in result["checks"] if item["status"] == "fail"}, {"study-lock", "generated-files"})
        self.assertEqual(inventory(study), before)
        self.assertEqual({p: p.stat().st_mtime_ns for p in study.rglob("*")}, mtimes)

    def test_native_inspection_never_runs_supplied_executable(self):
        program = self.work / "codex"
        marker = self.work / "executed"
        program.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
        program.chmod(0o755)
        with patch("platform.system", return_value="Linux"), patch("shutil.which", return_value=None):
            result = diagnose(ROOT, scope="native", codex=program)
        checks = {item["id"]: item for item in result["checks"]}
        self.assertEqual(checks["native-executable"]["status"], "pass")
        self.assertEqual(checks["native-platform"]["status"], "fail")
        self.assertEqual(checks["native-sandbox"]["status"], "fail")
        self.assertFalse(marker.exists())

    def test_malformed_documents_return_independent_cli_findings_without_writes(self):
        source = self.source_copy()
        study = self.work / "study"
        bundles.initialize(ROOT, study)
        module = next(iter(read_json(source / "registry.json")["modules"].values()))
        write_json(source / module / "module.yaml", [])
        write_json(study / ".allagma/lock.yaml", [])
        write_json(study / ".allagma/ownership.json", {"files": []})
        before = inventory(self.work)
        mtimes = {p: p.stat().st_mtime_ns for p in self.work.rglob("*")}
        process = subprocess.run(
            [sys.executable, "-B", "-m", "allagma", "doctor", "--source", str(source), "--study", str(study)],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(process.returncode, 1, process.stderr)
        self.assertEqual(process.stderr, "")
        report = json.loads(process.stdout)
        checks = {item["id"]: item for item in report["checks"]}
        self.assertEqual(report["status"], "fail")
        self.assertEqual({key for key, item in checks.items() if item["status"] == "fail"},
                         {"catalog", "study-lock", "generated-files"})
        self.assertEqual(checks["toy-resources"]["status"], "pass")
        self.assertTrue(all(item["remedy"] for item in checks.values() if item["status"] == "fail"))
        self.assertNotIn(str(self.work), process.stdout)
        self.assertEqual(inventory(self.work), before)
        self.assertEqual({p: p.stat().st_mtime_ns for p in self.work.rglob("*")}, mtimes)

    def test_excessively_nested_json_does_not_abort_other_checks(self):
        study = self.work / "study"
        bundles.initialize(ROOT, study)
        (study / ".allagma/lock.yaml").write_text("[" * 2000 + "0" + "]" * 2000)
        with patch("subprocess.Popen", side_effect=AssertionError("execution")):
            report = diagnose(ROOT, study=study)
        checks = {item["id"]: item for item in report["checks"]}
        self.assertEqual(checks["study-lock"]["status"], "fail")
        self.assertEqual(checks["generated-files"]["status"], "pass")

    def test_cli_reports_json_and_nonzero_for_failed_prerequisites(self):
        output = StringIO()
        with redirect_stdout(output):
            code = main(["doctor", "--source", str(self.work / "missing")])
        self.assertEqual(code, 1)
        self.assertIn('"status": "fail"', output.getvalue())
        with redirect_stderr(StringIO()):
            self.assertEqual(main(["doctor", "--codex", "missing"]), 2)
