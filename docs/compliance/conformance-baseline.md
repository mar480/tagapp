# XBRL specification and suite baseline

Official work-product indexes were checked on 2026-09-29. Exact URLs, sizes and
SHA-256 hashes are in [xbrl-conformance-pins.json](xbrl-conformance-pins.json).
Original specifications and archives remain in ignored local storage. This
record does not establish redistribution permission.

| Area | Specification selection | Official suite selection | Variations |
|---|---|---|---:|
| XBRL 2.1 | Recommendation 2003-12-31, corrected errata 2013-02-20 | 2025-07-16 | 606 |
| Dimensions 1.0 | Recommendation 2006-09-18, corrected errata 2012-01-25 | 2025-09-09 | 347 |
| Inline XBRL 1.1 | Part 1 corrected errata 2026-07-14; Part 2 recommendation 2013-11-18 | 2020-04-08 | 419 |

Sources: [XBRL 2.1 index](https://specifications.xbrl.org/work-product-index-group-base-spec-base-spec.html),
[Dimensions index](https://specifications.xbrl.org/work-product-index-group-dimensions-dimensions.html),
[Inline index](https://specifications.xbrl.org/work-product-index-inline-xbrl-inline-xbrl-1.1.html).
Dates embedded in older testcase XML are not archive release dates.

## Recorded result

[Final evidence](../qualification/conformance-result.json), observed 2026-09-29:

| Run | Accounted variations | Pass | Mismatch | Status |
|---|---:|---:|---:|---|
| Core, decimal inference | 606/606 | 606 | 0 | Passed |
| Dimensions | 347/347 | 347 | 0 | Passed |
| Inline, 20 groups with upstream comparison adapter | 419/419 | 418 | 1 | Review required |

The remaining Inline diagnostic is the exact additional diagnostic documented
by upstream for V-1003, described below. The harness applies no expected-error
override. The incomplete full Inline attempt is retained separately; it does not
invalidate or replace the fully accounted grouped evidence.

## Execution contract

The harness verifies pinned bytes, archive paths/types/size limits and CRCs,
then inventories the actual indexed testcase variations. It reads suite data
directly from ZIP files; it does not extract or execute supplied scripts.

Runs use installed Arelle 2.44.1 in a separate Linux network namespace, with
Arelle offline mode, a suite-local configuration directory and formula execution
disabled. Core uses XBRL 2.1 decimal-inference calculations (`--calc xbrl21`).
Inline uses the bundled `inlineXbrlDocumentSet` plugin, the suite's nested
example taxonomy package, and a pinned, reviewed upstream test-only HTML
comparison adapter. Expected-instance comparisons therefore use Arelle's
normalisations, described below. No application generator is exercised.

Each worker has a 600-second CPU limit, 720-second wall limit, 3 GiB address-space
limit and 128 MiB per-file limit. Initial core and Inline attempts used 120 CPU
seconds and returned without reports; these remain recorded locally. Increasing
the finite suite budget does not change expected testcase outcomes. An initial
core run with legacy precision inference produced five calculation mismatches.
The affected suite descriptions explicitly require decimal inference; the harness
was corrected to that mode without changing testcase expectations. The original
result remains local as `core-suite/legacy-precision-result.json`. The full Inline
run exceeded 600 CPU seconds; its result remains `unable_to_complete`. Subsequent
runs use the 20 groups in the official index, with at most four isolated workers.
Aggregation requires every indexed group and all 419 variation identities; skipped
cases in another group cannot count as passes.

Passing requires exit code zero, the expected number of uniquely identified
result rows, and `pass` for every variation. Missing/incomplete reports are
`unable_to_complete`; completed runs with other outcomes are `review_required`.
The processor's own expected-error matching remains distinct from an assertion
that every diagnostic code agrees across vendors.


## Inline test setup and comparison limits

Arelle's [2.44.1 suite configuration](https://github.com/Arelle/Arelle/blob/2.44.1/tests/integration_tests/validation/conformance_suite_configurations/xbrl_ixbrl_1_1.py)
identifies a nested taxonomy package (`schemas/www.example.com.zip`) and a
[test-only comparison adapter](https://github.com/Arelle/Arelle/blob/2.44.1/tests/plugin/testcaseIxExpectedHtmlFixup.py).
Their exact bytes are pinned. The adapter was read before execution; it is kept
local and is not an application runtime dependency.

The adapter normalises XHTML namespace declarations in expected escaped text and
resolves/encodes expected footnote URIs. It also emits a diagnostic for input
that is not Inline XBRL. It modifies the expected comparison model in memory;
this must not be described as byte-for-byte comparison of untouched expected
outputs. Original suite files remain unchanged.

The nested package provides the three example.com schema references. Its catalog
contains an external DTD declaration; package processing remains inside the
network-disabled worker. An initial run without this package produced missing
schema errors. Earlier unadapted group results remain under
`inline-suite/groups-before-upstream-setup/` and are not combined with the corrected
configuration.

Upstream also supplies a testcase-specific expected diagnostic for
`baseURIs/PASS-baseURI-on-ix-references-multiRefs.xml:V-1003`:
`xbrl:multipleTopLevelSchemasForNamespace`. This harness deliberately retains
that result as a visible mismatch rather than applying an expected-error override.
A complete adapted run with a mismatch remains `review_required`.

## Scope limits

- The 2020 Inline suite predates the selected 2026 Part 1 errata. Passing it cannot
  establish coverage of those later corrections; record focused regression cases
  when qualifying the generator.
- Transformation registry versions, additional XBRL modules, Companies House
  filing rules and exact profile applicability require separate qualification.
- Arelle suite results establish evidence about this processor configuration,
  not application certification, generated-report correctness or filing acceptance.
- Independent processor comparison has not been performed. It is an optional,
  vendor-neutral assurance activity, with no development, export or release gate.
  The user has a Companies House test account; applicable filing tests remain required.
- Original suite/resource redistribution and packaged processor supply-chain
  review remain separate from this local execution record.

Reproduction and evidence links are in the
[qualification instructions](../qualification/README.md#xbrl-conformance-suites).
