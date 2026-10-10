"""Check the required PR gate's selected commands without executing its suites."""
from contextlib import redirect_stdout
import importlib.util
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


TOOLS = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_changed", TOOLS / "check_changed.py")
selector = importlib.util.module_from_spec(SPEC)
with patch.object(sys, "path", [str(TOOLS), *sys.path]):
    SPEC.loader.exec_module(selector)


class ChangedChecks(unittest.TestCase):
    def selected(self, paths, *, diff_status=0, suite_status=0, docs_errors=None):
        commands = []

        def run(command, **kwargs):
            if command[:3] == ["git", "diff", "--name-only"]:
                return subprocess.CompletedProcess(command, diff_status, "\n".join(paths), "")
            self.assertEqual(command[:3], [sys.executable, "-m", "unittest"])
            commands.append(command[3:])
            return subprocess.CompletedProcess(command, suite_status)

        with patch.object(sys, "argv", ["check_changed.py", "--base", "fixture-base"]), \
             patch.object(selector.subprocess, "run", side_effect=run), \
             patch.object(selector, "check_docs", return_value={"checked_links": 1, "errors": docs_errors or []}), \
             redirect_stdout(StringIO()):
            status = selector.main()
        suites = {item for command in commands for item in command if item.startswith("conformance.")}
        return status, suites, commands

    def test_adapter_only_changes_run_the_adapter_regressions(self):
        cases = {
            "adapters/reference-assets/acquire.py": {"test_reference_assets", "test_references", "test_research_prepare"},
            "adapters/arxiv/package.py": {"test_papers"},
            "adapters/local-process/broker.py": {"test_broker", "test_resources"},
            "adapters/codex/session.py": {"test_native_capture", "test_research_prepare"},
        }
        for path, required in cases.items():
            with self.subTest(path=path):
                status, suites, _ = self.selected([path])
                self.assertEqual(status, 0)
                self.assertLessEqual({"conformance." + name for name in required}, suites)

    def test_policy_and_workflow_changes_cover_execution_and_configuration(self):
        for path in ("profiles/default/profile.json", "policies/local/policy.json",
                     "recipes/allagma-research/recipe.json", "templates/study/paper.json",
                     "examples/toy-study/domain/analyze.py"):
            with self.subTest(path=path):
                status, suites, _ = self.selected([path])
                self.assertEqual(status, 0)
                self.assertLessEqual({"conformance.test_contracts", "conformance.test_versions",
                                      "conformance.test_research", "conformance.test_analysis_policy",
                                      "conformance.test_study_adaptation"}, suites)

    def test_evaluation_fixture_changes_run_the_comparison(self):
        _, suites, _ = self.selected(["evals/context-retention/cases.json"])
        self.assertIn("conformance.test_improvement", suites)

    def test_mixed_changes_keep_both_context_and_adapter_checks(self):
        _, suites, _ = self.selected(["methods/allagma-context-active-brief/select.py",
                                      "adapters/reference-assets/acquire.py"])
        self.assertLessEqual({"conformance.test_improvement", "conformance.test_reference_assets"}, suites)

    def test_context_only_changes_keep_the_small_comparison_scope(self):
        _, suites, _ = self.selected(["methods/allagma-context-active-brief/select.py"])
        self.assertEqual(suites, {"conformance.test_modules", "conformance.test_improvement"})

    def test_core_changes_and_unknown_diffs_run_all_offline_suites(self):
        expected = {"conformance." + path.stem for path in (TOOLS.parent / "conformance").glob("test_*.py")}
        for paths, diff_status in ((["allagma/contracts.py"], 0), ([], 128)):
            with self.subTest(paths=paths, diff_status=diff_status):
                _, suites, _ = self.selected(paths, diff_status=diff_status)
                self.assertEqual(suites, expected)
        _, _, commands = self.selected([], diff_status=128)
        self.assertIn(["discover", "-s", "tools/tests", "-v"], commands)

    def test_documentation_only_and_empty_diffs_do_not_run_behavior_suites(self):
        for paths in (["docs/guides/troubleshooting.md"], []):
            with self.subTest(paths=paths):
                status, suites, commands = self.selected(paths)
                self.assertEqual(status, 0)
                self.assertFalse(suites)
                self.assertFalse(commands)

    def test_selected_test_failure_fails_the_required_gate(self):
        for path in ("adapters/reference-assets/acquire.py", "tools/check_changed.py"):
            with self.subTest(path=path):
                status, _, commands = self.selected([path], suite_status=7)
                self.assertEqual(status, 7)
                self.assertEqual(len(commands), 1)
        status, _, commands = self.selected(["allagma/contracts.py"], docs_errors=["Broken link"])
        self.assertEqual(status, 1)
        self.assertFalse(commands)


if __name__ == "__main__":
    unittest.main()
