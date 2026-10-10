"""Real processes must serialize study mutations and release locks on death."""
import json
import os
import selectors
import subprocess
import sys

from allagma.campaigns import start_campaign
from allagma.demo import create_toy
from allagma.files import inventory, read_json, write_json
from conformance.support import ROOT, WorkspaceTest


class StudyLocking(WorkspaceTest):
    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-B", "-m", "allagma", *map(str, args)], cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True, text=True, timeout=15,
        )

    def hold_lock(self, study):
        process = subprocess.Popen(
            [sys.executable, "-B", "-c",
             "import sys\nfrom allagma.files import study_mutex\n"
             "with study_mutex(sys.argv[1]):\n"
             "    print('locked', flush=True)\n"
             "    sys.stdin.read(1)\n", str(study)],
            cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )

        def cleanup():
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)

        self.addCleanup(cleanup)
        # A pipe handshake proves ownership; no sleep-based race or mocked flock.
        with selectors.DefaultSelector() as ready:
            ready.register(process.stdout, selectors.EVENT_READ)
            self.assertTrue(ready.select(timeout=10), "Lock owner did not become ready")
        self.assertEqual(process.stdout.readline(), "locked\n")
        return process

    @staticmethod
    def snapshot(study):
        files = inventory(study)
        return files, {name: (study / name).stat().st_mtime_ns for name in files}

    def test_contenders_preserve_the_study_and_another_study_can_progress(self):
        study = create_toy(ROOT, self.work / "locked-study")
        other = create_toy(ROOT, self.work / "other-study")
        start_campaign(study, "existing")
        baseline = read_json(study / ".allagma/scaffold-baseline.json")
        migration = self.work / "migration.json"
        write_json(migration, {"from": baseline["version"], "to": "next",
            "answers": baseline["answers"], "reason": "Lock fixture",
            "files": {"STUDY-LOG.md": "# Study log\n"}})
        owner = self.hold_lock(study)
        before = self.snapshot(study)
        commands = (
            ("campaign", "start", "--campaign", "new"),
            ("campaign", "run", "--campaign", "existing", "--stop-after", "1"),
            ("update", "plan", "--source", ROOT),
            ("migrate", "plan", "--spec", migration),
        )
        for command in commands:
            with self.subTest(command=command[:2]):
                result = self.cli(*command, "--study", study)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("holds this study's lock", result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(self.snapshot(study), before)
        result = self.cli("campaign", "start", "--study", other, "--campaign", "independent")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(owner.poll())
        self.assertEqual(self.snapshot(study), before)
        owner.communicate("release", timeout=5)
        self.assertEqual(owner.returncode, 0)
        result = self.cli("campaign", "run", "--study", study,
                          "--campaign", "existing", "--stop-after", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["execution_status"], "paused")
        attempts = list(study.glob("campaigns/existing/runs/*/attempts/*/record.json"))
        self.assertEqual(len(attempts), 1)
        self.assertEqual(read_json(attempts[0])["status"], "succeeded")

    def test_killed_owner_releases_lock_without_deleting_lock_file(self):
        study = create_toy(ROOT, self.work / "study")
        owner = self.hold_lock(study)
        lock = study / ".allagma/mutation.lock"
        identity = lock.stat().st_dev, lock.stat().st_ino
        before = self.snapshot(study)
        owner.kill()
        owner.communicate(timeout=5)
        self.assertLess(owner.returncode, 0)
        self.assertEqual(self.snapshot(study), before)
        result = self.cli("campaign", "start", "--study", study, "--campaign", "after-death")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((study / "campaigns/after-death/study.json").is_file())
        self.assertEqual((lock.stat().st_dev, lock.stat().st_ino), identity)
