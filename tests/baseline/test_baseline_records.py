import copy
import unittest

from tools.baseline.check import ROOT, check, load, validate_profiles, validate_foundation


class BaselineRecordTests(unittest.TestCase):
    def setUp(self):
        self.matrix = load(ROOT, "docs/compliance/profile-matrix.json")
        self.sources = {s["id"] for s in load(ROOT, "docs/compliance/sources.json")["sources"]}

    def test_public_checkout_does_not_require_private_inputs(self):
        self.assertEqual(check(ROOT), [])

    def test_foundation_ready_is_not_filing_qualification(self):
        self.assertEqual(check(ROOT, require_foundation_ready=True), [])
        self.assertTrue(check(ROOT, require_qualified=True))

    def test_unassigned_work_cannot_disappear_from_foundation_gate(self):
        record = load(ROOT, "docs/milestones/01-status.json")
        del record["foundation_readiness"]["deferred_gates"]["converter-feasibility"]
        self.assertTrue(validate_foundation(ROOT, record))

    def test_publication_boundary_cannot_be_deferred(self):
        record = load(ROOT, "docs/milestones/01-status.json")
        next(g for g in record["gates"] if g["id"] == "publication-boundary")["status"] = "partial"
        record["foundation_readiness"]["deferred_gates"]["publication-boundary"] = {"milestones": [14], "blocks": "Release"}
        self.assertTrue(validate_foundation(ROOT, record))

    def test_unverified_candidate_cannot_enable_production(self):
        matrix = copy.deepcopy(self.matrix)
        matrix["profiles"][0]["production_enabled"] = True
        self.assertTrue(validate_profiles(matrix, self.sources))

    def test_renaming_candidate_qualified_does_not_replace_evidence(self):
        matrix = copy.deepcopy(self.matrix)
        matrix["profiles"][0]["status"] = "qualified"
        matrix["profiles"][0]["eligibility"] = "reviewed"
        self.assertTrue(validate_profiles(matrix, self.sources))

    def test_unknown_regulatory_source_is_rejected(self):
        self.assertTrue(validate_profiles(self.matrix, set()))

    def test_removing_llp_scope_is_rejected(self):
        matrix = copy.deepcopy(self.matrix)
        matrix["profiles"] = [p for p in matrix["profiles"] if p["entity"] == "company"]
        self.assertTrue(validate_profiles(matrix, self.sources))


if __name__ == "__main__":
    unittest.main()
