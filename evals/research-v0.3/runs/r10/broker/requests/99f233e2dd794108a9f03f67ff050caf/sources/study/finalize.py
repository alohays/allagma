"""Bookkeeping: prepare revision-bound review and assemble final submission metadata."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from common import ROOT, read, ref, tree_manifest, write


def prepare_review():
    files = [ROOT / p for p in ["report.json", "REPORT.md", "REPRODUCE.md", "measurements.json",
        "requirements-lock.txt", "provenance/source-manifest.json", "provenance/environment.json",
        "provenance/platform.patch", "evidence/raw-manifest.json", "evidence/recovery.json",
        "evidence/verification.json", "evidence/critique.json", "evidence/literature-map.json",
        "evidence/pilot/qualification.json", "analysis/main/results.json", "analysis/main/report.json",
        "analysis/recomputed/comparison.json", "recomputations/verification/comparison.json",
        "reproductions/verification/complete.json", "reproductions/verification/comparison.json",
        "reproductions/verification/vanilla/verification.json", "campaigns/culp-v1/protocol.json",
        "campaigns/culp-v1/lock.yaml", "campaigns/culp-v1/code-manifest.json", "campaigns/culp-v1/analysis-record.json"]]
    files += list((ROOT / "study").glob("*.py")) + list((ROOT / "campaigns/culp-v1/claims").glob("*.json"))
    material = ROOT / "evidence/review-material.json"
    write(material, {"format": "culp-review-material-v1", "files": tree_manifest(files),
        "scope": "Scientific source, outputs, methods, manuscript, reproduction entrypoints and ten scoped claims at these exact digests",
        "excludes": "Final submission/manifest bookkeeping and future broker receipts; none alter scientific content"})
    criteria = ["Exact original task strings and original percentage scoring", "Only documented platform source edits",
        "Evidence connects printed values, actual predictors, saved labels and graph predictions", "Frozen protocol and input partitions respected",
        "Interruption retained and recovered with a new identity", "Fresh setup, all three scripts and retained-data recomputation actually tested",
        "Claims restricted to fixed-split script output; upstream limitations and review scope disclosed", "Current source/artifact hashes and evidence links resolve"]
    write(ROOT / "evidence/review-input.json", {"study": str(ROOT), "material": ref(material),
        "criteria": criteria, "claims": [read(p) for p in sorted((ROOT / "campaigns/culp-v1/claims").glob("*.json"))],
        "backend": "Locked reviewer/checklist, offline deterministic direct-evidence checker",
        "additional_check": ref(ROOT / "evidence/verification.json")})
    print("Prepared exact material digest and explicit review criteria.")


def finalize_review():
    checklist = read(ROOT / "evidence/checklist-output.json")
    technical = read(ROOT / "evidence/verification.json")
    assert checklist["verdict"] == "pass" and technical["status"] == "pass"
    critique = read(ROOT / "evidence/critique.json")
    lock = read(ROOT / "campaigns/culp-v1/lock.yaml")
    findings = [f"{f['id']} ({f['status']}): {f['finding']} Resolution: {f['resolution']}" for f in critique["findings"]]
    review = {"schema_version": "0.2", "record_type": "ReviewRecord", "review_id": "culp-review-v1",
        "reviewer": "Locked Allagma deterministic checklist plus study-owned technical checks and author critique",
        "backend": "reviewer/checklist + study/verify.py", "backend_version": lock["modules"]["reviewer/checklist"]["revision"],
        "material": ref(ROOT / "evidence/review-material.json"), "criteria": read(ROOT / "evidence/review-input.json")["criteria"],
        "verdict": "pass", "findings": findings,
        "trace": [ref(ROOT / p) for p in ["evidence/review-input.json", "evidence/checklist-output.json", "evidence/verification.json",
            "evidence/critique.json", "analysis/recomputed/comparison.json", "recomputations/verification/comparison.json",
            "reproductions/verification/comparison.json", "reproductions/verification/vanilla/verification.json"]],
        "assurance": "deterministic", "coverage": checklist["coverage"] +
            " Technical audit additionally verifies all 12 saved predictions from graph edges, six scores from stdout/counts, original input rows and partitions, preprocessing, fixed source and parameters, dependency hashes, recovery and manuscript table. Fresh isolated and direct executions agree. Critique is by the author, not independent peer review. Pass means the supplied script-reproduction package is supported at the material digest; original reference-answer agreement and broader scientific validity remain unassessed."}
    write(ROOT / "review.json", review)
    write(ROOT / "campaigns/culp-v1/review-record.json", review)
    submission = {"task_id": "core-culp", "execution_status": "complete", "report": "report.json", "manuscript": "REPORT.md",
        "review": "review.json", "artifact_manifest": "artifact-manifest.json", "measurements": "measurements.json",
        "reproduce": {"argv": ["python3", "study/reproduce.py"], "cwd": "."},
        "recompute": {"argv": ["python3", "study/recompute.py"], "cwd": "."},
        "completion_assessment": "All three required scripts executed; six original printed scores independently recomputed; controlled interruption retained/recovered; fresh isolated setup and uninstrumented runs verified; locked review passed. Complete for supplied executable task, with disclosed scientific limitations.",
        "unmet_required_deliverables": [],
        "limitations": ["Iris/Zoo print CN/AA labels while executing CS", "Original environment and original outputs unavailable", "Single prescribed split; no population uncertainty or algorithm ranking", "Deterministic checks and author critique, not independent peer review"]}
    write(ROOT / "submission.json", submission)
    state = {"phase": "audit", "execution_status": "complete", "assurance": "deterministic", "stop_reason": "Declared script-reproduction completeness; scoped limitations disclosed", "review": ref(ROOT / "review.json")}
    write(ROOT / "campaigns/culp-v1/events/completion.json", {"at": datetime.now(timezone.utc).isoformat(), **state})
    write(ROOT / "campaigns/culp-v1/state.json", state)
    print("Recorded review and complete submission for the supplied execution task.")


def manifest():
    excluded_dirs = {".git", ".compute", ".tmp", "__pycache__", ".pytest_cache"}
    excluded_files = {"artifact-manifest.json", ".DS_Store"}
    files = []
    for base, directories, names in os.walk(ROOT, followlinks=False):
        directories[:] = sorted(d for d in directories if d not in excluded_dirs and not d.startswith(".venv") and not (Path(base) / d).is_symlink())
        for name in sorted(names):
            path = Path(base) / name
            relative = path.relative_to(ROOT).as_posix()
            if name in excluded_files or name.endswith((".pyc", ".pyo")) or relative == ".allagma/mutation.lock" or path.is_symlink():
                continue
            if path.is_file():
                files.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    write(ROOT / "artifact-manifest.json", {"format": "sha256-artifact-manifest-v1", "task_id": "core-culp", "files": sorted(files, key=lambda x: x["path"]),
        "excluded": ["artifact-manifest.json (self-reference)", ".venv* environments", ".compute transient queue/convenience receipts (permanent copies retained under evidence/broker)", ".tmp", "__pycache__ and other caches", ".git", ".allagma/mutation.lock", "symlinks and .DS_Store"],
        "scope": "All retained regular workspace files except listed exclusions; includes supplied wheelhouse, raw unsuccessful history, pinned workflow, adapted/original sources and final deliverables"})
    print(f"Inventoried {len(files)} retained regular files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare-review", "finalize-review", "manifest"])
    mode = parser.parse_args().mode
    {"prepare-review": prepare_review, "finalize-review": finalize_review, "manifest": manifest}[mode]()
