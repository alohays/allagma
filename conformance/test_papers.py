"""Paper structure and evidence tests without a TeX or network dependency."""
from copy import deepcopy
from pathlib import Path
import subprocess
import io
import tarfile
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from allagma import papers, references
from allagma.files import AllagmaError, file_hash, inventory, read_json, write_json
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
    config = {"format": papers.FORMAT, "output": "arxiv", "title": "Evidence boundary fixture", "date": "9 October 2026",
        "authors": {"mode": "named", "entries": [{"name": "Fixture researcher"}],
                    "supplied_by": "conformance fixture", "supplied_at": "2026-10-09"},
        "references": "references", "sections": sections,
        "evidence": {"analysis": {"path": "analysis.json", "sha256": file_hash(study / "analysis.json")}},
        "values": {"count": {"evidence": "analysis", "pointer": "/n", "format": "d"},
                   "mean": {"evidence": "analysis", "pointer": "/mean", "format": ".3f"}},
        "claims": [{"id": "effect", "text": "The fixture mean is {{value:mean}}; its interval contains zero.",
                    "status": "inconclusive", "evidence": [{"id": "analysis", "locator": "#/rows/0"}],
                    "citations": ["Fixture2026:scope"], "limitations": ["Only a structural fixture."]}],
        "figures": [], "tables": [{"id": "estimates", "evidence": "analysis", "pointer": "/rows",
            "caption": "Fixture data only.", "columns": [{"title": "Cell", "pointer": "/name"},
            {"title": "Mean and interval", "pointers": ["/mean", "/interval/0", "/interval/1"],
             "format": ".3f", "pattern": "{0} [{1}, {2}]"}]}],
        "review": {kind: {"status": "complete", "scope": "Fixture structure only.", "record": kind}
                   for kind in ("scientific", "humanizer")}}
    bind_reviews(study, config)
    return config


