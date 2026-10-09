"""Release-boundary regressions, using synthetic committed repositories."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("package_source", Path(__file__).parents[1] / "package_source.py")
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="allagma-release-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.source.mkdir()
        self.write("registry.json", json.dumps({"modules": {"method/test": "methods/test"}}))
        self.write("release.json", '{"release":"0.3.0rc2"}')
        self.write("LICENSE", "Fixture license")
        self.write("tools/allagma.py", "# committed helper\n")
        self.write("methods/test/SKILL.md", "[Resource](resource.txt)\n")
        self.write("methods/test/resource.txt", "fixture")
        self.write("README.md", '[Local](LICENSE) [Guide](docs/guide.md#start)\n![Preview](media/poster.png)\n<img src="media/poster.png">\n')
        self.write(".gitignore", "*.env\n")
        self.git("init", "-q")
        self.commit()

    def write(self, name, data):
        p = self.source / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args], stderr=subprocess.STDOUT)

    def commit(self):
        self.git("add", ".")
        self.git("-c", "user.name=Release test", "-c", "user.email=audit@example.invalid", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "Synthetic release fixture")

    def archive(self, destination="out"):
        output = self.base / destination
        report = package.build(output, self.source)
        with tarfile.open(output / report["archive"]) as archive:
            files = {m.name.split("/", 1)[1]: archive.extractfile(m).read() for m in archive}
        return report, files

    def test_only_committed_bytes_are_distributed(self):
        self.write("tools/private.env", "SYNTHETIC_IGNORED_MARKER")
        self.write("tools/local-notes.txt", "SYNTHETIC_UNTRACKED_MARKER")
        self.write("tools/allagma.py", "SYNTHETIC_DIRTY_MARKER")
        report, files = self.archive()
        self.assertTrue(report["tracked_worktree_changes"])
        self.assertEqual(files["tools/allagma.py"], b"# committed helper\n")
        self.assertNotIn("tools/private.env", files)
        self.assertNotIn("tools/local-notes.txt", files)
        self.assertNotIn(b"SYNTHETIC", b"".join(files.values()))

    def test_omitted_links_are_pinned_and_core_bytes_preserved(self):
        report, files = self.archive()
        prefix = "https://github.com/alohays/allagma/blob/" + report["git_head"] + "/"
        text = files["README.md"].decode()
        self.assertIn("[Local](LICENSE)", text)
        self.assertIn(prefix + "docs/guide.md#start", text)
        raw = "https://raw.githubusercontent.com/alohays/allagma/" + report["git_head"] + "/media/poster.png"
        self.assertIn('src="' + raw + '"', text)
        self.assertIn('![Preview](' + raw + ')', text)
        self.assertEqual(files["methods/test/SKILL.md"], b"[Resource](resource.txt)\n")
        self.assertEqual(set(report["documentation_rewrites"]), {"README.md"})

    def test_reproducible_from_the_same_commit(self):
        first, _ = self.archive("one")
        second, _ = self.archive("two")
        self.assertEqual(first["sha256"], second["sha256"])

    def test_committed_symlink_rejected_before_output(self):
        (self.source / "tools/linked").symlink_to("../../private")
        self.commit()
        with self.assertRaisesRegex(ValueError, "regular files"):
            self.archive()
        self.assertFalse((self.base / "out").exists())

    def test_existing_output_is_preserved(self):
        self.archive()
        with self.assertRaisesRegex(ValueError, "existing release assets"):
            self.archive()

    def test_reference_caches_do_not_enter_release_and_force_tracking_fails(self):
        self.write("tools/local-cache/.allagma-reference-cache.json", '{"format":"allagma-raw-reference-cache-v1"}')
        self.write("tools/local-cache/paper.pdf", "RAW_REFERENCE_FIXTURE")
        exclude = self.source / ".git/info/exclude"
        with exclude.open("a") as stream:
            stream.write("\n/tools/local-cache/\n")
        _, files = self.archive("without-cache")
        self.assertNotIn(b"RAW_REFERENCE_FIXTURE", b"".join(files.values()))
        self.git("add", "-f", "tools/local-cache")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Force-tracked fixture")
        with self.assertRaisesRegex(ValueError, "Raw reference caches"):
            self.archive("blocked")

    def test_no_enclosing_repository_fallback(self):
        nested = self.source / "nested"
        nested.mkdir()
        with self.assertRaisesRegex(ValueError, "root of a committed Git checkout"):
            package.build(self.base / "out", nested)
        self.assertFalse((self.base / "out").exists())


if __name__ == "__main__":
    unittest.main()
