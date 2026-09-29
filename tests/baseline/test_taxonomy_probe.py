import hashlib
from pathlib import Path
import stat
import tempfile
import unittest
from zipfile import ZipFile, ZipInfo

from tools.baseline.taxonomy_probe import inspect_package, xml


class PackageIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "package.zip"

    def inspect(self, members):
        with ZipFile(self.path, "w") as z:
            for name, data in members:
                z.writestr(name, data)
        return inspect_package(self.path, hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_traversal_and_platform_ambiguous_paths_rejected(self):
        for name in ["../outside", "/absolute", "C:/drive", "a\\b", "a/./b"]:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Unsafe"):
                self.inspect([(name, "x")])

    def test_symlink_rejected(self):
        entry = ZipInfo("link")
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaisesRegex(ValueError, "links/special"):
            self.inspect([(entry, "../../outside")])

    def test_case_collisions_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.inspect([("dir/A", "1"), ("dir/a", "2")])

    def test_checksum_change_rejected_before_parse(self):
        self.path.write_bytes(b"not a ZIP")
        with self.assertRaisesRegex(ValueError, "checksum"):
            inspect_package(self.path, "0" * 64)

    def test_entity_declarations_rejected(self):
        with self.assertRaisesRegex(ValueError, "DTD/entity"):
            xml(b'<!DOCTYPE a [<!ENTITY value "unexpected">]><a>&value;</a>')

    def test_utf16_does_not_bypass_declaration_filter(self):
        with self.assertRaises((ValueError, UnicodeError)):
            xml('< !DOCTYPE a>'.replace("< !", "<!").encode("utf-16"))

    def test_entry_point_resolves_inside_package(self):
        result = self.inspect(self.package())
        self.assertEqual(result["entry_points"][0]["documents"][0]["archive_path"], "pkg/taxonomy/start.xsd")

    def test_escaping_catalog_rejected(self):
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.inspect(self.package("../../../outside/"))

    @staticmethod
    def package(prefix="../taxonomy/"):
        return [
            ("pkg/META-INF/taxonomyPackage.xml", '<taxonomyPackage xmlns="http://xbrl.org/2016/taxonomy-package"><entryPoints><entryPoint><name>Test</name><entryPointDocument href="https://example.test/start.xsd"/></entryPoint></entryPoints></taxonomyPackage>'),
            ("pkg/META-INF/catalog.xml", '<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"><rewriteURI uriStartString="https://example.test/" rewritePrefix="' + prefix + '"/></catalog>'),
            ("pkg/taxonomy/start.xsd", '<schema/>'),
        ]


if __name__ == "__main__":
    unittest.main()
