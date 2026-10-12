"""Assemble and verify an optional portable paper package without submission."""
from __future__ import annotations

from copy import deepcopy
import gzip
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

from allagma import papers, references
from allagma.files import (AllagmaError, canonical, confined, digest_bytes, file_hash, read_json,
                           write_bytes, write_json, write_text)
from allagma.references import require, tex_escape
from allagma.research import _load

ROOT = Path(__file__).resolve().parent
MAX_SOURCE_BYTES = 25 * 1024 ** 2
MAX_SOURCE_FILES = 1000


def check_budget(size, count):
    require(size <= MAX_SOURCE_BYTES and count <= MAX_SOURCE_FILES,
            f"Paper source package exceeds the {MAX_SOURCE_BYTES}-byte / "
            f"{MAX_SOURCE_FILES}-file integration ceiling; reduce declared sources "
            "and use a new paper revision/output directory. Failed revisions are retained.")


def source_size(path):
    path = Path(path)
    metadata = path.lstat()
    require(stat.S_ISREG(metadata.st_mode), f"Paper sources must be regular files: {path}")
    return metadata.st_size


def read_admitted(path, size, expected=None):
    require(source_size(path) == size, f"Paper source changed after admission: {path}")
    # Check the opened descriptor as well as the pathname. A replacement between
    # stat and open must not follow a symlink or wait for a FIFO writer.
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            require(stat.S_ISREG(metadata.st_mode) and metadata.st_size == size,
                    f"Paper source changed after admission: {path}")
            data = stream.read(size + 1)
    except OSError as exc:
        raise AllagmaError(f"Cannot safely read admitted paper source: {path}: {exc}") from exc
    require(len(data) == size and (expected is None or digest_bytes(data) == expected),
            f"Paper source changed after admission: {path}")
    return data


def copy_new(source, target, *, size=None, expected=None):
    """Bound a copy to its admitted size; never replace an existing target."""
    target = Path(target)
    require(not target.exists() and not target.is_symlink(),
            f"Paper source path collision: {target}")
    size = source_size(source) if size is None else size
    check_budget(size, 1)
    data = read_admitted(source, size, expected)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as output:
            output.write(data)
    except FileExistsError as exc:
        raise AllagmaError(f"Paper source path collision: {target}") from exc


class SourcePlan:
    """Admit the complete expanded source set before copying any payload."""

    def __init__(self):
        self.entries = {}
        self.size = 0

    def add(self, name, *, data=None, source=None, expected=None):
        # The same confinement and collision rules apply to generated and copied files.
        require(isinstance(name, str) and name and "\\" not in name and
                not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts and
                PurePosixPath(name).as_posix() == name, f"Invalid paper source path: {name}")
        require(all(name != old and not name.startswith(old + "/") and
                    not old.startswith(name + "/") for old in self.entries),
                f"Paper source path collision: {name}")
        size = len(data) if data is not None else source_size(source)
        check_budget(self.size + size, len(self.entries) + 1)
        sha = digest_bytes(data if data is not None else read_admitted(source, size))
        require(expected is None or sha == expected,
                f"Paper source differs from its validated digest: {name}; use a new paper revision")
        self.entries[name] = {"data": data, "source": source, "size": size, "sha256": sha}
        self.size += size

    def text(self, name, value):
        self.add(name, data=value.encode())

    def json(self, name, value):
        self.add(name, data=canonical(value))

    def inventory(self):
        return {name: item["sha256"] for name, item in sorted(self.entries.items())}

    def data(self, name):
        item = self.entries[name]
        return (item["data"] if item["data"] is not None else
                read_admitted(item["source"], item["size"], item["sha256"]))

    def write(self, destination):
        for name, item in self.entries.items():
            target = confined(destination, name)
            if item["data"] is None:
                copy_new(item["source"], target, size=item["size"], expected=item["sha256"])
            else:
                write_bytes(target, item["data"], immutable=True)


