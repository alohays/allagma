"""Preparation is offline; no native authentication or model call occurs."""
from pathlib import Path
import tempfile
import unittest

from allagma import bundles,research,resources
from allagma.files import AllagmaError,read_json

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

    def test_unbounded_or_insufficient_resource_policy_is_rejected(self):
        self.profile["budgets_seconds"]["compute"]=float("inf")
        with self.assertRaises(AllagmaError):self.prepare()
        self.profile["budgets_seconds"]["compute"]=60
        self.profile["storage_limit_bytes"]=100
        with self.assertRaisesRegex(AllagmaError,"storage ceiling"):self.prepare()


if __name__=="__main__":unittest.main()
