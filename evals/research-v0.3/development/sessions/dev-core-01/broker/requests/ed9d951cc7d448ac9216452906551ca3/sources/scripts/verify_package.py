"""Final broker check of manifest and review identity; no experiments or training."""
import hashlib
import json
from pathlib import Path
import sys

root = Path.cwd().resolve()
lock = json.loads((root / "campaigns/core-culp/lock.yaml").read_text())
sys.path.insert(0, str(root / ".allagma/bundles" / lock["bundle_id"]))
from allagma.campaigns import audit_evidence
from allagma.contracts import validate_record
from allagma.bundles import verify_study
verify_study(root)
manifest = json.loads((root / "artifact-manifest.json").read_text())
for ref in manifest["files"]:
    path = root / ref["path"]
    assert path.is_file(), ref["path"]
    assert path.stat().st_size == ref["size_bytes"], ref["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ref["sha256"], ref["path"]
review = json.loads((root / "review.json").read_text())
validate_record(review)
links = audit_evidence(root, review)
assert review["verdict"] == "pass"
submission = json.loads((root / "submission.json").read_text())
assert submission["execution_status"] == "complete"
for key in ["report", "manuscript", "review", "artifact_manifest"]:
    assert (root / submission[key]).is_file()
for key in ["reproduce", "recompute"]:
    assert submission[key]["cwd"] == "." and (root / submission[key]["argv"][1]).is_file()
result = {"passed": True, "manifest_files_verified": len(manifest["files"]), "transitive_review_references_verified": len(links),
          "coverage": "Exact artifact sizes/hashes at verification, generated bundle lock freshness, reviewed material identity, all typed evidence references and submission paths. No new source execution or independent peer review.",
          "manifest_sha256_at_verification": hashlib.sha256((root / "artifact-manifest.json").read_bytes()).hexdigest(),
          "sealing_note": "Final completed broker receipt and this check are archived after execution; manifest is then resealed as bookkeeping."}
print(json.dumps(result, indent=2))
(root / "evidence/final-verification.json").write_text(json.dumps(result, indent=2) + "\n")