def source_plan(source, *, exclude=()):
    plan = SourcePlan()
    for path in sorted(Path(source).rglob("*")):
        name = path.relative_to(source).as_posix()
        require(not path.is_symlink(), f"Paper sources must be regular files: {name}")
        if not path.is_dir() and name not in exclude:
            plan.add(name, source=path)
    return plan


def assemble(study, config, destination):
    study, destination = Path(study).resolve(), Path(destination).resolve()
    value = papers.validate(study, config)
    if value["status"] == "disabled":
        return value
    require(not destination.exists(), "Use a new paper revision/output directory")
    destination.mkdir(parents=True)
    plan = SourcePlan()
    for name in papers.SECTIONS:
        plan.text(f"sections/{name}.tex", value["sections"][name])
    body = "\n".join(r"\section{" + name.replace("-", " ").capitalize() + "}\n" +
                     r"\input{sections/" + name + ".tex}" for name in papers.SECTIONS if name != "abstract")
    appendix_body = []
    for i, appendix in enumerate(config.get("appendices", [])):
        name = f"sections/appendix-{i+1}.tex"
        plan.text(name, confined(study, appendix["path"]).read_text())
        appendix_body.append(r"\section{" + tex_escape(appendix["title"]) + "}\n" + r"\input{" + name + "}")
    template = config.get("template", {"name": "allagma-preprint"})
    if template.get("name") == "allagma-preprint":
        main = (ROOT / "main.tex.in").read_text()
        plan.add("allagma-preprint.sty", source=ROOT / "allagma-preprint.sty")
    else:
        require(template.get("name") == "custom" and template.get("files"), "Choose the provided preprint template or declare custom template files")
        template_root = confined(study, template["directory"])
        main = confined(template_root, template["main"]).read_text()
        require(file_hash(template_root / template["main"]) == template["sha256"], "Custom template digest changed")
        for item in template["files"]:
            path = confined(template_root, item["path"])
            require(path.suffix in (".sty", ".cls", ".bst") and file_hash(path) == item["sha256"], "Invalid or changed custom template style")
            plan.add(item["path"], source=path, expected=item["sha256"])
    replacements = {"TITLE": tex_escape(config["title"]), "AUTHORS": value["authors_tex"],
                    "DATE": tex_escape(config["date"]), "BODY": body,
                    "APPENDICES": "\\appendix\n" + "\n".join(appendix_body) if appendix_body else ""}
    for key, replacement in replacements.items():
        require("@@" + key + "@@" in main, "Preprint template is missing its " + key + " slot")
        main = main.replace("@@" + key + "@@", replacement)
    pdf_authors = "Anonymous draft" if config["authors"]["mode"] == "anonymous" else "; ".join(a["name"] for a in config["authors"]["entries"])
    main = main.replace("@@PDF_AUTHORS@@", tex_escape(pdf_authors))
    plan.text("main.tex", main)
    plan.text("evidence-macros.tex", papers.macros(value))
    plan.text("references.bib", references.bibliography(value["literature"]))
    if not value["citations"]:
        # A provided-only known-answer study may legitimately cite no external
        # work. Keep the requested References section explicit without inventing
        # a citation or delivering an archive that depends on a missing bbl.
        plan.text("main.bbl", r"\section*{References}" + "\n" +
            "No external bibliographic sources are cited in this manuscript. "
            "The ancillary reference map records the reviewed materials and "
            "the limits of literature coverage.\n")
    for figure in value["figures"].values():
        plan.add(figure["target"], source=figure["source_path"],
                 expected=config["evidence"][figure["evidence"]]["sha256"])
    plan.add("anc/build.py", source=ROOT / "build.py")
    reference_directory = confined(study, config["references"])
    for original, target in (("assets.json", "reference-assets.json"), ("retrieval.json", "reference-retrieval.json")):
        if (reference_directory / original).is_file():
            plan.add("anc/" + target, source=reference_directory / original)
    literature = deepcopy(value["literature"])
    note_copies = {}
    for record in literature["records"]:
        if record.get("note"):
            original = record["note"]
            record["note"] = f"reference-notes/{record['id']}/{Path(original).name}"
            plan.add("anc/" + record["note"], source=confined(reference_directory, original))
            note_copies[record["id"]] = {"original": original, "packaged": "anc/" + record["note"]}
    plan.json("anc/reference-map.json", literature)
    plan.text("anc/reference-index.md", references.render_index(literature,
        map_path="reference-map.json", bibliography_path="../references.bib"))
    plan.json("anc/paper.json", config)
    plan.json("anc/claim-result-links.json", {"claims": config["claims"], "values": value["value_provenance"],
        "tables": {key: {k: v for k, v in table.items() if k != "rendered_rows"} for key, table in value["tables"].items()},
        "figures": config.get("figures", []), "citations": value["citations"]})
    figure_evidence = {fig["evidence"]: fig["target"] for fig in value["figures"].values()}
    evidence_copies = {}
    for key, source in value["evidence_paths"].items():
        path = Path(source)
        if key in figure_evidence:
            evidence_copies[key] = figure_evidence[key]
        else:
            require(path.suffix in (".json", ".md", ".txt", ".csv"), "Put raw model/data/reference downloads in the cache, not the paper archive")
            target = f"anc/evidence/{key}{path.suffix}"
            plan.add(target, source=path, expected=config["evidence"][key]["sha256"])
            evidence_copies[key] = target
    plan.text("anc/README.md", "# Portable paper sources\n\n"
        "Compile from the unpacked archive root with an existing TeX distribution:\n\n"
        "```sh\npython3 anc/build.py --output /path/to/new-clean-build\n```\n\n"
        "The builder verifies the source manifest and compiles in an empty temporary directory. "
        "It requires macOS sandbox-exec or Linux bubblewrap, denies network access and does not "
        "mount the reference cache. It installs nothing. For an ordinary manual TeX build, run "
        "pdflatex -no-shell-escape main.tex, bibtex main, then pdflatex twice from this root. "
        "Manual commands alone do not establish network isolation.\n\n"
        "Use main.tex as the arXiv top-level file. References include BibTeX and the generated "
        "main.bbl. The archive contains required custom styles and final PDF/PNG/JPEG figures. "
        "No on-the-fly figure conversion, network retrieval or shell escape is needed. "
        "Build instructions, claim/result links and provenance are ancillary material in anc/. "
        "The compiled paper PDF is delivered separately. No submission has been made.\n\n"
        "arXiv requirements were checked on 2026-10-09: https://info.arxiv.org/help/submit_tex.html "
        "and https://info.arxiv.org/help/faq/texlive.html. Supported TeX releases at that check "
        "were 2023 and 2025, with 2025 the default. The build receipt reports the actual local "
        "compiler and its scope; local success is not arXiv server validation or peer review.\n")
    provenance = {"format": "allagma-paper-provenance-v1", "title": config["title"], "authors": config["authors"],
                  "template": template, "original_evidence": config["evidence"], "evidence_copies": evidence_copies,
                  "original_reference_map_sha256": file_hash(reference_directory / "map.json"),
                  "reference_note_copies": note_copies,
                  "reference_map_sha256": plan.inventory()["anc/reference-map.json"],
                  "source_files": plan.inventory(), "submission": "not-submitted",
                  "review": config["review"], "scope": value["scope"]}
    plan.json("anc/provenance.json", provenance)
    plan.write(destination)
    require(source_plan(destination).inventory() == plan.inventory(), "Paper sources changed during assembly")
    return provenance


