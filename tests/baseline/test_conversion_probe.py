import unittest

from tools.baseline.conversion_probe import TextCollector, check_text, make_pdf


class ConversionEvidenceTests(unittest.TestCase):
    def test_fragmentation_is_tolerated_but_changed_or_duplicated_amounts_are_not(self):
        self.assertEqual(check_text(["1,234.50"], "1, 234 .50")["status"], "pass")
        self.assertEqual(check_text(["1,234.50"], "1,234.60")["status"], "fail")
        self.assertEqual(check_text(["1,234.50"], "1,234.50 1,234.50")["status"], "fail")

    def test_script_and_style_text_cannot_satisfy_amount_check(self):
        parser = TextCollector()
        parser.feed('<style>.x {content:"123"}</style><script>123</script><div>456</div>')
        self.assertEqual(check_text(["123"], "".join(parser.parts))["status"], "fail")
        self.assertEqual(parser.scripts, 1)

    def test_blank_extraction_is_explicitly_unsupported(self):
        self.assertEqual(check_text([], "\n")["status"], "unsupported_image_only")
        self.assertEqual(check_text(["12"], "")["status"], "fail")

    def test_substring_of_another_amount_is_not_a_match(self):
        self.assertEqual(check_text(["0.00"], "10.00")["status"], "fail")

    def test_fixture_bytes_reproducible(self):
        self.assertEqual(make_pdf(b"BT ET"), make_pdf(b"BT ET"))


if __name__ == "__main__":
    unittest.main()
