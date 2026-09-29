import hashlib
import io
from pathlib import Path
import tempfile
import unittest

from tools.baseline.acquire import store_verified


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.destination = Path(self.tmp.name) / "artifact.zip"
        self.destination.write_bytes(b"existing verified copy")

    def test_bad_download_preserves_existing_file_and_cleans_temporary_data(self):
        for data in [b"a", b"bad", b"oversized"]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                store_verified(io.BytesIO(data), self.destination, size=3, digest=hashlib.sha256(b"new").hexdigest())
            self.assertEqual(self.destination.read_bytes(), b"existing verified copy")
            self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_exact_download_replaces_atomically(self):
        store_verified(io.BytesIO(b"new"), self.destination, size=3, digest=hashlib.sha256(b"new").hexdigest())
        self.assertEqual(self.destination.read_bytes(), b"new")


if __name__ == "__main__":
    unittest.main()