def archive_sources(source, target):
    source, target = Path(source), Path(target)
    require(not target.exists(), "Do not overwrite a prior source archive")
    plan = source_plan(source)
    require(not target.resolve().is_relative_to(source.resolve()), "Source archive must be outside its source directory")
    with target.open("xb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w|") as archive:
            for name in sorted(plan.entries):
                data = plan.data(name)
                member = tarfile.TarInfo(name)
                member.size, member.mode, member.mtime = len(data), 0o644, 0
                archive.addfile(member, io.BytesIO(data))
    require(source_plan(source).inventory() == plan.inventory(), "Paper sources changed during archiving")


def unpack_archive(archive_path, target):
    target = Path(target)
    require(not target.exists(), "Unpack into a new directory")
    total, names = 0, set()
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for member in archive:
            require(member.isfile() and member.name not in names, "Portable paper archive must contain unique regular files")
            names.add(member.name)
            total += member.size
            require(total <= MAX_SOURCE_BYTES and len(names) <= MAX_SOURCE_FILES, "Paper archive expansion limit exceeded")
            path = confined(target, member.name)
            write_bytes(path, archive.extractfile(member).read(), immutable=True)
    return target


def build(study, config, destination, *, engine="pdflatex", timeout=60):
    destination = Path(destination).resolve()
    if config.get("output") == "report":
        return papers.validate(study, config)
    require(not destination.exists(), "Use a new paper revision/output directory")
    source = destination / "source"
    assemble(study, config, source)
    builder = _load("allagma_clean_paper_builder", ROOT / "build.py")
    initial = builder.compile_sources(source, destination / "initial-build", engine=engine, timeout=timeout)
    bibliography = destination / "initial-build/main.bbl"
    replaced = ("anc/provenance.json", "main.bbl") if bibliography.exists() else ("anc/provenance.json",)
    final = source_plan(source, exclude=replaced)
    if bibliography.exists():
        final.add("main.bbl", source=bibliography)
    provenance = read_json(source / "anc/provenance.json")
    provenance["source_files"] = final.inventory()
    final.json("anc/provenance.json", provenance)
    # Admit the bibliography and its new manifest entry together before either write.
    if bibliography.exists():
        write_bytes(source / "main.bbl", final.data("main.bbl"))
    write_bytes(source / "anc/provenance.json", final.data("anc/provenance.json"))
    archive = destination / "paper-source.tar.gz"
    archive_sources(source, archive)
    with tempfile.TemporaryDirectory(prefix="allagma-paper-unpack-", dir="/tmp") as temporary:
        extracted = unpack_archive(archive, Path(temporary) / "source")
        require(file_hash(extracted / "anc/build.py") == file_hash(ROOT / "build.py"),
                "Packaged builder differs from the supplied integration")
        result = subprocess.run([sys.executable, "-B", str(extracted / "anc/build.py"),
            "--output", str(destination / "unpacked-build"), "--engine", engine, "--timeout", str(timeout)],
            cwd=extracted, capture_output=True, text=True, timeout=timeout * 8 + 30)
        write_text(destination / "unpacked-entrypoint.log", result.stdout + result.stderr, immutable=True)
        require(result.returncode == 0, "Packaged builder failed; see unpacked-entrypoint.log")
        verified = read_json(destination / "unpacked-build/build.json")
    shutil.copyfile(destination / "unpacked-build/main.pdf", destination / "paper.pdf")
    receipt = {"format": "allagma-paper-delivery-v1", "status": "pass", "paper": "paper.pdf",
               "paper_sha256": file_hash(destination / "paper.pdf"), "source_archive": archive.name,
               "archive_sha256": file_hash(archive), "archive_bytes": archive.stat().st_size,
               "initial_build": {k: initial[k] for k in ("compiler_version", "pdf_sha256", "network", "reference_cache")},
               "unpacked_build": {k: verified[k] for k in ("compiler_version", "pdf_sha256", "network", "reference_cache")},
               "pdf_bytes_reproduced": initial["pdf_sha256"] == verified["pdf_sha256"],
               "unpacked_entrypoint": "python3 anc/build.py", "packaged_builder_verified": True,
               "visual_inspection": "required separately", "submission": "not-submitted"}
    write_json(destination / "delivery.json", receipt, immutable=True)
    return receipt
