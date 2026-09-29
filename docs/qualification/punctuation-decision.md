# Punctuation finding: PDF ActualText

Observed 29 September 2026. The 16 report differences originate in **U+2011
NON-BREAKING HYPHEN**, not literal U+2010 characters in the PDF extraction.
The integrity comparison's NFKC normalisation maps U+2011 to U+2010. The
converted HTML contains ordinary U+002D hyphens instead.

The reviewed PDF's replacement-text metadata contains the 16 non-breaking
hyphens. The pinned converter follows the painted characters rather than this
`ActualText` replacement. Five tiny public synthetic PDFs isolate that behaviour:

| Case | Result |
|---|---|
| Ordinary painted hyphen | Preserved |
| Non-breaking hyphen supplied through a font ToUnicode map | Preserved |
| Same non-breaking hyphen supplied through ActualText | Ordinary hyphen emitted; difference detected |
| Identical painted and ActualText number | Preserved |
| Painted `12.34`, ActualText `72.34` | Converter emits painted number; reference extractor emits replacement; difference detected |

The last case is deliberately contradictory synthetic data. It demonstrates why
blindly trusting replacement text is also unsafe. Preserve both the visible and
logical representations and surface discrepancies for review. Do not repair an
arbitrary document by copying extracted text over the rendition.

## What changed

The integrity check now compares raw Unicode dash/hyphen codepoints separately
from its existing NFKC comparison. It rejects a U+2011-to-U+2010 substitution
even when the normalised character counts agree. Existing checks continue to
reject the U+2011-to-U+002D differences in this report.

The diagnostic locator uses the source extractor's page/word bounding boxes and
exact same-page text matches in the hashed HTML. All 16 occurrences fall in 12
word groups: eight groups have unique text candidates, four groups have repeated
candidates, and none is unmatched. Repeated candidates remain ambiguous. Their
PDF bounding boxes are retained privately for visual resolution.

No repair was applied. Proposals contain the original source/HTML hashes, page,
reference bounding box, line and character offsets, and `not_reviewed` status.
Offsets are Unicode codepoints and apply only to those exact HTML bytes; they
are diagnostic locations, not the application's future stable anchors. Report
text and proposals stay in ignored local storage.

## Decision and next work

Retain the current build as a conversion candidate with this explicit semantic
limitation. The missing images have been fixed; selection feasibility has been
demonstrated; this punctuation difference is now explained and locatable. Another
full-report conversion or speculative converter rebuild would not resolve the
review requirement.

At the document-conversion/repair milestone, present source and rendition
together, resolve repeated matches using geometry and user review, and record
accepted repairs in a new document revision. Preserve non-breaking semantics in
the logical text model and verify rendering/font coverage of any XHTML change.
Test general ActualText replacements, including conflicting numbers and spans
whose replacement text differs in length from the painted glyph sequence.

This closes the **cause investigation**, not conversion acceptance. The report
still requires visual review and reviewed repairs before it can be an accepted
tagging/export source. Application foundation, document repair UI, logical reading
order and accessible tagging remain unimplemented. Other baseline gates remain
open; production filing is not enabled.

## Reproduce and inspect

```sh
# Public synthetic inputs; requires the locally pinned converter runtime:
python3 -m tools.baseline.actualtext_probe
# Private report diagnostic; only metadata goes to stdout:
python3 -m tools.baseline.punctuation_probe
python3 -m unittest discover -s tests/baseline -q
```

Both probes currently return exit 1: the first exposes the converter's semantic
differences; the second produces unapproved review candidates. Neither reports
successful conversion merely because the expected defect was reproduced.

- [Synthetic evidence](actualtext-result.json)
- [Location counts](punctuation-result.json)
- [Reanalysis with raw-codepoint checks](punctuation-integrity-result.json)
- [Verification record](punctuation-checks-2026-09-29.json)
- [Synthetic probe](../../tools/baseline/actualtext_probe.py)
- [Read-only locator](../../tools/baseline/punctuation_probe.py)

Historical evidence describing U+2010 records the normalised comparison and is
retained. The raw source codepoint clarification here supersedes that shorthand.
