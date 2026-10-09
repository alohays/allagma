"""Preparation is offline; no native authentication or model call occurs."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from allagma import bundles,references,research,resources
from allagma.files import AllagmaError,file_hash,read_json,write_json
from conformance.test_references import reference_record

ROOT=Path(__file__).resolve().parents[1]


class ResearchPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);self.materials=self.root/"materials";self.materials.mkdir()
        (self.materials/"source.txt").write_text("Supplied source material.\n")
        self.brief=self.root/"brief.md";self.brief.write_text("Investigate a bounded, testable question.\n")
        self.profile={"format":resources.FORMAT,"budgets_seconds":{"compute":60,"setup":30},
            "command_timeout_seconds":{"compute":10,"setup":10},"attempt_limit":6,
            "rss_limit_bytes":200_000_000,"storage_limit_bytes":20_000_000,"file_limit_bytes":1_000_000,
            "poll_seconds":.05,"terminate_grace_seconds":.1}

    def prepare(self,**kwargs):
        return research.prepare(ROOT,self.root/"study",self.root/"control",brief=self.brief,
            materials=self.materials,profile=self.profile,**kwargs)

    def test_brief_materials_limits_and_portable_lock_are_retained(self):
        value=self.prepare(study_id="new-question")
        study=self.root/"study";control=self.root/"control"
        self.assertEqual((study/"inputs/BRIEF.md").read_bytes(),self.brief.read_bytes())
        self.assertEqual((study/"inputs/materials/source.txt").read_bytes(),(self.materials/"source.txt").read_bytes())
        self.assertEqual(bundles.verify_study(study)["lock_id"],value["lock_id"])
        self.assertEqual(resources.summary(control/"resources")["attempts"],0)
        self.assertFalse((study/".codex/config.toml").exists())
        self.assertFalse((control/"sessions").exists())
        self.assertEqual(research.status(study,control)["prepared"]["study_id"],"new-question")

    def test_material_links_and_nested_output_are_rejected_before_mutation(self):
        (self.materials/"linked").symlink_to(self.brief)
        with self.assertRaisesRegex(AllagmaError,"links"):
            self.prepare()
        self.assertFalse((self.root/"study").exists())
        (self.materials/"linked").unlink()
        with self.assertRaisesRegex(AllagmaError,"inside the materials"):
            research.prepare(ROOT,self.materials/"study",self.root/"control",brief=self.brief,
                             materials=self.materials,profile=self.profile)

    def test_reprepare_preserves_existing_workspace(self):
        self.prepare();path=self.root/"study/RESEARCH.md";old=path.read_bytes()
        with self.assertRaises(AllagmaError):self.prepare()
        self.assertEqual(path.read_bytes(),old)

    def test_baseline_has_identical_materials_but_no_methods(self):
        self.prepare(install_workflow=False)
        study=self.root/'study'
        self.assertFalse((study/'.allagma').exists())
        self.assertFalse((study/'.agents').exists())
        self.assertEqual((study/'inputs/BRIEF.md').read_bytes(),self.brief.read_bytes())
        self.assertTrue((study/'inputs/compute.py').exists())

    def test_unbounded_or_insufficient_resource_policy_is_rejected(self):
        self.profile["budgets_seconds"]["compute"]=float("inf")
        with self.assertRaises(AllagmaError):self.prepare()
        self.profile["budgets_seconds"]["compute"]=60
        self.profile["storage_limit_bytes"]=100
        with self.assertRaisesRegex(AllagmaError,"storage ceiling"):self.prepare()

    def dossier(self, note_bytes):
        directory = self.root / "references"
        value = references.initialize(directory, question="Test preparation storage admission.")
        record = reference_record()
        record["note"] = "notes/reading.md"
        (directory / "notes").mkdir()
        (directory / record["note"]).write_bytes(b"x" * note_bytes)
        value = references.add_record(value, record, directory=directory)
        write_json(directory / "map.json", value)
        return directory

    def test_oversized_reference_dossier_is_refused_before_workspace_creation(self):
        directory = self.dossier(3_000_000)
        self.profile["storage_limit_bytes"] = 2_000_000
        with self.assertRaisesRegex(AllagmaError, "storage ceiling"):
            self.prepare(reference_directory=directory)
        self.assertFalse((self.root / "study").exists())
        self.assertFalse((self.root / "control").exists())

    def test_admission_counts_working_dossier_only_when_workflow_is_installed(self):
        directory = self.dossier(800_000)
        self.profile["storage_limit_bytes"] = 2_500_000
        with self.assertRaisesRegex(AllagmaError, "storage ceiling"):
            self.prepare(reference_directory=directory)
        self.assertFalse((self.root / "study").exists())
        self.prepare(reference_directory=directory, install_workflow=False)
        self.assertFalse((self.root / "study/references").exists())
        self.assertLess(resources.storage_bytes(self.root / "study"), self.profile["storage_limit_bytes"])

    def test_both_admitted_dossier_copies_match_within_the_ceiling(self):
        directory = self.dossier(300_000)
        self.profile["storage_limit_bytes"] = 2_000_000
        self.prepare(reference_directory=directory)
        study = self.root / "study"
        record = references.verify_snapshot(study / "inputs/references")
        for name, expected in record["files"].items():
            self.assertEqual(file_hash(study / "references" / name), expected)
        self.assertLess(resources.storage_bytes(study), self.profile["storage_limit_bytes"])

    def test_dossier_growth_after_admission_cannot_exceed_the_copy_plan(self):
        directory = self.dossier(100)
        self.profile["storage_limit_bytes"] = 2_000_000
        snapshot = references.snapshot

        def grow_then_copy(*args, **kwargs):
            (directory / "notes/reading.md").write_bytes(b"x" * 3_000_000)
            return snapshot(*args, **kwargs)

        with patch.object(references, "snapshot", side_effect=grow_then_copy):
            with self.assertRaisesRegex(AllagmaError, "changed|storage ceiling"):
                self.prepare(reference_directory=directory)
        self.assertLess(resources.storage_bytes(self.root / "study"), self.profile["storage_limit_bytes"])
        self.assertFalse((self.root / "control").exists())


if __name__=="__main__":unittest.main()
