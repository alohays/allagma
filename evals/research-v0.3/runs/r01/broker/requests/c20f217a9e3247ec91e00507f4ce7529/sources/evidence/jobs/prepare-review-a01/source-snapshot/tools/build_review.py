"""Render reporting artifacts and prepare the exact revision for bounded review."""
import json
from pathlib import Path
from common import ROOT, now, ref, sha, write_json
from write_report import render

def claim(identity, text, supporting, limitations, dependencies=None):
    return {"schema_version": "0.2", "record_type": "ClaimRecord", "claim_id": identity,
        "text": text, "supporting": [ref(ROOT / p) for p in supporting], "contradicting": [],
        "dependencies": [ref(ROOT / p) for p in dependencies or ["analysis/record.json"]],
        "scope": "Supplied capsule, unchanged scientific configuration, local offline environment, fixed seed-42 partitions",
        "limitations": limitations, "status": "supported", "supersedes": None}

def main():
    campaign = ROOT / "campaigns/culp-reproduction"
    old = ROOT / "evidence/jobs/graph-audit-a01/source-snapshot/tools/audit_science.py"
    write_json(ROOT / "evidence/verification-revision.json", {
        "revision": "verification-v2", "reason": "Initial independent checker incorrectly treated self-loops; first saved Iris graph exposed disagreement",
        "prior_code": ref(old), "corrected_code": ref(ROOT / "tools/audit_science.py"),
        "failed_attempt": ref(ROOT / "evidence/jobs/graph-audit-a01/client-result.json"),
        "successful_attempt": ref(ROOT / "evidence/jobs/graph-audit-a02/client-result.json"),
        "evidence": ref(ROOT / "analysis/graph-audit.json"),
        "correction": "Degree counts self-loops twice; common-neighbor sets exclude queried endpoints, as NetworkX specifies",
        "affected_runs": [], "scientific_protocol_changed": False,
        "boundary": "Verifier-only correction under protocol editable evidence-check boundary. No rerun, data, parameter, source experiment or answer change.",
        "other_reporting_revisions": ["Writer expanded with graph-check finding and fresh verification evidence",
            "Broker bridge selects fresh environment metadata when present; actual interpreter is always recorded in argv",
            "Postconfirmation unprofiled and package verification tools added; confirmation runner, evaluator and analyzer unchanged"]})
    outputs = [ref(p) for p in sorted((ROOT / "analysis/primary").iterdir()) if p.is_file()]
    write_json(ROOT / "analysis/record.json", {"schema_version": "0.2", "record_type": "AnalysisRecord", "analysis_id": "culp-a001",
        "raw_manifest": ref(ROOT / "evidence/raw-manifest.json"), "analysis_revision": sha(ROOT / "tools/analyze.py"),
        "code": ref(ROOT / "tools/analyze.py"), "configuration": {"units": "percent", "minimum_confirmation_runs": 3,
            "fixed_split_per_dataset": True, "source_score": "round(100*float(numpy.mean(prediction==y_test)),2)",
            "independent_unit": "Dataset/fixed partition; retries and predictor calls are not independent repetitions"},
        "outputs": outputs, "exclusions": [{"attempt_id": "iris-a01", "reason": "Controlled interruption"},
            {"attempt_id": "pilot-a01", "reason": "Synthetic qualification only"},
            {"attempt_id": "fresh runs", "reason": "Reproduction agreement, not extra independent observations"}],
        "uncertainty": "No population interval: deterministic fixed-split reproduction with retained correct/total counts; no stochastic repetitions.",
        "dependencies": [ref(ROOT / p) for p in ["tools/evaluate.py", "tools/common.py", "campaigns/culp-reproduction/protocol.json",
            "analysis/recomputed/recomputation-check.json", "analysis/graph-audit.json", "reproduction/verified/agreement.json"]]})
    summary = json.loads((ROOT / "analysis/primary/summary.json").read_text())
    claims = []
    for dataset in ["iris", "zoo", "wine"]:
        rows = [r for r in summary["rows"] if r["dataset"] == dataset and r["printed_label"] in ["CN", "AA"]]
        for row in rows:
            claims.append(claim(dataset + "-" + row["printed_label"].lower(),
                f"{dataset.title()} source line labelled {row['printed_label']} reports {row['printed_percent']:.2f}% ({row['correct']}/{row['total']}); actual predictor {row['actual_predictor']}.",
                [f"analysis/primary/{dataset}-evaluation.json"],
                ["One source-prescribed fixed split; no population inference"] +
                (["Printed label does not identify the actual predictor: source hard-codes CS"] if dataset != "wine" else [])))
    claims.extend([
        claim("source-label-limitation", "Iris and Zoo hard-code CS for all four printed predictor labels; Wine selects lp.",
            ["source/original/code/iris_sample.py", "source/original/code/zoo_sample.py", "source/original/code/wine_sample.py"],
            ["No corrected CN/AA experiment was performed for Iris or Zoo"]),
        claim("recovery", "The controlled first marked Iris attempt was preserved and recovered by a new successful attempt without changing scientific inputs.",
            ["evidence/jobs/iris-a01/client-result.json", "evidence/jobs/iris-a02/client-result.json", "evidence/attempt-history.json"],
            ["Controller's original timed_out outcome is retained, with injected_interruption true"]),
        claim("recomputation", "Retained-data recomputation gives byte-identical six-answer report, summary and table; fresh-environment execution agrees on all six answers.",
            ["analysis/recomputed/recomputation-check.json", "reproduction/verified/agreement.json"],
            ["Deterministic reproduction checks do not create new statistical replicates"]),
        claim("graph-verification", "Independent retained-graph link scores agree within 1e-12 relative and absolute tolerance, with identical predictions.",
            ["analysis/graph-audit.json", "evidence/verification-revision.json"],
            ["Initial checker failed and was corrected for self-loops", "No proof for all possible inputs or external reference comparison"]),
        claim("unprofiled-execution", "All three scripts also execute normally without the capture hook and produce identical stdout.",
            ["verification/unprofiled/check.json"], ["Bounded check on these scripts and this environment"])
    ])
    write_json(ROOT / "claims.json", claims)
    (ROOT / "REPORT.md").write_text(render(ROOT / "analysis/primary"))
    findings = [
        {"id": "F1", "severity": "scientific interpretation", "finding": "CN/AA Iris/Zoo labels do not correspond to CN/AA algorithms",
         "evidence": ["source/original/code/iris_sample.py", "source/original/code/zoo_sample.py", "analysis/primary/summary.json"],
         "resolution": "Preserved original scoring and algorithms; report and claims explicitly identify actual CS; no unsupported corrected result supplied", "status": "disclosed upstream limitation"},
        {"id": "F2", "severity": "method limitation", "finding": "Graph includes test features; single fixed split is transductive and gives no cross-split variance",
         "evidence": ["source/original/code/culp/leg.py", "campaigns/culp-reproduction/protocol.json"],
         "resolution": "Describe transduction and independent unit; no generalization, population CI or superiority claim", "status": "bounded claims"},
        {"id": "F3", "severity": "source behavior", "finding": "Duplicate/tied neighbor ordering can leave self-loops when the source discards the first neighbor",
         "evidence": ["source/original/code/culp/leg.py", "analysis/graph-audit.json"],
         "resolution": "Preserve saved graphs and library semantics; document exact loop counts and version sensitivity", "status": "disclosed upstream limitation"},
        {"id": "F4", "severity": "verification defect", "finding": "Initial independent checker used incorrect degree/common-neighbor rules for self-loops and failed",
         "evidence": ["evidence/jobs/graph-audit-a01/client-stderr.txt", "evidence/verification-revision.json"],
         "resolution": "Retained failing revision and receipt; corrected checker only, reran as graph-audit-a02, verified every score and prediction", "status": "resolved"},
        {"id": "F5", "severity": "external evidence unavailable", "finding": "Original outputs, scorer, environment and paper experiments unavailable; network disabled",
         "evidence": ["inputs/materials/SOURCES.md", "evidence/literature-map.json"],
         "resolution": "Limit completeness to requested local capsule reproduction; do not claim historic numerical agreement or paper-level replication", "status": "unresolved external limitation"},
        {"id": "F6", "severity": "capture validity", "finding": "Instrumentation could in principle change execution",
         "evidence": ["tools/run_capsule.py", "verification/unprofiled/check.json"],
         "resolution": "Read-only return observation; unprofiled normal execution of all three scripts has identical stdout", "status": "resolved within tested scope"},
        {"id": "F7", "severity": "recovery integrity", "finding": "First marked scientific attempt interrupted by controller",
         "evidence": ["evidence/jobs/iris-a01/client-result.json", "evidence/jobs/iris-a02/client-result.json"],
         "resolution": "Preserve timed_out receipt and partial artifacts; exclude from answer evidence; rerun with new identity after terminal outcome", "status": "resolved"},
        {"id": "F8", "severity": "review scope", "finding": "Checklist backend is deterministic; critique comes from the same agent, not an independent scientific reviewer",
         "evidence": [".allagma/bundles/b-9a39b70665ba909edb8abc13/adapters/reviewer-checklist/README.md"],
         "resolution": "Assurance explicitly deterministic for checks; scientific critique provisional, with no claim of peer review", "status": "disclosed"},
        {"id": "F9", "severity": "interchange scope", "finding": "Supplied MEASUREMENTS.md lacks a CULP-specific schema",
         "evidence": ["inputs/materials/MEASUREMENTS.md", "measurements.json"],
         "resolution": "Use generic envelope and documented CULP array/call extension; do not claim compliance with unrelated task schemas", "status": "documented"}
    ]
    write_json(ROOT / "review-findings.json", {"reviewer": "Primary Codex agent; explicit source/method critique", "assurance": "provisional scientific critique",
        "review_revision": "culp-review-v1", "findings": findings,
        "criteria": ["Original task and scientific parameters preserved", "Results grounded in actual execution", "Recovery history intact",
            "Numerical reanalysis, unprofiled execution and fresh-environment checks", "Uncertainty and transduction interpreted correctly",
            "Exact current source/artifact revision with transitive evidence links", "Runnable full-reproduction and retained-data recomputation commands"]})
    fixed = ["REPORT.md", "report.json", "REPRODUCE.md", "measurements.json", "requirements.lock.txt", "protocol.json", "brief.json", "claims.json",
             "review-findings.json", "evidence/raw-manifest.json", "evidence/provenance.json", "evidence/source-adaptation.patch",
             "evidence/verification-revision.json", "evidence/literature-map.json", "evidence/attempt-history.json"]
    paths = [ROOT / p for p in fixed]
    for prefix in ["tools", "source", "analysis", "evidence/runs", "evidence/pilot", "evidence/setup", "verification/unprofiled", "reproduction/verified", "campaigns/culp-reproduction"]:
        paths.extend(p for p in (ROOT / prefix).rglob("*") if p.is_file() and "__pycache__" not in p.parts
                     and p.suffix != ".pyc" and p.name != "state.json" and "events" not in p.parts)
    paths = sorted(set(paths))
    write_json(ROOT / "review-material.json", {"format": "culp-review-material-v1", "files": [ref(p) for p in paths],
        "scope": "Exact manuscript, answers, science and reporting code, source provenance, raw science, analysis, commands and fresh-reproduction evidence; final review/check outputs are subsequent attestations"})
    write_json(ROOT / "review-input.json", {"study": ".", "material": ref(ROOT / "review-material.json"), "claims": claims,
        "criteria": json.loads((ROOT / "review-findings.json").read_text())["criteria"],
        "scientific_critique": ref(ROOT / "review-findings.json")})
    print(json.dumps({"review_material": ref(ROOT / "review-material.json"), "claims": len(claims), "files": len(paths)}, indent=2))

if __name__ == "__main__":
    main()
