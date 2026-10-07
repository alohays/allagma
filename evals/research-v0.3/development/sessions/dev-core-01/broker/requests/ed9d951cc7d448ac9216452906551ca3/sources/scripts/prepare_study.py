"""Freeze the study and qualify it using the exact installed Allagma bundle."""
import difflib
import json
import os
from pathlib import Path
import sys

root = Path.cwd().resolve()
lock = json.loads((root / ".allagma/lock.yaml").read_text())
bundle = root / ".allagma/bundles" / lock["bundle_id"]
sys.path.insert(0, str(bundle))
from allagma.bundles import resolve_entry, verify_study
from allagma.campaigns import start_campaign, run_campaign
from allagma.composition import select_context
from allagma.files import reference, write_json
from allagma.contracts import validate_record

os.environ["TMPDIR"] = str(root / ".tmp")
verify_study(root)
brief = {
    "study_id": "dev-core-01", "question": "Reproduce the six original CN/AA-labelled CULP accuracies on Iris, Zoo and Wine without changing the capsule science.",
    "motivation": "Test computational reproducibility and separate faithfully reproduced output from supported scientific interpretation.",
    "success_criteria": ["All three original sample scripts execute with path-only adaptation", "Preserve and recover the controlled interruption", "Printed answers agree with retained predictions and raw-only recomputation", "Fresh environment direct execution agrees", "Deliver evidence-linked report, review, reproduction commands and SHA-256 manifest"],
    "constraints": ["All setup and computation via supplied local broker; offline, one worker at a time", "Never change scientific algorithms, split seed 42, k or scoring labels", "Preserve Iris/Zoo hardcoded CS limitation", "Stay within both frozen Allagma budget (8 attempts, 300s, 90s each) and supplied remaining broker ceilings (9 compute requests, 1496.724144789623s compute, 845.0887466662098s setup at start)", "Synthetic pilot is distinct from source datasets; no new confirmatory splits", "Keep inputs, source revisions, failed attempts and generated bundle"],
    "output": "report.json, REPORT.md, review.json, REPRODUCE.md, artifact-manifest.json, submission.json",
    "stop_rules": ["Declared completion", "Any resource ceiling", "Failed known-answer qualification", "Repeated unrecoverable execution failure", "Missing required external input -> honest partial package"]}
code = ["scripts/run_capsule.py", "scripts/evaluate.py", "scripts/analyze.py", "scripts/write_report.py", "scripts/scientific_checks.py", "REPORT.template.md", "requirements.lock.txt"]
code += [str(p.relative_to(root)) for p in sorted((root / "source/adapted").rglob("*")) if p.is_file()]
protocol = {
    "revision": "culp-v1", "hypothesis": "Path-adapted source outputs are executable and their printed percentage scores agree with actual predictions on the original held-out partitions.",
    "runner": "scripts/run_capsule.py", "evaluator": "scripts/evaluate.py", "analyzer": "scripts/analyze.py", "writer": "scripts/write_report.py", "code": code,
    "runs": [{"id": "pilot", "split": "pilot", "input": {"seed": 7, "mode": "pilot"}},
             {"id": "capsule", "split": "confirmation", "input": {"seed": 42, "mode": "confirmation"}}],
    "metrics": ["correct test predictions / test count, percent rounded to 2 decimal places", "printed-to-recomputed equality", "fresh-environment stdout equality"],
    "independent_variables": ["Dataset and original printed predictor label; actual predictor recorded separately"],
    "baselines": ["Analytically solved synthetic two-class CULP pilot", "Uninstrumented direct source execution as wrapper-equivalence control"],
    "uncertainty": "Descriptive Wilson 95% binomial intervals only; shared transductive graph violates independence and no across-split variability is measured.",
    "partitions": {"confirmation": "Original random_state=42, test_size=0.2, shuffle=True, no stratification on each complete supplied dataset", "pilot": "Two training values 0 and 10, labels 0 and 1, test values 0.1 and 9.9; separate synthetic inputs, seed identifier 7 (no stochastic generation)"},
    "exclusions": ["Pilot excluded from capsule estimates", "Every interrupted/failed attempt excluded", "No selecting runs by accuracy"],
    "editable": ["Only file-path portability in Zoo/Wine capsule sources", "Study-owned logging, reporting and audit implementation with revision tracking"],
    "fixed": ["Original scientific source, data, random split, k, metric, link predictors and rounding", "Iris/Zoo hardcoded CS preserved"],
    "qualification": "All four original predictors return [0,1] on the known-answer synthetic graph; evaluator passes 0%, 66.67%, 100% controls before confirmation.",
    "completion": "Successful qualified full capsule execution, excluded interrupted attempt, raw-only recomputation equality, fresh direct execution agreement, review at final material digest and complete artifact manifest",
    "max_failures_per_run": 2,
    "analysis_handoff": "Use portable AnalysisRecord contract rather than native analyze_campaign, which requires two independent confirmation observations. This task mandates a single fixed split; combining datasets as replicates would be invalid."
}
write_json(root / "brief.json", brief, immutable=True)
write_json(root / "protocol.json", protocol, immutable=True)
start_campaign(root, "core-culp")
entries = [resolve_entry(root, module, "core-culp") for module in
           ["recipe/research", "context", "research/scope", "research/protocol", "research/experiment", "research/analysis", "research/writing", "research/audit", "runner", "reviewer"]]
