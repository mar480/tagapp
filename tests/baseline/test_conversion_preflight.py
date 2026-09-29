from contextlib import redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.baseline import illustrative_probe as probe


class ConversionPreflightTests(unittest.TestCase):
    def test_known_incompatibility_preserves_existing_conversion_and_does_not_run_converter(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'fixture.pdf'; source.write_bytes(b'SYNTHETIC INPUT')
            registry = root / 'registry.json'
            registry.write_text(json.dumps({'principal_fixture': 'example', 'fixtures': [
                {'id': 'example', 'source_path': 'fixture.pdf', 'size_bytes': source.stat().st_size,
                 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'pages': 1}]}))
            base = root / 'converted'; base.mkdir()
            old = base / 'report.html'; old.write_text('existing evidence')
            listing = b'page num type width height color comp bpc enc interp object ID x-ppi y-ppi size ratio\n---\n1 0 image 8 8 gray 1 8 jpx no 5 0 72 72 200B 30%\n'
            with patch.multiple(probe, ROOT=root, REGISTRY=registry, BASE=base), patch('sys.argv', ['probe']), \
                    patch.object(probe, 'sandbox', return_value=subprocess.CompletedProcess([], 0, listing, b'')) as worker, redirect_stdout(StringIO()):
                self.assertEqual(probe.main(), 1)
            self.assertEqual(old.read_text(), 'existing evidence')
            worker.assert_called_once()
            self.assertIn('/usr/bin/pdfimages', worker.call_args.args)


if __name__ == '__main__':
    unittest.main()
