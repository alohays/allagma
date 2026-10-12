"""Prerequisite reports must not launch hosts or mutate the inspected study."""
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
from unittest.mock import patch

from allagma import bundles
from allagma.catalog import Catalog
from allagma.demo import create_toy
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

    def run_helper(self, helper, *arguments):
        process = subprocess.run([sys.executable, "-B", str(helper), "doctor", *arguments],
            cwd=self.work, env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
            capture_output=True, text=True, timeout=20)
        self.assertEqual(process.stderr, "")
        return process, json.loads(process.stdout)

    def assert_read_only_helper(self, study, helper, *arguments):
        before = inventory(study)
        mtimes = {p: p.stat().st_mtime_ns for p in study.rglob("*")}
        result = self.run_helper(helper, "--study", str(study), *arguments)
        self.assertEqual(inventory(study), before)
        self.assertEqual({p: p.stat().st_mtime_ns for p in study.rglob("*")}, mtimes)
        return result

    def test_exported_helper_outside_checkout_scopes_toy_without_writes_or_host_execution(self):
        source = self.source_copy("source with spaces")
        study = create_toy(source, self.work / "study with spaces")
        lock = bundles.verify_study(study)
        bundle = bundles.bundle_path(study, lock)
        helper = bundle / "tools/allagma.py"
        process, report = self.assert_read_only_helper(study, source / "tools/allagma.py",
                                                      "--source", str(source))
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertEqual(report["distribution"], "source-checkout")
        self.assertEqual(report["excluded_checks"], [])
        self.assertIn("toy-resources", {c["id"] for c in report["checks"]})
        source.rename(self.work / "unavailable original checkout")
        self.assertFalse((bundle / "examples/toy-study").exists())
        process, report = self.assert_read_only_helper(study, helper)
        self.assertEqual(process.returncode, 0, process.stdout)
        self.assertEqual(report["distribution"], "standalone-bundle")
        self.assertEqual({c["id"] for c in report["checks"]},
                         {"python", "platform", "catalog", "study-lock", "generated-files"})
        self.assertTrue(all(c["status"] == "pass" for c in report["checks"]))
        self.assertEqual([c["id"] for c in report["excluded_checks"]], ["toy-resources"])
        self.assertIn("outside standalone-bundle scope", report["excluded_checks"][0]["reason"])
        program = self.work / "codex sentinel"
        marker = self.work / "unexpected execution"
        program.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
        program.chmod(0o755)
        process, native = self.assert_read_only_helper(study, helper, "--scope", "native", "--codex", str(program))
        self.assertEqual(native["distribution"], "standalone-bundle")
        self.assertEqual(next(c for c in native["checks"] if c["id"] == "native-executable")["status"], "pass")
        self.assertFalse(marker.exists())
        self.assertNotIn(str(self.work), process.stdout)

    def test_disposable_bundle_faults_remain_independent_and_read_only(self):
        original = create_toy(ROOT, self.work / "original study")
        lock = bundles.verify_study(original)
        for fault, expected in (("catalog", {"catalog", "study-lock"}),
                                ("registry", {"catalog", "study-lock"}),
                                ("lock", {"study-lock"}),
                                ("generated", {"generated-files"})):
            with self.subTest(fault=fault):
                # Corrupt only a disposable copy, never an existing retained bundle.
                study = self.work / fault
                shutil.copytree(original, study)
                bundle = bundles.bundle_path(study, lock)
                helper = bundle / "tools/allagma.py"
                if fault == "catalog":
                    catalog = Catalog(bundle)
                    module = next(catalog.module(key) for key in catalog.registry["modules"]
                                  if catalog.module(key)["resources"])
                    (catalog.directory(module["id"]) / module["resources"][0]).unlink()
                elif fault == "registry":
                    (bundle / "registry.json").write_text("[]")
                elif fault == "lock":
                    (study / ".allagma/lock.yaml").write_text("[]")
                else:
                    (study / "ALLAGMA.md").write_text("A retained user edit.\n")
                process, report = self.assert_read_only_helper(study, helper)
                self.assertEqual(process.returncode, 1, process.stdout)
                self.assertEqual(report["distribution"], "standalone-bundle")
                self.assertEqual({c["id"] for c in report["checks"] if c["status"] == "fail"}, expected)
                self.assertTrue(all(c["remedy"] for c in report["checks"] if c["status"] == "fail"))
                if "catalog" in expected:
                    remedy = next(c["remedy"] for c in report["checks"] if c["id"] == "catalog")
                    self.assertIn("never insert files into or rewrite a locked bundle", remedy)
                    self.assertNotIn("Restore examples/toy-study", str(report))

    def test_relocated_selected_catalog_does_not_need_a_study_or_central_example(self):
        study = create_toy(ROOT, self.work / "study")
        bundle = bundles.bundle_path(study, bundles.verify_study(study))
        relocated = self.work / "relocated bundle"
        shutil.copytree(bundle, relocated)
        original_open = Path.open

        def confined_open(path, *args, **kwargs):
            self.assertTrue(path.resolve().is_relative_to(relocated.resolve()),
                            "Diagnostics must not read credentials or other ambient files")
            return original_open(path, *args, **kwargs)

        with patch("shutil.which", side_effect=AssertionError("host lookup")), \
             patch("subprocess.Popen", side_effect=AssertionError("execution")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch.object(Path, "open", confined_open):
            report = diagnose(relocated)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["distribution"], "standalone-bundle")
        self.assertEqual({c["id"] for c in report["checks"]}, {"python", "platform", "catalog"})
        self.assertEqual([c["id"] for c in report["excluded_checks"]], ["toy-resources"])

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
