import copy
from pathlib import Path
import shutil
import subprocess
import sys

from allagma import bundles as b
from allagma.campaigns import start_campaign, run_campaign
from allagma.demo import create_toy
from allagma.files import AllagmaError, file_hash, inventory, read_json, write_json, write_text
from allagma.migrations import plan_migration, apply_migration, rollback_migration, recover_migration
from conformance.support import ROOT, WorkspaceTest


def new_release(source, *, retire=False):
    metadata = read_json(source / "release.json")
    metadata.update(release="0.3.0", release_tag="v0.3.0")
    write_json(source / "release.json", metadata)
    if retire:
        for recipe in (source / "recipes").glob("*/recipe.json"):
            value = read_json(recipe); value["roles"]["context"] = "context/full-record"; write_json(recipe, value)
        path = source / "methods/allagma-context-active-brief/module.yaml"
        value = read_json(path); value["lifecycle"] = "retired"; value["replacement"] = {"id":"context/full-record","migration":"select full record explicitly","earliest_retirement":"0.3.0","reason":"fixture retirement following a simulated coexistence release"}; write_json(path, value)
        path = source / "methods/allagma-context-full-record/module.yaml"
        value = read_json(path); value["lifecycle"] = "stable"; write_json(path, value)
    else:
        path = source / "methods/allagma-context-active-brief/SKILL.md"
        path.write_text(path.read_text() + "\nCompatible clarification used by the update fixture.\n")


