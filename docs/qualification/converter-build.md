# Replacement converter build

Observed 29 September 2026. This is a local qualification candidate, not a
distributed production runtime. The old AppImage omits JPEG2000 images; this
build passes the paired codec regression and restores the observed graphics.

## Inputs and provenance

- [Five source archive pins](converter-build-sources.json): Ubuntu Base 24.04.4,
  pdf2htmlEX commit `cb7806aecbbee435e086be248fa068fbe3dc24c9`, Poppler 24.06.1,
  FontForge 20230101 and poppler-data 0.4.12.
- [Installed package versions](converter-build-packages.tsv) and
  [213 retained package archive hashes](converter-build-debs.json).
- [Executable and 418 runtime file hashes](converter-build-result.json), including
  dynamically linked libraries, converter assets, CMaps and font configuration.
- [Build recipe](../../tools/baseline/converter_compile.sh) enables OpenJPEG and
  LCMS2. It supplies GIO header flags and the LCMS2 linker flag, and installs CMaps
  at the converter's compiled data path. No upstream source patches were needed.

Ubuntu Base's hash was compared with its publisher checksum list. Other source
archive hashes identify downloaded bytes; they are not publisher signatures.
Dependency acquisition used authenticated Ubuntu package repositories. The
dependency command uses those repositories' current versions: exact rebuilds
require the recorded package versions and retained archives. This is not yet a
byte-reproducible or independently reproducible container build.

## Local build procedure

Requirements: Linux, Python 3.12+, bubblewrap and working user namespaces. Host
Docker/CMake/Ninja are unnecessary. Put the five verified source archives, using
their manifest filenames, in `.local/converter-build/downloads/`. Acquisition is
an administrative step; report processing never downloads dependencies.

For a fresh build directory:

```sh
python3 -m tools.baseline.converter_build prepare
python3 -m tools.baseline.converter_build dependencies
python3 -m tools.baseline.converter_build configure
python3 -m tools.baseline.converter_build compile
python3 -m tools.baseline.converter_build version
```

`prepare` refuses an existing rootfs and verifies every archive before unpacking.
Do not remove or overwrite the qualified local candidate to test a new build.
Build logs stay under `.local/converter-build/`. Only `dependencies` has network
access. The source/build tree is the writable root inside a private userspace;
no host package installation occurs. The dependency step precreates the fonts
directory to avoid a package post-install ownership change unsupported by the
single-UID namespace. Compilation uses four jobs and a 30-minute wall limit.

`converter_pin.py` runs with the build namespace's Python after compilation. Its
JSON output is the runtime pin; copy `build/installed-packages.tsv` from that
rootfs and hash the retained `.deb` files separately. Pin updates are explicit
administrative evidence changes, not automatic acceptance of new runtime bytes.
The recorded build's pinning and archive acquisition were performed explicitly;
the build command does not yet automate these two steps.

## Qualification order

With the recorded runtime present, these commands verify its hashes before use:

```sh
python3 -m tools.baseline.codec_probe --runtime sourcebuild
python3 -m tools.baseline.sourcebuild_probe
python3 -m tools.baseline.browser_probe --candidate sourcebuild-page1
# Review the first-page image evidence before the full conversion.
python3 -m tools.baseline.sourcebuild_probe --full
python3 -m tools.baseline.browser_probe --candidate sourcebuild
python3 -m tools.baseline.visual_probe --candidate sourcebuild
```

The full conversion checks the recorded codec and first-page text results.
Its code does not automatically approve visual fidelity. The browser needs the
separately pinned Playwright runtime described in [qualification](README.md).
Image measurement needs Pillow. The visual probe reuses existing PDF reference
images only when their source and image hashes match; it does not reconvert HTML.

Report workers have a read-only rootfs/input mount, writable output, private
temporary directories, dropped capabilities and no network. Conversion limits
are 180 CPU seconds, 240 wall seconds, 2 GiB address space, 128 MiB per output
file and 128 file descriptors. These are process bounds, not aggregate disk or
cgroup memory quotas. Runtime pin verification resolves absolute symlinks inside
the namespace, avoiding accidental checks against host libraries.

## Actual results and remaining work

Both synthetic codecs pass. The full report completed in 73.465 seconds with all
108 pages and 3,467 numeric occurrences preserved. No private-use glyphs remain.
There are 16 hyphen substitutions on six pages. The original near-edge selection matched 210 of
238 drags; the subsequent fixed interior-glyph comparison matches 238/238 without
report edits. See [selection evidence](selection-decision.md). All eight ordinary
synthetic controls passed. Seven report fonts loaded
and the script canary was blocked. The 18-page image comparison is measured but
awaits visual review. Detailed text, screenshots and logs remain ignored locally.

Text and browser probes therefore return `review_required` (exit 1). A visual
probe exit 0 means measurement completed, not that visual acceptance passed.
See the [decision and next work](converter-decision.md). Selection, punctuation,
broader corpus checks, distribution obligations and production worker hardening
remain open. No application or filing eligibility follows from these probes.
