# Qualification tooling and evidence

These are administrative development probes, not application services or filing
approval. Inputs include public synthetic regressions and the user-selected
Grant Thornton illustrative report for local proof of concept. Downloads and generated
PDFs/HTML/logs stay under ignored `.local/`; public evidence contains only selected
metadata and results. No report has been sent to Companies House.

## Reproduce the public checks

Python 3.12+ and Git are sufficient; private reference inputs are unnecessary:

```sh
python3 -m unittest discover -s tests/baseline -v
python3 -m tools.baseline.check
python3 -m tools.baseline.publication_guard --worktree
python3 -m tools.baseline.publication_guard
```

With the original local materials and bare mirrors present:

```sh
python3 -m tools.baseline.check --local-materials
```

This compares original document/bundle hashes and reviewed branch pins. It does
not rescan entire histories for secrets. `--require-qualified` is separate and
deliberately fails while milestone gates remain open.

## Pinned acquisition

The following commands acquire only the two approved public artefacts, check
exact size/SHA-256 and atomically store them locally. Already verified copies are
reused. Failed or oversized downloads do not replace an existing file.

```sh
python3 -m tools.baseline.acquire frc2026
python3 -m tools.baseline.acquire pdf2htmlex-probe
```

[tool-pins.json](tool-pins.json) records exact URLs and checksums. These are
observed release-byte pins, not publisher signatures. FRC initially returned HTTP
403; a subsequent request using ordinary browser headers succeeded. No alternate
publisher, proxy or unauthorised source was used.

Acquisition requires network access. Processing probes below disable networking;
they never download packages or models implicitly.

## Current candidate

The replacement source build passes the paired image-codec control and preserves
all 108 pages / 3,467 numeric occurrences in the principal fixture. The old
AppImage below is retained for failure regressions. Use the
[replacement build instructions](converter-build.md) and [decision](converter-decision.md)
for current work. Selection, punctuation and visual review remain open.

## PDF conversion probe

Linux requirements: `bwrap`, `unsquashfs`, `pdftotext`, available user namespaces
and the pinned AppImage. It runs the verified archive after fresh extraction,
with read-only system/runtime/input mounts, an output mount, a private temporary
directory, no home directory access and no network. CPU, address-space, output-file
and file-descriptor limits plus a wall-clock timeout are applied.

```sh
python3 -m tools.baseline.conversion_probe
```

The generated corpus covers ordinary financial amounts, fragmented digits,
rotated text, image-only input and paired correct/incorrect Unicode maps.
`expectation_met` describes whether the probe saw the intended result. The
incorrect-map case must fail text integrity; it is not a successful conversion.
The image-only case is explicitly unsupported, not silently accepted as taggable.

The paired Unicode-map PDFs render identically in the local Poppler preview
(both show **12.34**) but the incorrect map extracts **72.34**. A test based solely
on visual fidelity or agreement between two extractors would miss this problem.
This is direct evidence for the required comparison/repair workflow, not a claim
that arbitrary real-world mapping errors can now be detected automatically.

Raw converter output includes scripts. It must not enter the future report canvas
without resource sanitisation and XHTML normalisation. Text concatenation tests
do not establish selection boundaries, DOM visibility, accessibility or reading
order. The corpus does not yet qualify subset/embedded fonts, ligatures, complex
tables, mixed scans, hostile PDFs or 300-page performance. HTML hashes have varied
across repeated conversion runs; preserve the accepted document revision rather
than reconverting at export time. Deterministic iXBRL generation remains a later
and separate requirement.

## Processor and taxonomy probes

Run using an interpreter containing `arelle-release==2.44.1`. This environment has
it at `/home/robert-marks/.pyenv/versions/3.12.8/bin/python`. It was already installed;
the probes do not install or change global dependencies. That version is a
feasibility pin, not a claim to be the latest or production-qualified release.

```sh
python3.12 -m tools.baseline.processor_probe
python3.12 -m tools.baseline.taxonomy_probe
```

Use the absolute interpreter path above if `python3.12` resolves elsewhere. These
commands require Linux `unshare` and working unprivileged network namespaces.
They use offline mode and private configuration; the taxonomy probe additionally
starts each entry point with a fresh user cache. Arelle's bundled standard-schema
cache remains part of its installed runtime. This is not proof that the FRC ZIP
alone contains every dependency.

The taxonomy intake checks archive checksum, size, expansion limits, paths,
duplicates, link/special-file entries, CRCs, manifest/catalog structure and local
entry-point mappings. It never extracts the taxonomy. FRS101, FRS102 and IFRS are
loaded/validated independently. Other entry points remain outside this probe.
No framework/category filing profile is qualified merely because its taxonomy
loads without error.

The processor probe accepts a synthetic valid iXBRL fact and rejects an invalid
monetary value with `xmlSchema:valueError`. This does not exercise dimensional
conformance, calculations, filing rules or full generated-fact equivalence.

## Synthetic regression fixture

