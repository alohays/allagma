"""Finalize review and package inventory (bookkeeping only, no experiments)."""
import json
import os
from pathlib import Path
import sys
from common import ROOT, now, ref, sha, write_json

def main():
    locked = json.loads((ROOT / "verification/locked-review.json").read_text())
    checked = json.loads((ROOT / "verification/preseal.json").read_text())
    assert locked["verdict"] == "pass" and checked["passed"]
    findings = json.loads((ROOT / "review-findings.json").read_text())
    review = {"schema_version": "0.2", "record_type": "ReviewRecord", "review_id": "culp-review-v1",
        "reviewer": "Locked Allagma reviewer/checklist plus primary-agent critique and study-owned executable verification",
        "backend": "reviewer/checklist + tools/verify_package.py + primary Codex source critique",
        "backend_version": "Allagma 0.3.0rc1, bundle b-9a39b70665ba909edb8abc13; code revisions in review material",
        "material": ref(ROOT / "review-material.json"), "criteria": findings["criteria"], "verdict": "pass",
        "findings": [f"{f['id']}: {f['finding']} Resolution: {f['resolution']} Status: {f['status']}." for f in findings["findings"]],
        "trace": [ref(ROOT / p) for p in ["review-input.json", "review-findings.json", "verification/locked-review.json", "verification/preseal.json",
            "analysis/recomputed/recomputation-check.json", "analysis/graph-audit.json", "verification/unprofiled/check.json", "reproduction/verified/agreement.json"]],
        "assurance": "deterministic", "coverage": "Locked adapter: claim schemas and direct evidence/material digests. Study verifier: exact source adaptations, preconfirmation science revision, transitive references, six answers, manuscript rendering, 120 arrays versus fresh execution, interruption recovery and measurement archives. Agent critique is provisional, not independent scientific peer review. No original-output agreement or generalization claim."}
    write_json(ROOT / "review.json", review)
    # Separate final accounting avoids altering the already reviewed history.
    receipts = []
    for base in [ROOT / "evidence/jobs", ROOT / "reproduction/verified/jobs"]:
        for p in sorted(base.glob("*/client-result.json")):
            value = json.loads(p.read_text())
            before = json.loads((p.parent / "before.json").read_text())
            receipts.append({"category": before["category"], "identity": before["identity"], "receipt": ref(p),
                             "charged_seconds": value["result"]["charged_seconds"], "status": value["result"]["status"]})
    for base in [ROOT / "evidence/setup/venv", ROOT / "evidence/setup/packages"]:
        for p in base.glob("*.json"):
            value = json.loads(p.read_text())
            if "result" in value:
                receipts.append({"category": "setup", "identity": base.name, "receipt": ref(p),
                    "charged_seconds": value["result"]["charged_seconds"], "status": value["result"]["status"]})
    write_json(ROOT / "evidence/resources-at-seal.json", {"receipts": receipts,
        "charged_seconds": {cat: sum(r["charged_seconds"] for r in receipts if r["category"] == cat) for cat in ["setup", "compute"]},
        "compute_requests": sum(r["category"] == "compute" for r in receipts),
        "scope": "Copied broker charges through review; final package verification adds one compute request and its separate retained receipt. Controller accounting is authoritative.",
        "ceilings": {"compute_seconds": 600, "setup_seconds": 300, "compute_requests": 32, "native_wall_seconds": 3600}})
    submission = {"task_id": "core-culp", "execution_status": "complete", "report": "report.json", "manuscript": "REPORT.md",
        "review": "review.json", "artifact_manifest": "artifact-manifest.json", "measurements": "measurements.json",
        "reproduce": {"argv": ["python3", "tools/reproduce.py", "--env", ".venv-reproduce", "--output", "reproduction/fresh"], "cwd": "."},
        "recompute": {"argv": ["python3", "inputs/compute.py", "--category", "compute", "--label", "retained-recompute", "--timeout", "30", "--",
            ".venv/bin/python", "tools/analyze.py", "--manifest", "evidence/raw-manifest.json", "--out", "recomputation/submission", "--compare", "analysis/primary"], "cwd": "."},
        "completion_assessment": "Complete local execution, recovery, exact-question answers, retained-data verification, fresh-environment reproduction and scoped review. Original upstream limitations preserved. Historical reference-output agreement and true CN/AA measurements for Iris/Zoo are not established by the supplied code.",
        "unmet_requirements": [],
        "limitations": ["Iris/Zoo CN and AA printed labels actually use CS", "Original outputs/scorer/environment unavailable",
            "Fixed transductive split; no population confidence intervals", "Same-agent scientific critique with deterministic checks, not independent peer review",
            "CULP extension to generic measurement envelope; supplied task-specific schemas describe other tasks"],
        "verification": "verification/final.json", "final_verification_receipt": "evidence/jobs/final-package-a01/client-result.json",
        "resource_accounting": "evidence/resources-at-seal.json"}
    write_json(ROOT / "submission.json", submission)
    bundle = ROOT / ".allagma/bundles/b-9a39b70665ba909edb8abc13"
    sys.path.insert(0, str(bundle))
    from allagma.campaigns import _state
    _state(ROOT / "campaigns/culp-reproduction", phase="audit", status="complete", assurance="deterministic",
           reason="All planned local reproduction work and preseal checks passed; final sealed-file verification is the supplemental last check")
    write_json(ROOT / "evidence/workflow/completion.json", {"at": now(), "campaign": "culp-reproduction", "protocol_revision": "culp-v1",
        "steps": ["scope and evidence map", "frozen protocol and synthetic pilot", "confirmation with interruption/recovery",
                  "retained-data analysis and separate-directory recomputation", "evidence-linked manuscript and claims", "current-revision scoped audit"],
        "review": ref(ROOT / "review.json"), "preseal": ref(ROOT / "verification/preseal.json"),
        "method_execution": "Sequential portable artifact handoffs using exact locked methods; all executable science/setup via common broker"})
    skip_dirs = {".compute", ".tmp", ".git", "__pycache__", ".pytest_cache"}
    files = []
    for directory, dirs, names in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in skip_dirs and not d.startswith(".venv"))
        for name in sorted(names):
            p = Path(directory) / name
            rel = p.relative_to(ROOT).as_posix()
            if p.is_symlink() or name.endswith(".pyc") or name == ".DS_Store":
                continue
            if rel in ["artifact-manifest.json", ".allagma/mutation.lock", "verification/final.json"] or rel.startswith("evidence/jobs/final-package-"):
                continue
            files.append({**ref(p), "bytes": p.stat().st_size})
    write_json(ROOT / "artifact-manifest.json", {"format": "sha256-artifact-manifest-v1", "created_at": now(),
        "files": sorted(files, key=lambda f:f["path"]),
        "exclusions": ["artifact-manifest.json (self-hash cycle)", ".venv* environments", "__pycache__/.pyc and other caches", ".compute transient queue/deliveries (permanent copies retained under evidence)",
            ".tmp and .git", ".allagma/mutation.lock (transient mutex)",
            "verification/final.json and evidence/jobs/final-package-* (supplemental final verification attestations, excluded to avoid hash cycles)"],
        "reviewed_material_sha256": sha(ROOT / "review-material.json")})
    print(json.dumps({"files": len(files), "artifact_manifest_sha256": sha(ROOT / "artifact-manifest.json"), "reviewed_material_sha256": sha(ROOT / "review-material.json")}, indent=2))

if __name__ == "__main__":
    main()
