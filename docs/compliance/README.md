# Compliance baseline

[sources.json](sources.json) records authority, version, URL, verification limits
and document hashes where available. [profile-matrix.json](profile-matrix.json)
is a qualification backlog, **not runtime eligibility or filing rules**.

The matrix contains 22 candidate entity/category rows, four framework entry-point
references and 66 positive/negative case specifications. None is an executed
filing fixture. No company/LLP profile is production-enabled. A technical filing
category in the TIS does not establish that a particular entity may use it.
Statutory exclusions, framework eligibility, effective dates, size thresholds,
group restrictions and audit exemptions require separate review. Do not treat
frameworks and account categories as an eligible Cartesian product.

## Source locations

ODT paragraph references are 1-based positions in `content.xml`, counting both
`text:p` and `text:h` in document order, including empty elements. Document hashes
identify exact source bytes; reflow-dependent page numbers are not used.

| Topic | Accounts TIS paragraphs | Implementation consequence |
|---|---|---|
| Technical categories | 271–297, 781–816 | Keep entity/category matrix and historical cases distinct |
| 2026 entry points | 753–779 | FRS101, FRS102 and IFRS have separate entry points |
| Micro framework mapping | 794–802 | FRS105 uses the FRS102 entry point and applicable standard classification |
| Common facts and defaults | 826–865 | Entity/period/approval/classification; LLP legal form; do not serialize default members explicitly |
| Audited categories | 867–1020 | Preserve entity/category exceptions, including audited-micro treatment |
| Unaudited categories | 1555–1656 | Entity-specific exemption/responsibility wording and period conditions |
| Revised accounts | 306–330 | Original/revised dimension semantics depend on taxonomy version |

The TIS sources are published by [Companies House](https://www.gov.uk/government/publications/technical-interface-specifications-for-companies-house-software).
Derived descriptions are attributed to Companies House under OGL v3, subject to
the source's third-party exceptions. Original FRC guidance remains local pending
its separate copyright review.

## Qualification work remaining

1. Complete transformation-registry/profile selection and later-errata coverage.
   Core, dimensions and Inline specification/suite bytes are now pinned; see
   [conformance baseline](conformance-baseline.md). The twelve-file CH transport
   schema closure is pinned and compiles offline; see [schema baseline](schema-baseline.md).
   FRC entry-point loading evidence remains separate from full conformance.
2. Review legal eligibility and exceptions per candidate/framework with effective
   dates; split candidate rows into exact versioned profiles.
3. Resolve auditor-concept changes and TIS date/version labels. `GatewayTest`
   integer lexical constraints are now tested; the conflicting prose and operational
   test-mode behaviour still require gateway confirmation at the filing milestone.
4. Generate substantial synthetic FRS102 accounts and companion FRS101, IFRS,
   LLP and micro fixtures. Each supported profile needs positive and deliberate
   negative cases. The small processor probe does not satisfy this requirement.
5. Record Arelle, conformance, generated-fact comparison and Companies House
   results at their relevant milestones, with exact hashes, versions, findings
   and receipts. Independent processor comparison is optional and vendor-neutral;
   it is not a development, export or release prerequisite.

Entry-point URLs are identifiers/acquisition references. Processing workers must
load pinned local packages rather than fetch dependencies during report handling.

## Fixture design contract

The principal synthetic report should contain financial statements and notes with
comparatives, narrative and realistic tables. Use invented entities, identifiers
and people, visibly marked not for filing, and deterministic fixture generation.

Maintain an expected-fact manifest independently of generated markup: expanded
QNames, decimal strings, contexts, units, dimensions, source ranges and expected
findings. Cover signs/scale/decimals, zero/nil/false/absent, repeated text,
continuations, exclusions and footnotes. Technical conformance fixtures for typed
dimensions or other constructs must remain separate where the filing profile
does not permit them.

The conversion corpus must cover subset/embedded fonts, Unicode maps, ligatures,
multi-column order, fragmented numbers, rotated/invisible text, mixed scans,
encryption, corruption and resource limits. Compare appearance and selected text;
concatenated text equality alone does not establish anchors or reading order.
