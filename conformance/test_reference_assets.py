"""Real local I/O and loopback HTTP; no external service, model or TeX needed."""
from copy import deepcopy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

from allagma.files import AllagmaError, digest, read_json, write_json
from allagma.research import _load

ROOT = Path(__file__).resolve().parents[1]
adapter = _load("test_reference_acquisition", ROOT / "adapters/reference-assets/acquire.py")


def asset(name="paper", kind="paper-pdf", **changes):
    value = {"id": name, "kind": kind, "url": "https://example.org/" + name,
             "revision": "v1" if kind.startswith("paper-") else "a" * 40,
             "purpose": "Small conformance fixture, not research evidence.", "use": "reading",
             "access": "public", "extract": "none", "license": {
                 "name": "Test fixture", "url": "https://example.org/license", "note": "Locally authored fixture."}}
    value.update(changes)
    return value


class AssetTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = self.root / "repository"
        self.repo.mkdir()
        self.git("init", "-q")
        self.cache = self.repo / ".allagma-reference-cache"
        self.refs = self.repo / "references"
        self.policy = {**adapter.DEFAULTS, "asset_bytes": 2 * adapter.MIB,
                       "expanded_bytes": 3 * adapter.MIB, "study_bytes": 6 * adapter.MIB,
                       "cache_bytes": 20 * adapter.MIB, "minimum_free_bytes": 1,
                       "study_transfer_bytes": 10 * adapter.MIB}
        adapter.initialize(self.cache, policy=self.policy)

    def git(self, *args, cwd=None):
        return subprocess.run(["git", "-C", str(cwd or self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def manifest(self, *items, study_id="test-study"):
        return {"format": "allagma-reference-assets-v1", "study_id": study_id, "assets": list(items)}

    def provided(self, data=b"small reference bytes", name="source"):
        path = self.root / name
        path.write_bytes(data)
        return path

    def fetch(self, item, data=b"small reference bytes", **kwargs):
        path = self.provided(data)
        return adapter.acquire(self.cache, self.manifest(item), self.refs, provided={item["id"]: str(path)}, **kwargs)

    def test_info_exclude_preserves_entries_and_supports_linked_worktrees(self):
        exclude = Path(self.git("rev-parse", "--path-format=absolute", "--git-path", "info/exclude"))
        with exclude.open("a") as stream:
            stream.write("\nexisting-entry\n")
        before = exclude.read_bytes()
        special = self.repo / "cache [test] space"
        adapter.initialize(special, policy=self.policy)
        self.assertTrue(exclude.read_bytes().startswith(before))
        (special / "raw.bin").write_bytes(b"hidden")
        self.assertEqual(self.git("check-ignore", "cache [test] space/raw.bin"), "cache [test] space/raw.bin")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "--allow-empty", "-qm", "fixture")
        worktree = self.root / "linked"
        self.git("worktree", "add", "-q", "--detach", str(worktree))
        self.assertTrue((worktree / ".git").is_file())
        second = worktree / ".allagma-reference-cache"
        result = adapter.initialize(second, policy=self.policy)
        self.assertEqual(Path(result["exclusion"]["exclude_file"]), exclude)
        (second / "raw.bin").write_bytes(b"hidden")
        self.assertIn("raw.bin", self.git("check-ignore", ".allagma-reference-cache/raw.bin", cwd=worktree))
        self.assertNotIn("raw.bin", self.git("ls-files", "--others", "--exclude-standard", cwd=worktree))

    def test_tracked_cache_is_rejected(self):
        path = self.repo / "tracked"
        path.mkdir()
        (path / "raw.bin").write_bytes(b"bad location")
        self.git("add", "tracked/raw.bin")
        with self.assertRaisesRegex(AllagmaError, "tracked files"):
            adapter.initialize(path)

    def test_every_asset_kind_uses_pinned_bytes_and_offline_restart_reuse(self):
        items, bindings = [], {}
        for kind in sorted(adapter.KINDS):
            payload = (kind + " fixture").encode()
            item = asset(kind, kind, sha256=hashlib.sha256(payload).hexdigest(), size_bytes=len(payload))
            if kind == "dataset":
                item["split"] = "validation fixture"
            items.append(item)
            bindings[kind] = str(self.provided(payload, kind))
        manifest = self.manifest(*items)
        first = adapter.acquire(self.cache, manifest, self.refs, provided=bindings)
        self.assertTrue(all(a["status"] == "available" for a in first["assets"]))
        second = adapter.acquire(self.cache, manifest, self.refs)
        self.assertEqual(first["transfer_bytes"], second["transfer_bytes"])
        self.assertTrue(all(a["reused"] for a in second["assets"]))
        adapter.verify(self.cache, second)
        self.assertNotIn(str(self.root), (self.refs / "retrieval.json").read_text())

    def test_corruption_is_detected_preserved_and_repaired_with_new_attempt(self):
        payload = b"important source"
        item = asset(sha256=hashlib.sha256(payload).hexdigest())
        first = self.fetch(item, payload)
        cached = self.cache / first["assets"][0]["cache_path"]
        cached.chmod(0o644)
        cached.write_bytes(b"damaged")
        with self.assertRaisesRegex(AllagmaError, "corrupt"):
            adapter.verify(self.cache, first)
        corrupt = adapter.acquire(self.cache, self.manifest(item), self.refs)
        self.assertEqual(corrupt["assets"][0]["status"], "corrupt")
        retained = adapter.quarantine(self.cache, first, "paper")
        self.assertEqual((self.cache / retained["preserved_paths"][0]).read_bytes(), b"damaged")
        repaired = self.fetch(item, payload)
        self.assertEqual(repaired["assets"][0]["status"], "available")
        self.assertEqual(repaired["transfer_bytes"], len(payload) * 2)

    def test_per_asset_transfer_storage_and_free_space_budgets_are_enforced(self):
        policy = {**self.policy, "asset_bytes": 10}
        adapter.adopt_policy(self.cache, policy)
        result = self.fetch(asset(), b"x" * 11)
        self.assertEqual(result["assets"][0]["reason"], "asset_bytes")
        self.assertEqual(result["transfer_bytes"], 0)
        policy["study_transfer_bytes"] = 4
        adapter.adopt_policy(self.cache, policy)
        result = self.fetch(asset("another"), b"123456")
        self.assertEqual(result["assets"][0]["status"], "budget-exceeded")
        self.assertEqual(result["transfer_bytes"], 4)
        usage = __import__("shutil").disk_usage(self.cache)
        with patch.object(adapter.shutil, "disk_usage", return_value=type(usage)(usage.total, usage.total, 0)):
            result = self.fetch(asset("no-space"), b"123")
        self.assertIn(result["assets"][0]["reason"], ("study_transfer_bytes", "minimum_free_bytes"))

    def test_adopted_limit_expansion_requires_bound_researcher_decision(self):
        policy = {**self.policy, "attempts_per_asset": 3}
        with self.assertRaisesRegex(AllagmaError, "Ask the researcher"):
            adapter.adopt_policy(self.cache, policy)
        approval = {"decision": "expand-acquisition-limits", "previous_policy_sha256": digest(self.policy),
                    "policy_sha256": digest(policy), "approved_by": "fixture researcher", "approved_at": "2026-10-09",
                    "reason": "Test explicit approval validation."}
        self.assertEqual(adapter.adopt_policy(self.cache, policy, approval=approval)["expanded_fields"], ["attempts_per_asset"])

    def test_gated_and_unavailable_assets_are_explicit_without_automatic_acceptance(self):
        gated = asset(access="gated", access_reason="Requires acceptance of terms")
        result = self.fetch(gated)
        self.assertEqual(result["assets"][0]["status"], "gated")
        self.assertEqual(result["transfer_bytes"], 0)
        missing = asset("missing", access="unavailable", access_reason="Author did not release source")
        result = adapter.acquire(self.cache, self.manifest(missing), self.refs)
        self.assertEqual(result["assets"][0]["status"], "unavailable")
        self.assertEqual(result["assets"][0]["reason"], missing["access_reason"])

    def test_tar_and_zip_extraction_reject_escape_links_and_expansion_bombs(self):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:gz") as archive:
            member = tarfile.TarInfo("../escape")
            member.size = 3
            archive.addfile(member, io.BytesIO(b"bad"))
        result = self.fetch(asset("escape", "paper-source", extract="tar"), stream.getvalue())
        self.assertEqual(result["assets"][0]["status"], "failed")
        self.assertFalse((self.cache / "escape").exists())
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("expanded.bin", b"x" * (self.policy["expanded_bytes"] + 1))
        result = self.fetch(asset("bomb", "paper-source", extract="zip"), stream.getvalue())
        self.assertEqual(result["assets"][0]["status"], "budget-exceeded")
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:gz") as archive:
            member = tarfile.TarInfo("linked")
            member.type = tarfile.SYMTYPE
            member.linkname = "/etc/passwd"
            archive.addfile(member)
        result = self.fetch(asset("symlink", "paper-source", extract="tar"), stream.getvalue())
        self.assertEqual(result["assets"][0]["status"], "failed")

    def test_extracted_tree_is_verified_on_reuse(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("paper/main.tex", "A source fixture.")
        item = asset("source", "paper-source", extract="zip")
        result = self.fetch(item, stream.getvalue())
        self.assertEqual(result["assets"][0]["status"], "available")
        tree = result["assets"][0]["tree"]
        path = self.cache / tree["cache_path"] / "paper/main.tex"
        path.chmod(0o644)
        path.write_text("Changed")
        with self.assertRaisesRegex(AllagmaError, "corrupt"):
            adapter.verify(self.cache, result)

    def test_study_and_total_cache_caps_count_actual_retained_bytes(self):
        policy = {**self.policy, "asset_bytes": 1000, "study_bytes": 1500}
        adapter.adopt_policy(self.cache, policy)
        first = self.fetch(asset("one"), b"a" * 1000)
        self.assertEqual(first["assets"][0]["status"], "available")
        second = self.fetch(asset("two"), b"b" * 1000)
        self.assertEqual(second["assets"][0]["reason"], "study_bytes")
        policy["cache_bytes"] = 5000
        adapter.adopt_policy(self.cache, policy)
        third = self.fetch(asset("three"), b"c")
        self.assertEqual(third["assets"][0]["reason"], "cache_bytes")

    def test_shared_digest_reuses_one_object_across_studies_and_urls(self):
        payload = b"shared source"
        item = asset(sha256=hashlib.sha256(payload).hexdigest())
        first = self.fetch(item, payload)
        other = {**item, "id": "second-url", "url": "https://example.org/second"}
        result = adapter.acquire(self.cache, self.manifest(other, study_id="another-study"), self.refs,
                                 provided={other["id"]: str(self.root / "source")})
        self.assertEqual(result["assets"][0]["cache_path"], first["assets"][0]["cache_path"])
        self.assertEqual(result["transfer_bytes"], 0)
        self.assertEqual(len(list((self.cache / "objects").glob("*/data"))), 1)

    def test_preparation_copies_only_execution_assets_and_protects_them(self):
        from allagma import references, research, resources
        payload = b"a selected dataset fixture"
        item = asset("data", "dataset", use="execution", filename="data.txt", split="validation",
                     sha256=hashlib.sha256(payload).hexdigest())
        self.fetch(item, payload)
        references.initialize(self.refs, question="Use only supplied reference data.")
        write_json(self.refs / "assets.json", self.manifest(item))
        materials = self.repo / "materials"
        materials.mkdir()
        (materials / "README.md").write_text("Study-owned scientific materials.")
        hidden = materials / "private-cache"
        hidden.mkdir()
        write_json(hidden / ".allagma-reference-cache.json", {"format": "allagma-raw-reference-cache-v1"})
        (hidden / "unselected.bin").write_bytes(b"never copy")
        brief = self.repo / "brief.md"
        brief.write_text("A bounded preparation fixture.")
        profile = {"format": resources.FORMAT, "budgets_seconds": {"compute": 60, "setup": 30},
                   "command_timeout_seconds": {"compute": 10, "setup": 10}, "attempt_limit": 4,
                   "rss_limit_bytes": 200_000_000, "storage_limit_bytes": 20_000_000,
                   "file_limit_bytes": 1_000_000, "poll_seconds": .05, "terminate_grace_seconds": .1}
        study, control = self.repo / "study", self.root / "control"
        prepared = research.prepare(ROOT, study, control, brief=brief, materials=materials, profile=profile,
                                    reference_directory=self.refs, reference_cache=self.cache)
        copied = study / "inputs/reference-assets/data/data.txt"
        self.assertEqual(copied.read_bytes(), payload)
        self.assertFalse((study / "inputs/materials/private-cache").exists())
        self.assertIn("inputs", [Path(p).name for p in prepared["readonly"]])
        self.assertEqual(references.verify_snapshot(study / "inputs/references")["format"], "allagma-reference-snapshot-v1")
        self.assertIn("data.txt", self.git("check-ignore", str(copied)))
        copied.chmod(0o644)
        copied.write_bytes(b"changed")
        with self.assertRaisesRegex(AllagmaError, "Prepared inputs changed"):
            research.run(study, control, codex=self.root / "nonexistent", timeout=1, session_id="test",
                         config=self.root / "config", auth=self.root / "auth")

    def test_interrupted_http_resumes_after_restart_and_charges_repeated_bytes(self):
        payload = bytes(range(256)) * 3000
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                start = int(self.headers.get("Range", "bytes=0-").split("=")[1].split("-")[0])
                seen.append(start)
                self.send_response(206 if start else 200)
                self.send_header("Content-Length", str(len(payload) - start))
                self.send_header("ETag", '"fixture-v1"')
                if start:
                    self.send_header("Content-Range", f"bytes {start}-{len(payload)-1}/{len(payload)}")
                self.end_headers()
                self.wfile.write(payload[start:] if start else payload[:adapter.CHUNK + 100])
                self.wfile.flush()
                self.close_connection = True

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        item = asset(url=f"http://127.0.0.1:{server.server_port}/fixture", sha256=hashlib.sha256(payload).hexdigest())
        manifest = self.manifest(item)
        first = adapter.acquire(self.cache, manifest, self.refs, online=True)
        self.assertIn(first["assets"][0]["status"], ("partial", "failed"))
        second = adapter.acquire(self.cache, manifest, self.refs, online=True)
        self.assertEqual(second["assets"][0]["status"], "available")
        self.assertGreater(seen[1], 0)
        self.assertGreaterEqual(second["transfer_bytes"], len(payload))
        adapter.verify(self.cache, second)
        third = adapter.acquire(self.cache, manifest, self.refs)
        self.assertTrue(third["assets"][0]["reused"])
        self.assertEqual(len(seen), 2)


if __name__ == "__main__":
    unittest.main()
