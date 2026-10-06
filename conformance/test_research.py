import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from allagma.bundles import bundle_path, verify_study
from allagma.campaigns import (analyze_campaign, audit_campaign, run_campaign, start_campaign)
from allagma.demo import create_toy, toy_workflow
from allagma.files import AllagmaError, file_hash, inventory, read_json, write_json
from conformance.support import ROOT, WorkspaceTest


class Research(WorkspaceTest):
    @classmethod
    def setUpClass(cls):
        cls.fixture_temp = tempfile.TemporaryDirectory(prefix="allagma-research-fixture-")
        cls.fixture = Path(cls.fixture_temp.name) / "complete"
        cls.walkthrough = toy_workflow(ROOT, cls.fixture)

    @classmethod
    def tearDownClass(cls):
        cls.fixture_temp.cleanup()

    def clone(self):
        self.study = self.work / "study"
        shutil.copytree(self.fixture, self.study)
        return self.study

    def test_complete_workflow_records_success_failure_and_interruption(self):
        records = [read_json(path) for path in self.fixture.glob("campaigns/toy-v1/runs/*/attempts/*/record.json")]
        statuses = [item["status"] for item in records]
        self.assertEqual(statuses.count("succeeded"), 26)
        self.assertEqual(statuses.count("failed"), 1)
        self.assertEqual(statuses.count("interrupted"), 1)
        self.assertEqual(len({item["attempt_id"] for item in records}), 28)
        self.assertEqual(self.walkthrough["audit"]["verdict"], "pass")
        self.assertEqual(read_json(self.fixture / "campaigns/toy-v1/state.json")["execution_status"], "completed")
        values = read_json(self.fixture / "campaigns/toy-v1/analyses/a001/outputs/summary.json")
        self.assertEqual(values["replicates"], 24)
        self.assertGreater(values["ci95_normal"][0], 0)
        self.assertTrue(values["counterexample_seeds"])
        claims = read_json(self.fixture / "campaigns/toy-v1/analyses/a001/paper/claims.json")
        self.assertEqual([item["status"] for item in claims], ["supported", "contradicted"])

    def test_resume_does_not_rerun_valid_successes(self):
        study = self.clone()
        before = inventory(study / "campaigns/toy-v1/runs")
        run_campaign(study, "toy-v1")
        self.assertEqual(inventory(study / "campaigns/toy-v1/runs"), before)

    def test_raw_tampering_stales_dependent_claims(self):
        study = self.clone()
        path = study / "campaigns/toy-v1/runs/confirm-102/attempts/001/raw.json"
        raw = read_json(path); raw["samples"][0] *= -1; write_json(path, raw)
        result = audit_campaign(study, "toy-v1")
        self.assertEqual(result["verdict"], "revise")
        self.assertEqual(set(result["stale_claims"]), {"C1", "C2"})
        self.assertTrue(any("Missing or changed evidence" in finding for finding in result["findings"]))
        self.assertEqual(read_json(study / "campaigns/toy-v1/state.json")["execution_status"], "needs_revision")

    def test_review_is_not_reused_for_edited_manuscript(self):
        study = self.clone()
        paper = study / "campaigns/toy-v1/analyses/a001/paper/manuscript.md"
        paper.write_text(paper.read_text().replace("0.06510417", "99.00000000"))
        result = audit_campaign(study, "toy-v1")
        self.assertEqual(result["verdict"], "revise")
        self.assertTrue(any("regeneration" in text or "reproduction" in text for text in result["findings"]))
        old = read_json(study / "campaigns/toy-v1/analyses/a001/reviews/review-001/record.json")
        self.assertNotEqual(old["material"]["sha256"], file_hash(paper))

    def test_reanalysis_and_relocation_preserve_results(self):
        study = self.clone()
        audit = audit_campaign(study, "toy-v1")
        self.assertEqual(audit["verdict"], "pass")
        self.assertGreater(audit["checked_references"], 200)

    def test_budget_stops_before_an_extra_attempt(self):
        study = create_toy(ROOT, self.work / "budget", budget={"max_attempts":1,"max_seconds":10,"money_usd":0,"per_attempt_seconds":2})
        start_campaign(study, "limited")
        result = run_campaign(study, "limited")
        self.assertEqual(result["execution_status"], "budget_exhausted")
        run_campaign(study, "limited")
        self.assertEqual(len(list(study.glob("campaigns/limited/runs/*/attempts/*/record.json"))), 1)
        self.assertTrue(list(study.glob("campaigns/limited/reports/partial-*.md")))

    def test_confirmation_is_blocked_after_a_failed_pilot(self):
        study = create_toy(ROOT, self.work / "pilot")
        start_campaign(study, "pilot")
        run_campaign(study, "pilot", fault={"run_id":"pilot-zero","mode":"failure"})
        self.assertFalse(list(study.glob("campaigns/pilot/runs/confirm-*/attempts/*")))

    def test_repeated_failures_stop_automatically(self):
        study = create_toy(ROOT, self.work / "failures")
        start_campaign(study, "failures")
        for _ in range(2):
            run_campaign(study, "failures", fault={"run_id":"pilot-zero","mode":"failure"})
        result = run_campaign(study, "failures")
        self.assertEqual(result["execution_status"], "failed")
        self.assertIn("Repeated failure", result["stop_reason"])
        self.assertEqual(len(list(study.glob("campaigns/failures/runs/*/attempts/*/record.json"))), 2)

    def test_pilot_and_confirmation_overlap_is_rejected(self):
        study = create_toy(ROOT, self.work / "leakage")
        protocol = read_json(study / "protocol.json")
        protocol["runs"][2]["input"]["seed"] = 1
        write_json(study / "protocol.json", protocol)
        with self.assertRaisesRegex(AllagmaError, "reused"):
            start_campaign(study, "leakage")
        protocol["runs"][2]["input"]["seed"] = 100
        protocol["runs"][3]["input"]["seed"] = 100
        write_json(study / "protocol.json", protocol)
        with self.assertRaisesRegex(AllagmaError, "Duplicate seeds"):
            start_campaign(study, "leakage")

    def test_missing_or_changed_success_outputs_are_not_silently_rerun(self):
        study = self.clone()
        (study / "campaigns/toy-v1/runs/confirm-102/attempts/001/raw.json").unlink()
        with self.assertRaisesRegex(AllagmaError, "Missing or changed"):
            run_campaign(study, "toy-v1")

    def test_frozen_scientific_code_cannot_change_during_resume(self):
        study = self.clone()
        runner = study / "campaigns/toy-v1/materials/domain/runner.py"
        runner.write_text(runner.read_text() + "\n# mutation\n")
        with self.assertRaisesRegex(AllagmaError, "Missing or changed"):
            run_campaign(study, "toy-v1")

    def test_controller_crash_is_retained_as_a_separate_attempt(self):
        study = create_toy(ROOT, self.work / "crash")
        start_campaign(study, "crashed")
        result = subprocess.run([sys.executable, "-m", "allagma", "campaign", "run", "--study", str(study), "--campaign", "crashed", "--crash-after-start"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 86, result.stderr)
        run_campaign(study, "crashed", stop_after=1)
        paths = sorted(study.glob("campaigns/crashed/runs/pilot-zero/attempts/*/record.json"))
        self.assertEqual([read_json(path)["status"] for path in paths], ["interrupted", "succeeded"])

    def test_analysis_does_not_overwrite_an_earlier_revision(self):
        study = self.clone()
        with self.assertRaisesRegex(AllagmaError, "Analysis ID exists"):
            analyze_campaign(study, "toy-v1")

    def test_alternative_recipe_and_adapters_complete_the_same_handoffs(self):
        result = toy_workflow(ROOT, self.work / "alternative", roles={"context":"context/full-record","reviewer":"reviewer/trace"}, recipe="recipe/replication")
        self.assertEqual(result["audit"]["verdict"], "pass")
        self.assertEqual(result["context_method"]["module_id"], "context/full-record")
        self.assertEqual(result["audit"]["analysis_repetitions"], 2)
