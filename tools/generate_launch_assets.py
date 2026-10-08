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
    for theme, bg, ink, muted, panel, teal in [
        ("light", "#f7f8f2", "#172e32", "#506267", "#ffffff", "#087568"),
        ("dark", "#102427", "#f1f5eb", "#b4c4c2", "#183438", "#77dfc5"),
    ]:
        for mobile in (False, True):
            w, h = (600, 530) if mobile else (1000, 350)
            nodes = [("01", "Brief", "Ask a question"), ("02", "Plan", "Pin the methods"),
                     ("03", "Attempts", "Keep the record"), ("04", "Findings", "Check the claims")]
            svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>A research brief becomes a pinned plan, retained attempts, and evidence-linked findings.</title>',
                   f'<rect width="{w}" height="{h}" rx="16" fill="{bg}"/>',
                   f'<g font-family="system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" fill="{ink}">',
                   f'<text x="32" y="52" font-size="16" letter-spacing="3" fill="{teal}">ALLAGMA / FOLLOW THE EVIDENCE</text>']
            if mobile:
                svg.append('<text x="32" y="102" font-size="33" font-weight="650">Your question. A checkable record.</text>')
            else:
                svg.append('<text x="32" y="107" font-size="39" font-weight="650">Your question. A checkable research record.</text>')
            for i, (n, title, sub) in enumerate(nodes):
                x, y, nw, nh = (32, 130 + i*87, 536, 74) if mobile else (32 + i*242, 153, 210, 128)
                svg.append(f'<rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="6" fill="{panel}" stroke="{muted}" stroke-opacity=".3"/>')
                if mobile:
                    svg.append(f'<text x="{x+18}" y="{y+46}" fill="{teal}" font-size="18">{n}</text><text x="{x+64}" y="{y+31}" font-size="25" font-weight="600">{title}</text><text x="{x+64}" y="{y+56}" font-size="17" fill="{muted}">{sub}</text>')
                else:
                    svg.append(f'<text x="{x+17}" y="{y+29}" fill="{teal}" font-size="15">{n}</text><text x="{x+17}" y="{y+66}" font-size="29" font-weight="600">{title}</text><text x="{x+17}" y="{y+99}" font-size="18" fill="{muted}">{sub}</text>')
                    if i<3: svg.append(f'<path d="M{x+216} {y+62}h20m-6-6 6 6-6 6" fill="none" stroke="{teal}" stroke-width="2"/>')
            svg.append(f'<text x="32" y="{h-24}" font-size="16" fill="{muted}">Portable methods · Exact locks · Evidence-linked claims</text></g></svg>')
            (media / f'workflow-{theme}{"-mobile" if mobile else ""}.svg').write_text(''.join(svg))
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
