"""Offline configuration checks; these do not qualify a native model session."""
import importlib.util
from pathlib import Path
import tempfile
import tomllib
import unittest

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


if __name__ == "__main__":
    unittest.main()
