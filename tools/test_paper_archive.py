#!/usr/bin/env python3
"""Optional real-TeX regression for the shipped paper archive entrypoint.

Run separately from the offline conformance kit. Requires TeX and OS isolation.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from allagma.files import file_hash, read_json, write_json
from conformance.test_papers import adapter, bind_reviews, paper_fixture


class PaperArchiveTests(unittest.TestCase):
    def test_packaged_entrypoint_compiles_when_a_reading_note_is_named_build_py(self):
        with tempfile.TemporaryDirectory(prefix="allagma-paper-regression-") as temporary:
            root = Path(temporary)
            study = root / "study"
            study.mkdir()
            config = paper_fixture(study)
            literature = read_json(study / "references/map.json")
            literature["records"][0]["note"] = "build.py"
            note = b"print('A reading note is not a paper builder.')\n"
            (study / "references/build.py").write_bytes(note)
            write_json(study / "references/map.json", literature)
            bind_reviews(study, config)
            result = adapter.build(study, config, root / "delivery")
            self.assertTrue(result["packaged_builder_verified"])
            self.assertTrue(result["pdf_bytes_reproduced"])
            unpacked = adapter.unpack_archive(root / "delivery/paper-source.tar.gz", root / "unpacked")
            self.assertEqual((unpacked / "anc/reference-notes/Fixture2026/build.py").read_bytes(), note)
            command = subprocess.run([sys.executable, "-B", str(unpacked / "anc/build.py"),
                "--output", str(root / "standalone")], cwd=root, capture_output=True, text=True, timeout=180)
            self.assertEqual(command.returncode, 0, command.stdout + command.stderr)
            self.assertEqual(file_hash(root / "standalone/main.pdf"), result["paper_sha256"])
            self.assertEqual(read_json(root / "standalone/build.json")["network"], "denied")


if __name__ == "__main__":
    unittest.main(verbosity=2)
