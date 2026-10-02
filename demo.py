"""Run a reproducible integrity experiment in a temporary directory."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from watch import main


def run():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        lab = root / 'lab'
        lab.mkdir()
        (lab / 'config.txt').write_text('mode=safe\n', encoding='utf-8')
        (lab / 'obsolete.txt').write_text('old\n', encoding='utf-8')
        manifest, report = root / 'baseline.json', root / 'report.json'
        with contextlib.redirect_stdout(io.StringIO()):
            main(['baseline', str(lab), '--manifest', str(manifest)])
            clean = main(['check', str(lab), '--manifest', str(manifest)])
            (lab / 'config.txt').write_text('mode=evil\n', encoding='utf-8')
            (lab / 'obsolete.txt').unlink()
            (lab / 'new.txt').write_text('new\n', encoding='utf-8')
            changed = main(['check', str(lab), '--manifest', str(manifest), '--output', str(report)])
        result = json.loads(report.read_text(encoding='utf-8'))
        assert clean == 0 and changed == 1
        assert result['summary'] == {'added': 1, 'removed': 1, 'modified': 1}
        print(json.dumps({'clean_exit': clean, 'changed_exit': changed, 'report': result}, indent=2))

if __name__ == '__main__':
    run()
