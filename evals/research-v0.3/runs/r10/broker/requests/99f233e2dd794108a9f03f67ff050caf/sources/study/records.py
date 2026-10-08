"""Bookkeeping: link immutable analysis and claim handoffs for the locked workflow."""
from common import ROOT, digest, read, ref, write

campaign = ROOT / "campaigns/culp-v1"
raw = read(ROOT / "evidence/raw-manifest.json")
results = read(ROOT / "analysis/main/results.json")
analysis = {"schema_version": "0.2", "record_type": "AnalysisRecord", "analysis_id": "culp-analysis-v1",
    "raw_manifest": ref(ROOT / "evidence/raw-manifest.json"), "analysis_revision": digest(ROOT / "study/analyze.py"),
    "code": ref(ROOT / "study/analyze.py"), "configuration": {"minimum_confirmation_runs": 3, "datasets": ["iris", "zoo", "wine"],
        "scoring": "Exact original numpy mean accuracy and Python round(..., 2)", "independent_predictor_check": "Retained graph edges; no capsule imports or kNN reconstruction"},
    "outputs": [ref(ROOT / p) for p in ["analysis/main/report.json", "analysis/main/results.json", "analysis/main/results-table.md", "analysis/recomputed/comparison.json"]],
    "exclusions": raw["exclusions"], "uncertainty": results["uncertainty"]["reason"] + " " + results["uncertainty"]["scope"],
    "dependencies": [ref(ROOT / "campaigns/culp-v1/protocol.json"), ref(ROOT / "provenance/source-manifest.json"), ref(ROOT / "provenance/environment.json")]}
write(campaign / "analysis-record.json", analysis)
for row in results["rows"]:
    if row["printed_label"] not in ("CN", "AA"):
        continue
    identity = f"{row['dataset']}-{row['printed_label'].lower()}"
    directory = next(r["directory"] for r in raw["runs"] if r["dataset"] == row["dataset"])
    claim = {"schema_version": "0.2", "record_type": "ClaimRecord", "claim_id": identity,
        "text": f"The supplied {row['dataset'].capitalize()} script prints {row['accuracy_percent']:.2f}% under {row['printed_label']}; saved predictions have {row['correct']} correct among {row['test_n']}. The actual executed predictor is {row['executed_predictor']}.",
        "supporting": [row["arrays"], ref(ROOT / directory / "stdout.txt"), ref(ROOT / directory / "calls.json"), ref(ROOT / "analysis/main/results.json")],
        "contradicting": [], "dependencies": [ref(campaign / "analysis-record.json"), ref(ROOT / "evidence/raw-manifest.json"), ref(ROOT / "study/analyze.py")],
        "scope": "Only the supplied script's printed task output at fixed random_state=42 with documented source/library versions",
        "limitations": ["One fixed split; no population accuracy or replicate uncertainty", "Original environment/reference outputs unavailable"] +
                        (["The CN/AA label does not identify the executed algorithm; the upstream script uses CS"] if row["dataset"] != "wine" else []),
        "status": "supported", "supersedes": None}
    write(campaign / "claims" / f"{identity}.json", claim)
for identity, text, supporting, scope, limitations in [
    ("upstream-labels", "Iris and Zoo print four predictor names but call CS on all four iterations; Wine dispatches the loop's predictor.",
     ["work/capsule/code/iris_sample.py", "work/capsule/code/zoo_sample.py", "work/capsule/code/wine_sample.py", "raw/iris-a002/calls.json", "raw/zoo-a001/calls.json", "raw/wine-a001/calls.json"],
     "Static supplied source and observed call arguments", ["No corrected-algorithm Iris/Zoo comparison performed"]),
    ("graph-loops", "Saved confirmation graphs contain 1 Iris self-loop, 28 Zoo self-loops and no Wine self-loops; the original neighbor-slicing behavior was preserved.",
     ["analysis/main/results.json", "work/capsule/code/culp/leg.py"], "Only the retained graphs in this local environment",
     ["No source repair or claim that tie order is identical in the unavailable original dependency versions"]),
    ("fresh-reproduction", "A fresh isolated environment reproduces all six answers and all 12 call measurements; direct uninstrumented source stdout exactly matches the observed execution.",
     ["reproductions/verification/comparison.json", "reproductions/verification/vanilla/verification.json", "reproductions/verification/complete.json"],
     "Same supplied Mac and pinned offline packages", ["Not an independent-host or historical-environment replication"]),
    ("interruption-recovery", "The marked Iris attempt was interrupted by the controller, retained and excluded; the distinct successor completed successfully.",
     ["evidence/recovery.json", "campaigns/culp-v1/runs/iris/attempts/iris-a001/record.json", "campaigns/culp-v1/runs/iris/attempts/iris-a002/record.json"],
     "One configured controlled interruption", ["Does not establish recovery from every failure mode"])
]:
    write(campaign / "claims" / f"{identity}.json", {"schema_version": "0.2", "record_type": "ClaimRecord", "claim_id": identity,
        "text": text, "supporting": [ref(ROOT / p) for p in supporting], "contradicting": [],
        "dependencies": [ref(campaign / "analysis-record.json"), ref(ROOT / "evidence/raw-manifest.json")],
        "scope": scope, "limitations": limitations, "status": "supported", "supersedes": None})
print("Linked AnalysisRecord and ten scoped ClaimRecords to retained evidence.")
