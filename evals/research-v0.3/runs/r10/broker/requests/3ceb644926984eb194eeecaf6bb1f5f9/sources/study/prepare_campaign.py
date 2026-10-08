"""Bookkeeping: declare a finite protocol and freeze it using the locked helper."""
import subprocess
import sys
from common import ROOT, read, ref, tree_manifest, write

BUNDLE = ".allagma/bundles/b-9a39b70665ba909edb8abc13"
brief = {
    "study_id": "r10", "question": "What accuracies do the supplied Iris, Zoo and Wine scripts print under CN and AA, and what do those measurements actually establish?",
    "motivation": "Faithful offline computational reproduction of the supplied CULP capsule, preserving upstream scoring and limitations.",
    "success_criteria": ["All three exact scripts executed after path-only compatibility adaptation", "Six exact task keys answered from original stdout and saved predictions", "Interruption preserved and recovered with a new attempt", "Recomputed evidence agrees and reviewed artifact revisions are retained"],
    "constraints": ["All setup and scientific computation through inputs/compute.py", "Offline wheelhouse and isolated environment", "No scientific source parameter or algorithm changes", "600 compute seconds, 300 setup seconds, 32 compute attempts, 180 seconds per request; 3600 second native session", "Only one scientific worker at a time"],
    "output": "submission.json; report.json; REPORT.md; review.json; REPRODUCE.md; artifact-manifest.json; measurements.json",
    "stop_rules": ["Declared completeness with concrete verification", "Resource ceiling -> partial", "Pilot qualification failure -> stop confirmation", "Irrecoverable repeated failure or required missing input -> honest partial/blocked"]}
write(ROOT / "brief.json", brief)
code = ["study/common.py", "study/runner.py", "study/analyze.py", "study/pilot.py", "study/write_report.py"]
code += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "work/capsule").rglob("*")) if p.is_file()]
protocol = {
    "revision": "culp-protocol-v1", "hypothesis": "The supplied scripts are locally executable with path-only compatibility edits and their displayed scores are exactly reconstructible from retained predictions.",
    "runner": "study/runner.py", "evaluator": "study/analyze.py", "analyzer": "study/analyze.py", "writer": "study/write_report.py", "code": code,
    "paired_seeds": True, "minimum_confirmation_runs": 3,
    "runs": [{"id": "synthetic-pilot", "split": "pilot", "input": {"seed": 314159, "synthetic": True}}] +
            [{"id": d, "split": "confirmation", "condition_id": d, "input": {"seed": 42, "dataset": d, "test_size": 0.2, "similarity": "manhattan", "k": k}} for d,k in [("iris",11),("zoo",2),("wine",12)]],
    "seed_interpretation": "Shared prescribed seed across distinct dataset conditions, not replicate seeds; synthetic pilot has no random data and a separate identity seed.",
    "fixed": ["Original 80/20 random_state=42 unstratified partitions", "k values, metric, label conversion and Wine train-only normalization", "CN/AA/RA/CS print loop and Iris/Zoo CS literal", "Original mean accuracy rounded to 2 decimals", "CPU, n_jobs=1"],
    "editable": ["Only absolute data paths for local portability", "Observation wrapper and evidence storage without changing algorithm inputs/outputs"],
    "independent_variables": "Dataset and source loop label; actual predictor recorded separately; no optimization or tuning",
    "baselines": "Analytical synthetic graph controls; no scientific external baseline supplied",
    "metrics": "Number correct, test denominator, accuracy percent and original printed values; save confusion matrices and graph diagnostics",
    "uncertainty": "One deterministic prescribed split per dataset. Exact descriptive counts; no inferential CI or extra pseudo-replicates.",
    "exclusions": "Interrupted/failed attempts and synthetic pilot excluded from reported confirmation; retain all history",
    "qualification": "All four link predictors and independent graph formulas checked on known-answer synthetic graphs; full synthetic CULP call and scoring parser; pilot must pass before confirmation",
    "verification": ["Retained prediction/label counts equal original stdout", "Independent graph-based link scores yield saved predictions", "Recompute same raw inputs into separate output directory", "Audit fixed partitions, preprocessing, all exact answer keys, source diff and transitive hashes"],
    "interruption": "Mark first substantive source-script attempt with --attempt; retain authoritative receipt and any partial files, then recover with new attempt id only after terminal status",
    "failure_criteria": ["Mismatch between score, prediction, source or stdout", "Unexpected algorithm/parameter edits", "Pilot failure", "Missing required script output"],
    "completion": "Three successful source script runs, six verified answers, retained failure history, passing documented audit, reproducible commands and hash manifest",
    "budget": read(ROOT / "inputs/RESOURCES.json")["profile"],
    "broker_handoff": "Campaign helper freezes records only. Study-owned orchestration uses the mandated inputs/compute.py broker and creates RunRecords; the built-in direct execution campaign helper is not used.",
    "measurement_interchange": "Generic research-measurements-v1 envelope with CULP extension; supplied MEASUREMENTS.md has no CULP-specific field contract."}
write(ROOT / "protocol.json", protocol)
subprocess.run([sys.executable, str(ROOT / BUNDLE / "tools/allagma.py"), "campaign", "start", "--study", str(ROOT), "--campaign", "culp-v1"], check=True)
entries = {}
for module in ["recipe/research", "context", "research/scope", "research/protocol", "research/experiment", "research/analysis", "research/writing", "research/audit", "runner", "reviewer"]:
    result = subprocess.run([sys.executable, str(ROOT / BUNDLE / "tools/allagma.py"), "entry", "--study", str(ROOT), "--campaign", "culp-v1", "--module", module], check=True, capture_output=True, text=True)
    entries[module] = __import__("json").loads(result.stdout)
write(ROOT / "campaigns/culp-v1/resolved-methods.json", entries)
write(ROOT / "evidence/literature-map.json", {"network": "unavailable", "sources": [
    {"source": ref(ROOT / "inputs/materials/SOURCES.md"), "metadata": "Capsule DOI and CORE-Bench commit", "support": "Identifies supplied local capsule", "uncertainty": "DOI landing page and benchmark commit not remotely verified"},
    {"source": ref(ROOT / "inputs/materials/capsule-6460826/metadata/metadata.yml"), "metadata": "CULP title, authors, abstract", "support": "Local metadata only", "uncertainty": "Novelty and competitive performance claims untested; full paper unavailable"},
    {"source": ref(ROOT / "inputs/materials/capsule-6460826/code/README.md"), "metadata": "Dataset commands and GitHub URL", "support": "Direct execution scope", "uncertainty": "No requirements list or original version pins; run.sh absent"}]})
required = ["question", "constraints", "stop_rules", "protocol", "unresolved"]
records = {"question": brief["question"], "constraints": brief["constraints"], "stop_rules": brief["stop_rules"],
           "protocol": ref(ROOT / "campaigns/culp-v1/protocol.json"), "unresolved": ["Iris/Zoo label bug preserved", "Original environment and reference outputs absent", "No external literature access"]}
payload = {"context_id": "culp-v1-active", "required": required, "records": records, "relevant": [], "max_chars": 12000}
write(ROOT / "campaigns/culp-v1/context-input.json", payload)
subprocess.run([sys.executable, str(ROOT / BUNDLE / "methods/allagma-context-active-brief/select.py"), str(ROOT / "campaigns/culp-v1/context-input.json"), str(ROOT / "campaigns/culp-v1/context.json")], check=True)
print("Frozen campaign culp-v1 and resolved all canonical methods from its exact lock.")
