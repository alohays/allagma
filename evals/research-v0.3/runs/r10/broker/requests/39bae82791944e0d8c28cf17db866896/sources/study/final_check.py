"""Final package verification, run only through the scientific broker."""
import argparse
import json
from pathlib import Path
import re
import sys
from common import ROOT, digest, read, ref, verify_refs, write

parser = argparse.ArgumentParser()
parser.add_argument("--output", default="evidence/final-verification.json")
args = parser.parse_args()
submission = read(ROOT / "submission.json")
assert submission["task_id"] == "core-culp" and submission["execution_status"] == "complete"
for key in ("report", "manuscript", "review", "artifact_manifest", "measurements"):
    assert (ROOT / submission[key]).is_file()
for key in ("reproduce", "recompute"):
    assert submission[key]["cwd"] == "." and isinstance(submission[key]["argv"], list)
    assert all(isinstance(part, str) for part in submission[key]["argv"])
    assert (ROOT / submission[key]["argv"][1]).is_file()
assert submission["reproduce"]["argv"] == ["python3", "study/reproduce.py"]
assert submission["recompute"]["argv"] == ["python3", "study/recompute.py"]
review = read(ROOT / "review.json")
verify_refs([review["material"], *review["trace"]])
verify_refs(read(ROOT / review["material"]["path"])["files"])
assert review["verdict"] == "pass" and review["assurance"] == "deterministic"
sys.path.insert(0, str(ROOT / ".allagma/bundles/b-9a39b70665ba909edb8abc13"))
from allagma.contracts import validate_record
validate_record(review)
assert read(ROOT / "evidence/verification.json")["status"] == "pass"
assert read(ROOT / "reproductions/verification/complete.json")["status"] == "complete"
assert read(ROOT / "recomputations/verification/comparison.json")["status"] == "pass"
measurements = read(ROOT / "measurements.json")
assert measurements["format"] == "research-measurements-v1" and measurements["task_id"] == "core-culp"
assert len(measurements["runs"]) == 3
known = {(r["dataset"], r["printed_label"]): r for r in read(ROOT / "analysis/main/results.json")["rows"]}
for run in measurements["runs"]:
    assert run["phase"] == "confirmation" and run["seed"] == 42
    for call in run["calls"]:
        row = known[(run["dataset"], call["printed_label"])]
        assert call["arrays"] == row["arrays"]["path"] and call["executed_predictor"] == row["executed_predictor"]
        for key, value in call["metrics"].items():
            assert row[key] == value
links = []
for document in ("REPORT.md", "REPRODUCE.md"):
    for target in re.findall(r"\]\(([^)]+)\)", (ROOT / document).read_text()):
        if "://" not in target and not target.startswith("#"):
            assert (ROOT / target.split("#")[0]).exists(), (document, target)
            links.append({"document": document, "target": target})
artifacts = read(ROOT / "artifact-manifest.json")
paths = set()
for item in artifacts["files"]:
    path = ROOT / item["path"]
    assert not Path(item["path"]).is_absolute() and ".." not in Path(item["path"]).parts
    assert path.is_file() and not path.is_symlink()
    assert item["path"] not in paths
    paths.add(item["path"])
    assert path.stat().st_size == item["bytes"] and digest(path) == item["sha256"], item["path"]
assert {submission[k] for k in ("report", "manuscript", "review", "measurements")} <= paths
assert {"submission.json", "REPRODUCE.md", "evidence/raw-manifest.json", "requirements-lock.txt"} <= paths
write(ROOT / args.output, {"status": "pass", "review_material": review["material"], "checked_manifest_entries": len(paths),
    "coverage": ["Submission task ID, execution status, required artifact paths and exact executable reproduction/recomputation entrypoints",
                 "Review schema and exact reviewed material and trace digests", "Successful scientific audit and actually executed public reproduction/recomputation evidence",
                 "All CULP measurement metrics/paths match analysis", "Local manuscript/reproduction evidence links exist",
                 "Every listed artifact is a unique regular relative file with matching SHA-256 and size"],
    "limitations": "The manifest checked here predates this check's own receipt/output. Final bookkeeping adds these retained files and rehashes the manifest without changing reviewed scientific content.",
    "local_links_checked": len(links)})
print(f"Final package checks passed; {len(paths)} artifact hashes and {len(links)} document links verified.")
