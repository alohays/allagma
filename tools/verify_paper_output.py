#!/usr/bin/env python3
"""Verify a delivered paper archive and PDF metadata using installed Poppler."""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from allagma.files import file_hash, read_json, write_json


def verify(directory, *, author, tex_release=None):
    directory = Path(directory)
    delivery = read_json(directory / "delivery.json")
    for path_key, digest_key in (("paper", "paper_sha256"), ("source_archive", "archive_sha256")):
        if file_hash(directory / delivery[path_key]) != delivery[digest_key]:
            raise ValueError("Delivered paper or archive has changed")
    if delivery["status"] != "pass" or delivery["submission"] != "not-submitted":
        raise ValueError("The delivery does not have a successful, non-submitted state")
    for build in ("initial_build", "unpacked_build"):
        receipt = delivery[build]
        if receipt["network"] != "denied" or receipt["reference_cache"] != "not accessible":
            raise ValueError("The build did not establish clean isolation")
        if tex_release and not re.search(r"TeX Live " + re.escape(tex_release) + r"\b", receipt["compiler_version"]):
            raise ValueError("Unexpected TeX release: " + receipt["compiler_version"])
    with tarfile.open(directory / delivery["source_archive"]) as archive:
        names = archive.getnames()
        required = {"main.tex", "references.bib", "main.bbl", "anc/build.py", "anc/provenance.json",
                    "anc/claim-result-links.json", "anc/reference-map.json"}
        if not required <= set(names):
            raise ValueError("The portable archive is missing required sources")
        if any(name.endswith((".aux", ".log", ".fls", ".npz", ".pt", ".pth")) or
               ".allagma-reference-cache" in name or name == "main.pdf" for name in names):
            raise ValueError("Raw cache or build output entered the source archive")
    info = subprocess.check_output(["pdfinfo", str(directory / delivery["paper"])], text=True)
    metadata = dict(line.split(":", 1) for line in info.splitlines() if ":" in line)
    if metadata.get("Author", "").strip() != author:
        raise ValueError("PDF attribution differs from the configured author")
    if not metadata.get("Title", "").strip() or metadata.get("JavaScript", "").strip() != "no":
        raise ValueError("PDF title is missing or active JavaScript is present")
    text = subprocess.check_output(["pdftotext", str(directory / delivery["paper"]), "-"], text=True)
    for section in ("Abstract", "Introduction", "Related work", "Methods", "Results", "Discussion", "Limitations", "References"):
        if section not in text:
            raise ValueError("Missing rendered section: " + section)
    if re.search(r"\b(?:TODO|TBD|PLACEHOLDER)\b|\[\?\]|\?\?", text):
        raise ValueError("Unresolved text or references in the rendered PDF")
    result = {"format": "allagma-paper-output-verification-v1", "status": "pass",
              "paper_sha256": delivery["paper_sha256"], "archive_sha256": delivery["archive_sha256"],
              "author": author, "pages": int(metadata["Pages"]), "source_files": len(names),
              "tex_release_required": tex_release, "javascript": False, "sections_present": True,
              "scope": "Archive, metadata and text checks; page-by-page visual inspection is separate"}
    write_json(directory / "verification.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--tex-release")
    args = parser.parse_args()
    print(verify(args.directory, author=args.author, tex_release=args.tex_release))
