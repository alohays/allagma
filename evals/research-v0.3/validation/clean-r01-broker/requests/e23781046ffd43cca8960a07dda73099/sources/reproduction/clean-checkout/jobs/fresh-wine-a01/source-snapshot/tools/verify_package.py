"""Broker-only scoped verification of the reviewed and sealed package."""
import argparse
import ast
import json
from pathlib import Path
import re
import sys
import numpy as np
from common import ROOT, check_ref, ref, sha, write_json

def verify(preseal=False):
    bundle = ROOT / ".allagma/bundles/b-9a39b70665ba909edb8abc13"
    sys.path.insert(0, str(bundle))
    from allagma.contracts import validate_record
    from allagma.campaigns import audit_evidence
    from allagma.bundles import verify_lock
    from write_report import render
    checks = []
    campaign = ROOT / "campaigns/culp-reproduction"
    lock = json.loads((campaign / "lock.yaml").read_text())
    verify_lock(ROOT, lock)
    assert json.loads((ROOT / "protocol.json").read_text()) == json.loads((campaign / "protocol.json").read_text())
    checks.append("Campaign lock content, selected exact bundle and frozen protocol identity verified")
    records = [campaign / "study.json", campaign / "context.json", ROOT / "analysis/record.json"]
    records += sorted(campaign.glob("runs/*/spec.json")) + sorted(campaign.glob("runs/*/attempts/*/record.json"))
    claims = json.loads((ROOT / "claims.json").read_text())
    allrecords = [json.loads(p.read_text()) for p in records] + claims
    if not preseal:
        allrecords.append(json.loads((ROOT / "review.json").read_text()))
    visited = set()
    for record in allrecords:
        validate_record(record)
        audit_evidence(ROOT, record, visited)
    checks.append(f"{len(allrecords)} Allagma records validate; {len(visited)} distinct evidence references verified transitively")
    # Explicitly limit capsule changes to the two approved path adaptations.
    provenance = json.loads((ROOT / "evidence/provenance.json").read_text())
    changed = []
    for item in provenance["files"]:
        original, adapted, supplied = [check_ref(item[k]) for k in ["original", "adapted", "supplied"]]
        assert original.read_bytes() == supplied.read_bytes()
        if original.read_bytes() != adapted.read_bytes():
            dataset = original.stem.split("_")[0]
            assert dataset in ["wine", "zoo"]
            expected = original.read_text().replace("import pandas\n", "import pandas\nfrom pathlib import Path\n")
            expected = expected.replace("'/data/" + dataset + ".txt'", "Path(__file__).resolve().parents[1] / 'data' / '" + dataset + ".txt'")
            assert expected == adapted.read_text()
            changed.append(dataset)
    assert sorted(changed) == ["wine", "zoo"]
    checks.append("All original copied capsule files match supplied bytes; only exact Wine/Zoo path edits exist")
    # The frozen scientific runner, evaluator and analyzer must still match.
    frozen = json.loads((campaign / "code-manifest.json").read_text())
    for path in ["tools/common.py", "tools/run_capsule.py", "tools/evaluate.py", "tools/analyze.py", "tools/pilot.py"]:
        assert sha(ROOT / path) == frozen[path]["sha256"], path
    checks.append("Scientific runner/evaluator/analyzer/pilot revisions match the preconfirmation snapshot")
    questions = ast.literal_eval(re.search(r"dict_keys\((\[.*?\])\)", (ROOT / "inputs/materials/task.txt").read_text()).group(1))
    answer = json.loads((ROOT / "report.json").read_text())
    assert sorted(answer) == sorted(questions) and len(answer) == 6
    for path in ["analysis/primary/report.json", "analysis/recomputed/report.json", "reproduction/verified/analysis/report.json"]:
        assert answer == json.loads((ROOT / path).read_text())
    summary = json.loads((ROOT / "analysis/primary/summary.json").read_text())
    for q in questions:
        dataset = re.search(r"for the (Iris|Zoo|Wine) dataset", q).group(1).lower()
        lp = re.search(r"Report the (CN|AA) prediction", q).group(1)
        row = next(r for r in summary["rows"] if r["dataset"] == dataset and r["printed_label"] == lp)
        assert answer[q] == row["printed_percent"]
    checks.append("Six exact original question strings and numerical answers agree with primary, recomputed and fresh-run evidence")
    assert (ROOT / "REPORT.md").read_text() == render(ROOT / "analysis/primary")
    checks.append("Entire manuscript equals deterministic rendering of verified analysis, including every results-table number")
    # Compare every retained scientific array across independently created environments.
    comparisons = 0
    for dataset, attempt in [("iris", "iris-a02"), ("zoo", "zoo-a01"), ("wine", "wine-a01")]:
        old = ROOT / "evidence/runs" / attempt
        new = ROOT / "reproduction/verified" / (dataset + "-a01")
        for a in sorted(old.glob("*.npz")):
            with np.load(a, allow_pickle=False) as left, np.load(new / a.name, allow_pickle=False) as right:
                assert sorted(left.files) == sorted(right.files)
                for key in left.files:
                    assert np.array_equal(left[key], right[key]), (dataset, a.name, key)
                    comparisons += 1
    checks.append(f"{comparisons} retained arrays (data/splits/graphs/scores/predictions/labels) exactly match fresh-environment execution")
    assert json.loads((ROOT / "analysis/graph-audit.json").read_text())["passed"]
    assert json.loads((ROOT / "verification/unprofiled/check.json").read_text())["passed"]
    assert json.loads((ROOT / "reproduction/verified/agreement.json").read_text())["answers_identical"]
    failed = json.loads((ROOT / "evidence/jobs/iris-a01/client-result.json").read_text())
    retried = json.loads((ROOT / "evidence/jobs/iris-a02/client-result.json").read_text())
    assert failed["injected_interruption"] and failed["result"]["status"] == "timed_out"
    assert retried["result"]["status"] == "completed" and failed["request_id"] != retried["request_id"]
    checks.append("Controlled interrupted attempt retained with exact original status and a distinct successful retry")
    measurement = json.loads((ROOT / "measurements.json").read_text())
    assert measurement["format"] == "research-measurements-v1" and measurement["task_id"] == "core-culp"
    assert measurement["protocol"] == "campaigns/culp-reproduction/protocol.json"
    assert len(measurement["runs"]) == 3
    for run in measurement["runs"]:
        for path in [run["arrays"]] + [c["arrays"] for c in run["calls"]]:
            with np.load(ROOT / path, allow_pickle=False) as data:
                for key in data.files:
                    assert data[key].dtype.kind != "O"
    checks.append("Generic measurement envelope and documented CULP extension contain valid pickle-free archives")
    # Ensure the inventory actually supplied to review still matches all reviewed files.
    material = json.loads((ROOT / "review-material.json").read_text())
    for item in material["files"]:
        check_ref(item)
    checks.append(f"All {len(material['files'])} files in the exact review material inventory match their hashes")
    final_hash = None
    if not preseal:
        review = json.loads((ROOT / "review.json").read_text())
        assert review["verdict"] == "pass" and review["assurance"] == "deterministic"
        check_ref(review["material"])
        manifest = json.loads((ROOT / "artifact-manifest.json").read_text())
        seen = set()
        for item in manifest["files"]:
            path = item["path"]
            assert path not in seen and not Path(path).is_absolute() and ".." not in Path(path).parts
            seen.add(path)
            p = check_ref(item)
            assert p.stat().st_size == item["bytes"]
        expected = {"report.json", "REPORT.md", "review.json", "REPRODUCE.md", "submission.json", "measurements.json"}
        assert expected <= seen
        final_hash = sha(ROOT / "artifact-manifest.json")
        submission = json.loads((ROOT / "submission.json").read_text())
        assert submission["task_id"] == "core-culp" and submission["execution_status"] == "complete"
        for key in ["report", "manuscript", "review", "artifact_manifest", "measurements"]:
            assert (ROOT / submission[key]).is_file()
        for key in ["reproduce", "recompute"]:
            assert isinstance(submission[key]["argv"], list) and all(isinstance(x,str) for x in submission[key]["argv"])
            assert submission[key]["cwd"] == "."
        checks.append(f"Sealed artifact manifest verifies {len(seen)} unique relative regular-file hashes and submission references")
    return {"passed": True, "preseal": preseal, "checks": checks, "artifact_manifest_sha256": final_hash,
        "reviewed_material_sha256": sha(ROOT / "review-material.json"),
        "limitations": ["Deterministic artifact/scientific-invariant checks, not independent scientific peer review",
                        "No historical outputs, original environment or scorer were supplied",
                        "Source CN/AA print labels for Iris/Zoo continue to represent CS calls",
                        "No population uncertainty or generalization claim from one fixed split"]}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preseal", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    value = verify(args.preseal)
    write_json(ROOT / args.out, value)
    print(json.dumps(value, indent=2))
