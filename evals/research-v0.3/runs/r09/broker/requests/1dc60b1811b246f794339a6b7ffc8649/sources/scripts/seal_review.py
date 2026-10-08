"""Attach immutable artifact identities to the completed written review."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / "review.json"
    review = json.loads(target.read_text())
    files = [ROOT / p for p in ["PROTOCOL.md", "REPORT.md", "REPRODUCE.md", "report.json", "submission.json",
              "requirements.lock", "evidence/source-revision.json", "evidence/compatibility.patch",
              "evidence/environment.json", "evidence/run-index.json"]]
    for folder in ["source/original", "source/adapted", "scripts", "analysis", "evidence/attempts",
                   "evidence/review-history", "reproduction/fresh-check", "recomputed/entrypoint-check"]:
        files.extend(p for p in (ROOT / folder).rglob("*") if p.is_file()
                     and ".venv" not in p.parts and "__pycache__" not in p.parts and p.suffix != ".pyc")
    files = [p for p in files if str(p.relative_to(ROOT)) != "analysis/package-verification.json"]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
    revision = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    review["reviewed_revision"]["artifacts"] = hashes
    review["reviewed_revision"]["artifact_revision_sha256"] = revision
    target.write_text(json.dumps(review, indent=2) + "\n")
    print(json.dumps({"reviewed_files": len(hashes), "artifact_revision_sha256": revision}, indent=2))


if __name__ == "__main__":
    main()
