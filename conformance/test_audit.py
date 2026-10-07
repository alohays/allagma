"""Adversarial regressions derived from the post-delivery self-audit."""
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from unittest.mock import patch

from allagma import bundles as b, campaigns as c
from allagma.catalog import Catalog
from allagma.configuration import DEFAULT_BUDGET, resolve_configuration
from allagma.contracts import validate
from allagma.demo import create_toy, toy_workflow
from allagma.files import AllagmaError, read_json, reference, write_json, write_text
from allagma.migrations import plan_migration, apply_migration
from conformance.support import ROOT, WorkspaceTest


class Audit(WorkspaceTest):
    def test_json_exponent_overflow_is_rejected(self):
        path = self.work / "overflow.json"
        path.write_text('{"value": 1e999}')
        with self.assertRaises(AllagmaError):
            read_json(path)

    def test_timestamp_requires_rfc3339_time_and_zone(self):
        for value in ("2026-10-07 12:00:00+00:00", "2026-10-07T12:00+00:00",
                      "2026-W41-3T12:00:00+00:00", "2026-10-07T12:00:00+01:60"):
            with self.subTest(value=value), self.assertRaises(AllagmaError):
                validate(value, {"type": "string", "format": "date-time"})

    def test_reference_rejects_symlink_alias(self):
        write_json(self.work / "raw.json", {"value": 1})
        alias = self.work / "alias.json"
        alias.symlink_to(self.work / "raw.json")
        with self.assertRaises(AllagmaError):
            reference(self.work, alias)

    def test_configuration_matches_budget_schema(self):
        for value in (0.005, math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(AllagmaError):
                resolve_configuration([("module", {"budget": DEFAULT_BUDGET}),
                                       ("request", {"budget": {"per_attempt_seconds": value}})], [])

    def test_unset_resources_do_not_authorize_execution(self):
        study = create_toy(ROOT, self.work / "study", budget=DEFAULT_BUDGET)
        c.start_campaign(study, "unset")
        result = c.run_campaign(study, "unset", stop_after=1)
        self.assertEqual(result["execution_status"], "blocked")
        self.assertFalse(list(study.glob("campaigns/unset/runs/*/attempts/*")))

    def test_failed_campaign_creation_does_not_publish_partial_campaign(self):
        study = create_toy(ROOT, self.work / "study")
        brief = read_json(study / "brief.json")
        brief["question"] = ""
        write_json(study / "brief.json", brief)
        with self.assertRaises(AllagmaError):
            c.start_campaign(study, "invalid")
        self.assertFalse((study / "campaigns/invalid").exists())
        brief["question"] = "A repaired question"
        write_json(study / "brief.json", brief)
        c.start_campaign(study, "invalid")

    def test_interrupted_attempt_preparation_can_resume(self):
        study = create_toy(ROOT, self.work / "study")
        c.start_campaign(study, "prepare")
        original = c.record

        def interrupt(path, value):
            if path.name == "started.json":
                raise KeyboardInterrupt()
            return original(path, value)

        with patch.object(c, "record", side_effect=interrupt), self.assertRaises(KeyboardInterrupt):
            c.run_campaign(study, "prepare", stop_after=1)
        result = c.run_campaign(study, "prepare", stop_after=1)
        self.assertEqual(result["execution_status"], "paused")
        records = list(study.glob("campaigns/prepare/runs/*/attempts/*/record.json"))
        self.assertEqual(sum(read_json(p)["status"] == "succeeded" for p in records), 1)

    def test_recovery_preserves_post_interruption_user_edits(self):
        study = create_toy(ROOT, self.work / "study")
        write_json(study / "overrides/settings.json", {"language": "French"})
        plan = b.plan_update(ROOT, study)
        b.reconcile_update(study, plan["id"])
        b.validate_update(study, plan["id"])
        with self.assertRaises(AllagmaError):
            b.adopt_update(study, plan["id"], fault="after-first-write")
        write_text(study / "ALLAGMA.md", "User work after interruption\n")
        with self.assertRaises(AllagmaError):
            b.recover_update(study)
        self.assertEqual((study / "ALLAGMA.md").read_text(), "User work after interruption\n")
        self.assertTrue((study / ".allagma/transaction.json").exists())

    def test_replacement_does_not_resolve_unused_default(self):
        intent = b.default_intent("replacement")
        intent.update(roles={"context": "context/full-record"}, allow_experimental=True)
        modules = Catalog(ROOT).resolve(intent)["modules"]
        self.assertIn("context/full-record", modules)
        self.assertNotIn("context/active-brief", modules)

    def test_recipe_cannot_disable_reproduction(self):
        source = self.source_copy()
        path = source / "recipes/allagma-research/recipe.json"
        value = read_json(path)
        value["analysis_repetitions"] = 0
        write_json(path, value)
        with self.assertRaises(AllagmaError):
            Catalog(source).check("recipe/research")

    def test_export_rejects_source_changes_during_copy(self):
        source = self.source_copy()
        study = create_toy(ROOT, self.work / "study")
        intent = read_json(study / "allagma.yaml")
        original = b.write_bytes
        changed = False

        def mutate(path, data, **kwargs):
            nonlocal changed
            original(path, data, **kwargs)
            if path.name == "campaigns.py" and not changed:
                changed = True
                target = source / "allagma/campaigns.py"
                target.write_text(target.read_text() + "\n# concurrent edit\n")

        with patch.object(b, "write_bytes", side_effect=mutate), self.assertRaises(AllagmaError):
            b.build_bundle(source, study, intent, self.work / "bundle")

    def test_toy_executes_the_selected_source_helper(self):
        source = self.source_copy()
        path = source / "allagma/campaigns.py"
        path.write_text(path.read_text().replace(
            "def start_campaign(study, campaign):",
            'def start_campaign(study, campaign):\n    raise AllagmaError("Pinned helper sentinel")'))
        with self.assertRaisesRegex(AllagmaError, "Pinned helper sentinel"):
            toy_workflow(source, self.work / "selected-source", faults=False)

    def test_protocol_changes_require_revision_and_amendment_lineage(self):
        study = create_toy(ROOT, self.work / "study")
        c.start_campaign(study, "original")
        original = (study / "campaigns/original/protocol.json").read_bytes()
        protocol = read_json(study / "protocol.json")
        protocol["runs"][-1]["input"]["bias"] = 0.5
        write_json(study / "protocol.json", protocol)
        with self.assertRaises(AllagmaError):
            c.start_campaign(study, "reused-revision")
        protocol["revision"] = "toy-v3"
        write_json(study / "protocol.json", protocol)
        with self.assertRaises(AllagmaError):
            c.start_campaign(study, "missing-amendment")
        protocol["amendment"] = {"from_campaign": "original", "reason": "Sensitivity to larger bias",
                                 "affected_runs": [protocol["runs"][-1]["id"]]}
        write_json(study / "protocol.json", protocol)
        c.start_campaign(study, "amended")
        self.assertEqual((study / "campaigns/original/protocol.json").read_bytes(), original)
        self.assertTrue((study / "campaigns/amended/amendment.json").exists())

    def test_omitted_frozen_material_is_rejected(self):
        study = create_toy(ROOT, self.work / "study")
        c.start_campaign(study, "frozen")
        manifest = study / "campaigns/frozen/code-manifest.json"
        contents = read_json(manifest)
        contents.pop("domain/analyze.py")
        write_json(manifest, contents)
        with self.assertRaises(AllagmaError):
            c.run_campaign(study, "frozen", stop_after=1)

    def test_study_metadata_cannot_disagree_with_frozen_lock(self):
        study = create_toy(ROOT, self.work / "study")
        c.start_campaign(study, "frozen")
        path = study / "campaigns/frozen/study.json"
        record = read_json(path)
        record["effective_configuration"]["language"] = "Unrecorded change"
        write_json(path, record)
        with self.assertRaises(AllagmaError):
            c.run_campaign(study, "frozen", stop_after=1)

    def test_scaffold_baseline_uses_selected_release(self):
        source = self.source_copy()
        release = read_json(source / "release.json")
        release["scaffold_version"] = "2"
        write_json(source / "release.json", release)
        study = create_toy(source, self.work / "study")
        self.assertEqual(read_json(study / ".allagma/scaffold-baseline.json")["version"], "2")

    def test_method_update_does_not_claim_scaffold_migration(self):
        source = self.source_copy()
        study = create_toy(source, self.work / "study")
        release = read_json(source / "release.json")
        release["scaffold_version"] = "2"
        write_json(source / "release.json", release)
        plan = b.plan_update(source, study)
        candidate = read_json(study / ".allagma/updates" / plan["id"] / "lock.yaml")
        self.assertEqual(candidate["scaffold"]["version"], "1")
        baseline = read_json(study / ".allagma/scaffold-baseline.json")
        migration = plan_migration(study, {"from": "1", "to": "2", "answers": baseline["answers"],
                                          "reason": "Explicit scaffold change", "files": {"LOG.md": "Study log\n"}})
        apply_migration(study, migration["id"])
        with self.assertRaisesRegex(AllagmaError, "Scaffold changed"):
            b.reconcile_update(study, plan["id"])

    def test_partial_analysis_recovers_interrupted_attempt_before_manifest(self):
        study = create_toy(ROOT, self.work / "study")
        c.start_campaign(study, "partial")
        c.run_campaign(study, "partial", stop_after=4)
        result = subprocess.run([sys.executable, "-m", "allagma", "campaign", "run",
                                 "--study", str(study), "--campaign", "partial", "--crash-after-start"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 86, result.stderr)
        c.analyze_campaign(study, "partial", allow_partial=True)
        manifest = read_json(study / "campaigns/partial/analyses/a001/raw-manifest.json")
        self.assertEqual(len(manifest["runs"]), 5)
        self.assertIn("interrupted", [item["reason"] for item in manifest["exclusions"]])

    def test_new_analysis_does_not_inherit_review_assurance(self):
        study = create_toy(ROOT, self.work / "study")
        c.start_campaign(study, "partial")
        c.run_campaign(study, "partial", stop_after=4)
        c.analyze_campaign(study, "partial", allow_partial=True)
        c.audit_campaign(study, "partial")
        c.analyze_campaign(study, "partial", analysis_id="a002", allow_partial=True)
        state = read_json(study / "campaigns/partial/state.json")
        self.assertEqual(state["assurance"], "unreviewed")

    def test_review_retry_preserves_incomplete_review_directory(self):
        study = create_toy(ROOT, self.work / "study")
        c.start_campaign(study, "partial")
        c.run_campaign(study, "partial", stop_after=4)
        c.analyze_campaign(study, "partial", allow_partial=True)
        orphan = study / "campaigns/partial/analyses/a001/reviews/review-001/input.json"
        write_json(orphan, {"interrupted_review": "retained"})
        result = c.audit_campaign(study, "partial")
        self.assertEqual(result["verdict"], "pass")
        self.assertIn("review-002/record.json", result["review"]["path"])
        self.assertEqual(read_json(orphan), {"interrupted_review": "retained"})

    def test_worker_cleans_descendants_after_leader_exits(self):
        # A normal parent exit must not leave a descendant producing late data.
        descendant = "from pathlib import Path; import time; time.sleep(0.4); Path('late').write_text('escaped'); time.sleep(3)"
        leader = ("import subprocess,sys; from pathlib import Path; "
                  f"p=subprocess.Popen([sys.executable,'-c',{descendant!r}]); "
                  "Path('pid').write_text(str(p.pid))")
        try:
            c._execute([sys.executable, "-c", leader], self.work,
                       self.work / "stdout.txt", self.work / "stderr.txt", 0.15)
            time.sleep(0.6)
            self.assertFalse((self.work / "late").exists(), "Descendant survived the completed worker")
        finally:
            if (self.work / "pid").exists():
                try:
                    os.kill(int((self.work / "pid").read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_helper_timeout_cleans_descendants(self):
        descendant = "from pathlib import Path; import time; time.sleep(0.4); Path('late').write_text('escaped'); time.sleep(3)"
        leader = ("import subprocess,sys,time; from pathlib import Path; "
                  f"p=subprocess.Popen([sys.executable,'-c',{descendant!r}]); "
                  "Path('pid').write_text(str(p.pid)); time.sleep(3)")
        try:
            with self.assertRaises(AllagmaError):
                c._run_helper([sys.executable, "-c", leader], self.work, timeout=0.15)
            time.sleep(0.6)
            self.assertFalse((self.work / "late").exists(), "Helper timeout left a descendant running")
        finally:
            if (self.work / "pid").exists():
                try:
                    os.kill(int((self.work / "pid").read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_worker_escalates_for_descendant_ignoring_termination(self):
        descendant = ("from pathlib import Path; import signal,time; "
                      "signal.signal(signal.SIGTERM, signal.SIG_IGN); Path('ready').touch(); "
                      "time.sleep(0.7); Path('late').touch(); time.sleep(3)")
        leader = ("import subprocess,sys,time\nfrom pathlib import Path\n"
                  f"p=subprocess.Popen([sys.executable,'-c',{descendant!r}])\n"
                  "Path('pid').write_text(str(p.pid))\n"
                  "while not Path('ready').exists(): time.sleep(0.01)\n")
        try:
            c._execute([sys.executable, "-c", leader], self.work,
                       self.work / "stdout.txt", self.work / "stderr.txt", 0.5)
            time.sleep(0.8)
            self.assertFalse((self.work / "late").exists())
        finally:
            if (self.work / "pid").exists():
                try:
                    os.kill(int((self.work / "pid").read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass
