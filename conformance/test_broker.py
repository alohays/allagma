"""Offline request/protection contracts; execution fixtures are explicitly mocked."""
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from allagma.files import AllagmaError, write_json
from allagma import resources

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("allagma_broker", ROOT/"adapters/local-process/broker.py")
broker_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(broker_module)


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root/"candidate"
        self.workspace.mkdir()
        resources.initialize(self.root/"ledger", {"format": resources.FORMAT,
            "budgets_seconds": {"compute": 60, "setup": 30},
            "command_timeout_seconds": {"compute": 5, "setup": 5},
            "attempt_limit": 6, "rss_limit_bytes": 200_000_000,
            "storage_limit_bytes": 1_000_000, "file_limit_bytes": 500_000,
            "poll_seconds": .03, "terminate_grace_seconds": .03}, self.workspace)
        self.broker = broker_module.Broker(self.workspace, self.root/"ledger", self.root/"controller", readonly=[self.workspace/"inputs"])

    def request(self, **changes):
        value = {"request_id": "a"*32, "argv": ["python3", "science.py"], "cwd": ".",
                 "category": "compute", "timeout_seconds": 1, "attempt": True, "label": "attempt"}
        value.update(changes)
        write_json(self.workspace/".compute/requests"/(value["request_id"]+".json"), value)

    def test_path_escape_is_rejected_without_execution(self):
        self.request(cwd="..")
        with patch.object(broker_module.resources, "execute") as execute:
            result = self.broker.poll()
            execute.assert_not_called()
        self.assertEqual(result["result"]["status"], "rejected")

    def test_source_snapshot_and_authoritative_replay_guard(self):
        (self.workspace/"science.py").write_text("print('example')\n")
        self.request()
        with patch.object(broker_module.resources, "execute", return_value={"status": "completed"}) as execute:
            result = self.broker.poll()
            self.assertEqual(result["result"]["status"], "completed")
            self.assertEqual(execute.call_count, 1)
            # Candidate removal of a convenience response must not rerun science.
            (self.workspace/".compute/responses"/("a"*32+".json")).unlink()
            self.assertIsNone(self.broker.poll())
            self.assertEqual(execute.call_count, 1)
            self.assertTrue((self.workspace/".compute/responses"/("a"*32+".json")).exists())
        retained = self.root/"controller/requests"/("a"*32)/"sources/science.py"
        self.assertEqual(retained.read_text(), "print('example')\n")

    def test_controller_and_ledger_cannot_be_candidate_owned(self):
        with self.assertRaisesRegex(AllagmaError, "outside"):
            broker_module.Broker(self.workspace, self.workspace/"ledger", self.root/"another")
        with self.assertRaisesRegex(AllagmaError, "outside"):
            broker_module.Broker(self.workspace, self.root/"ledger", self.workspace/"controller")

    def test_profile_denies_network_and_preserves_readonly_paths(self):
        text = self.broker.isolation
        self.assertIn("(deny network*)", text)
        self.assertIn(str(self.root/"ledger"), text)
        self.assertIn(str(self.root/"controller"), text)
        self.assertIn(str(self.workspace/"inputs"), text)

    def test_recovery_delivers_completed_job_without_a_second_execution(self):
        self.request()
        actual_execute = resources.execute
        def completed_then_controller_lost(ledger, command, **options):
            actual_execute(ledger, [sys.executable, "-c", "from pathlib import Path; Path('once').write_text('executed')"], **options)
            raise RuntimeError("simulated controller loss after durable job completion")
        with patch.object(broker_module.resources, "execute", side_effect=completed_then_controller_lost):
            with self.assertRaisesRegex(RuntimeError, "controller loss"):
                self.broker.poll()
        result = self.broker.recover()
        self.assertEqual(result[0]["result"]["status"], "completed")
        self.assertEqual(len(resources.summary(self.root/"ledger")["entries"]), 1)
        self.assertEqual((self.workspace/"once").read_text(), "executed")
        self.assertIsNone(self.broker.poll())

    def test_recovery_refuses_a_live_job_then_conservatively_abandons_it(self):
        self.request()
        request_id = "a"*32
        destination = self.root/"controller/requests"/request_id
        destination.mkdir(parents=True)
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
        job = self.root/"ledger/jobs/0001-live"
        policy = resources._policy(self.root/"ledger")
        write_json(job/"reservation.json", {"profile_sha256": policy["profile_sha256"],
            "category": "compute", "attempt": True, "reserved_seconds": 7,
            "request_id": request_id, "command": ["unused"]})
        write_json(job/"process.json", {"pid": child.pid})
        try:
            with self.assertRaisesRegex(AllagmaError, "live processes"):
                self.broker.recover()
        finally:
            child.terminate()
            child.wait(timeout=3)
        result = self.broker.recover()
        self.assertEqual(result[0]["result"]["status"], "abandoned")
        self.assertEqual(result[0]["result"]["charged_seconds"], 7)

    def test_recorded_request_without_reservation_never_launches_on_recovery(self):
        self.request()
        (self.root/"controller/requests"/("a"*32)).mkdir(parents=True)
        result = self.broker.recover()
        self.assertEqual(result[0]["result"]["status"], "not_started")
        self.assertEqual(resources.summary(self.root/"ledger")["attempts"], 0)

    def test_computation_cannot_bypass_attempt_count_by_omitting_flag(self):
        self.request(attempt=False)
        with patch.object(broker_module.resources, "execute", return_value={"status": "completed"}) as execute:
            self.broker.poll()
            self.assertTrue(execute.call_args.kwargs["attempt"])

    def test_new_controller_does_not_replay_an_inherited_queue(self):
        self.request()
        other=broker_module.Broker(self.workspace,self.root/"ledger",self.root/"different-controller")
        with patch.object(broker_module.resources,"execute") as execute:
            self.assertIsNone(other.poll())
            execute.assert_not_called()

    def test_source_snapshots_exclude_named_virtual_environments(self):
        environment=self.workspace/'environment-two';environment.mkdir()
        (environment/'pyvenv.cfg').write_text('home = /python\n')
        (environment/'installed.py').write_text('installed_dependency=True\n')
        (self.workspace/'science.py').write_text('print(4)\n')
        self.request()
        with patch.object(broker_module.resources,'execute',return_value={'status':'completed'}):self.broker.poll()
        snapshot=self.root/'controller/requests'/('a'*32)/'sources'
        self.assertTrue((snapshot/'science.py').exists())
        self.assertFalse((snapshot/'environment-two').exists())


if __name__ == "__main__":
    unittest.main()
