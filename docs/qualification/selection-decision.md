# Selection boundary investigation

Observed 29 September 2026. All **238 sampled numeric selections** match with
fixed pointer coordinates one quarter of a glyph width inside the first/last
glyph. The original coordinates, only 0.2 CSS pixels inside each edge, still
match 210/238. Neither run edits the report HTML, styles, fonts or values.

## Evidence and scope

The same 18 pages, two zoom levels (100% and 150%), candidate selection rule,
eight-step native mouse drags and comparison function are used for both methods.
The inset coordinates are fixed before inspecting the selected result. There
are no retries, programmatic Range selection, guessed replacements or hidden
changes to the expected text. Comparison remains NFKC-normalised with whitespace
removed; this is not an assertion of exact whitespace preservation.

Of the 28 original mismatches, 14 endpoints hit outside the intended text line,
and five selections collapse at their start. These categories can overlap.
The converted lines use quarter-scale transforms, fractional positions and
negative character spacing. Caret lookup and an actual drag can disagree near
their edges. Small-sample CSS experiments (removing pseudo-elements, changing
bidi handling, or disabling image hit-testing) did not provide a general fix.
Adding line padding helped some cases, but was unnecessary with interior points.

An independent **public synthetic geometry control** reproduces the sensitivity
without report text or embedded report fonts. It covers scaled, fractionally
positioned text, trailing punctuation, a negative value and a number split across
spans. The old edge coordinates match 3/8; interior coordinates match 8/8.
The original ordinary-text control matches 8/8 with both methods.

Results:

- [Full 238-sample comparison](selection-result.json)
- [Public synthetic regression](selection-control-result.json)
- [Verification record](selection-checks-2026-09-29.json)

The full comparison precedes addition of the independent geometry control; each
record identifies its actual harness hash. Only the focused synthetic/one-page
checks were repeated after adding that control. No PDF rebuild or full conversion
was needed for the selection investigation. Original edge-based evidence remains
unchanged in `sourcebuild-browser-result.json`.

## Reproduce

With the pinned local Playwright installation from [qualification](README.md):

```sh
# Requires no private report or converter runtime:
python3 -m tools.baseline.browser_probe --synthetic-only

# Optional local report checks; separate output from original browser evidence:
python3 -m tools.baseline.browser_probe --candidate sourcebuild --diagnose-selection --pages 1 32 33 35
python3 -m tools.baseline.browser_probe --candidate sourcebuild --diagnose-selection
```

Diagnostic report runs retain `review_required` / exit 1 because the original
edge test still fails. The `inset_pointer_matches` field separately records the
interior-coordinate result. The synthetic-only command returns success when its
ordinary and geometry controls pass the interior-coordinate checks and the
script-blocking canary passes. It never loads the illustrative report.

## Application decision

The 28 mismatches are **not evidence that those values are missing or impossible
to select**. They establish a fragile native-selection boundary and an overly
edge-sensitive automated test. Raw native selection is still insufficient as
the tagging interaction contract. Users can start near edges, select across
lines, or use keyboard and click-only paths.

Keep the planned explicit selection preview, adjustable boundaries, stable
anchors and logical reading view. The tagging milestone must test actual user
interactions, overlays, zoom, narrow values, repeated text and cross-page ranges.
Do not silently expand a user's selection merely to match a numeric token.
Interior-glyph coordinates are a diagnostic/testing method, not an application
repair or a promise of accessible tagging. No product selection layer exists yet.

## Separate punctuation finding

The 16 U+2010 to U+002D differences remain flagged. A second installed Poppler
extractor produced the same reference-text hash. Enabling `--decompose-ligature 1`
on affected page 6 retained both hyphen substitutions on that page and all 42
numeric occurrences. The unsuccessful option was not applied to the full report.
Keep this issue in conversion repair/qualification; do not normalise it away in
the integrity check or claim that the selection result resolves it.

Follow-up: [the punctuation investigation](punctuation-decision.md) establishes
that the raw source uses U+2011 in ActualText metadata. U+2010 above describes
the prior normalised comparison. The integrity check now preserves that distinction.
