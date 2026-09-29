import copy
import json
import unittest
from xml.etree import ElementTree as ET

from tools.baseline.report_fixture import SPEC, build, display, verify_accounting


class ReportFixtureTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(SPEC.read_text())

    def test_authoring_mistake_breaks_reconciliation(self):
        altered = copy.deepcopy(self.spec)
        revenue = next(r for p in altered["pages"] for r in p["rows"] if r["id"] == "revenue")
        revenue["current"] = "1500000.01"
        with self.assertRaisesRegex(ValueError, "gross profit"):
            verify_accounting(altered)

    def test_expected_occurrences_have_unique_semantic_source_nodes(self):
        _, reference, expected = build(self.spec)
        nodes = {n.get("id"): n for n in ET.fromstring(reference).iter() if n.get("id")}
        ids = [f["source"]["node_id"] for f in expected["facts"]]
        self.assertEqual(len(ids), len(set(ids)))
        for fact in expected["facts"]:
            self.assertEqual(nodes[fact["source"]["node_id"]].text, fact["displayed_text"])
        self.assertTrue(any(f["dimensions"] for f in expected["facts"]))
        self.assertEqual({f["unit"] for f in expected["facts"]}, {"GBP", "pure"})

    def test_fixture_generation_is_deterministic(self):
        self.assertEqual(build(self.spec), build(self.spec))

    def test_numeric_display_preserves_cents_and_negative_sign(self):
        self.assertEqual(display("1234.50", "GBP"), "1,234.50")
        self.assertEqual(display("-12.34", "GBP"), "(12.34)")
        self.assertEqual(display("0.00", "GBP"), "0.00")
        with self.assertRaises(ValueError):display("NaN", "GBP")
        with self.assertRaises(ValueError):display("1.001", "GBP")
        with self.assertRaises(ValueError):display("1.5", "pure")


if __name__ == "__main__":
    unittest.main()
