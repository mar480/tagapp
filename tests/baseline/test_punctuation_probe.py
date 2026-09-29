import unittest

from tools.baseline.actualtext_probe import fixtures
from tools.baseline.punctuation_probe import LineText, proposals


class PunctuationProposalTests(unittest.TestCase):
    def test_split_spans_have_one_locator_and_script_text_is_excluded(self):
        index = LineText()
        index.feed('<div data-page-no="1"><div class="t">Alpha-<span>Beta</span><script>Alpha-Beta</script></div></div>')
        rows = proposals([{'page': 1, 'text': 'Alpha\u2011Beta'}], index.lines)
        self.assertEqual(rows[0]['status'], 'unique_candidate')
        self.assertEqual(rows[0]['candidates'], [{'line': 0, 'start': 0, 'end': 10, 'hyphen_offsets': [5]}])
        self.assertEqual(rows[0]['approval'], 'not_reviewed')

    def test_repeated_text_is_ambiguous_and_other_pages_cannot_supply_a_match(self):
        lines = {1: ['Alpha-Beta Alpha-Beta'], 2: ['Alpha-Beta']}
        rows = proposals([{'page': 1, 'text': 'Alpha\u2011Beta'}, {'page': 3, 'text': 'Alpha\u2011Beta'}], lines)
        self.assertEqual([r['status'] for r in rows], ['ambiguous', 'unmatched'])
        self.assertEqual(len(rows[0]['candidates']), 2)

    def test_ordinary_hyphens_and_numeric_differences_are_not_repair_candidates(self):
        rows = proposals([{'page': 1, 'text': 'Alpha-Beta'}, {'page': 1, 'text': '72.34'}], {1: ['Alpha-Beta 12.34']})
        self.assertEqual(rows, [])

    def test_multiple_hyphens_and_unicode_offsets_remain_explicit(self):
        row = proposals([{'page': 1, 'text': 'A\u2011B\u2011C'}], {1: ['\U0001f600 A-B-C']})[0]
        self.assertEqual(row['candidates'][0]['hyphen_offsets'], [3, 5])
        self.assertEqual(row['candidates'][0]['start'], 2)  # Codepoints, not UTF-16.

    def test_page_and_line_scope_survive_void_and_nested_elements(self):
        index = LineText()
        index.feed('<div data-page-no="a"><img/><div class="t">A-<span>B</span></div>outside<div class="t">C-D</div></div><div data-page-no="b"><div class="t">E-F</div></div>')
        self.assertEqual(dict(index.lines), {10: ['A-B', 'C-D'], 11: ['E-F']})

    def test_synthetic_cases_distinguish_actualtext_from_tounicode(self):
        cases = fixtures()
        self.assertIn(b'/ActualText <feff2011>', cases['actualtext-hyphen'][0])
        self.assertIn(b'<2D> <2011>', cases['tounicode-hyphen'][0])
        self.assertNotIn(b'/ActualText', cases['tounicode-hyphen'][0])
        self.assertNotEqual(cases['actualtext-conflicting-number'][1], cases['actualtext-conflicting-number'][2])


if __name__ == '__main__':
    unittest.main()
