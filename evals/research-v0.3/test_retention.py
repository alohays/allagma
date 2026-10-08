"""Transport regressions: direct queue evidence must survive package hydration."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('retention', Path(__file__).with_name('retention.py'))
retention = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retention)


class RetentionTests(unittest.TestCase):
    def fixture(self, root):
        candidate = root / 'candidate'
        receipt = candidate / '.compute/responses/request-1.json'
        receipt.parent.mkdir(parents=True)
        receipt.write_text('{"status":"completed","exit_code":0}\n')
        (candidate / 'REPORT.md').write_text('Evidence: .compute/responses/request-1.json\n')
        (candidate / 'artifact-manifest.json').write_text(json.dumps({'files': [
            {'path': '.compute/responses/request-1.json', 'sha256': retention.sha(receipt)}]}))
        return candidate

    def test_new_collection_retains_direct_queue_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = self.fixture(root)
            result = retention.collect(candidate, root / 'package')
            self.assertEqual(result['manifest_errors'], [])
            restored = root / 'restored'
            retention.restore(root / 'package', restored)
            self.assertEqual((candidate / '.compute/responses/request-1.json').read_bytes(),
                             (restored / '.compute/responses/request-1.json').read_bytes())

    def test_legacy_supplement_restores_exact_bytes_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = self.fixture(root)
            original_paths = retention.paths
            with patch.object(retention, 'paths', lambda source: (
                    p for p in original_paths(source) if '.compute' not in p.parts)):
                retention.collect(candidate, root / 'package')
            original_index = (root / 'package/package-index.json').read_bytes()
            result = retention.supplement(candidate, root / 'package')
            self.assertEqual(result['supplemental_files'], 1)
            self.assertEqual(original_index, (root / 'package/package-index.json').read_bytes())
            restored = root / 'restored'
            retention.restore(root / 'package', restored)
            self.assertEqual((candidate / '.compute/responses/request-1.json').read_bytes(),
                             (restored / '.compute/responses/request-1.json').read_bytes())
            (root / 'package/terminal-queue/.compute/responses/request-1.json').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'supplement changed'):
                retention.restore(root / 'package', root / 'tampered-restore')

    def test_internal_absolute_dependency_alias_is_explicit_and_relocatable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = self.fixture(root)
            materials = candidate / 'inputs/materials'
            materials.mkdir(parents=True)
            (materials / 'source.txt').write_text('retained scientific input\n')
            copied = candidate / 'reproduction/inputs'
            copied.mkdir(parents=True)
            (copied / 'materials').symlink_to(materials, target_is_directory=True)
            result = retention.collect(candidate, root / 'package')
            self.assertEqual(result['retained_links'], 1)
            index = json.loads((root / 'package/package-index.json').read_text())
            link = index['symlinks']['reproduction/inputs/materials']
            self.assertEqual(link['original_target'], str(materials))
            restored = root / 'restored'
            retention.restore(root / 'package', restored)
            alias = restored / 'reproduction/inputs/materials'
            self.assertTrue(alias.is_symlink())
            self.assertEqual(alias.resolve(), (restored / 'inputs/materials').resolve())
            self.assertEqual((alias / 'source.txt').read_text(), 'retained scientific input\n')

    def test_external_dependency_alias_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = self.fixture(root)
            outside = root / 'outside.txt'
            outside.write_text('outside candidate')
            (candidate / 'external.txt').symlink_to(outside)
            with self.assertRaisesRegex(ValueError, 'escapes candidate'):
                retention.collect(candidate, root / 'package')


if __name__ == '__main__':
    unittest.main()
