"""Final artifact consistency check; execute through the local broker."""
import ast
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from freeze_sources import main as verify_frozen_sources

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    submission = read("submission.json")
    assert submission["task_id"] == "core-culp" and submission["execution_status"] == "complete"
    for name in ["report", "manuscript", "review", "measurements"]:
        assert (ROOT / submission[name]).is_file()
    assert submission["artifact_manifest"] == "artifact-manifest.json"
    for name in ["reproduce", "recompute"]:
        command = submission[name]
        assert command["cwd"] == "." and all(isinstance(s, str) for s in command["argv"])
        assert (ROOT / command["argv"][1]).is_file()
    task = (ROOT / "inputs/materials/task.txt").read_text()
    keys = ast.literal_eval(re.search(r"dict_keys\((\[.*?\])\)", task).group(1))
    report = read("report.json")
    assert list(report) == keys and report == read("analysis/report.json")
    assert report == read("reproduction/fresh-check/analysis/report.json")
    assert report == read("recomputed/entrypoint-check/analysis/report.json")
    verify_frozen_sources()
    inputs = read("research-workspace.json")["common_inputs"]
    for relative, digest in inputs.items():
        assert sha(ROOT / "inputs" / relative) == digest, relative
    environment = read("evidence/environment.json")["packages"]
    for line in (ROOT / "requirements.lock").read_text().splitlines():
        if line:
            package, version = line.split("==")
            assert environment[package] == version, package
    review = read("review.json")
    reviewed = review["reviewed_revision"]["artifacts"]
    assert reviewed
    revision = hashlib.sha256(json.dumps(reviewed, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert revision == review["reviewed_revision"]["artifact_revision_sha256"]
    for path, digest in reviewed.items():
        assert sha(ROOT / path) == digest, path
    diagnostics = read("analysis/diagnostics.json")
    assert diagnostics["status"] == "passed" and diagnostics["fresh_run_comparison"]["all_arrays_exactly_equal"]
    assert read("analysis/verification.json")["checks"]["submitted_report_matches"] is True
    measurements = read(submission["measurements"])
    assert measurements["format"] == "research-measurements-v1" and measurements["task_id"] == "core-culp"
    assert measurements["protocol"] == "PROTOCOL.md" and len(measurements["runs"]) == 12
    for run in measurements["runs"]:
        path = ROOT / run["arrays"]
        assert path.is_file() and not path.is_symlink()
        with np.load(path, allow_pickle=False) as arrays:
            correct = int(np.count_nonzero(arrays["prediction"] == arrays["test_labels"]))
            assert correct == run["metrics"]["correct"]
            assert round(100 * correct / len(arrays["test_labels"]), 2) == run["metrics"]["accuracy_percent"]
    links = []
    for document in ["REPORT.md", "REPRODUCE.md"]:
        for link in re.findall(r"\]\(([^)]+)\)", (ROOT / document).read_text()):
            if "://" in link:
                continue
            path = link.split("#")[0]
            if path == "artifact-manifest.json":
                continue  # Created only after this verification and its receipt are finalized.
            assert (ROOT / path).exists(), (document, path)
            links.append(path)
    for path in (ROOT / "scripts").glob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
    output = {"status": "passed", "review_artifact_revision_sha256": revision,
              "reviewed_artifacts_verified": len(reviewed), "protected_input_files_verified": len(inputs),
              "local_document_links_verified": len(links), "measurement_calls_verified": 12,
              "checks": ["exact six original question keys and answers", "fresh and recomputed reports equal",
                         "frozen source fidelity", "supplied input byte hashes", "installed requirements",
                         "reviewed artifact revision matches current files", "measurement arrays and metrics",
                         "local report/document links", "Python script syntax"],
              "scope": "Package consistency and traceability; scientific checks are separately retained in analysis/verification.json and analysis/diagnostics.json.",
              "manifest": "Created and separately verified after this result and broker receipt are archived."}
    (ROOT / "analysis/package-verification.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
