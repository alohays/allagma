"""Paper structure and evidence tests without a TeX or network dependency."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from allagma import papers, references
from allagma.files import AllagmaError, file_hash, read_json, write_json
from allagma.research import _load
from conformance.test_references import reference_record

ROOT = Path(__file__).resolve().parents[1]
adapter = _load("test_arxiv_package", ROOT / "adapters/arxiv/package.py")


def paper_fixture(study):
    study = Path(study)
    refs = study / "references"
    literature = references.initialize(refs, question="A fixture for paper validation.")
    literature = references.add_record(literature, reference_record())
    literature["decisions"] = [{"phase": phase, "decision": "Exercise the declared evidence boundary.",
        "references": ["Fixture2026:scope"]} for phase in references.PHASES]
    write_json(refs / "map.json", literature)
    references.refresh(refs)
    data = {"n": 4, "mean": -.025, "rows": [{"name": "A", "mean": -.025, "interval": [-.1, .05]}]}
    write_json(study / "analysis.json", data)
    (study / "review.md").write_text("Conformance fixture review only, not a scientific qualification.\n")
    sections = {}
    for section in papers.SECTIONS:
        path = study / (section + ".tex")
        text = "This is a conformance fixture, not a research result.\n"
        if section == "introduction":
            text += r"The reference describes the fixture boundary \cite{Fixture2026}." + "\n"
        if section == "results":
            text += r"\AllagmaClaim{effect} The sample count is \AllagmaValue{count}. \AllagmaTable{estimates}" + "\n"
        path.write_text(text)
        sections[section] = path.name
    return {"format": papers.FORMAT, "output": "arxiv", "title": "Evidence boundary fixture", "date": "9 October 2026",
        "authors": {"mode": "named", "entries": [{"name": "Fixture researcher"}],
                    "supplied_by": "conformance fixture", "supplied_at": "2026-10-09"},
        "references": "references", "sections": sections,
        "evidence": {"analysis": {"path": "analysis.json", "sha256": file_hash(study / "analysis.json")},
                     "review": {"path": "review.md", "sha256": file_hash(study / "review.md")}},
        "values": {"count": {"evidence": "analysis", "pointer": "/n", "format": "d"},
                   "mean": {"evidence": "analysis", "pointer": "/mean", "format": ".3f"}},
        "claims": [{"id": "effect", "text": "The fixture mean is {{value:mean}}; its interval contains zero.",
                    "status": "inconclusive", "evidence": [{"id": "analysis", "locator": "#/rows/0"}],
                    "citations": ["Fixture2026:scope"], "limitations": ["Only a structural fixture."]}],
        "figures": [], "tables": [{"id": "estimates", "evidence": "analysis", "pointer": "/rows",
            "caption": "Fixture data only.", "columns": [{"title": "Cell", "pointer": "/name"},
            {"title": "Mean and interval", "pointers": ["/mean", "/interval/0", "/interval/1"],
             "format": ".3f", "pattern": "{0} [{1}, {2}]"}]}],
        "review": {kind: {"status": "complete", "scope": "Fixture structure only.", "record": "review"}
                   for kind in ("scientific", "humanizer")}}


class PaperTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.study = self.root / "study"
        self.study.mkdir()
        self.config = paper_fixture(self.study)

    def test_report_default_never_requires_authors_references_or_tex(self):
        config = papers.default_configuration()
        self.assertEqual(papers.validate(self.root / "missing", config)["status"], "disabled")
        destination = self.root / "no-output"
        self.assertEqual(adapter.build(self.study, config, destination)["status"], "disabled")
        self.assertFalse(destination.exists())

    def test_values_tables_claims_and_citations_resolve_to_retained_evidence(self):
        value = papers.validate(self.study, self.config)
        self.assertEqual(value["values"]["count"], "4")
        self.assertEqual(value["tables"]["estimates"]["rendered_rows"], [["A", "-0.025 [-0.100, 0.050]"]])
        self.assertIn("mean is -0.025", value["claims"]["effect"])
        self.assertEqual(value["citations"], ["Fixture2026"])
        self.assertIn(r"\begin{longtable}", papers.macros(value))

    def test_corrupt_evidence_missing_citations_and_unlocated_claims_fail(self):
        for change in ("digest", "citation", "locator"):
            config = deepcopy(self.config)
            if change == "digest":
                config["evidence"]["analysis"]["sha256"] = "0" * 64
            elif change == "citation":
                config["claims"][0]["citations"] = ["Unknown:passage"]
            else:
                config["claims"][0]["evidence"][0]["locator"] = "#/missing"
            with self.subTest(change=change), self.assertRaises(AllagmaError):
                papers.validate(self.study, config)
        (self.study / "introduction.tex").write_text(r"An unsupported source \cite{Unknown}.")
        with self.assertRaisesRegex(AllagmaError, "unknown manuscript citations"):
            papers.validate(self.study, self.config)

    def test_missing_sections_review_and_external_input_fail(self):
        config = deepcopy(self.config)
        del config["sections"]["limitations"]
        with self.assertRaisesRegex(AllagmaError, "required English paper section"):
            papers.validate(self.study, config)
        config = deepcopy(self.config)
        config["review"]["humanizer"]["status"] = "pending"
        with self.assertRaisesRegex(AllagmaError, "humanizer review"):
            papers.validate(self.study, config)
        (self.study / "methods.tex").write_text(r"\input{/private/cache/paper.tex}")
        with self.assertRaisesRegex(AllagmaError, "declare extra template files"):
            papers.validate(self.study, self.config)

    def test_researcher_configures_authors_without_repository_identity_fallback(self):
        config = deepcopy(self.config)
        config["authors"]["entries"] = [{"name": "allagma"}]
        self.assertEqual(papers.author_tex(config), "allagma")
        config["authors"] = {"mode": "anonymous", "entries": [], "supplied_by": "researcher", "supplied_at": "2026-10-09"}
        self.assertEqual(papers.author_tex(config), "Anonymous draft")
        del config["authors"]["supplied_by"]
        with self.assertRaisesRegex(AllagmaError, "researcher-supplied attribution"):
            papers.author_tex(config)
        write_json(self.study / "inputs/PAPER.json", {**self.config, "authors": {"mode": "anonymous"}})
        with self.assertRaisesRegex(AllagmaError, "protected researcher request"):
            papers.validate(self.study, self.config)

    def test_source_archive_contains_declared_sources_and_no_cache_or_build_outputs(self):
        source = self.root / "source"
        provenance = adapter.assemble(self.study, self.config, source)
        self.assertIn("references.bib", provenance["source_files"])
        self.assertIn("allagma-preprint.sty", provenance["source_files"])
        self.assertIn("anc/evidence/analysis.json", provenance["source_files"])
        self.assertNotIn("main.pdf", provenance["source_files"])
        self.assertFalse(any("cache" in name for name in provenance["source_files"]))
        archive = self.root / "source.tar.gz"
        adapter.archive_sources(source, archive)
        unpacked = adapter.unpack_archive(archive, self.root / "unpacked")
        self.assertEqual((unpacked / "main.tex").read_bytes(), (source / "main.tex").read_bytes())
        self.assertEqual(file_hash(unpacked / "anc/evidence/analysis.json"), self.config["evidence"]["analysis"]["sha256"])
        with self.assertRaisesRegex(AllagmaError, "new paper revision"):
            adapter.assemble(self.study, self.config, source)

    def test_numeric_formatting_cannot_silently_truncate_or_use_missing_values(self):
        with self.assertRaisesRegex(AllagmaError, "cannot truncate"):
            papers.format_value(3.5, "d")
        with self.assertRaisesRegex(AllagmaError, "finite"):
            papers.format_value(float("inf"), ".2f")
        config = deepcopy(self.config)
        config["claims"][0]["text"] = "The value is {{value:missing}}."
        with self.assertRaisesRegex(AllagmaError, "Unknown result value"):
            papers.validate(self.study, config)


if __name__ == "__main__":
    unittest.main()
