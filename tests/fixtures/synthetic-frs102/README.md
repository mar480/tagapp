# Synthetic financial report fixture

`report.json` is newly authored, public synthetic content. No client documents or
MVP account data were reused. It creates a 16-page conversion/tagging fixture with
comparatives, reconciled financial statements, notes, repeated disclosures,
cross-page prose, footnote exercises, negative amounts, zero, exact cents, GBP/pure
units and explicit equity-dimension tagging candidates.

Generate local review artefacts:

```sh
python3 -m tools.baseline.report_fixture
# With the pinned taxonomy available locally:
python3 -m tools.baseline.report_fixture --check-taxonomy
python3 -m tools.baseline.report_conversion_probe
```

Outputs are in `.local/qualification/report-fixture/`: a selectable PDF, a semantic
XHTML reference, candidate expected facts and checksums. The XHTML is authored
reference output, **not converted PDF output or iXBRL**. Stable source-node IDs
are fixture identifiers, not an implemented application anchoring service.

The report is incomplete illustrative financial information, not statutory
accounts, a compliant FRS102 assertion or a positive Companies House test filing.
Concept existence and arithmetic can be checked now; dimensions, mandatory
disclosures, contexts and filing eligibility still require qualification. Untagged
exercise rows are deliberate. Typed dimensions, nil/false/absent states and legal
continuation/footnote markup need companion conformance fixtures.

This is now a focused regression fixture; the principal local proof of concept
uses the Grant Thornton report recorded in
[the fixture registry](../../../docs/qualification/fixture-registry.json).
Use this synthetic fixture to test conversion, selection, repeated-source
occurrences and reviewed reconciliation. Extend it with independently reviewed
expected facts before using it as a generation or profile-acceptance oracle.
