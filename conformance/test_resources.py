"""Actual subprocess failures and watchdogs; no model or scientific packages."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from allagma.files import AllagmaError, read_json, write_json
from allagma import resources


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name) / "study"
        self.work.mkdir()
        self.ledger = Path(self.temp.name) / "ledger"
        self.profile = {"format": resources.FORMAT,
            "budgets_seconds": {"compute": 30., "setup": 30.},
            "command_timeout_seconds": {"compute": 5., "setup": 5.},
            "attempt_limit": 2, "rss_limit_bytes": 200_000_000,
            "storage_limit_bytes": 1_000_000, "file_limit_bytes": 500_000,
            "poll_seconds": .03, "terminate_grace_seconds": .03}

    def initialize(self):
        resources.initialize(self.ledger, self.profile, self.work)

    def run_code(self, code, **kwargs):
        return resources.execute(self.ledger, [sys.executable, "-c", code],
            label="test", category="compute", timeout=kwargs.pop("timeout", 2), **kwargs)

    def test_failure_retry_and_separate_categories_preserve_history(self):
        self.initialize()
        first = self.run_code("raise SystemExit(3)", attempt=True)
        self.assertEqual(first["status"], "failed")
        old = (Path(first["job"])/"reservation.json").read_bytes()
        second = self.run_code("print('real success')", attempt=True)
        self.assertEqual(second["status"], "completed")
        self.assertEqual(old, (Path(first["job"])/"reservation.json").read_bytes())
        self.assertEqual((Path(second["job"])/"stdout.txt").read_text(), "real success\n")
        summary = resources.summary(self.ledger)
        self.assertEqual(summary["attempts"], 2)
        self.assertEqual(summary["charged_seconds"]["setup"], 0)
        with self.assertRaisesRegex(AllagmaError, "Attempt ceiling"):
            self.run_code("pass", attempt=True)

    def test_timeout_stops_actual_child(self):
        self.initialize()
        result = self.run_code("import time; time.sleep(30)", timeout=.12)
        self.assertEqual(result["status"], "timed_out")
        self.assertLess(result["charged_seconds"], 3)
        pid = read_json(Path(result["job"])/"process.json")["pid"]
        self.assertNotIn(pid, resources.process_table())

    def test_memory_watchdog(self):
        self.profile["rss_limit_bytes"] = 30_000_000
        self.initialize()
        result = self.run_code("import time; x=bytearray(80_000_000); time.sleep(5)")
        self.assertEqual(result["status"], "memory_exceeded")

    def test_storage_and_per_file_limits(self):
        self.profile["storage_limit_bytes"] = 80_000
        self.initialize()
        result = self.run_code("from pathlib import Path; import time; Path('big').write_bytes(b'x'*100000); time.sleep(5)")
        self.assertEqual(result["status"], "storage_exceeded")

    def test_per_file_kernel_limit(self):
        self.initialize()
        result = self.run_code("from pathlib import Path; Path('too-big').write_bytes(b'x'*800000)")
        self.assertEqual(result["status"], "failed")
        self.assertLessEqual((self.work/"too-big").stat().st_size, self.profile["file_limit_bytes"])

    def test_final_storage_is_checked_after_fast_exit_without_masking_failure(self):
        for exit_code, expected_status in [(0, "storage_exceeded"), (3, "failed")]:
            with self.subTest(exit_code=exit_code), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary); work = base/"work"; work.mkdir()
                ledger = base/"ledger"
                resources.initialize(ledger, {**self.profile, "storage_limit_bytes": 1000}, work)
                original_popen, original_storage = subprocess.Popen, resources.storage_bytes
                state = {"process": None, "gated": False}
                def capture(*args, **kwargs):
                    process = original_popen(*args, **kwargs)
                    if kwargs.get("preexec_fn") is not None: state["process"] = process
                    return process
                def storage(path):
                    value = original_storage(path)
                    if state["process"] is not None and not state["gated"]:
                        state["gated"] = True
                        (work/"go").touch()
                        state["process"].wait(timeout=3)
                    return value
                code = ("from pathlib import Path; import time,sys\n"
                        "while not Path('go').exists(): time.sleep(.005)\n"
                        f"Path('payload').write_bytes(b'x'*2000)\nsys.exit({exit_code})\n")
                with patch.object(subprocess, "Popen", capture), patch.object(resources, "storage_bytes", storage):
                    result = resources.execute(ledger, [sys.executable, "-c", code],
                                               label="final-storage", category="compute", timeout=4)
                self.assertEqual(result["status"], expected_status)
                self.assertEqual(result["final_storage_bytes"], 2000)
                self.assertEqual(result["peak_storage_bytes"], 2000)
                self.assertTrue(result["final_storage_limit_exceeded"])

    def test_cli_preserves_command_arguments_and_nonzero_status(self):
        self.initialize()
        result = subprocess.run([sys.executable, "-m", "allagma", "resource", "run",
            "--ledger", str(self.ledger), "--label", "cli", "--timeout", "2", "--",
            sys.executable, "-c", "import sys; print(sys.argv[1]); raise SystemExit(4)", "--literal"],
            text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual((self.ledger/"jobs/0001-cli/stdout.txt").read_text(), "--literal\n")

    def test_normal_subprocess_exit_is_not_an_orphan(self):
        self.initialize()
        result = self.run_code("import subprocess,sys; subprocess.run([sys.executable,'-c','import time; time.sleep(.08)'],check=True)")
        self.assertEqual(result["status"], "completed")

    def test_command_cwd_stays_inside_budgeted_storage(self):
        self.initialize()
        subdirectory = self.work/"capsule"
        subdirectory.mkdir()
        result = resources.execute(self.ledger, [sys.executable, "-c", "from pathlib import Path; Path('result').write_text('done')"],
            label="subdir", category="compute", timeout=2, workdir=subdirectory)
        self.assertEqual(result["status"], "completed")
        self.assertEqual((subdirectory/"result").read_text(), "done")
        with self.assertRaisesRegex(AllagmaError, "budgeted workspace"):
            resources.execute(self.ledger, [sys.executable, "-c", "pass"], label="outside",
                category="compute", timeout=2, workdir=self.work.parent)

    def test_observed_detached_child_is_stopped_after_parent_exits(self):
        self.initialize()
        result = self.run_code("import subprocess,sys,time; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)'],start_new_session=True); Path('pid').write_text(str(p.pid)); time.sleep(.15)")
        self.assertEqual(result["status"], "orphaned_children")
        self.assertNotIn(int((self.work/"pid").read_text()), resources.process_table())

    def test_failed_launch_is_fully_charged_until_recovered(self):
        self.initialize()
        with self.assertRaises(FileNotFoundError):
            resources.execute(self.ledger, ["/nonexistent-allagma-executable"],
                label="missing", category="setup", timeout=2)
        summary = resources.summary(self.ledger)
        self.assertAlmostEqual(summary["charged_seconds"]["setup"], 6.06)
        with self.assertRaisesRegex(AllagmaError, "unresolved"):
            self.run_code("pass")
        resources.recover(self.ledger)
        result = self.run_code("pass")
        self.assertEqual(result["status"], "completed")
        self.assertAlmostEqual(resources.summary(self.ledger)["charged_seconds"]["setup"], 6.06)

    def test_profile_immutable_and_invalid_limits_fail_closed(self):
        self.initialize()
        with self.assertRaises(AllagmaError):
            resources.initialize(self.ledger, self.profile, self.work)
        for bad in (float("nan"), float("inf"), True, 0, -1):
            invalid = {**self.profile, "budgets_seconds": {"compute": bad}}
            with self.assertRaises(AllagmaError):
                resources.validate_profile(invalid)
        with self.assertRaisesRegex(AllagmaError, "timeout exceeds"):
            self.run_code("pass", timeout=10)

    def test_full_reservation_required_before_start(self):
        self.profile["budgets_seconds"]["compute"] = 5
        self.initialize()
        with self.assertRaisesRegex(AllagmaError, "Insufficient"):
            self.run_code("from pathlib import Path; Path('started').touch()")
        self.assertFalse((self.work/"started").exists())

    def test_unresolved_live_job_is_not_recovered_or_restarted(self):
        self.initialize()
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
        try:
            job = self.ledger/"jobs/0001-test"
            write_json(job/"reservation.json", {"profile_sha256": resources.digest(self.profile),
                "category": "compute", "attempt": True, "reserved_seconds": 10})
            write_json(job/"process.json", {"pid": child.pid})
            with self.assertRaisesRegex(AllagmaError, "live processes"):
                resources.recover(self.ledger)
        finally:
            child.terminate()
            child.wait(timeout=3)
        self.assertEqual(resources.recover(self.ledger)["recovered"], ["0001-test"])


if __name__ == "__main__":
    unittest.main()
