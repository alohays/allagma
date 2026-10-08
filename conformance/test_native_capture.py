"""Offline configuration/lifecycle fixtures; no native model qualification."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("allagma_native_capture", ROOT/"adapters/codex/session.py")
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class NativeCaptureTests(unittest.TestCase):
    def test_only_existing_model_controls_are_selected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"config.toml"
            path.write_text('model = "chosen-model"\nmodel_reasoning_effort = "high"\nsecret = "never-export"\n[plugins.example]\nenabled = true\n')
            self.assertEqual(native.selected_settings(path), {"model": "chosen-model", "model_reasoning_effort": "high"})
            path.write_text('model = "chosen-model"\nmodel_provider = "private-provider"\n')
            with self.assertRaisesRegex(ValueError, "Custom provider"):
                native.selected_settings(path)

    def test_no_model_is_not_silently_substituted(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"config.toml"
            path.write_text('model_reasoning_effort = "high"\n')
            with self.assertRaisesRegex(ValueError, "existing user model"):
                native.selected_settings(path)

    def test_native_permissions_are_explicit_and_round_trip(self):
        workspace, runtime = Path("/work/candidate"), Path("/control/runtime")
        permission = native.permission_config(workspace, runtime, ["/control"], [workspace/"inputs"])
        config = {"model": "chosen-model", "default_permissions": "allagma-eval", "permissions": permission}
        text = native.config_text(config, ["/personal/skill/SKILL.md"])
        parsed = tomllib.loads(text)
        self.assertNotIn("sandbox_mode", parsed)
        policy = parsed["permissions"]["allagma-eval"]
        self.assertEqual(policy["filesystem"]["/control"], "deny")
        self.assertEqual(policy["filesystem"][str(runtime)], "deny")
        self.assertEqual(policy["filesystem"][str(workspace)], "write")
        self.assertEqual(policy["filesystem"][str(workspace/"inputs")], "read")
        self.assertFalse(policy["network"]["enabled"])
        self.assertEqual(parsed["skills"]["config"][0]["enabled"], False)

    def test_runtime_cannot_be_a_project_model_pin(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)/"candidate"
            workspace.mkdir()
            with self.assertRaisesRegex(ValueError, "non-overlapping"):
                native.capture(codex="unused", workspace=workspace, record=Path(temporary)/"evidence",
                    runtime=workspace/".codex", prompt="unused", timeout=1,
                    config=Path(temporary)/"missing", auth=Path(temporary)/"missing")

    def test_final_storage_after_fake_cli_exit_is_enforced(self):
        # This exercises lifecycle bookkeeping with an actual local process,
        # not the Codex service, native permissions or a hosted model.
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve(); workspace = base/"work"; workspace.mkdir()
            cli = base/"fake-cli"
            cli.write_text("#!/usr/bin/env python3\nimport sys,time\nfrom pathlib import Path\n"
                           "if '--version' in sys.argv: print('offline-fixture-no-model'); raise SystemExit(0)\n"
                           "sys.stdin.read()\nwhile not Path('go').exists(): time.sleep(.005)\n"
                           "Path('payload').write_bytes(b'x'*200000)\n")
            cli.chmod(0o755)
            config, auth = base/"config.toml", base/"fixture-auth.json"
            config.write_text('model = "offline-fixture-no-model"\n'); auth.write_text('{}\n')
            original_popen, original_storage = subprocess.Popen, native.storage_bytes
            state = {"process": None, "gated": False}
            def capture(*args, **kwargs):
                process = original_popen(*args, **kwargs)
                if kwargs.get("stdin") == subprocess.PIPE and kwargs.get("start_new_session"):
                    state["process"] = process
                return process
            def storage(path):
                value = original_storage(path)
                if Path(path).resolve() == workspace and state["process"] is not None and not state["gated"]:
                    state["gated"] = True
                    (workspace/"go").touch()
                    state["process"].wait(timeout=3)
                return value
            platform_fixture = os.uname_result(('Darwin', 'fixture', 'fixture', 'fixture', 'arm64'))
            with patch.object(subprocess, "Popen", capture), patch.object(native, "storage_bytes", storage), patch.object(native.os, "uname", return_value=platform_fixture):
                result = native.capture(codex=cli, workspace=workspace, record=base/"record", runtime=base/"runtime",
                                        prompt="Offline fixture; no model", timeout=10, config=config, auth=auth,
                                        rss_limit_bytes=200000000, storage_limit_bytes=100000)
            self.assertEqual(result["status"], "storage_exceeded")
            self.assertGreaterEqual(result["final_storage_bytes"], 200000)
            self.assertEqual(result["peak_storage_bytes"], result["final_storage_bytes"])
            self.assertTrue(result["final_storage_limit_exceeded"])


if __name__ == "__main__":
    unittest.main()
