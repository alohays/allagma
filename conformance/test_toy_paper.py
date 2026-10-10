"""Exercise the study-owned publication helper against a real offline toy."""
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import unittest

from allagma import papers, references
from allagma.demo import toy_workflow
from allagma.files import AllagmaError, file_hash, read_json, write_json
from allagma.research import _load

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/toy-study/paper"
prepare = _load("toy_paper_prepare", EXAMPLE / "prepare.py").prepare
record_review = _load("toy_paper_record_review", EXAMPLE / "record_review.py").record_review


def snapshot(root):
    return {p.relative_to(root).as_posix(): (file_hash(p), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


def fixture_judgments(study, config):
    return {"reviewer": "Conformance fixture; no scientific approval",
            "reviewed_content_sha256": papers.review_fingerprint(study, config),
            **{kind: {"verdict": "accept", "scope": "Review-record mechanics only.",
                      "observations": ["Synthetic review input for the conformance test, not a reviewer judgment."]}
               for kind in ("scientific", "humanizer")}}


class ToyPaperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.original = cls.root / "completed toy"
        toy_workflow(ROOT, cls.original)

    def setUp(self):
        self.study = self.root / self._testMethodName / "study with spaces"
        shutil.copytree(self.original, self.study)
        self.before = snapshot(self.study)
        self.authors = read_json(EXAMPLE / "authors.anonymous.json")
        self.publication = self.study / "publications/toy-paper-r1"

    def prepared(self):
        prepare(self.study, "toy-paper-r1", self.authors)
        return read_json(self.publication / "paper.json")

    def assertOriginalsPreserved(self):
        current = snapshot(self.study)
        self.assertEqual(self.before, {key: current[key] for key in self.before})
        self.assertTrue(all(key.startswith("publications/") for key in current.keys() - self.before.keys()))

    def test_prepare_binds_real_results_and_requires_explicit_review(self):
        config = self.prepared()
        self.assertEqual(config["authors"], self.authors)
        self.assertEqual(read_json(self.study / "paper.json"), {"format": papers.FORMAT, "output": "report"})
        literature = references.validate_map(read_json(self.publication / "references/map.json"), require_review=True)
        self.assertEqual((literature["mode"], literature["records"]), ("provided-only", []))
        with self.assertRaisesRegex(AllagmaError, "Retain a scoped scientific review"):
            papers.validate(self.study, config)
        record_review(self.study, "toy-paper-r1", "paper.json", "r1", fixture_judgments(self.study, config))
        checked = papers.validate(self.study, read_json(self.publication / "reviews/r1/paper.json"))
        summary = read_json(self.study / config["evidence"]["summary"]["path"])
        self.assertEqual(checked["values"]["difference"], format(summary["difference"], ".8f"))
        self.assertEqual(checked["claims"]["average"], read_json(self.study / config["evidence"]["toy-claims"]["path"])[0]["text"])
        self.assertIn("contradicted", checked["claims"]["universal"])
        self.assertEqual(checked["authors_tex"], "Anonymous draft")
        self.assertOriginalsPreserved()

    def test_pending_or_unattributed_review_cannot_be_recorded(self):
        config = self.prepared()
        pending = read_json(self.publication / "review-input.json")
        for case in (pending, {**fixture_judgments(self.study, config), "reviewer": ""},
                     {**fixture_judgments(self.study, config), "humanizer": {"verdict": "pending"}}):
            with self.subTest(case=case), self.assertRaises(AllagmaError):
                record_review(self.study, "toy-paper-r1", "paper.json", "r1", case)
        self.assertFalse((self.publication / "reviews").exists())
        self.assertOriginalsPreserved()

    def test_changed_section_invalidates_old_judgments_and_new_review_preserves_old_revision(self):
        config = self.prepared()
        old_input = fixture_judgments(self.study, config)
        record_review(self.study, "toy-paper-r1", "paper.json", "r1", old_input)
        reviewed = read_json(self.publication / "reviews/r1/paper.json")
        original_publication = snapshot(self.publication)
        changed = deepcopy(reviewed)
        new_section = self.publication / "sections/discussion-r2.tex"
        new_section.write_text((self.study / changed["sections"]["discussion"]).read_text() +
                               "This publication reuses the same completed experiment.\n")
        changed["sections"]["discussion"] = new_section.relative_to(self.study).as_posix()
        write_json(self.publication / "paper-r2.json", changed)
        with self.assertRaisesRegex(AllagmaError, "scientific review is stale"):
            papers.validate(self.study, changed)
        with self.assertRaisesRegex(AllagmaError, "Review input is stale"):
            record_review(self.study, "toy-paper-r1", "paper-r2.json", "r2", old_input)
        self.assertFalse((self.publication / "reviews/r2").exists())
        new_input = fixture_judgments(self.study, changed)
        record_review(self.study, "toy-paper-r1", "paper-r2.json", "r2", new_input)
        self.assertEqual(papers.validate(self.study, read_json(self.publication / "reviews/r2/paper.json"))["status"], "pass")
        self.assertEqual(read_json(self.publication / "reviews/r2/scientific.json")["supersedes"],
                         reviewed["evidence"][reviewed["review"]["scientific"]["record"]])
        current_publication = snapshot(self.publication)
        self.assertEqual(original_publication, {key: current_publication[key] for key in original_publication})
        self.assertOriginalsPreserved()

    def test_no_overwrite_or_escape_for_publications_or_reviews(self):
        config = self.prepared()
        before = snapshot(self.study)
        for revision in ("toy-paper-r1", "../escape"):
            with self.subTest(revision=revision), self.assertRaises(AllagmaError):
                prepare(self.study, revision, self.authors)
        self.assertEqual(before, snapshot(self.study))
        notes = fixture_judgments(self.study, config)
        record_review(self.study, "toy-paper-r1", "paper.json", "r1", notes)
        before = snapshot(self.study)
        for configuration, revision in (("paper.json", "r1"), ("../paper.json", "r2"), ("paper.json", "../r2")):
            with self.subTest(configuration=configuration, revision=revision), self.assertRaises(AllagmaError):
                record_review(self.study, "toy-paper-r1", configuration, revision, notes)
        self.assertEqual(before, snapshot(self.study))

    def test_changed_retained_evidence_is_refused_before_writing(self):
        summary = self.study / "campaigns/toy-v1/analyses/a001/outputs/summary.json"
        data = read_json(summary)
        data["difference"] = 100
        write_json(summary, data)
        before = snapshot(self.study)
        with self.assertRaisesRegex(AllagmaError, "Missing or changed evidence"):
            self.prepared()
        self.assertEqual(before, snapshot(self.study))
        self.assertFalse(self.publication.exists())

    def test_partial_or_adapted_study_and_missing_attribution_are_refused(self):
        analysis = self.study / "campaigns/toy-v1/analyses/a001/record.json"
        data = read_json(analysis)
        data["configuration"]["partial"] = True
        write_json(analysis, data)
        with self.assertRaisesRegex(AllagmaError, "Complete the toy"):
            self.prepared()
        protocol = self.study / "campaigns/toy-v1/protocol.json"
        data = read_json(protocol)
        data["revision"] = "adapted"
        write_json(protocol, data)
        with self.assertRaisesRegex(AllagmaError, "default toy protocol"):
            self.prepared()
        with self.assertRaisesRegex(AllagmaError, "attribution"):
            prepare(self.study, "toy-paper-r1", {"mode": "anonymous", "entries": []})
        self.assertFalse(self.publication.exists())


if __name__ == "__main__":
    unittest.main()
