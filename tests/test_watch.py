import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from watch import scan, compare, main, validate

class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.lab = self.root/'lab'
        self.lab.mkdir()
        (self.lab/'config.txt').write_text('mode=safe\n')
        self.manifest = self.root/'baseline.json'
    def tearDown(self):
        self.temp.cleanup()
    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return main(list(map(str, args)))
    def baseline(self):
        self.call('baseline', self.lab, '--manifest', self.manifest)
    def test_unchanged(self):
        self.assertFalse(any(compare(scan(self.lab),scan(self.lab))['summary'].values()))
    def test_same_size_change(self):
        old=scan(self.lab)
        (self.lab/'config.txt').write_text('mode=evil\n')
        self.assertEqual(compare(old,scan(self.lab))['modified'],['config.txt'])
    def test_added_removed_unicode(self):
        old=scan(self.lab)
        (self.lab/'config.txt').unlink()
        (self.lab/'dados').mkdir()
        (self.lab/'dados/ação.txt').write_text('example')
        result=compare(old,scan(self.lab))
        self.assertEqual(result['added'],['dados/ação.txt'])
        self.assertEqual(result['removed'],['config.txt'])
    def test_symlink_and_cycle(self):
        outside=self.root/'outside.txt';outside.write_text('private')
        try:
            (self.lab/'link').symlink_to(outside)
            (self.lab/'cycle').symlink_to(self.lab,target_is_directory=True)
        except OSError:
            self.skipTest('Symlinks unavailable')
        result=scan(self.lab)
        self.assertEqual(set(result['files']),{'config.txt'})
        self.assertEqual(len(result['skipped']),2)
    def test_manifest_inside_root(self):
        manifest=self.lab/'baseline.json'
        self.call('baseline',self.lab,'--manifest',manifest)
        self.assertEqual(self.call('check',self.lab,'--manifest',manifest),0)
    def test_cli_report_and_exit_status(self):
        self.baseline();(self.lab/'config.txt').write_text('changed')
        output=self.root/'report.json'
        self.assertEqual(self.call('check',self.lab,'--manifest',self.manifest,'--output',output),1)
        self.assertEqual(json.loads(output.read_text())['modified'],['config.txt'])
    def assert_error(self,*args):
        with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
            self.call(*args)
        self.assertEqual(error.exception.code,2)
    def test_no_silent_baseline_replacement(self):
        self.baseline();original=self.manifest.read_bytes()
        self.assert_error('baseline',self.lab,'--manifest',self.manifest)
        self.assertEqual(self.manifest.read_bytes(),original)
    def test_no_report_over_baseline(self):
        self.baseline()
        self.assert_error('check',self.lab,'--manifest',self.manifest,'--output',self.manifest)
    def test_invalid_paths(self):
        old=scan(self.lab);old['files']['../outside']=old['files'].pop('config.txt')
        with self.assertRaises(ValueError):validate(old)
    def test_read_failure(self):
        with patch('watch.digest',side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):scan(self.lab)
    def test_different_root(self):
        self.baseline();self.assert_error('check',self.root,'--manifest',self.manifest)

if __name__ == '__main__':unittest.main()
