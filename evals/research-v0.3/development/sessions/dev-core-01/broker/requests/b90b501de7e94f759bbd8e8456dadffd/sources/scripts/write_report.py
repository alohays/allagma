"""Generate manuscript from verified numerical outputs and a reviewed prose template."""
import json
from pathlib import Path


def write_report(root, analysis_directory):
    template = (Path(__file__).resolve().parents[1] / "REPORT.template.md").read_text()
    table = (analysis_directory / "table.md").read_text()
    assert "{{RESULTS_TABLE}}" in template
    (root / "REPORT.md").write_text(template.replace("{{RESULTS_TABLE}}", table))
    answers = json.loads((analysis_directory / "report.json").read_text())
    (root / "report.json").write_text(json.dumps(answers, indent=2) + "\n")
