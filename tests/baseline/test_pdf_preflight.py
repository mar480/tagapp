import unittest

from tools.baseline.conversion_probe import ARTIFACT_SHA256
from tools.baseline.pdf_preflight import assess, image_codecs

HEADER = 'page num type width height color comp bpc enc interp object ID x-ppi y-ppi size ratio\n---\n'


class PdfPreflightTests(unittest.TestCase):
    def test_known_broken_codec_blocks_before_conversion(self):
        listing = HEADER + '1 0 image 8 8 gray 1 8 jpx no 5 0 72 72 200B 30%\n'
        result = assess(listing, ARTIFACT_SHA256)
        self.assertEqual(result['status'], 'converter_incompatible')
        self.assertEqual(result['findings'][0]['affected_image_streams'], 1)

    def test_new_build_is_not_incorrectly_declared_supported(self):
        listing = HEADER + '1 0 image 8 8 gray 1 8 jpx no 5 0 72 72 200B 30%\n'
        result = assess(listing, 'different-build')
        self.assertEqual(result['status'], 'known_codec_blocker_not_detected')
        self.assertFalse(result['production_qualified'])

    def test_empty_and_unrecognised_inventory_are_distinct(self):
        self.assertEqual(image_codecs(HEADER), {})
        with self.assertRaises(ValueError):
            image_codecs('')
        with self.assertRaises(ValueError):
            image_codecs(HEADER + 'damaged processor output')


if __name__ == '__main__':
    unittest.main()
