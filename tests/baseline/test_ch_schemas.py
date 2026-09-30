import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.baseline.ch_schemas import allowed_url, dependency_path, verify
from tools.baseline.ch_schema_probe import strict_base64


class SchemaBoundaryTests(unittest.TestCase):
    def schema_set(self, base):
        body = b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:test"/>'
        (base / 'test.xsd').write_bytes(body)
        return {'roots': {'test': 'test.xsd'}, 'files': [{'path': 'test.xsd', 'size_bytes': len(body),
            'sha256': hashlib.sha256(body).hexdigest(), 'target_namespace': 'urn:test', 'dependencies': []}]}

    def test_byte_changes_are_rejected_before_schema_compilation(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); pins = self.schema_set(base)
            self.assertEqual(set(verify(pins, base)), {'test.xsd'})
            (base / 'test.xsd').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                verify(pins, base)

    def test_missing_roots_and_duplicate_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); pins = self.schema_set(base)
            duplicate = copy.deepcopy(pins); duplicate['files'] *= 2
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                verify(duplicate, base)
            pins['roots']['other'] = 'missing.xsd'
            with self.assertRaisesRegex(ValueError, 'root'):
                verify(pins, base)

    def test_dependency_must_be_in_the_pinned_set(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); pins = self.schema_set(base)
            data = b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:test"><xs:include schemaLocation="missing.xsd"/></xs:schema>'
            (base / 'test.xsd').write_bytes(data)
            pins['files'][0].update(size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), dependencies=['missing.xsd'])
            with self.assertRaisesRegex(ValueError, 'dependency'):
                verify(pins, base)

    def test_declared_namespace_cannot_differ_from_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); pins = self.schema_set(base)
            pins['files'][0]['target_namespace'] = 'urn:wrong'
            with self.assertRaisesRegex(ValueError, 'namespace'):
                verify(pins, base)

    def test_relative_includes_resolve_but_external_resources_do_not(self):
        self.assertEqual(dependency_path('forms/poll.xsd', '../base.xsd'), 'base.xsd')
        for ref in ('https://attacker.invalid/base.xsd', 'file:///etc/passwd', '../%2e%2e/base.xsd', '../base.xsd?query=1', '../../outside.xsd', '/etc/passwd'):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                dependency_path('forms/poll.xsd', ref)

    def test_acquisition_cannot_target_gateway_or_other_hosts(self):
        allowed_url('https://xmlgw.companieshouse.gov.uk/v1-0/schema/test.xsd')
        for url in ('http://xmlgw.companieshouse.gov.uk/v1-0/schema/test.xsd',
                    'https://xmlgw.companieshouse.gov.uk/v1-0/xmlgw/Gateway',
                    'https://attacker.invalid/v1-0/schema/test.xsd'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                allowed_url(url)

    def test_xml_whitespace_is_accepted_in_canonical_base64(self):
        self.assertTrue(strict_base64(' YQ==\r\n\t'))

    def test_invalid_alphabet_padding_and_nonzero_pad_bits_are_rejected(self):
        for value in ('!', '!!!', '%%%','!YQ==', 'A', 'YQ=', 'YQ===', 'YR==', '\u00a0YQ=='):
            with self.subTest(value=value):
                self.assertFalse(strict_base64(value))


if __name__ == '__main__':
    unittest.main()
