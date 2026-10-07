"""Offline request/protection contracts; execution fixtures are explicitly mocked."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from allagma.files import AllagmaError, write_json

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


if __name__ == "__main__":
    unittest.main()
