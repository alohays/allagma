"""Create study-owned planning artifacts and source provenance (no science)."""
import difflib
import json
import shutil
from common import ROOT, now, ref, write_json

def main():
    original = ROOT / "source/original"
    adapted = ROOT / "source/adapted"
    changes = []
    files = []
    for p in sorted(original.rglob("*")):
        if not p.is_file():
            continue
        relative = p.relative_to(original)
        a = adapted / relative
        files.append({"original": ref(p), "adapted": ref(a),
                      "supplied": ref(ROOT / "inputs/materials/capsule-6460826" / relative)})
        if p.read_bytes() != a.read_bytes():
            changes.extend(difflib.unified_diff(p.read_text().splitlines(True), a.read_text().splitlines(True),
                                               fromfile=str(p.relative_to(ROOT)), tofile=str(a.relative_to(ROOT))))
    (ROOT / "evidence/source-adaptation.patch").write_text("".join(changes))
    write_json(ROOT / "evidence/provenance.json", {"capsule": "capsule-6460826", "files": files,
        "adaptation": "Only Wine/Zoo /data filenames replaced by capsule-relative pathlib paths; imports added",
        "diff": ref(ROOT / "evidence/source-adaptation.patch"),
        "preserved_limitation": "Iris and Zoo execute CS for all four printed predictor labels"})
    write_json(ROOT / "evidence/literature-map.json", {"network": False, "entries": [
        {"source_metadata": {"title": "CULP: Classification Using Link Prediction", "authors": ["Seyed Amin Fadaee", "Maryam Amir Haeri"],
                             "doi_as_supplied": "10.24433/CO.0609cc4f-8b95-4d94-8fd0-9456d262b3a5"},
         "source_location": "inputs/materials/capsule-6460826/metadata/metadata.yml",
         "support_assessment": "Metadata supports attribution and intended algorithm description; source code supports actual sample behavior",
         "uncertainties": ["No network metadata verification", "No paper text or historic output provided", "Abstract performance/novelty claims not verified"]},
        {"source_metadata": {"selection": "CORE-Bench public training capsule", "commit": "e32a2980e72fe6eb04ee04eb749458f570625663"},
         "source_location": "inputs/materials/SOURCES.md", "support_assessment": "User-supplied provenance; local selected-task execution only",
         "uncertainties": ["Not an independent upstream commit lookup or leaderboard evaluation"]}]})
    brief = {"study_id": "r01", "question": "Reproduce the supplied CULP sample scripts and answer the six exact source-task CN/AA questions.",
        "motivation": "Traceable computational reproduction with honest interpretation of source limitations.",
        "success_criteria": ["Known-answer synthetic pilot passes", "All three original script computations complete without scientific edits",
            "Six exact original question keys answered from observed stdout and retained predictions", "Controlled interruption retained and recovered with a new identity",
            "Retained-data recomputation and concrete current-revision critique pass within stated scope", "Fresh-environment reproduction and manifests delivered"],
        "constraints": ["All setup/scientific work through inputs/compute.py; sequential single worker", "No network",
            "600 seconds compute, 300 seconds setup, 32 compute requests, 180-second per-command ceiling",
            "3600-second native wall ceiling including model work", "No altered algorithms, seeds, partitions or scoring",
            "Preserve all attempts and source revisions; do not modify installed bundles or inputs"],
        "output": "report.json, REPORT.md, review.json, REPRODUCE.md, artifact-manifest.json, measurements.json, submission.json",
        "stop_rules": ["Declared bounded reproduction completion", "Resource or native deadline stop => partial package",
                       "Unresolved pilot failure stops confirmation", "Repeated failure or required unavailable input => honest partial/blocked assessment"]}
    write_json(ROOT / "brief.json", brief)
    code = [str(p.relative_to(ROOT)) for p in sorted((ROOT / "tools").glob("*.py"))]
    code += [str(p.relative_to(ROOT)) for p in sorted(adapted.rglob("*")) if p.is_file()]
    code += ["requirements.lock.txt"]
    protocol = {"revision": "culp-v1", "frozen_at": now(),
        "hypothesis": "The supplied scripts execute with path-only adaptation and yield internally verifiable printed accuracies; no presumed numeric target.",
        "runner": "tools/run_capsule.py", "evaluator": "tools/evaluate.py", "analyzer": "tools/analyze.py", "writer": "tools/write_report.py",
        "code": code, "minimum_confirmation_runs": 3, "paired_seeds": True,
        "run_group_interpretation": "Three separate datasets share the source's fixed seed; no paired statistical inference or independent retry replication",
        "runs": [{"id": "pilot", "split": "pilot", "input": {"seed": 123, "data": "synthetic-hand-defined", "kind": "known-answer"}}] + [
            {"id": dataset, "condition_id": dataset, "split": "confirmation", "input": {"seed": 42, "dataset": dataset,
                "test_size": 0.2, "stratify": None, "k": k, "similarity": "manhattan", "n_jobs": 1,
                "printed_predictors": ["CN", "AA", "RA", "CS"], "actual_predictors": ["CN", "AA", "RA", "CS"] if dataset == "wine" else ["CS"]*4}}
            for dataset, k in [("iris",11), ("zoo",2), ("wine",12)]],
        "independent_variables": "Dataset and source-defined link predictor; preserve source bugs",
        "baselines": "Source CN/AA/RA/CS calls where actually selected; no external comparative performance baseline",
        "metrics": "Original round(100*float(numpy.mean(prediction==y_test)),2); retain integer numerator/denominator",
        "uncertainty": "Deterministic fixed-split reproduction only. No population confidence interval or invented replicates.",
        "pilot": "Hand-known graph predictions for four predictors; two separated anchors; 2/3 accuracy, perfect/zero and invalid-shape controls. Seed identifier 123, no random or capsule data.",
        "completion": "Successful qualified all-three execution, six prediction-checked answers, separate-dir exact recomputation, graph check, revision-bound review, fresh-env reproduction and valid artifact package",
        "exclusions": ["Pilot excluded from task answers", "Failed/interrupted outputs excluded; all retained", "Fresh rerun is reproducibility check, not additional sample size"],
        "failure_criteria": ["Unresolved pilot qualification failure", "Missing/incorrect raw data or stdout disagreement", "Altered scientific source", "Digest mismatch", "Unreconciled worker state"],
        "fixed": ["Source algorithm and known predictor-label limitation", "Input datasets", "Seed 42, test_size 0.2, no stratification", "Original scoring and preprocessing", "k and Manhattan distance"],
        "editable": ["Portable file paths", "Capture/bookkeeping that does not alter source behavior", "Reporting and evidence checks"],
        "amendment_policy": "New scientific protocol revision requires new campaign and reason/affected-run handoff; reporting-only changes preserve prior snapshots",
        "resource_policy": json.loads((ROOT / "inputs/RESOURCES.json").read_text()),
        "execution_adapter": "Study-owned broker_job bridge to mandated common local broker, with portable Allagma records; no direct campaign subprocess science",
        "measurement_interchange": "MEASUREMENTS.md has no CULP-specific run schema. Use its generic format/task_id/protocol/runs envelope and an explicitly documented CULP extension."}
    write_json(ROOT / "protocol.json", protocol)
    # Preserve initial setup request/response deliveries as evidence, not transient queue references.
    for reqid, name in [("7f6a63c8dad9416dbcb663d3509f3d7f", "venv"), ("61b7bc100dec4a28908d2179d77223c9", "packages")]:
        dest = ROOT / "evidence/setup" / name
        dest.mkdir(parents=True, exist_ok=True)
        for p in (ROOT / ".compute/responses").glob(reqid + "*"):
            shutil.copyfile(p, dest / p.name)
        p = ROOT / ".compute/requests" / (reqid + ".json")
        if p.exists():
            shutil.copyfile(p, dest / "request.json")

if __name__ == "__main__":
    main()
