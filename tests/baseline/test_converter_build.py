from io import BytesIO
from pathlib import Path
import tarfile
import tempfile
import unittest

from tools.baseline.converter_build import unpack


class BuildArchiveTests(unittest.TestCase):
    def archive(self, path, entries):
        with tarfile.open(path, 'w') as archive:
            for name, target in entries:
                member = tarfile.TarInfo(name)
                if target is None:
                    member.size = 4
                    archive.addfile(member, BytesIO(b'test'))
                else:
                    member.type = tarfile.SYMTYPE; member.linkname = target
                    archive.addfile(member)

    def test_archive_cannot_write_outside_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); archive = root / 'source.tar'
            self.archive(archive, [('../escape', None)])
            with self.assertRaises(ValueError):
                unpack(archive, root / 'output')
            self.assertFalse((root / 'escape').exists())

    def test_source_symlink_cannot_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); archive = root / 'source.tar'
            self.archive(archive, [('link', '../../escape')])
            with self.assertRaises(ValueError):
                unpack(archive, root / 'output')

    def test_rootfs_absolute_links_are_created_after_regular_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); archive = root / 'rootfs.tar'
            self.archive(archive, [('bin', '/usr/bin'), ('usr/bin/example', None)])
            unpack(archive, root / 'output', rootfs=True)
            self.assertEqual((root / 'output/usr/bin/example').read_bytes(), b'test')
            self.assertEqual((root / 'output/bin').readlink(), Path('/usr/bin'))


if __name__ == '__main__':
    unittest.main()
