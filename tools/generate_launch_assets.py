#!/usr/bin/env python3
"""Generate editable identity SVGs and copy exact, selected study artifacts."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]


def generate(study):
    media = ROOT / "media"
    media.mkdir(exist_ok=True)
    mark = '''<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"><title>Allagma</title><path d="M14 5H5v30h9M26 5h9v30h-9M11 20h18m-6-6 6 6-6 6" fill="none" stroke="#168575" stroke-width="3" stroke-linecap="square" stroke-linejoin="miter"/></svg>'''
    (media / "mark.svg").write_text(mark)
    for destination in (ROOT / "site/src/assets/mark.svg", ROOT / "site/public/favicon.svg"):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(mark)
    from generate_presentation_assets import generate_workflows
    generate_workflows(media)
    social = '''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640"><rect width="1280" height="640" fill="#102427"/><g fill="none" stroke="#78dfc4" stroke-width="5"><path d="M97 67H67v67h30m38-67h30v67h-30M84 100h64m-16-16 16 16-16 16"/></g><g font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"><text x="199" y="119" fill="#f1f5eb" font-size="56" font-weight="650">Allagma</text><text x="68" y="269" fill="#f1f5eb" font-size="67" font-weight="650">Research workflows</text><text x="68" y="354" fill="#f1f5eb" font-size="67" font-weight="650">for coding agents.</text><path d="M68 401H1212" stroke="#466064"/><text x="68" y="465" fill="#b8ccc8" font-size="29">Pin the plan. Retain every attempt. Check the claims.</text><text x="68" y="574" fill="#78dfc4" font-size="24">alohays / allagma</text><text x="1212" y="574" text-anchor="end" fill="#b8ccc8" font-size="23">MIT core · Python · v0.3.0rc2</text></g></svg>'''
    (media / 'social-preview.svg').write_text(social)
    evidence = media / "evidence"
    evidence.mkdir(exist_ok=True)
    analysis = Path("campaigns/toy-v1/analyses/a001")
    files = {"toy-brief.json": Path("brief.json"), "toy-summary.json": analysis/"outputs/summary.json",
             "toy-claims.json": analysis/"paper/claims.json", "toy-manuscript.md": analysis/"paper/manuscript.md",
             "toy-paired-differences.svg": analysis/"outputs/paired-differences.svg"}
    provenance = {"format": "allagma-public-preview-v1", "scope": "Exact selected outputs of a fresh offline toy execution; no model session. Copied bytes, not a substitute for the complete study.", "files": {}}
    for target, source in files.items():
        data = (study/source).read_bytes()
        (evidence/target).write_bytes(data)
        provenance["files"][target] = {"study_relative_source": str(source), "sha256": hashlib.sha256(data).hexdigest()}
    original = ROOT / "studies/ema-schedule/figures/r07-main-figure.png"
    shutil.copyfile(original, evidence/"ema-r07.png")
    shutil.copyfile(ROOT/"studies/ema-schedule/reference/LICENSE", evidence/"EMA-LICENSE.txt")
    provenance["files"]["ema-r07.png"] = {"repository_source": str(original.relative_to(ROOT)), "sha256": hashlib.sha256(original.read_bytes()).hexdigest(), "scope": "Retained r07 results, not a new training run. See the study license/disclosure."}
    (evidence/"provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Generated SVG sources and {len(provenance['files'])} exact artifact previews.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--study", required=True, type=Path)
    generate(p.parse_args().study)