class Versions(WorkspaceTest):
    def toy(self, source=ROOT):
        self.study = create_toy(source, self.work / "study")
        return self.study

    def adopt(self, source):
        plan = b.plan_update(source, self.study)
        b.reconcile_update(self.study, plan["id"])
        b.validate_update(self.study, plan["id"])
        b.adopt_update(self.study, plan["id"])
        return plan

    def test_existing_entrypoints_are_preserved_and_namespaced(self):
        study = self.work / "study"
        for name in ("AGENTS.md", "CLAUDE.md", "ALLAGMA.md", ".agents/skills/allagma-scope/SKILL.md"):
            write_text(study / name, "User content\n")
        lock = b.initialize(ROOT, study)
        for name in ("AGENTS.md", "CLAUDE.md", "ALLAGMA.md", ".agents/skills/allagma-scope/SKILL.md"):
            self.assertEqual((study / name).read_text(), "User content\n")
        owner = b.check_ownership(study)
        self.assertEqual(owner["mapping"]["generic"], ".allagma/entrypoints/ALLAGMA.md")
        self.assertNotEqual(owner["mapping"]["codex:research/scope"], ".agents/skills/allagma-scope/SKILL.md")
        self.assertFalse((study / ".codex/config.toml").exists())

    def test_export_is_closed_and_same_across_hosts(self):
        study = self.toy()
        lock = b.verify_study(study)
        owner = b.check_ownership(study)
        for host in ("codex", "claude-code"):
            self.assertIn("context/active-brief", (study / owner["mapping"][host + ":context/active-brief"]).read_text())
        self.assertTrue((b.bundle_path(study, lock) / "contracts/StudySpec.schema.json").is_file())
        with self.assertRaises(AllagmaError):
            altered = copy.deepcopy(lock); altered["release"] = "latest"; b.verify_lock(study, altered)

    def test_campaign_start_dispatches_to_the_pinned_helper(self):
        source = self.source_copy(); study = self.toy(source)
        implementation = source / "allagma/campaigns.py"
        implementation.write_text(implementation.read_text().replace(
            'def start_campaign(study, campaign):',
            'def start_campaign(study, campaign):\n    raise RuntimeError("New central implementation leaked")'))
        result = subprocess.run([sys.executable, str(source / "tools/allagma.py"), "campaign", "start", "--study", str(study), "--campaign", "pinned-start"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((study / "campaigns/pinned-start/study.json").exists())

    def test_resealed_lock_cannot_misidentify_module_or_release(self):
        study = self.toy(); lock = b.verify_study(study)
        for field in ("release", "module"):
            altered = copy.deepcopy(lock)
            if field == "release": altered["release"] = "latest"
            else: altered["modules"]["context/active-brief"]["revision"] = "sha256:" + "0" * 64
            with self.assertRaises(AllagmaError):
                b.verify_lock(study, b.seal_lock(altered))

    def test_rollback_preserves_unadopted_intent_edits(self):
        source = self.source_copy(); study = self.toy(source); new_release(source)
        plan = self.adopt(source)
        intent = read_json(study / "allagma.yaml"); intent["settings"]["language"] = "French"; write_json(study / "allagma.yaml", intent)
        with self.assertRaisesRegex(AllagmaError, "Post-update local edit"):
            b.rollback(study, plan["id"])
        self.assertEqual(read_json(study / "allagma.yaml"), intent)

    def test_central_edits_and_profiles_do_not_change_a_campaign(self):
        source = self.source_copy()
        study = self.toy(source)
        start_campaign(study, "frozen")
        entry = b.resolve_entry(study, "context", "frozen")
        snapshot = (study / "campaigns/frozen/lock.yaml").read_bytes()
        new_release(source)
        profile = read_json(study / "profiles/study.json"); profile["settings"]["language"] = "Korean"; write_json(study / "profiles/study.json", profile)
        self.assertEqual(b.resolve_entry(study, "context", "frozen"), entry)
        self.assertEqual((study / "campaigns/frozen/lock.yaml").read_bytes(), snapshot)
        with self.assertRaisesRegex(AllagmaError, "Configuration changed"):
            b.verify_study(study)
        result = run_campaign(study, "frozen", stop_after=1)
        self.assertEqual(result["execution_status"], "paused")

    def test_generated_bundle_and_entrypoint_edits_block_updates(self):
        for area in ("bundle", "entrypoint"):
            with self.subTest(area=area):
                study = create_toy(ROOT, self.work / area)
                lock = b.verify_study(study)
                path = b.bundle_path(study, lock) / "methods/allagma-scope/SKILL.md" if area == "bundle" else study / "ALLAGMA.md"
                path.write_text(path.read_text() + "\nLocal change\n")
                with self.assertRaises(AllagmaError):
                    b.plan_update(ROOT, study)
                self.assertIn("Local change", path.read_text())

    def test_plan_is_read_only_to_active_files_and_detects_late_changes(self):
        source = self.source_copy(); self.toy(source)
        before = (self.study / ".allagma/lock.yaml").read_bytes()
        new_release(source)
        plan = b.plan_update(source, self.study)
        self.assertEqual((self.study / ".allagma/lock.yaml").read_bytes(), before)
        write_json(self.study / "overrides/settings.json", {"language": "French"})
        with self.assertRaisesRegex(AllagmaError, "Configuration changed after"):
            b.reconcile_update(self.study, plan["id"])

    def test_update_retirement_historical_resume_and_full_rollback(self):
        source = self.source_copy(); study = self.toy(source)
        start_campaign(study, "old")
        run_campaign(study, "old", stop_after=1)
        old = b.verify_study(study)
        old_entry = b.resolve_entry(study, "context", "old")
        domain = inventory(study / "domain")
        write_json(study / "overrides/settings.json", {"language": "French"})
        new_release(source, retire=True)
        plan = self.adopt(source)
        new = b.verify_study(study)
        self.assertNotIn("context/active-brief", new["modules"])
        self.assertEqual(b.resolve_entry(study, "context", "old"), old_entry)
        self.assertEqual(run_campaign(study, "old", stop_after=1)["execution_status"], "paused")
        self.assertEqual(inventory(study / "domain"), domain)
        result = b.rollback(study, plan["id"])
        self.assertEqual(b.verify_study(study)["lock_id"], old["lock_id"])
        self.assertEqual(read_json(study / "overrides/settings.json"), {})
        self.assertTrue(b.bundle_path(study, new).exists())

    def test_adoption_requires_validation_and_a_campaign_boundary(self):
        source = self.source_copy(); study = self.toy(source); new_release(source)
        plan = b.plan_update(source, study)
        with self.assertRaisesRegex(AllagmaError, "Validate"):
            b.adopt_update(study, plan["id"])
        b.reconcile_update(study, plan["id"]); b.validate_update(study, plan["id"])
        start_campaign(study, "running")
        state = read_json(study / "campaigns/running/state.json"); state["execution_status"] = "running"; write_json(study / "campaigns/running/state.json", state)
        with self.assertRaisesRegex(AllagmaError, "boundary"):
            b.adopt_update(study, plan["id"])

    def test_interrupted_adoption_restores_the_preimage(self):
        source = self.source_copy(); study = self.toy(source); new_release(source)
        before = b.verify_study(study)
        plan = b.plan_update(source, study); b.reconcile_update(study, plan["id"]); b.validate_update(study, plan["id"])
        with self.assertRaisesRegex(AllagmaError, "Injected"):
            b.adopt_update(study, plan["id"], fault="after-first-write")
        with self.assertRaisesRegex(AllagmaError, "transaction"):
            b.verify_study(study)
        self.assertTrue(b.recover_update(study)["recovered"])
        self.assertEqual(b.verify_study(study)["lock_id"], before["lock_id"])
        b.adopt_update(study, plan["id"])
        self.assertNotEqual(b.verify_study(study)["lock_id"], before["lock_id"])

    def test_local_variant_is_snapshotted_and_source_edits_are_detected(self):
        study = self.toy()
        variant = study / "modules-local/allagma-context-custom"
        shutil.copytree(ROOT / "methods/allagma-context-active-brief", variant)
        path = variant / "SKILL.md"; path.write_text(path.read_text().replace("name: allagma-context-active-brief", "name: allagma-context-custom"))
        meta = read_json(variant / "module.yaml"); meta.update(id="context/custom", lifecycle="experimental"); write_json(variant / "module.yaml", meta)
        intent = read_json(study / "allagma.yaml")
        intent.update(local_modules=[{"id":"context/custom","path":"modules-local/allagma-context-custom","base":"context/active-brief","scope":"method"}],allow_experimental=True)
        intent["roles"]["context"] = "context/custom"; write_json(study / "allagma.yaml", intent)
        self.adopt(ROOT)
        lock = b.verify_study(study)
        self.assertEqual(b.resolve_entry(study, "context")["module_id"], "context/custom")
        path.write_text(path.read_text() + "\nUser edit\n")
        with self.assertRaisesRegex(AllagmaError, "Configuration changed"):
            b.verify_study(study)
        b.verify_lock(study, lock)

    def test_scaffold_three_way_migration_and_inverse(self):
        study = self.toy(); lock_bytes = (study / ".allagma/lock.yaml").read_bytes()
        baseline = read_json(study / ".allagma/scaffold-baseline.json")
        spec = {"from":"1","to":"2","answers":baseline["answers"],"reason":"Add a study log","files":{"STUDY-LOG.md":"# Study log\n"}}
        plan = plan_migration(study, spec); apply_migration(study, plan["id"])
        self.assertEqual((study / "STUDY-LOG.md").read_text(), "# Study log\n")
        self.assertEqual((study / ".allagma/lock.yaml").read_bytes(), lock_bytes)
        rollback_migration(study, plan["id"])
        self.assertFalse((study / "STUDY-LOG.md").exists())
        self.assertEqual(read_json(study / ".allagma/scaffold-baseline.json"), baseline)

    def test_scaffold_conflicts_and_post_migration_edits_are_preserved(self):
        study = self.toy(); baseline = read_json(study / ".allagma/scaffold-baseline.json")
        write_text(study / "README.md", "My research notes\n")
        spec = {"from":"1","to":"2","answers":baseline["answers"],"reason":"Fixture update","files":{"README.md":"New template\n"}}
        plan = plan_migration(study, spec)
        self.assertEqual(plan["conflicts"], ["README.md"])
        with self.assertRaises(AllagmaError): apply_migration(study, plan["id"])
        self.assertEqual((study / "README.md").read_text(), "My research notes\n")
        spec["files"] = {"NEW.md":"Base\n"}; plan = plan_migration(study, spec); apply_migration(study, plan["id"])
        write_text(study / "NEW.md", "New local work\n")
        with self.assertRaisesRegex(AllagmaError, "post-migration"):
            rollback_migration(study, plan["id"])

    def test_interrupted_multi_file_migration_is_recoverable(self):
        study = self.toy(); baseline = read_json(study / ".allagma/scaffold-baseline.json")
        spec = {"from":"1","to":"2","answers":baseline["answers"],"reason":"Two-file migration", "files":{"ONE.md":"One\n","TWO.md":"Two\n"}}
        plan = plan_migration(study, spec)
        with self.assertRaisesRegex(AllagmaError, "Injected"):
            apply_migration(study, plan["id"], fault="after-first-write")
        with self.assertRaisesRegex(AllagmaError, "Unfinished scaffold migration"):
            b.verify_study(study)
        self.assertTrue(recover_migration(study, plan["id"])["recovered"])
        self.assertFalse((study / "ONE.md").exists())
        self.assertFalse((study / "TWO.md").exists())
        self.assertEqual(read_json(study / ".allagma/scaffold-baseline.json"), baseline)
        apply_migration(study, plan["id"])
        self.assertTrue((study / "TWO.md").exists())
        with self.assertRaisesRegex(AllagmaError, "Injected inverse"):
            rollback_migration(study, plan["id"], fault="after-first-write")
        self.assertTrue(recover_migration(study, plan["id"])["recovered"])
        self.assertTrue((study / "ONE.md").exists())
        rollback_migration(study, plan["id"])
        self.assertFalse((study / "TWO.md").exists())
