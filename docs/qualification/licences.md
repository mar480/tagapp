# Licence and distribution inventory

New Tagger code is GPL-3.0-or-later. The repository licence does not automatically
relicense reference repositories, documentation or third-party assets. The user
authorises reuse of their first-party code; exact extracted files still require
authorship and third-party notice review.

No first-party root licence file was found in Charles, Cake or Soft. Cake's pinned
frontend lockfile has 486 dependency entries with declared licence metadata,
recorded in [cake-dependency-inventory.json](cake-dependency-inventory.json).

| Declared expression | Entries |
|---|---:|
| MIT | 424 |
| ISC | 27 |
| Apache-2.0 | 19 |
| BSD-2-Clause | 6 |
| BSD-3-Clause | 4 |
| Apache-2.0 AND BSD-3-Clause | 1 |
| BlueOak-1.0.0 | 1 |
| Python-2.0 | 1 |
| CC-BY-4.0 | 1 |
| 0BSD | 1 |
| MIT AND ISC | 1 |

These count package entries, not unique products. This is metadata, not a reviewed
SBOM or distribution clearance. Audit licence text, icon/font terms, notices and
build dependencies in the exact selected distributions. Do not copy all unused
MVP dependencies into the new application.

| Item | Evidence / obligations still to review |
|---|---|
| pdf2htmlEX | GPLv3-or-later with separately licensed resources; inspect exact bundled libraries, fonts and JavaScript and corresponding-source/build obligations |
| Arelle | Apache-2.0; local probe version 2.44.1; pin production wheel, dependencies and plugins and preserve notices |
| FRC guidance/packages | Copyrighted; review package-specific and dependency terms before redistribution; default to private administrative acquisition |
| CH documentation | OGL v3 with exceptions; attribute derived rules and inspect schema-specific notices |
| XBRL specifications/suites | Review each downloaded artefact's terms and pin permitted test assets |
| Qwen/llama.cpp | Separate future model/runtime downloads; verify exact terms at AI milestone |
| Application foundation | Exact Python/npm versions are locked; 32 Python and 84 Node entries have declared licence metadata in [foundation-dependencies.json](foundation-dependencies.json). Full notice/resource and distribution review remains required. |

Independent processor comparison is optional and vendor-neutral. No second
processor licence needs to be acquired. Review the terms of any tool selected
for that optional activity before use or redistribution.

References: [pdf2htmlEX licence](https://raw.githubusercontent.com/pdf2htmlEX/pdf2htmlEX/master/LICENSE),
[Arelle](https://arelle.org/about/),
[FRC copyright](https://www.frc.org.uk/about-us/policies-and-procedures/disclaimer-and-copyright/).

The converter AppImage remains ignored and is retained for synthetic controls
and local illustrative-report failure evidence. Its observed hash identifies downloaded bytes; the reviewed GitHub
asset metadata did not provide a publisher digest. This is neither a signature nor
evidence that its old bundled libraries are suitable for production.

The replacement source build is also local qualification tooling. Its five source
archives, installed package versions, 213 retained package archive hashes and
418 runtime file hashes are recorded in the [build record](converter-build.md).
These provenance records do not complete licence, corresponding-source, font or
resource redistribution review. No binary/runtime distribution is included.