def bind_reviews(study, config):
    for kind in config["review"]:
        path = study / (kind + "-review.json")
        write_json(path, {"format": "allagma-paper-review-v1", "kind": kind,
                         "reviewed_content_sha256": papers.review_fingerprint(study, config),
                         "scope": "Conformance fixture only, not a scientific qualification"})
        config["evidence"][kind] = {"path": path.name, "sha256": file_hash(path)}


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

    def source_bytes(self, source):
        return sum(path.stat().st_size for path in source.rglob("*") if path.is_file())

    def test_complete_source_budget_includes_provenance_and_accepts_exact_limit(self):
        before = inventory(self.study)
        mtimes = {p: p.stat().st_mtime_ns for p in self.study.rglob("*")}
        baseline = self.root / "baseline"
        adapter.assemble(self.study, self.config, baseline)
        total = self.source_bytes(baseline)
        old_limit = total - (baseline / "anc/provenance.json").stat().st_size
        failed = self.root / "failed"
        with patch.object(adapter, "MAX_SOURCE_BYTES", old_limit):
            with self.assertRaisesRegex(AllagmaError, "new paper revision"):
                adapter.assemble(self.study, self.config, failed)
        self.assertTrue(failed.is_dir())
        self.assertEqual(list(failed.iterdir()), [])
        with self.assertRaisesRegex(AllagmaError, "new paper revision"):
            adapter.assemble(self.study, self.config, failed)
        with patch.object(adapter, "MAX_SOURCE_BYTES", total):
            source = self.root / "fitting"
            adapter.assemble(self.study, self.config, source)
            self.assertEqual(self.source_bytes(source), total)
            adapter.archive_sources(source, self.root / "fitting.tar.gz")
            unpacked = adapter.unpack_archive(self.root / "fitting.tar.gz", self.root / "unpacked")
            self.assertEqual(inventory(unpacked), inventory(source))
        self.assertEqual(inventory(self.study), before)
        self.assertEqual({p: p.stat().st_mtime_ns for p in self.study.rglob("*")}, mtimes)

    def test_oversized_declared_copy_is_rejected_before_any_payload_write(self):
        payload = self.study / "retained.txt"
        payload.write_bytes(b"x" * 65536)
        self.config["evidence"]["retained"] = {"path": payload.name, "sha256": file_hash(payload)}
        bind_reviews(self.study, self.config)
        before = inventory(self.study)
        destination = self.root / "oversized"
        with patch.object(adapter, "MAX_SOURCE_BYTES", 32768), \
             patch.object(adapter, "copy_new", wraps=adapter.copy_new) as copies:
            with self.assertRaisesRegex(AllagmaError, "integration ceiling"):
                adapter.assemble(self.study, self.config, destination)
        copies.assert_not_called()
        self.assertEqual(list(destination.iterdir()), [])
        self.assertEqual(inventory(self.study), before)

    def test_changed_copies_after_admission_never_write_unadmitted_payload(self):
        original = self.study / "analysis.json"
        data = original.read_bytes()
        for index, changed in enumerate((data + b" " * 65536, data[:-1], b" " + data[1:])):
            original.write_bytes(data)
            destination = self.root / f"changed-{index}"
            write = adapter.SourcePlan.write

            def mutate_then_write(plan, target):
                original.write_bytes(changed)
                write(plan, target)

            with self.subTest(change=index), patch.object(adapter.SourcePlan, "write", mutate_then_write):
                with self.assertRaisesRegex(AllagmaError, "changed after admission"):
                    adapter.assemble(self.study, self.config, destination)
            self.assertTrue(destination.is_dir())
            self.assertFalse((destination / "anc/evidence/analysis.json").exists())
            self.assertEqual(original.read_bytes(), changed)
            before = inventory(destination)
            original.write_bytes(data)
            with self.assertRaisesRegex(AllagmaError, "new paper revision"):
                adapter.assemble(self.study, self.config, destination)
            self.assertEqual(inventory(destination), before)
        original.write_bytes(data)

    def test_growth_between_stat_and_read_is_bounded_and_rejected(self):
        source = self.study / "analysis.json"
        original = source.read_bytes()
        size = len(original)
        target = self.root / "copy.json"
        real_size = adapter.source_size

        def grow_after_stat(path):
            admitted = real_size(path)
            with source.open("ab") as stream:
                stream.write(b" " * 65536)
            return admitted

        with patch.object(adapter, "source_size", side_effect=grow_after_stat):
            with self.assertRaisesRegex(AllagmaError, "changed after admission"):
                adapter.copy_new(source, target, size=size, expected=file_hash(source))
        self.assertFalse(target.exists())
        self.assertEqual(source.stat().st_size, size + 65536)

    def test_reader_retains_traversal_type_duplicate_and_expansion_guards(self):
        for case in ("traversal", "symlink", "duplicate", "bytes", "count"):
            archive_path = self.root / f"{case}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                member = tarfile.TarInfo("../escaped.txt" if case == "traversal" else "source.txt")
                member.size = 1
                if case == "symlink":
                    member.type, member.linkname = tarfile.SYMTYPE, "target.txt"
                archive.addfile(member, io.BytesIO(b"x"))
                if case == "duplicate":
                    archive.addfile(member, io.BytesIO(b"x"))
            with self.subTest(case=case), patch.object(adapter, "MAX_SOURCE_BYTES", 0 if case == "bytes" else 1024), \
                 patch.object(adapter, "MAX_SOURCE_FILES", 0 if case == "count" else 1000):
                with self.assertRaises(AllagmaError):
                    adapter.unpack_archive(archive_path, self.root / f"unpacked-{case}")
        self.assertFalse((self.root / "escaped.txt").exists())

    def test_copy_admission_retains_the_validated_evidence_digest(self):
        for label in ("analysis", "figure"):
            with self.subTest(kind=label):
                study = self.root / f"input-{label}"
                study.mkdir()
                config = paper_fixture(study)
                path = study / "analysis.json"
                original = path.read_bytes()
                if label == "figure":
                    path = study / "fixture.png"
                    path.write_bytes(b"Structural figure fixture; no rendering claim.")
                    config["evidence"]["plot"] = {"path": path.name, "sha256": file_hash(path)}
                    config["figures"] = [{"id": "plot", "evidence": "plot", "caption": "Fixture only."}]
                    results = study / "results.tex"
                    results.write_text(results.read_text() + r"\AllagmaFigure{plot}" + "\n")
                    bind_reviews(study, config)
                validate = adapter.papers.validate

                def validate_then_change(*args, **kwargs):
                    value = validate(*args, **kwargs)
                    path.write_bytes(path.read_bytes() + b" ")
                    return value

                destination = self.root / f"after-validation-{label}"
                with patch.object(adapter.papers, "validate", side_effect=validate_then_change):
                    with self.assertRaisesRegex(AllagmaError, "validated digest"):
                        adapter.assemble(study, config, destination)
                self.assertEqual(list(destination.iterdir()), [])
                if label == "analysis":
                    self.assertEqual(path.read_bytes(), original + b" ")
                    path.write_bytes(original)

    def test_copy_rechecks_the_opened_file_after_admission(self):
        # A separate bounded process makes a FIFO regression a test failure,
        # not an indefinitely blocked conformance runner.
        script = r"""
from pathlib import Path
import os, sys
from unittest.mock import patch
from allagma.files import AllagmaError
from allagma.research import _load
adapter = _load('copy_race_adapter', Path(sys.argv[1]))
root, kind = Path(sys.argv[2]), sys.argv[3]
source, other, target = root/'source.txt', root/'other.txt', root/'output.txt'
source.write_bytes(b'hello'); other.write_bytes(b'hello')
original = adapter.source_size

def swap_after_stat(path):
    size = original(path)
    source.unlink()
    if kind == 'symlink':
        source.symlink_to(other)
    else:
        os.mkfifo(source)
    return size

with patch.object(adapter, 'source_size', side_effect=swap_after_stat):
    try:
        adapter.copy_new(source, target, size=5)
    except AllagmaError:
        assert not target.exists()
    else:
        raise AssertionError('A non-regular or symlink replacement was accepted')
"""
        for kind in ("symlink", "fifo"):
            with self.subTest(kind=kind):
                root = self.root / kind
                root.mkdir()
                try:
                    result = subprocess.run([sys.executable, "-B", "-c", script,
                        str(adapter.ROOT / "package.py"), str(root), kind],
                        cwd=ROOT, capture_output=True, text=True, timeout=5)
                except subprocess.TimeoutExpired:
                    self.fail("Copy blocked opening a FIFO after admission")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_compiled_bibliography_and_updated_provenance_are_admitted_together(self):
        baseline = self.root / "baseline"
        adapter.assemble(self.study, self.config, baseline)
        total = self.source_bytes(baseline)
        bibliography = b"% generated bibliography\n" * 100

        def compile_fixture(source, output, **kwargs):
            output.mkdir()
            (output / "main.bbl").write_bytes(bibliography)
            return {}  # No compiler or successful TeX qualification is simulated.

        output = self.root / "delivery"
        with patch.object(adapter, "MAX_SOURCE_BYTES", total + len(bibliography)), \
             patch.object(adapter, "_load", return_value=SimpleNamespace(compile_sources=compile_fixture)):
            with self.assertRaisesRegex(AllagmaError, "integration ceiling"):
                adapter.build(self.study, self.config, output)
        self.assertEqual((output / "initial-build/main.bbl").read_bytes(), bibliography)
        self.assertEqual(inventory(output / "source"), inventory(baseline))
        self.assertFalse((output / "paper-source.tar.gz").exists())
        self.assertFalse((output / "delivery.json").exists())

    def test_archive_writer_enforces_reader_byte_and_file_limits_before_creation(self):
        source = self.root / "source"
        adapter.assemble(self.study, self.config, source)
        for index, limits in enumerate(({"MAX_SOURCE_BYTES": self.source_bytes(source) - 1},
                                        {"MAX_SOURCE_FILES": len(inventory(source)) - 1})):
            target = self.root / f"over-limit-{index}.tar.gz"
            with self.subTest(limits=limits), patch.multiple(adapter, **limits):
                with self.assertRaisesRegex(AllagmaError, "integration ceiling"):
                    adapter.archive_sources(source, target)
            self.assertFalse(target.exists())
        (source / "linked.txt").symlink_to(self.study / "analysis.json")
        with self.assertRaisesRegex(AllagmaError, "regular files"):
            adapter.archive_sources(source, self.root / "symlink.tar.gz")

    def test_reading_notes_cannot_replace_packaged_entrypoint_or_provenance(self):
        literature = read_json(self.study / "references/map.json")
        note = b"print('A reading note, not the portable builder.')\n"
        for index, name in enumerate(("build.py", "reference-map.json", "reference-index.md",
                                      "provenance.json", "evidence/analysis.json", "README.md")):
            with self.subTest(note=name):
                path = self.study / "references" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(note)
                literature["records"][0]["note"] = name
                write_json(self.study / "references/map.json", literature)
                bind_reviews(self.study, self.config)
                source = self.root / f"source-{index}"
                adapter.assemble(self.study, self.config, source)
                archive = self.root / f"source-{index}.tar.gz"
                adapter.archive_sources(source, archive)
                unpacked = adapter.unpack_archive(archive, self.root / f"unpacked-{index}")
                result = subprocess.run([sys.executable, str(unpacked / "anc/build.py"), "--help"],
                                        cwd=self.root, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--output", result.stdout)
                self.assertEqual(file_hash(unpacked / "anc/build.py"), file_hash(adapter.ROOT / "build.py"))
                packaged = read_json(unpacked / "anc/reference-map.json")
                mapped = packaged["records"][0]["note"]
                self.assertTrue(mapped.startswith("reference-notes/Fixture2026/"))
                self.assertEqual((unpacked / "anc" / mapped).read_bytes(), note)
                self.assertIn(f"]({mapped})", (unpacked / "anc/reference-index.md").read_text())
                self.assertIn("`reference-map.json`", (unpacked / "anc/reference-index.md").read_text())
                provenance = read_json(unpacked / "anc/provenance.json")
                self.assertEqual(provenance["original_reference_map_sha256"], file_hash(self.study / "references/map.json"))
                self.assertEqual(file_hash(unpacked / "anc/evidence/analysis.json"), self.config["evidence"]["analysis"]["sha256"])

    def test_archive_copy_refuses_existing_targets(self):
        target = self.root / "reserved.txt"
        target.write_text("Retain generated content.\n")
        with self.assertRaisesRegex(AllagmaError, "collision"):
            adapter.copy_new(self.study / "analysis.json", target)
        self.assertEqual(target.read_text(), "Retain generated content.\n")

    def test_evidence_identifiers_cannot_address_generated_ancillary_files(self):
        self.config["evidence"]["../reference-map"] = self.config["evidence"]["analysis"]
        bind_reviews(self.study, self.config)
        with self.assertRaisesRegex(AllagmaError, "Evidence IDs"):
            papers.validate(self.study, self.config)

    def test_numeric_formatting_cannot_silently_truncate_or_use_missing_values(self):
        with self.assertRaisesRegex(AllagmaError, "cannot truncate"):
            papers.format_value(3.5, "d")
        with self.assertRaisesRegex(AllagmaError, "finite"):
            papers.format_value(float("inf"), ".2f")
        config = deepcopy(self.config)
        config["claims"][0]["text"] = "The value is {{value:missing}}."
        with self.assertRaisesRegex(AllagmaError, "Unknown result value"):
            papers.validate(self.study, config)

    def test_prose_changes_invalidate_both_retained_reviews(self):
        with (self.study / "discussion.tex").open("a") as stream:
            stream.write("This added interpretation requires review.\n")
        with self.assertRaisesRegex(AllagmaError, "review is stale"):
            papers.validate(self.study, self.config)

    def test_section_roles_are_bound_to_both_reviews(self):
        (self.study / "limitations.tex").write_text("This fixture cannot establish scientific validity.\n")
        bind_reviews(self.study, self.config)
        original = papers.review_fingerprint(self.study, self.config)
        config = deepcopy(self.config)
        config["sections"] = dict(reversed(list(config["sections"].items())))
        self.assertEqual(papers.review_fingerprint(self.study, config), original)
        config["sections"]["abstract"], config["sections"]["limitations"] = (
            config["sections"]["limitations"], config["sections"]["abstract"])
        self.assertNotEqual(papers.review_fingerprint(self.study, config), original)
        with self.assertRaisesRegex(AllagmaError, "scientific review is stale"):
            papers.validate(self.study, config)
        scientific = self.study / config["evidence"]["scientific"]["path"]
        record = read_json(scientific)
        record["reviewed_content_sha256"] = papers.review_fingerprint(self.study, config)
        write_json(scientific, record)
        config["evidence"]["scientific"]["sha256"] = file_hash(scientific)
        with self.assertRaisesRegex(AllagmaError, "humanizer review is stale"):
            papers.validate(self.study, config)

    def test_short_tables_stay_together_and_pdf_attribution_is_configured(self):
        value = papers.validate(self.study, self.config)
        value["tables"]["estimates"]["breakable"] = False
        self.assertIn(r"\begin{table}", papers.macros(value))
        source = self.root / "source"
        adapter.assemble(self.study, self.config, source)
        main = (source / "main.tex").read_text()
        self.assertIn("pdfauthor={Fixture researcher}", main)
        self.assertNotIn("@@PDF_AUTHORS@@", main)

    def test_provided_only_paper_without_external_citations_retains_an_honest_reference_section(self):
        config = deepcopy(self.config)
        write_json(self.study / "references/map.json", references.empty_map("A self-contained known-answer derivation."))
        references.refresh(self.study / "references")
        (self.study / "introduction.tex").write_text("This derivation uses only the supplied study evidence.\n")
        config["claims"][0]["citations"] = []
        for kind in config["review"]:
            path = self.study / config["evidence"][kind]["path"]
            record = read_json(path)
            record["reviewed_content_sha256"] = papers.review_fingerprint(self.study, config)
            write_json(path, record)
            config["evidence"][kind]["sha256"] = file_hash(path)
        source = self.root / "provided-only"
        adapter.assemble(self.study, config, source)
        self.assertIn("No external bibliographic sources", (source / "main.bbl").read_text())
        self.assertIn(r"\section*{References}", (source / "main.bbl").read_text())
        self.assertEqual((source / "references.bib").read_text().strip(), "")


if __name__ == "__main__":
    unittest.main()
