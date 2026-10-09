"""Assemble and verify an optional portable paper package without submission."""
from __future__ import annotations

import gzip
import io
from pathlib import Path
import shutil
import tarfile
import tempfile

from allagma import papers, references
from allagma.files import (AllagmaError, confined, file_hash, inventory, read_json,
                           write_bytes, write_json, write_text)
from allagma.references import require, tex_escape
from allagma.research import _load

ROOT = Path(__file__).resolve().parent
MAX_SOURCE_BYTES = 25 * 1024 ** 2


def assemble(study, config, destination):
    study, destination = Path(study).resolve(), Path(destination).resolve()
    value = papers.validate(study, config)
    if value["status"] == "disabled":
        return value
    require(not destination.exists(), "Use a new paper revision/output directory")
    destination.mkdir(parents=True)
    for name in papers.SECTIONS:
        write_text(destination / f"sections/{name}.tex", value["sections"][name], immutable=True)
    body = "\n".join(r"\section{" + name.replace("-", " ").capitalize() + "}\n" +
                     r"\input{sections/" + name + ".tex}" for name in papers.SECTIONS if name != "abstract")
    appendix_body = []
    for i, appendix in enumerate(config.get("appendices", [])):
        name = f"sections/appendix-{i+1}.tex"
        write_text(destination / name, confined(study, appendix["path"]).read_text(), immutable=True)
        appendix_body.append(r"\section{" + tex_escape(appendix["title"]) + "}\n" + r"\input{" + name + "}")
    template = config.get("template", {"name": "allagma-preprint"})
    if template.get("name") == "allagma-preprint":
        main = (ROOT / "main.tex.in").read_text()
        shutil.copyfile(ROOT / "allagma-preprint.sty", destination / "allagma-preprint.sty")
    else:
        require(template.get("name") == "custom" and template.get("files"), "Choose the provided preprint template or declare custom template files")
        template_root = confined(study, template["directory"])
        main = confined(template_root, template["main"]).read_text()
        require(file_hash(template_root / template["main"]) == template["sha256"], "Custom template digest changed")
        for item in template["files"]:
            path = confined(template_root, item["path"])
            require(path.suffix in (".sty", ".cls", ".bst") and file_hash(path) == item["sha256"], "Invalid or changed custom template style")
            target = confined(destination, item["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    replacements = {"TITLE": tex_escape(config["title"]), "AUTHORS": value["authors_tex"],
                    "DATE": tex_escape(config["date"]), "BODY": body,
                    "APPENDICES": "\\appendix\n" + "\n".join(appendix_body) if appendix_body else ""}
    for key, replacement in replacements.items():
        require("@@" + key + "@@" in main, "Preprint template is missing its " + key + " slot")
        main = main.replace("@@" + key + "@@", replacement)
    pdf_authors = "Anonymous draft" if config["authors"]["mode"] == "anonymous" else "; ".join(a["name"] for a in config["authors"]["entries"])
    main = main.replace("@@PDF_AUTHORS@@", tex_escape(pdf_authors))
    write_text(destination / "main.tex", main, immutable=True)
    write_text(destination / "evidence-macros.tex", papers.macros(value), immutable=True)
    write_text(destination / "references.bib", references.bibliography(value["literature"]), immutable=True)
    for figure in value["figures"].values():
        target = destination / figure["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(figure["source_path"], target)
    (destination / "anc").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "build.py", destination / "anc/build.py")
    write_json(destination / "anc/reference-map.json", value["literature"], immutable=True)
    write_text(destination / "anc/reference-index.md", references.render_index(value["literature"]), immutable=True)
    reference_directory = confined(study, config["references"])
    for original, target in (("assets.json", "reference-assets.json"), ("retrieval.json", "reference-retrieval.json")):
        if (reference_directory / original).is_file():
            shutil.copyfile(reference_directory / original, destination / "anc" / target)
    for record in value["literature"]["records"]:
        if record.get("note"):
            target = confined(destination / "anc", record["note"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(confined(reference_directory, record["note"]), target)
    write_json(destination / "anc/paper.json", config, immutable=True)
    write_json(destination / "anc/claim-result-links.json", {"claims": config["claims"], "values": value["value_provenance"],
        "tables": {key: {k: v for k, v in table.items() if k != "rendered_rows"} for key, table in value["tables"].items()},
        "figures": config.get("figures", []), "citations": value["citations"]}, immutable=True)
    figure_evidence = {fig["evidence"]: fig["target"] for fig in value["figures"].values()}
    evidence_copies = {}
    for key, source in value["evidence_paths"].items():
        path = Path(source)
        if key in figure_evidence:
            evidence_copies[key] = figure_evidence[key]
        else:
            require(path.suffix in (".json", ".md", ".txt", ".csv"), "Put raw model/data/reference downloads in the cache, not the paper archive")
            target = f"anc/evidence/{key}{path.suffix}"
            target_path = confined(destination, target)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target_path)
            evidence_copies[key] = target
    write_text(destination / "anc/README.md", "# Portable paper sources\n\n"
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
        "compiler and its scope; local success is not arXiv server validation or peer review.\n", immutable=True)
    provenance = {"format": "allagma-paper-provenance-v1", "title": config["title"], "authors": config["authors"],
                  "template": template, "original_evidence": config["evidence"], "evidence_copies": evidence_copies,
                  "reference_map_sha256": file_hash(destination / "anc/reference-map.json"),
                  "source_files": inventory(destination), "submission": "not-submitted",
                  "review": config["review"], "scope": value["scope"]}
    size = sum(p.stat().st_size for p in destination.rglob("*") if p.is_file())
    require(size <= MAX_SOURCE_BYTES, "Paper source package exceeds the 25 MiB integration ceiling")
    write_json(destination / "anc/provenance.json", provenance, immutable=True)
    return provenance


def archive_sources(source, target):
    source, target = Path(source), Path(target)
    require(not target.exists(), "Do not overwrite a prior source archive")
    with target.open("xb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w|") as archive:
            for name in sorted(inventory(source)):
                data = (source / name).read_bytes()
                member = tarfile.TarInfo(name)
                member.size, member.mode, member.mtime = len(data), 0o644, 0
                archive.addfile(member, io.BytesIO(data))


def unpack_archive(archive_path, target):
    target = Path(target)
    require(not target.exists(), "Unpack into a new directory")
    total, names = 0, set()
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for member in archive:
            require(member.isfile() and member.name not in names, "Portable paper archive must contain unique regular files")
            names.add(member.name)
            total += member.size
            require(total <= MAX_SOURCE_BYTES and len(names) <= 1000, "Paper archive expansion limit exceeded")
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
    if (destination / "initial-build/main.bbl").exists():
        shutil.copyfile(destination / "initial-build/main.bbl", source / "main.bbl")
    provenance = read_json(source / "anc/provenance.json")
    provenance["source_files"] = {name: value for name, value in inventory(source).items() if name != "anc/provenance.json"}
    write_json(source / "anc/provenance.json", provenance)
    archive = destination / "paper-source.tar.gz"
    archive_sources(source, archive)
    with tempfile.TemporaryDirectory(prefix="allagma-paper-unpack-", dir="/tmp") as temporary:
        extracted = unpack_archive(archive, Path(temporary) / "source")
        verified = builder.compile_sources(extracted, destination / "unpacked-build", engine=engine, timeout=timeout)
    shutil.copyfile(destination / "unpacked-build/main.pdf", destination / "paper.pdf")
    receipt = {"format": "allagma-paper-delivery-v1", "status": "pass", "paper": "paper.pdf",
               "paper_sha256": file_hash(destination / "paper.pdf"), "source_archive": archive.name,
               "archive_sha256": file_hash(archive), "archive_bytes": archive.stat().st_size,
               "initial_build": {k: initial[k] for k in ("compiler_version", "pdf_sha256", "network", "reference_cache")},
               "unpacked_build": {k: verified[k] for k in ("compiler_version", "pdf_sha256", "network", "reference_cache")},
               "pdf_bytes_reproduced": initial["pdf_sha256"] == verified["pdf_sha256"],
               "visual_inspection": "required separately", "submission": "not-submitted"}
    write_json(destination / "delivery.json", receipt, immutable=True)
    return receipt
