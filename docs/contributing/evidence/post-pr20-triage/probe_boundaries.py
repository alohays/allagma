"""Reproduce the two post-PR20 triage boundaries in disposable offline fixtures.

Run from the repository checkout. This is a historical issue probe, not an
additional conformance suite or a scientific/model qualification.
"""
from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from allagma import bundles
from allagma.demo import create_toy
from allagma.files import AllagmaError, file_hash, inventory, read_json
from conformance.test_papers import adapter, bind_reviews, paper_fixture


def source_limits():
    with tempfile.TemporaryDirectory(prefix="allagma-source-limit-") as temporary:
        root = Path(temporary)
        study = root / "study"
        study.mkdir()
        config = paper_fixture(study)
        padding = study / "padding.txt"
        padding.write_bytes(b"")
        config["evidence"]["padding"] = {"path": padding.name, "sha256": file_hash(padding)}
        bind_reviews(study, config)
        small = root / "small"
        adapter.assemble(study, config, small)
        overhead = sum(p.stat().st_size for p in small.rglob("*")
                       if p.is_file() and p != small / "anc/provenance.json")
        padding.write_bytes(b"x" * (adapter.MAX_SOURCE_BYTES - overhead))
        config["evidence"]["padding"]["sha256"] = file_hash(padding)
        bind_reviews(study, config)
        before = inventory(study)
        boundary = root / "boundary"
        result = {"limit_bytes": adapter.MAX_SOURCE_BYTES}
        try:
            adapter.assemble(study, config, boundary)
        except AllagmaError as exc:
            result["boundary_admission"] = str(exc)
        else:
            result["boundary_admission"] = "accepted"
            result["expanded_bytes"] = sum(p.stat().st_size for p in boundary.rglob("*") if p.is_file())
            archive = root / "boundary.tar.gz"
            adapter.archive_sources(boundary, archive)
            try:
                adapter.unpack_archive(archive, root / "unpacked")
                result["round_trip"] = "pass"
            except AllagmaError as exc:
                result["round_trip"] = str(exc)
        result["inputs_unchanged"] = before == inventory(study)
        padding.write_bytes(b"y" * (adapter.MAX_SOURCE_BYTES + 1))
        config["evidence"]["padding"]["sha256"] = file_hash(padding)
        bind_reviews(study, config)
        before = inventory(study)
        oversized = root / "oversized"
        try:
            adapter.assemble(study, config, oversized)
            result["oversized_admission"] = "accepted"
        except AllagmaError as exc:
            result["oversized_admission"] = str(exc)
        copied = oversized / "anc/evidence/padding.txt"
        result["oversized_payload_copied"] = copied.stat().st_size if copied.exists() else 0
        result["oversized_inputs_unchanged"] = before == inventory(study)
        return result


def bundled_diagnostics():
    with tempfile.TemporaryDirectory(prefix="allagma-doctor-control-") as temporary:
        study = create_toy(ROOT, Path(temporary) / "study with spaces")
        lock = bundles.verify_study(study)
        helper = study / ".allagma/bundles" / lock["bundle_id"] / "tools/allagma.py"

        def run(*args):
            completed = subprocess.run(
                [sys.executable, "-B", str(helper), *args, "--study", str(study)],
                cwd=study, capture_output=True, text=True, timeout=30)
            return completed.returncode, json.loads(completed.stdout)

        before = inventory(study)
        mtimes = {name: (study / name).stat().st_mtime_ns for name in before}
        doctor_exit, report = run("doctor")
        unchanged = before == inventory(study) and mtimes == {
            name: (study / name).stat().st_mtime_ns for name in before}
        verify_exit, _ = run("verify")
        start_exit, _ = run("campaign", "start", "--campaign", "control")
        run_exit, execution = run("campaign", "run", "--campaign", "control", "--stop-after", "1")
        return {"doctor_exit": doctor_exit, "failed_checks": [
                    c["id"] for c in report["checks"] if c["status"] == "fail"],
                "doctor_bytes_and_mtimes_unchanged": unchanged,
                "verify_exit": verify_exit, "start_exit": start_exit, "run_exit": run_exit,
                "execution_status": execution["execution_status"],
                "attempts": [read_json(p)["status"] for p in
                             study.glob("campaigns/control/runs/*/attempts/*/record.json")]}


if __name__ == "__main__":
    print(json.dumps({"paper": source_limits(), "doctor": bundled_diagnostics()}, indent=2))
