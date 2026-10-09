"""Offline record checks; fixture metadata is not a scientific qualification."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from allagma import references
from allagma.files import AllagmaError, read_json, write_json


def reference_record():
    return {"id": "Fixture2026", "metadata": {
        "title": "A test of evidence boundaries", "authors": ["Example, Alice"],
        "year": 2026, "url": "https://example.org/paper", "doi": "10.1234/fixture"},
        "roles": ["primary", "baseline"], "relevance": "Fixture for record validation.",
        "limitations": ["Invented fixture, not a real paper."],
        "consequences": {phase: "Exercise the test boundary." for phase in references.PHASES},
        "bibliography": {"status": "verified", "checked_at": "2026-10-09", "sources": [{
            "url": "https://example.org/paper", "locator": "Fixture title page",
            "fields": ["title", "authors", "year"]}]},
        "passages": [{"id": "scope", "locator": "Fixture section 1", "summary": "Tests are scoped.",
            "claim": "Record validation is not a scientific review.", "assessment": "supports",
            "limitation": "Fixture assertion only.", "url": "https://example.org/paper"}]}


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.refs = self.root / "references"
        self.value = references.initialize(self.refs, question="How do records preserve evidence scope?")

    def test_offline_empty_map_is_honest_and_has_no_invented_bibliography(self):
        self.assertEqual(references.refresh(self.refs, require_review=True)["records"], 0)
        self.assertIn("No external literature search", (self.refs / "INDEX.md").read_text())
        self.assertEqual((self.refs / "citations.bib").read_text().strip(), "")
        self.value["coverage"]["limitations"] = []
        with self.assertRaisesRegex(AllagmaError, "coverage limitations"):
            references.validate_map(self.value)

    def test_deduplication_preserves_key_and_rejects_conflicting_metadata(self):
        record = reference_record()
        value = references.add_record(self.value, record)
        incoming = deepcopy(record)
        incoming["id"] = "AnotherKey"
        incoming["roles"].append("competing")
        value = references.add_record(value, incoming)
        self.assertEqual(len(value["records"]), 1)
        self.assertEqual(value["records"][0]["id"], "Fixture2026")
        self.assertIn("competing", value["records"][0]["roles"])
        incoming["metadata"]["year"] = 2025
        with self.assertRaisesRegex(AllagmaError, "conflicting year"):
            references.add_record(value, incoming)
        value["records"].append(record)
        with self.assertRaises(AllagmaError):
            references.validate_map(value)

    def test_identifiers_normalize_doi_and_arxiv_versions(self):
        record = reference_record()
        record["metadata"]["doi"] = "https://doi.org/10.1234/FIXTURE"
        record["metadata"]["arxiv"] = "https://arxiv.org/abs/2006.11239v2"
        self.assertIn("doi:10.1234/fixture", references.identities(record))
        self.assertIn("arxiv:2006.11239", references.identities(record))
        plain = reference_record()
        merged = references.add_record(references.add_record(self.value, plain), record)
        self.assertEqual(len(merged["records"]), 1)

    def test_same_title_with_different_authors_is_not_silently_conflated(self):
        first = reference_record()
        first["metadata"].pop("doi")
        second = deepcopy(first)
        second["id"] = "DifferentWork"
        second["metadata"]["authors"] = ["Other, Bob"]
        value = references.add_record(references.add_record(self.value, first), second)
        self.assertEqual(len(value["records"]), 2)

    def test_bibliographic_accuracy_does_not_imply_claim_support(self):
        record = reference_record()
        record["passages"][0]["assessment"] = "unassessed"
        value = references.add_record(self.value, record)
        self.assertIn("@misc{Fixture2026", references.bibliography(value))
        with self.assertRaisesRegex(AllagmaError, "critical reading"):
            references.validate_map(value, require_review=True)
        record["bibliography"]["status"] = "unverified"
        value["records"] = [record]
        self.assertNotIn("Fixture2026", references.bibliography(value))

    def test_passage_to_asset_and_phase_decision_links(self):
        record = reference_record()
        passage = record["passages"][0]
        passage.update(asset_id="paper-pdf", sha256="a" * 64)
        value = references.add_record(self.value, record)
        value["decisions"] = [{"phase": "planning", "decision": "Use scoped checks.",
                               "references": ["Fixture2026:scope"]}]
        retrieval = {"assets": [{"id": "paper-pdf", "status": "available", "sha256": "a" * 64}]}
        references.validate_map(value, retrieval=retrieval, require_review=True)
        retrieval["assets"][0]["sha256"] = "b" * 64
        with self.assertRaisesRegex(AllagmaError, "acquired bytes"):
            references.validate_map(value, retrieval=retrieval)
        value["decisions"][0]["references"] = ["unknown:passage"]
        with self.assertRaisesRegex(AllagmaError, "unknown source passage"):
            references.validate_map(value)

    def test_snapshot_contains_selected_notes_and_detects_changes(self):
        record = reference_record()
        record["note"] = "notes/reading.md"
        (self.refs / "notes").mkdir()
        (self.refs / record["note"]).write_text("A critical reading note.\n")
        value = references.add_record(self.value, record, directory=self.refs)
        write_json(self.refs / "map.json", value)
        (self.refs / "unselected.pdf").write_bytes(b"not a real PDF")
        target = self.root / "snapshot"
        result = references.snapshot(self.refs, target, require_review=True)
        self.assertNotIn("unselected.pdf", result["files"])
        references.verify_snapshot(target)
        (target / record["note"]).write_text("Changed\n")
        with self.assertRaisesRegex(AllagmaError, "snapshot changed"):
            references.verify_snapshot(target)

    def test_sources_cannot_leak_credentials_or_escape_notes_directory(self):
        for url in ("file:///private/source", "https://user:password@example.org/x",
                    "https://example.org/x?token=private", "https://example.org/x?X-Amz-Signature=private"):
            with self.assertRaises(AllagmaError):
                references.public_url(url)
        record = reference_record()
        record["note"] = "../outside.md"
        with self.assertRaises(AllagmaError):
            references.add_record(self.value, record, directory=self.refs)

    def test_new_studies_include_reference_index_without_changing_report_defaults(self):
        from allagma import bundles
        root = Path(__file__).resolve().parents[1]
        study = self.root / "study"
        bundles.initialize(root, study)
        self.assertTrue((study / "references/INDEX.md").is_file())
        self.assertEqual(read_json(study / "references/map.json")["mode"], "provided-only")
        entry = bundles.resolve_entry(study, "research/scope")
        self.assertIn("reference-research.md", Path(entry["path"]).read_text())
        self.assertFalse((study / "paper.pdf").exists())

    def test_raw_cache_inside_distributable_source_cannot_enter_a_bundle(self):
        from allagma.bundles import distributable_inventory
        source = self.root / "source"
        raw = source / "nested-cache"
        raw.mkdir(parents=True)
        write_json(raw / ".allagma-reference-cache.json", {"format": "allagma-raw-reference-cache-v1"})
        (raw / "weights.bin").write_bytes(b"Never package raw cached assets")
        with self.assertRaisesRegex(AllagmaError, "Raw reference cache"):
            distributable_inventory(source)


if __name__ == "__main__":
    unittest.main()