write_json(root / "evidence/workflow/resolved-entries.json", entries, immutable=True)
payload = {"context_id": "culp-initial", "required": ["question", "constraints", "stop_rules", "protocol", "unresolved", "lock"],
           "relevant": ["source", "compute"], "max_chars": 12000,
           "records": {"question": brief["question"], "constraints": brief["constraints"], "stop_rules": brief["stop_rules"],
                       "protocol": reference(root, root / "campaigns/core-culp/protocol.json"),
                       "lock": reference(root, root / "campaigns/core-culp/lock.yaml"),
                       "unresolved": "Original environment unspecified; Iris/Zoo outputs mislabeled; execution and recovery not yet established.",
                       "source": reference(root, root / "inputs/SOURCES.md"), "compute": reference(root, root / "inputs/COMPUTE.md")}}
context = select_context(payload, "context/active-brief")
validate_record(context)
write_json(root / "evidence/workflow/context.json", context, immutable=True)
diff = []
for old in sorted((root / "source/original").rglob("*")):
    if old.is_file():
        relative = old.relative_to(root / "source/original")
        new = root / "source/adapted" / relative
        if old.read_bytes() != new.read_bytes():
            diff.extend(difflib.unified_diff(old.read_text().splitlines(True), new.read_text().splitlines(True),
                        fromfile="source/original/"+str(relative), tofile="source/adapted/"+str(relative)))
(root / "evidence/source-adaptation.diff").write_text("".join(diff))
write_json(root / "evidence/literature-map.json", [
    {"source": "inputs/SOURCES.md", "metadata": {"capsule": "capsule-6460826", "doi": "10.24433/CO.0609cc4f-8b95-4d94-8fd0-9456d262b3a5", "benchmark_revision": "e32a2980e72fe6eb04ee04eb749458f570625663"}, "support": "Supplied provenance identity", "uncertainty": "Offline; external metadata and reference results not verified"},
    {"source": "source/original/metadata/metadata.yml", "metadata": {"title": "CULP: Classification Using Link Prediction", "authors": ["Seyed Amin Fadaee", "Maryam Amir Haeri"]}, "support": "Supplied algorithm motivation and broad empirical claims", "uncertainty": "Paper unavailable; capsule reproduction cannot establish competitiveness or novelty"},
    {"source": "source/original/code", "metadata": {"scripts": ["iris_sample.py", "zoo_sample.py", "wine_sample.py"]}, "support": "Exact task algorithm and partitions; Iris/Zoo labels do not name actual predictor", "uncertainty": "No original dependency pins, outputs or README requirement list"}
], immutable=True)
state = run_campaign(root, "core-culp", stop_after=1)
print(json.dumps(state, indent=2))
assert (root / "campaigns/core-culp/runs/pilot/attempts/001/record.json").exists()
assert json.loads((root / "campaigns/core-culp/runs/pilot/attempts/001/record.json").read_text())["status"] == "succeeded"