```sh
python3 -m tools.baseline.report_fixture --check-taxonomy
python3 -m tools.baseline.report_conversion_probe
```

The first command creates a 16-page synthetic PDF, semantic XHTML reference and
60 candidate tagging facts, checking authored concepts/period types/dimension
identifiers against the pinned taxonomy. Omit `--check-taxonomy` to generate it in
a public-only checkout without local taxonomy assets. Arithmetic, source IDs and
byte-stable generation are tested. The second command runs actual pdf2htmlEX on
the PDF; all 16 pages and 86 monetary occurrences were preserved in the observed
run. The balance-sheet PDF preview was visually checked for column clipping.

See the [fixture source and limits](../../tests/fixtures/synthetic-frs102/README.md),
[fixture evidence](report-fixture-result.json) and
[conversion evidence](report-conversion-result.json). This remains focused regression
content, not the principal development report, complete statutory accounts or a profile-acceptance
fixture. It does not close the company/LLP qualification matrix.

## Principal local illustrative report

The user selected Grant Thornton's 108-page FY26 FRS 102 illustrative accounts
as the principal proof-of-concept fixture. Its checksum and intended use are in
[fixture-registry.json](fixture-registry.json). This is an advisory development
reference, not a normative authority or an accepted filing. Publisher guidance
and company disclosures must be classified before deriving tagging expectations.
Local use is authorised; redistribution of its contents is not part of this work.

```sh
python3 -m tools.baseline.illustrative_probe
python3 -m tools.baseline.illustrative_probe --tounicode force
# Recheck already converted bytes without rerunning the converter:
python3 -m tools.baseline.illustrative_probe --tounicode force --analyse-existing
```

These optional commands require the local PDF and pinned converter. CI does not
download or require the report. Both modes use the network-disabled bounded
sandbox above and preserve separate outputs under `.local/qualification/gt-frs102/`.
The default run uses `converted/`; forced Unicode uses `converted-force-tounicode/`.
Raw HTML, source text, logs and `private-differences.json` stay ignored locally.
Only an explicit metadata allowlist is printed or copied into public evidence.
Existing-output analysis verifies source, HTML and text hashes and configuration.

[Recorded results](illustrative-conversion-result.json): both modes produced all
108 pages. Auto Unicode produced 7,204 private-use characters and failed numeric
integrity. Forced ToUnicode preserved all 3,467 numeric runs per page with no
private-use characters. Six pages (6, 7, 63, 65, 78, 85) still contain 16 substitutions
from U+2010 HYPHEN to U+002D HYPHEN-MINUS. They remain explicitly flagged;
**both probes return exit status 1 (`review_required`)**, not a qualified pass.

Comparison uses numeric occurrence multisets and non-whitespace character counts
per page after NFKC normalisation. Numeric comparison also normalises U+2212 minus;
character comparison does not hide punctuation differences. This detects changed,
missing and duplicated values and missing narrative characters, but not all changes
of meaning, order or position. It is not an independent correctness oracle. Forced
ToUnicode is a promising candidate for this report, not a universal safe setting:
a PDF can contain an incorrect map. Visual comparison and selection/reading-order
checks remain required. Raw HTML includes scripts and has not been sanitised into
application XHTML.

## Evidence and limitations

- [Conversion results](conversion-result.json)
- [Processor results](processor-result.json)
- [Offline taxonomy results](taxonomy-result.json)
- [Dependency metadata and licence review](licences.md)
- [Original material hashes](materials-manifest.json)
- [Repository pins and complete supplied ref inventory](repository-pins.json)

CI runs only public record/guard tests, with an immutable checkout-action pin and
read-only repository permissions. It does not fetch FRC assets, execute supplied
repositories, use credentials, or assert conformance. Its commands are verified
locally; the hosted workflow has not run because nothing has been pushed.

## Browser, graphics and codec qualification

The pinned AppImage is now **rejected for the principal report**, not merely
awaiting a visual review. It was built with OpenJPEG disabled. The report contains
20 JPEG2000 image streams; the paired synthetic codec regression reproduces image
loss independently of the report. PNG/SVG background settings do not fix this.
See [the converter decision and next action](converter-decision.md).

The standard `illustrative_probe` command now performs image preflight and stops
before conversion when this incompatibility is detected. Existing outputs are
preserved. `--analyse-existing` still examines old evidence. The explicit
`--exercise-known-incompatibility` flag exists solely to reproduce qualification
failures; it does not make the output acceptable.

Optional local browser tooling is pinned in [browser-tool-pins.json](browser-tool-pins.json).
Install into ignored local storage, separately from report processing:

```sh
npm install --prefix .local/tools/browser-probe --save-exact --ignore-scripts --no-audit --no-fund playwright@1.63.0
PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/tools/browser-probe/browsers" node .local/tools/browser-probe/node_modules/playwright/cli.js install chromium --only-shell
python3 -m tools.baseline.pdf_preflight
python3 -m tools.baseline.codec_probe
python3 -m tools.baseline.browser_probe
python3 -m tools.baseline.visual_probe
```

