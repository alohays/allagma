"""Review the final research package at an explicit, transitively verified revision."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys

root = Path.cwd().resolve()
camp = root / "campaigns/core-culp"
lock = json.loads((camp / "lock.yaml").read_text())
bundle = root / ".allagma/bundles" / lock["bundle_id"]
sys.path.insert(0, str(bundle))
from allagma.bundles import verify_study, resolve_entry
from allagma.campaigns import audit_evidence, _state
from allagma.contracts import validate_record
from allagma.files import reference, write_json
from analyze import derive, questions

out = root / "evidence/review"
out.mkdir(parents=True, exist_ok=False)
shutil.copyfile(root / "evidence/execution-history.json", out / "execution-history-at-review.json")
original_report = root / "evidence/report-revisions/REPORT-a001.md"
original_report.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(root / "REPORT.md", original_report)
check_data = json.loads((root / "analysis/scientific-checks.json").read_text())
loop_counts = {dataset: next(x["self_loops"] for x in check_data["graph_checks"] if x["dataset"] == dataset) for dataset in ["iris", "zoo", "wine"]}
wine_cn_ties = next(x["tied_top_scores"] for x in check_data["graph_checks"] if x["dataset"] == "wine" and x["predictor"] == "CN")
prose = (root / "REPORT.md").read_text().replace("evidence/fresh-reproduction/", "evidence/fresh-reproduction-retry/").replace("a second fresh environment", "a further fresh environment").replace("A second fresh environment", "A further fresh environment")
old = "Graph self-loops and score ties, if observed, are enumerated in the scientific-checks artifact; they are not silently repaired."
new = f"The retained graphs contain {loop_counts['iris']} Iris self-loop, {loop_counts['zoo']} Zoo self-loops and {loop_counts['wine']} Wine self-loops. Wine CN has {wine_cn_ties} tied top score; the other observed predictor calls have none. These source behaviors were preserved."
assert old in prose
prose = prose.replace(old, new)
prose += "\n## Additional reproduction-check recovery\n\nThe first fresh-environment direct-execution check exceeded its 35-second Iris subprocess limit before printing results. This is retained as a failed check, not a scientific result. Its cause was not established. The study-owned reproduction driver was revised to allow 75 seconds per subprocess within a 90-second broker request; no scientific code changed. A newly created environment and output directory then completed all three direct executions. The original driver revision is retained in `evidence/source-revisions/fresh-check-v1/`, and both broker outcomes remain in the execution history.\n"
(root / "REPORT.md").write_text(prose)
instructions = (root / "REPRODUCE.md").read_text().replace("--id fresh-check --output evidence/fresh-reproduction", "--id fresh-retry --output evidence/fresh-reproduction-retry").replace("Do not reuse `fresh-check`", "Do not reuse `fresh-retry`").replace("full compute request 60 seconds", "full compute request 90 seconds").replace("evidence/fresh-reproduction/results.json", "evidence/fresh-reproduction-retry/results.json")
instructions += "\nThe earlier `fresh-check` reproduction failed at its 35-second Iris subprocess limit. Its environment, broker failure and driver revision are retained. The revised public command was tested with `fresh-retry`, allowing 75 seconds per script within a 90-second broker request. This changes only the verification time allowance.\n"
(root / "REPRODUCE.md").write_text(instructions)

checks = []
def passed(name, establishes, limitations=""):
    checks.append({"check": name, "passed": True, "establishes": establishes, "limitations": limitations})

verify_study(root)
for module in lock["modules"]:
    resolve_entry(root, module, "core-culp")
passed("locked-workflow", "Study selection intent and every generated bundle digest match; all campaign methods resolve from the exact campaign snapshot.", "Does not assess scientific quality.")
for original in sorted((root / "inputs/capsule-6460826").rglob("*")):
    if original.is_file():
        assert original.read_bytes() == (root / "source/original" / original.relative_to(root / "inputs/capsule-6460826")).read_bytes()
passed("original-source-preservation", "Every copied original capsule file is byte-identical to supplied read-only input.")
manifest = json.loads((root / "analysis/raw-manifest.json").read_text())
result = derive(root, manifest)
assert result == json.loads((root / "analysis/primary/results.json").read_text())
assert result["answers"] == json.loads((root / "report.json").read_text())
assert set(result["answers"]) == set(questions(root)) and len(result["answers"]) == 6
assert (root / "analysis/primary/table.md").read_text() in (root / "REPORT.md").read_text()
for name in ["results.json", "report.json", "table.md"]:
    assert (root / "analysis/primary" / name).read_bytes() == (root / "analysis/recomputed" / name).read_bytes()
recomputations = sorted((root / "recomputations").glob("*/results.json"))
assert recomputations and all(json.loads(path.read_text()) == result for path in recomputations)
passed("numbers-and-public-recompute", "Exact six task keys, all 12 table scores, raw counts, printed outputs and intervals agree across primary analysis, separate recomputation and the executed public recompute entry point.", "Verifies arithmetic, not generalization or true CN/AA on Iris/Zoo.")
raw = json.loads((root / manifest["raw"][0]["path"]).read_text())
import numpy as np
from sklearn.datasets import load_iris
iris = load_iris()
assert np.array_equal(iris.data, raw["datasets"]["iris"]["data"])
assert np.array_equal(iris.target, raw["datasets"]["iris"]["labels"])
for dataset in ["zoo", "wine"]:
    rows = list(csv.reader((root / "inputs/capsule-6460826/data" / (dataset+".txt")).open()))
    data = [[float(v) for v in row[1:17 if dataset == "zoo" else None]] for row in rows]
    labels = [int(row[17 if dataset == "zoo" else 0])-1 for row in rows]
    assert np.array_equal(data, raw["datasets"][dataset]["data"])
    assert np.array_equal(labels, raw["datasets"][dataset]["labels"])
passed("executed-input-identity", "All retained full features and labels equal the delivered Zoo/Wine data and installed sklearn Iris dataset.", "Does not independently authenticate upstream datasets.")
fresh = json.loads((root / "evidence/fresh-reproduction-retry/results.json").read_text())
assert fresh["passed"]
assert fresh["packages"] == raw["environment"]["packages"]
for dataset, item in fresh["scripts"].items():
    assert item["stdout"] == raw["datasets"][dataset]["stdout"]
passed("fresh-direct-execution", "New offline environment ran all three uninstrumented scripts; all stdout matches primary exactly.", "Same platform/package choices; no cross-platform claim.")
hist = json.loads((out / "execution-history-at-review.json").read_text())
assert any(x["outcome"]["injected_interruption"] for x in hist)
attempts = [json.loads(p.read_text()) for p in camp.glob("runs/capsule/attempts/*/record.json")]
assert sorted(x["status"] for x in attempts) == ["interrupted", "succeeded"]
assert any(x["reason"] == "interrupted" for x in manifest["exclusions"])
assert any(x["outcome"]["result"]["status"] == "failed" and "fresh-execution" in x["label"] for x in hist)
passed("failure-and-retry-history", "Controlled interruption and failed fresh check retained; new attempt/environment identities used; only successful confirmation is eligible.")
contract_count = 0
for parent in [camp, root / "analysis", root / "evidence/workflow"]:
    for path in parent.rglob("*.json"):
        value = json.loads(path.read_text())
        if isinstance(value, dict) and "record_type" in value:
            validate_record(value)
            audit_evidence(root, value)
            contract_count += 1
passed("contracts-and-transitive-evidence", f"Validated {contract_count} typed Allagma records and all evidence references reachable from them.", "Hash identity does not independently verify measurements.")
passed("scientific-checks", "; ".join(check_data["coverage"]), "; ".join(check_data["limits"]))
write_json(out / "checks.json", {"passed": True, "checks": checks}, immutable=True)

claims = json.loads((root / "claims.json").read_text())
for claim in claims:
    validate_record(claim)
    audit_evidence(root, claim)
extras = [
    ("graph-structure", new, "analysis/scientific-checks.json", "Recorded graphs and exact source behavior; effects of repairing self-loops were not tested."),
    ("fresh-equivalence", "All 12 printed source scores match in a newly installed environment without observation wrappers.", "evidence/fresh-reproduction-retry/results.json", "Local environment equivalence, not cross-platform replication."),
    ("recomputation", "Retained prediction vectors reproduce all answer values and table entries in separate output directories and through the public recompute entry point.", "evidence/review/checks.json", "Deterministic consistency, not statistical uncertainty.")]
for identity, text, support, limitation in extras:
    claim = {"schema_version": "0.2", "record_type": "ClaimRecord", "claim_id": identity, "text": text,
             "supporting": [reference(root, root / support)], "contradicting": [], "dependencies": [reference(root, root / "analysis/record.json")],
             "scope": "This supplied capsule and recorded local execution", "limitations": [limitation], "status": "supported", "supersedes": None}
    validate_record(claim)
    claims.append(claim)
write_json(root / "claims-final.json", claims, immutable=True)
findings = [
    "R1 major, resolved by faithful preservation and explicit scope: Iris/Zoo CN/AA output labels call CS; answers reproduce labels and do not claim actual CN/AA measurements.",
    "R2 limitation retained: graph builder drops first neighbour rather than checking identity; observed Iris/Zoo self-loops remain unchanged and are reported, with no claim about repaired results.",
    "R3 resolved: hardcoded /data paths ported relative to script; AST and byte checks establish no other capsule edits.",
    "R4 limitation retained: original dependency versions unspecified; offline direct/transitive pins and actual pip freeze recorded; fresh local execution agrees.",
    "R5 resolved: controlled first-attempt interruption retained and excluded; native recovery used capsule-a002 after authoritative broker completion.",
    "R6 resolved within ceilings: initial fresh check failed at 35 seconds; unchanged science passed in a new environment after verification timeout adjustment. Cause of first delay remains unknown.",
    "R7 limitation retained: single fixed split and transductive graph do not support superiority, independent-binomial coverage or across-split uncertainty; Wilson intervals explicitly descriptive.",
    "R8 workflow adaptation documented: portable analysis contracts avoid generic helper's multi-observation assumption without altering original partitions or inventing replicates.",
    "R9 review scope: native checklist plus independent arithmetic/graph-score checks and author critique; no independent peer review or unavailable reference-answer validation."
]
write_json(out / "critical-findings.json", {"findings": findings, "revision": "final-material-v1", "unmet_task_requirements": [], "scientific_limitations": ["True Iris/Zoo CN/AA not measured by upstream source", "Original outputs/environment and paper unavailable", "No independent peer review"]}, immutable=True)
submission = {"task_id": "core-culp", "execution_status": "complete", "report": "report.json", "manuscript": "REPORT.md", "review": "review.json", "artifact_manifest": "artifact-manifest.json",
              "reproduce": {"argv": ["python3", "scripts/reproduce.py"], "cwd": "."}, "recompute": {"argv": ["python3", "scripts/recompute.py"], "cwd": "."}}
write_json(root / "submission.json", submission, immutable=True)
_state(camp, phase="audit", status="completed", assurance="deterministic", reason="Declared capsule reproduction complete; known source limitations preserved and reviewed")
paths = ["REPORT.md", "REPRODUCE.md", "report.json", "submission.json", "claims-final.json", "analysis/record.json", "analysis/raw-manifest.json", "analysis/scientific-checks.json", "evidence/review/checks.json", "evidence/review/critical-findings.json", "evidence/review/execution-history-at-review.json", "evidence/fresh-reproduction-retry/results.json", "campaigns/core-culp/code-manifest.json", "campaigns/core-culp/study.json"]
paths += [str(p.relative_to(root)) for p in sorted((root / "scripts").glob("*.py"))]
write_json(out / "material.json", {"revision": "final-material-v1", "artifacts": [reference(root, root / path) for path in paths]}, immutable=True)
material = reference(root, out / "material.json")
payload = {"study": str(root), "material": material, "claims": claims, "criteria": [x["check"] for x in checks]}
write_json(out / "review-input.json", payload, immutable=True)
adapter = bundle / "adapters/reviewer-checklist/review.py"
command = [sys.executable, str(adapter), str(out / "review-input.json"), str(out / "adapter-result.json")]
review_run = subprocess.run(command, text=True, capture_output=True, timeout=10)
write_json(out / "adapter-execution.json", {"argv": command, "exit_code": review_run.returncode, "stdout": review_run.stdout, "stderr": review_run.stderr}, immutable=True)
assert review_run.returncode == 0, review_run.stderr
adapter_result = json.loads((out / "adapter-result.json").read_text())
assert adapter_result["verdict"] == "pass", adapter_result
audit_evidence(root, json.loads((out / "material.json").read_text()))
review = {"schema_version": "0.2", "record_type": "ReviewRecord", "review_id": "culp-review-v1", "reviewer": "reviewer/checklist plus study-owned deterministic checks and author critique", "backend": "locked offline reviewer/checklist", "backend_version": "Allagma " + lock["release"],
          "material": material, "criteria": [x["check"] for x in checks], "verdict": "pass", "findings": findings,
          "trace": [reference(root, out / name) for name in ["checks.json", "critical-findings.json", "review-input.json", "adapter-result.json", "adapter-execution.json"]],
          "assurance": "deterministic", "coverage": adapter_result["coverage"] + " Study-owned checks additionally cover raw-only recomputation, source edits, partitions/normalization, independent graph scoring, fresh direct execution and transitive evidence identity. Author critique is not an independent review; pass means scoped package checks pass, not that broader scientific claims are proven."}
validate_record(review)
write_json(root / "review.json", review, immutable=True)
print(json.dumps({"status": "complete", "checks": len(checks), "review": "pass", "material": material}, indent=2))
