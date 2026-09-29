import unittest

from tools.baseline.illustrative_probe import PageText, compare, numbers, public_summary


class IllustrativeProbeTests(unittest.TestCase):
    def test_inline_fragments_and_cells(self):
        result, differences = compare("1,234.50 987\f", '<div data-page-no="1"><div>1,<span>234</span>.50</div><div>987</div></div>', 1)
        self.assertEqual(differences, [])
        self.assertEqual(result["status"], "text_checks_pass_visual_review_pending")

    def test_changed_value_despite_same_count(self):
        result, _ = compare("12.34\f", '<div data-page-no="1">72.34</div>', 1)
        self.assertEqual(result["pages_requiring_review"], [1])

    def test_signs_and_duplicates(self):
        tokens = numbers("(12.34) -12.34 12.34 12.34 5%")
        self.assertEqual(tokens["12.34"], 2)
        self.assertEqual(tokens["(12.34)"], 1)
        self.assertEqual(tokens["-12.34"], 1)
        self.assertEqual(tokens["5%"], 1)

    def test_missing_duplicate_and_reordered_pages(self):
        for page_ids in ([1], [1, 1], [2, 1]):
            html = "".join(f'<div data-page-no="{n}">12</div>' for n in page_ids)
            result, _ = compare("12\f12\f", html, 2)
            self.assertEqual(result["status"], "review_required")
            self.assertFalse(result["page_sequence_matches"])

    def test_script_cannot_supply_missing_number(self):
        result, _ = compare("42\f", '<div data-page-no="1"><script>42</script>abc</div>', 1)
        self.assertEqual(result["pages_requiring_review"], [1])

    def test_hex_pages_and_void_elements(self):
        parser = PageText()
        parser.feed('<div data-page-no="a"><img src="x"/><div>12<br>34</div></div>99')
        self.assertEqual(parser.pages[0][0], 10)
        self.assertEqual(numbers("".join(parser.pages[0][1])), numbers("12 34"))

    def test_private_use_glyph_requires_review_without_numeric_difference(self):
        result, _ = compare("a\f", '<div data-page-no="1">a\ue000</div>', 1)
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["private_use_characters"], 1)

    def test_numeric_references_survive_layout_boundary_changes(self):
        result, _ = compare("REF 102 GBP 000\f", '<div data-page-no="1">REF102 GBP000</div>', 1)
        self.assertEqual(result["missing_numeric_occurrences"], 0)
        self.assertEqual(result["added_numeric_occurrences"], 0)

    def test_dropped_narrative_requires_review(self):
        result, _ = compare("Revenue 12\f", '<div data-page-no="1">12</div>', 1)
        self.assertEqual(result["status"], "review_required")
        self.assertGreater(result["missing_characters"], 0)

    def test_hyphen_substitution_stays_visible(self):
        result, _ = compare("a\u2010b\f", '<div data-page-no="1">a-b</div>', 1)
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["missing_characters"], 1)

    def test_nfkc_must_not_hide_loss_of_nonbreaking_hyphen(self):
        result, _ = compare("a\u2011b\f", '<div data-page-no="1">a\u2010b</div>', 1)
        self.assertEqual(result['missing_characters'], 0)  # Equal after NFKC.
        self.assertEqual(result['status'], 'review_required')
        self.assertEqual(result['pages_requiring_review'], [1])
        self.assertEqual(result['raw_hyphen_changes'], [{'page': 1,
            'source': {'U+2011': 1}, 'converted': {'U+2010': 1}}])

    def test_summary_drops_report_content(self):
        self.assertEqual(public_summary({"status": "review_required", "pages": [{"text": "PRIVATE"}], "missing": "PRIVATE", "processor_output": "PRIVATE"}), {"status": "review_required"})


if __name__ == "__main__":
    unittest.main()
