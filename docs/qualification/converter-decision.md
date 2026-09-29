# Converter qualification decision

The source-built replacement restores the missing graphics and preserves all
3,467 numeric occurrences across 108 pages. Qualification remains open for
application selection, punctuation and visual review.

The downloaded pdf2htmlEX AppImage remains **unsuitable for the principal fixture**.
Retain it only as a reproducible failure case. Do not try more report-specific
background settings or ask the user to review output already known to omit images.

## Evidence

1. The first source page contains JPEG2000 images. The full report inventory finds
   20 JPEG2000 image streams, including masks, plus four other image streams.
2. The paired synthetic control uses identical decoded pixels compressed as
   Flate and JPEG2000. The PDF rasterizer sees the image in both. The pinned
   converter retains the Flate image and loses the JPEG2000 image.
3. The release's [buildPoppler source](https://github.com/pdf2htmlEX/pdf2htmlEX/blob/v0.18.8.rc1/buildScripts/buildPoppler)
   sets `-DENABLE_LIBOPENJPEG="none"`. The file blob is
   `8c0df801757818f13862900ffd3109dac988e0c1`, verified from the official GitHub API.
   The current upstream [build script](https://github.com/pdf2htmlEX/pdf2htmlEX/blob/master/buildScripts/buildPoppler)
   enables `openjpeg2`; that moving branch is a lead for a replacement build,
   not a qualified or pinned dependency.
4. A one-page SVG-background experiment still loses the graphics. Its unmatched
   source-ink metric is approximately 96%, compared with approximately 96% for
   PNG. Do not scale this unsuccessful workaround to the full report.

The official release inventory was checked on 28 September 2026. It exposes old
2020 AppImages, including the August continuous build. Another binary from that
era is not presumed fixed. No alternate binary was downloaded on that assumption.

The image capability blocker is detected before new conversion runs. The original
PDF and prior conversion evidence are preserved. The diagnostic experiment flag
allows explicit reproduction only; it is not a way to approve or file the output.

## Replacement built and checked — 29 September 2026

Pinned pdf2htmlEX commit `cb7806aecbbee435e086be248fa068fbe3dc24c9`,
Poppler 24.06.1, FontForge 20230101 and poppler-data 0.4.12 were built in a
private Ubuntu 24.04 userspace. OpenJPEG and LCMS2 are enabled. No host packages
were installed and no report was mounted during build/dependency acquisition.
Compilation and report processing run without network access.

The tiny paired Flate/JPEG2000 control passed before the one-page report check;
the one-page text and image checks preceded full conversion. The 108-page run
completed in 73.465 seconds and preserved all 3,467 numeric occurrences with no
private-use glyphs. Six pages retain 16 raw U+2011 to U+002D substitutions (shown as U+2010
after NFKC in the original comparison). This is
`review_required`, not qualified output. An initial 60-second CPU limit stopped
an earlier full run; the recorded successful run has explicit 180-second CPU and
240-second wall limits, not an unbounded timeout.

The 18-page visual sample reuses checksum-verified PDF reference images. On page
1, unmatched source ink fell from 0.958643 to 0.001053; pages 33 and 37 have
fractions 0.000330 and 0.000144. All 18 image pairs have matching dimensions.
These measurements confirm recovery of the observed graphics defect; they do
not replace manual visual approval. Across sampled pages, unmatched source ink
ranges from 0 to 0.014138.

The replacement retains the original 210/238 near-edge drag result. A subsequent
paired test selects all 238 ranges with fixed interior-glyph coordinates and no
HTML/CSS changes. A public synthetic control independently reproduces the edge
sensitivity. See [the selection investigation](selection-decision.md). The native
selection boundary is fragile; this is neither missing numeric content nor a
completed application selection layer.

The [punctuation investigation](punctuation-decision.md) now isolates ignored
PDF ActualText replacements and records private repair candidates. Eight word
groups have unique matches; four require visual disambiguation. No repairs were
applied. Further speculative converter rebuilds are not justified by this finding.

Next: complete the outstanding baseline/profile evidence and retain reviewed
ActualText handling for the conversion/repair milestone; complete
visual and corpus review, and retain explicit selection preview/anchor tests for
the tagging milestone. No further rebuild or full conversion is justified by the
old edge-only selection result. See the [build record](converter-build.md).

Do not silently transcode/rewrite the original PDF, flatten it into page images,
or hide tag text over a raster and call that a qualified faithful XHTML conversion.
Any preprocessing would need its own recorded derivative and integrity tests.

## Separate selection finding

The 18-page sample at two zoom levels has 210 matching native drags out of 238.
All eight drags on a synthetic control pass. Seven fonts load; measured numeric
ranges fit within page boundaries. The subsequent interior-coordinate comparison passes 238/238, with the same
report bytes. This isolates sensitivity at transformed glyph boundaries; neither
result establishes a population failure rate or application acceptance.

Keep this separate from the JPEG2000 defect. The future tagging layer must offer
explicit, reviewable selection boundaries and stable anchors, as already required
by the plan. Do not assume a correct `textContent` value or an in-bounds rectangle
proves that a user selected the intended fact. App keyboard/click-only tagging and
accessible logical reading order remain future work.

## Evidence files

- [Replacement text and timing](sourcebuild-conversion-result.json)
- [Replacement codec control](sourcebuild-codec-result.json)
- [Replacement browser sample](sourcebuild-browser-result.json)
- [Replacement visual measurements](sourcebuild-visual-result.json)
- [Source and runtime build record](converter-build.md)

- [Codec regression](image-codec-result.json)
- [Input preflight](pdf-preflight-result.json)
- [Browser sample and control](browser-result.json)
- [Image measurements](visual-result.json)
- [Rejected SVG experiment](svg-background-result.json)
- [Browser dependency pins](browser-tool-pins.json)

The baseline milestone remains open. These findings do not qualify a filing
profile or advance production filing eligibility. No application UI, filing or
publication has been performed.
