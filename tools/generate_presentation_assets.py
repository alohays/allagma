#!/usr/bin/env python3
"""Build presentation graphics from existing artifacts, without running science."""
from pathlib import Path
import base64
import hashlib
import html
import json
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate_workflows(media):
    nodes = [
        ("01 / YOU SUPPLY", "Question", ["Brief, sources", "and resource limits"]),
        ("02 / AGENT PLANS", "Protocol + code", ["Comparisons", "and feasibility checks"]),
        ("03 / AGENT RUNS", "Runs + analysis", ["Experiments, recovery", "and interpretation"]),
        ("04 / YOU REVIEW", "Figures + report", ["Findings, critique", "and reproducible code"]),
    ]
    for theme, bg, ink, muted, panel, teal in [
        ("light", "#f7f8f2", "#172e32", "#506267", "#ffffff", "#087568"),
        ("dark", "#102427", "#f1f5eb", "#b4c4c2", "#183438", "#77dfc5"),
    ]:
        for mobile in (False, True):
            w, h = (600, 670) if mobile else (1000, 332)
            svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><title>You supply the question and limits. The agent plans, runs and analyzes the study. You review figures, report and reproducible code.</title>',
                   f'<rect width="{w}" height="{h}" rx="14" fill="{bg}"/>',
                   f'<g font-family="Arial,Helvetica,sans-serif" fill="{ink}">',
                   f'<text x="28" y="40" font-size="15" letter-spacing="1.4" fill="{teal}">ALLAGMA / HOW THE STUDY GETS DONE</text>']
            if mobile:
                svg.append('<text x="28" y="89" font-size="32" font-weight="600">A research question becomes</text><text x="28" y="130" font-size="32" font-weight="600">work you can inspect.</text>')
            else:
                svg.append('<text x="28" y="92" font-size="35" font-weight="600">A research question becomes work you can inspect.</text>')
            for i, (label, title, lines) in enumerate(nodes):
                x, y, nw, nh = (28, 157+i*112, 544, 96) if mobile else (28+i*245, 126, 210, 160)
                svg.append(f'<rect x="{x}" y="{y}" width="{nw}" height="{nh}" rx="6" fill="{panel}" stroke="{muted}" stroke-opacity=".3"/>')
                if mobile:
                    svg.append(f'<text x="{x+17}" y="{y+26}" font-size="14" fill="{teal}">{label}</text><text x="{x+17}" y="{y+62}" font-size="26" font-weight="600">{title}</text>')
                    for j, line in enumerate(lines):
                        svg.append(f'<text x="{x+274}" y="{y+42+j*26}" font-size="19" fill="{muted}">{html.escape(line)}</text>')
                else:
                    svg.append(f'<text x="{x+16}" y="{y+29}" font-size="12" fill="{teal}">{label}</text><text x="{x+16}" y="{y+70}" font-size="23" font-weight="600">{title}</text>')
                    for j, line in enumerate(lines):
                        svg.append(f'<text x="{x+16}" y="{y+106+j*25}" font-size="16" fill="{muted}">{html.escape(line)}</text>')
                    if i < 3:
                        svg.append(f'<path d="M{x+217} {y+80}h19m-6-6 6 6-6 6" fill="none" stroke="{teal}" stroke-width="2"/>')
            svg.append(f'<text x="28" y="{h-18}" font-size="15" fill="{muted}">Allagma keeps the plan, attempts and evidence with the result.</text></g></svg>')
            (media/f'workflow-{theme}{"-mobile" if mobile else ""}.svg').write_text("".join(svg))


def generate_poster():
    figure = ROOT/"media/evidence/toy-paired-differences.svg"
    report = ROOT/"media/evidence/toy-manuscript.md"
    text = report.read_text()
    quote = "The biased estimator had higher average squared error across 24 confirmation seeds."
    assert quote in " ".join(text.split())
    image = base64.b64encode(figure.read_bytes()).decode()
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img"><title>The offline study produces a paired-difference figure and a report that explains its findings and counterexamples.</title>',
           '<rect width="1280" height="720" fill="#f5f7ef"/>',
           '<g font-family="Arial,Helvetica,sans-serif" fill="#173b31">',
           '<text x="40" y="43" font-size="18" letter-spacing="1.8" fill="#376c5d">ALLAGMA / THE OFFLINE EXAMPLE</text>',
           '<text x="40" y="94" font-size="42" font-weight="600">A figure and a report you can inspect</text>',
           '<rect x="40" y="124" width="630" height="480" rx="7" fill="#fff" stroke="#cad6cd"/>',
           f'<image href="data:image/svg+xml;base64,{image}" x="53" y="137" width="604" height="454"/>',
           '<rect x="696" y="124" width="544" height="480" rx="7" fill="#fff" stroke="#cad6cd"/>',
           '<text x="726" y="167" font-size="18" fill="#376c5d">FROM THE GENERATED MANUSCRIPT</text>',
           '<text x="726" y="211" font-size="30" font-weight="600">The average error increased.</text>']
    for i, line in enumerate(textwrap.wrap(quote, 36)):
        svg.append(f'<text x="726" y="{264+i*36}" font-size="26">{html.escape(line)}</text>')
    svg += ['<path d="M726 378H1210" stroke="#cad6cd"/>',
            '<text x="726" y="420" font-size="25" font-weight="600">But not on every seed.</text>',
            '<text x="726" y="458" font-size="24">The report identifies four</text>',
            '<text x="726" y="492" font-size="24">counterexamples to that claim.</text>',
            '<text x="726" y="557" font-size="19" fill="#52665c">24 seeds · known-answer study</text>',
            '</g></svg>']
    destination = ROOT/"media/source/results-poster.svg"
    destination.write_text("".join(svg))
    receipt = {
        "format": "allagma-results-poster-v1",
        "scope": "Presentation layout around the unchanged toy figure and an exact sentence from its manuscript. The counterexample annotation summarizes the same report. No product UI, fresh execution or new data.",
        "sources": {str(p.relative_to(ROOT)): digest(p) for p in (figure, report)},
        "editable_source": str(destination.relative_to(ROOT)),
        "editable_sha256": digest(destination),
        "rendered_file": "media/demo/results-poster.png",
        "render_command": "cd site && node scripts/render-results-poster.mjs",
    }
    (ROOT/"media/demo/results-poster-provenance.json").write_text(json.dumps(receipt, indent=2)+"\n")


if __name__ == "__main__":
    generate_workflows(ROOT/"media")
    generate_poster()
    print("Generated workflow SVGs and the results-poster source from retained artifacts.")
