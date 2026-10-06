import json
from pathlib import Path
import subprocess
import sys
import time

from allagma.campaigns import run_campaign, start_campaign
from allagma.demo import create_toy
from allagma.files import read_json, write_json
from conformance.support import ROOT, WorkspaceTest


class Worker(WorkspaceTest):
    def test_worker_enforces_deadline_after_controller_is_killed(self):
        code = ('from pathlib import Path\nimport sys\n'
                'from allagma.campaigns import _execute\n'
                'd=Path(sys.argv[1]).resolve()\n'
                '_execute([sys.executable,"-c","import time; print(42, flush=True); time.sleep(30)"],'
                'd,d/"stdout.txt",d/"stderr.txt",0.5)\n')
        parent = subprocess.Popen([sys.executable, "-c", code, str(self.work)], cwd=ROOT,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: parent.kill() if parent.poll() is None else None)
        stdout = self.work / "stdout.txt"
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and (not stdout.exists() or not stdout.read_text()):
            time.sleep(0.01)
        self.assertTrue(stdout.exists() and stdout.read_text().strip() == "42")
        parent.kill(); parent.wait(timeout=2)
        result = self.work / "stdout.job-result.json"
        deadline = time.monotonic() + 4
        while not result.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(result.exists(), "Worker did not finish independently of the controller")
        self.assertEqual(read_json(result)["stop"], "timeout")
        self.assertLess(read_json(result)["wall_seconds"], 3)

    def test_per_attempt_timeout_is_a_failed_record(self):
        study = create_toy(ROOT, self.work / "timeout", budget={"max_attempts":3,"max_seconds":5,"money_usd":0,"per_attempt_seconds":0.15})
        protocol = read_json(study / "protocol.json")
        protocol["runs"][0]["input"]["fault"] = "interrupt"
        write_json(study / "protocol.json", protocol)
        start_campaign(study, "timeout")
        run_campaign(study, "timeout")
        result = read_json(study / "campaigns/timeout/runs/pilot-zero/attempts/001/record.json")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["kind"], "timeout")
        self.assertTrue(any(item["path"].endswith("job-result.json") for item in result["outputs"]))
