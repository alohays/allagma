"""Portable Allagma analysis handoff for the required single fixed-split task."""
import importlib.util
import json
from pathlib import Path
import sys

root = Path.cwd().resolve()
camp = root / "campaigns/core-culp"
lock = json.loads((camp / "lock.yaml").read_text())
sys.path.insert(0, str(root / ".allagma/bundles" / lock["bundle_id"]))
from allagma.files import reference, write_json, verify_reference, file_hash
from allagma.contracts import validate_record
from allagma.campaigns import audit_evidence

def module(name):
    path = camp / "materials/scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

manifest = {"campaign_id": "core-culp", "protocol_revision": "culp-v1", "raw": [], "runs": [], "exclusions": []}
for path in sorted(camp.glob("runs/*/attempts/*/record.json")):
    record = json.loads(path.read_text())
    validate_record(record)
    audit_evidence(root, record)
    manifest["runs"].append(reference(root, path))
    if record["status"] == "succeeded" and record["split"] == "confirmation":
        manifest["raw"].append(next(ref for ref in record["outputs"] if ref["path"].endswith("/raw.json")))
    else:
        manifest["exclusions"].append({"attempt_id": record["attempt_id"], "reason": record["status"] if record["status"] != "succeeded" else "pilot excluded from capsule results"})
assert len(manifest["raw"]) == 1
analysis = root / "analysis"
analysis.mkdir(exist_ok=False)
write_json(analysis / "raw-manifest.json", manifest, immutable=True)
analyzer = module("analyze")
first = analyzer.write_analysis(root, analysis / "raw-manifest.json", analysis / "primary")
second = analyzer.write_analysis(root, analysis / "raw-manifest.json", analysis / "recomputed")
assert first == second
for name in ["results.json", "report.json", "table.md"]:
    assert (analysis / "primary" / name).read_bytes() == (analysis / "recomputed" / name).read_bytes()
write_json(analysis / "recomputation-check.json", {"passed": True, "checks": "Byte-identical results.json, report.json and table.md from separate directories using immutable raw evidence; no source experiments executed."}, immutable=True)
raw = json.loads((root / manifest["raw"][0]["path"]).read_text())
check = module("scientific_checks").checks(root, raw)
write_json(analysis / "scientific-checks.json", check, immutable=True)
code = camp / "materials/scripts/analyze.py"
record = {"schema_version": "0.2", "record_type": "AnalysisRecord", "analysis_id": "culp-a001",
          "raw_manifest": reference(root, analysis / "raw-manifest.json"), "analysis_revision": file_hash(code), "code": reference(root, code),
          "configuration": {"protocol_revision": "culp-v1", "single_split": True, "answer_semantics": "original printed labels", "partial": False},
          "outputs": [reference(root, p) for p in sorted((analysis / "primary").iterdir())] + [reference(root, analysis / "scientific-checks.json"), reference(root, analysis / "recomputation-check.json")],
          "exclusions": manifest["exclusions"], "uncertainty": first["uncertainty"],
          "dependencies": [reference(root, camp / "protocol.json"), *manifest["runs"], *manifest["raw"]]}
validate_record(record)
write_json(analysis / "record.json", record, immutable=True)
module("write_report").write_report(root, analysis / "primary")
claims = []
for row in first["rows"]:
    if row["printed_label"] not in ["CN", "AA"]:
        continue
    claim = {"schema_version": "0.2", "record_type": "ClaimRecord", "claim_id": row["dataset"].lower() + "-" + row["printed_label"].lower(),
             "text": f"The original {row['dataset']} output labelled {row['printed_label']} is {row['accuracy_percent']:.2f}% ({row['correct']}/{row['n_test']}); executed predictor is {row['actual_predictor']}.",
             "supporting": [reference(root, analysis / "primary/results.json"), *manifest["raw"]], "contradicting": [],
             "dependencies": [reference(root, analysis / "record.json"), reference(root, camp / "materials/source/adapted/code" / (row["dataset"].lower()+"_sample.py"))],
             "scope": "Original fixed split, adapted capsule and locally pinned environment", "limitations": ["Single split, no original reference output", first["interpretation"], first["uncertainty"]], "status": "supported", "supersedes": None}
    validate_record(claim)
    claims.append(claim)
write_json(root / "claims.json", claims, immutable=True)
print(json.dumps(first["answers"], indent=2))
print(json.dumps(check, indent=2))