The last three commands also need the pinned converter/previous outputs and,
for image diagnostics, Pillow with JPEG2000 support. Their dependencies are not
required by public CI; optional image-metric unit tests are skipped without Pillow.
The browser driver verifies the recorded lockfile and executable hashes. The
worker has read-only runtime/input mounts, private output/temp storage, no host
network, no capabilities and a separate PID namespace. CPU, file-size, descriptor
and wall-time limits apply; there is no aggregate browser memory cgroup limit yet.
Chromium's internal sandbox is disabled by Playwright's default here; outer
isolation is qualification infrastructure, not completed production hardening.

The exact report bytes are fulfilled in memory at a reserved `.invalid` URL;
no web server, DNS access or report upload is used. Response CSP blocks scripts,
external resources, frames and form submissions. The browser is also offline,
service workers are disabled and unexpected requests are aborted. A synthetic
inline-script canary verifies script blocking. Only the harness's automation runs.

The report sample covers 18 pages at 100% and 150% CSS zoom: 210/238 native number
selections match; all eight synthetic control selections pass. Seven fonts load,
with no failures. All measured numeric ranges have rectangles within their page,
but that alone does not establish correct selection. See [browser results](browser-result.json).
The sample is deterministic, not a statistically representative failure rate.
It does not qualify keyboard, assistive-technology, cross-page or application
selection, none of which has been implemented yet.

`visual_probe` produces a private `review.html` and paired images in
`.local/qualification/gt-frs102/browser/`, with 18 PDF pages rasterised at 72 dpi
to match the HTML's measured dimensions. No silent resizing is applied. Metrics
measure pixel differences and unmatched ink with two-pixel tolerance; they are
triage evidence, not visual acceptance. [Visual results](visual-result.json)
remain `visual_review_pending`. Screenshots, selected strings and error logs stay
local. Public evidence contains only tool/input hashes, page identifiers and counts.

The intentionally nonzero preflight, codec and browser probe exits expose known
problems. Unit tests pass because they verify the checks, not because conversion
or filing qualification has passed. The full application remains unimplemented.

## Selection boundary result

The original near-edge sample remains 210/238. A paired fixed interior-glyph
strategy passes 238/238 without report HTML/CSS changes. The public synthetic
geometry regression reproduces the boundary sensitivity. Run it without private
materials using `python3 -m tools.baseline.browser_probe --synthetic-only` after
installing the pinned local browser tooling. See the
[selection decision and limits](selection-decision.md). Native edge behaviour,
application interaction/accessibility, punctuation and visual acceptance remain
distinct checks; this result does not qualify the tagging workflow.

## ActualText and punctuation

Five tiny synthetic PDFs isolate the converter's ActualText limitation. The report's
16 differences are non-breaking U+2011 hyphens exposed as U+2010 by the former
normalised diagnostic description. Raw codepoint comparison now also detects
loss of non-breaking semantics. Eight word groups have unique repair candidates;
four have repeated matches requiring review. No report bytes were changed.

See [punctuation evidence and reproduction](punctuation-decision.md). This is a
known conversion/repair requirement, not a reason to keep rebuilding the converter
or to silently accept the differences.

## Companies House transport schemas

The [schema baseline](../compliance/schema-baseline.md) pins twelve official XSDs
and records thirty offline synthetic checks across envelope, wrapper and polling.
These checks use no credentials, contain no report data and make no submissions.
Schema success is kept distinct from attachment, filing-profile and gateway acceptance.


## XBRL conformance suites

The [conformance baseline](../compliance/conformance-baseline.md) records exact
specification/suite selections, offline execution boundaries and coverage limits.
The original archives and processor logs remain under ignored
`.local/qualification/xbrl-conformance/`.

```sh
# Administrative acquisition only; reuse present files after verifying exact bytes.
python3 -m tools.baseline.conformance --acquire
# Inventory only, with no processor dependency or network access.
python3 -m tools.baseline.conformance
# Use a Python environment containing arelle-release==2.44.1 and Linux unshare.
python -m tools.baseline.conformance --run core
python -m tools.baseline.conformance --run dimensions
# The full Inline run exceeded its finite CPU budget on the baseline host.
# Grouped execution keeps every official testcase, with at most four workers.
python -m tools.baseline.conformance --list-inline-groups | \
  xargs -r -n1 -P4 python -m tools.baseline.conformance --run inline --inline-group
python -m tools.baseline.conformance --summarize-inline
```

A nonzero suite exit must be investigated. It must not be waived by the ordinary
unit tests or by successful loading of the FRC taxonomy. No credentials or
unpublished report data are used by these runs. Downloading dependencies and
archives is separate from network-disabled report/suite processing.

[Conformance results](conformance-result.json) distinguish full-suite attempts
from grouped Inline results. The Inline comparison uses pinned upstream test
normalisations; see the baseline for the exact scope. Nonzero exits are retained
when the processor reports a mismatch, including the documented base-URI case.
