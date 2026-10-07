"""Budget supervisor tests in isolated temporary workspaces, not study data."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

import compute


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.original=compute.ROOT
        self.temp=tempfile.TemporaryDirectory()
        compute.ROOT=Path(self.temp.name)

    def tearDown(self):
        compute.ROOT=self.original
        self.temp.cleanup()

    def test_insufficient_reservation_never_launches(self):
        marker=compute.ROOT/"launched"
        with self.assertRaisesRegex(RuntimeError,"Insufficient"):
            compute.execute("refused",[sys.executable,"-c",f"open({str(marker)!r},'w').close()"],1800,attempt=True)
        self.assertFalse(marker.exists())
        self.assertEqual(compute.ledger()["attempts"],0)

    def test_unknown_completion_charges_full_reservation(self):
        compute.dump(compute.ROOT/"evidence/compute/001-uncertain.json",
                     {"label":"fixture","attempt":True,"reservation_seconds":162.,"status":"running"})
        self.assertAlmostEqual(compute.ledger()["charged_seconds"],177.3)
        self.assertEqual(compute.ledger()["attempts"],1)

    def test_attempt_ceiling_prevents_launch(self):
        for index in range(18):
            compute.dump(compute.ROOT/f"evidence/compute/{index:03d}.json",
                {"label":"fixture","attempt":True,"reservation_seconds":2.,"charged_seconds":.01,"status":"completed"})
        with self.assertRaisesRegex(RuntimeError,"attempt ceiling"):
            compute.execute("refused",[sys.executable,"-c","raise SystemExit(99)"],1,attempt=True)

    def test_success_and_timeout_are_retained_and_charged(self):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(compute.execute("success",[sys.executable,"-c","print('success')"],2,attempt=True),0)
            self.assertEqual(compute.execute("timeout",[sys.executable,"-c","import time; time.sleep(10)"],.1,attempt=True),124)
        entries=compute.ledger()["entries"]
        self.assertEqual([e["status"] for e in entries],["completed","timeout"])
        self.assertTrue(all(e["charged_seconds"]>0 for e in entries))
        self.assertEqual(compute.ledger()["attempts"],2)


if __name__=="__main__":
    unittest.main(verbosity=2)
