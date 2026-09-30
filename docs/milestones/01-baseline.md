# Milestone 1 — baseline and qualification

Status: **foundation ready; full qualification in progress**. Step 2 has started;
the tagging UI has not. See the [foundation decision](../decisions/0001-foundation-boundary.md)
for the explicit reassignment of outstanding qualification. Gate status is machine-readable in
[01-status.json](01-status.json). The accepted scope is unchanged; the user has replaced the principal local
fixture with Grant Thornton's FY26 illustrative accounts.

## Delivered and checked locally

- Publication exclusions and an index/worktree guard, including forced staging,
  staged-versus-working-copy differences, symlinks, binary files and selected
  secret formats. Supplied materials remain local and untouched.
- Pinned bundle/document inventories, the 16-section intake assessment and Cake
  preservation checklist, with source citations corrected to local Git paths.
- Candidate company/LLP matrix: four framework references, 22 category/entity rows
  and 66 acceptance-case specifications. All remain unqualified.
- Reproducible, bounded acquisition of the official FRC package and synthetic
  converter artefact, with hashes and resource/path checks.
- Network-disabled validation of the FRC 2026 FRS101, FRS102 and IFRS entry points
  in Arelle 2.44.1 with fresh user caches.
- Synthetic iXBRL positive/negative processor probes, and six PDF conversion cases
  including an appearance/text mismatch from an incorrect Unicode map.
- A 16-page authored synthetic report, 60 tagging candidates, and an actual
  conversion comparison preserving all 86 monetary occurrences; concept IDs and
  period types checked against the downloaded package.
- Principal local fixture registered: Grant Thornton FY26 illustrative accounts,
  108 pages. Both Unicode conversion settings were exercised. Forced ToUnicode
  preserves all numeric runs; 16 punctuation substitutions remain flagged across
  six pages. Subsequent browser/codec checks reject this AppImage for missing
  JPEG2000 graphics and flag native selection mismatches; see
  [the converter decision](../qualification/converter-decision.md).
- Replacement converter built from pinned sources in an isolated Ubuntu userspace,
  with OpenJPEG and LCMS2 enabled. Both codec controls pass; all 108 pages and
  3,467 numeric occurrences survive conversion. The 18-page browser/image sample
  confirms graphics recovery; 16 punctuation substitutions and 28 of 238 native
  near-edge drag mismatches were subsequently isolated: fixed interior-glyph
  coordinates pass 238/238 without report changes. A public synthetic geometry
  control independently reproduces the boundary sensitivity. Punctuation, visual
  review and application selection remain open.
- Punctuation cause isolated with five synthetic controls: the converter ignores
  ActualText replacement hyphens. All 16 source occurrences are located in 12 word
  groups (eight unique, four ambiguous); no repair applied. Raw codepoint checks
  now prevent NFKC hiding loss of non-breaking semantics. See
  [the punctuation decision](../qualification/punctuation-decision.md).
- Twelve official CH transport schemas pinned with complete selected dependency
  closure; four roots compile offline and thirty synthetic checks pass expectations.
  [Schema findings](../compliance/schema-baseline.md) record GatewayTest lexical
  constraints, lax envelope validation and local base64-validator limits.
- Official core, dimensions and Inline specification/suite bytes pinned. Core
  passes 606/606 and dimensions 347/347 offline in Arelle 2.44.1. Inline uses
  bounded groups and a pinned upstream comparison adapter: 419/419 cases accounted
  for, 418 passes and one upstream-documented expectation mismatch retained. See
  [conformance evidence](../qualification/conformance-result.json) and
  [comparison limits](../compliance/conformance-baseline.md).
- Public CI definition and licence/dependency review records.
- CH test presenter account availability confirmed by the user. No credentials
  have been stored, no messages sent and no filing attempted.

## Qualification work retained and assigned to later milestones

| ID | Work | Required evidence |
|---|---|---|
| B1 | Finish exact profile applicability | Effective-date/legal references, entity/framework exceptions and explicit unsupported combinations |
| B2 | Materialise profile examples | Use the 108-page local illustrative report for PoC; create reviewed public synthetic accounts and companion profile/negative fixtures; case specifications alone are insufficient |
| B3 | Complete normative asset pins | CH transport closure and core/dimensions/Inline specification/suite pins completed; transformation-registry/profile selection, later-errata coverage and packaged processor provenance remain |
| B4 | Expand converter qualification | Replacement build and codec gate passed. Selection boundary sensitivity isolated; preserve explicit application selection/anchor gates. ActualText cause isolated and repair candidates recorded; reviewed repairs remain a conversion requirement. Complete visual review and remaining corpus/build obligations |
| B5 | Complete distribution review | Exact component/resource notices, FRC package terms and converter corresponding-source obligations |

Decision update — 29 September 2026: the user removed mandatory RaptorXML
qualification. B6 has been removed; independent processor comparison is optional
and vendor-neutral, with no development, export or release gate. B1–B5 and all
other unresolved qualification requirements remain in force.

Cake browser screenshots and interaction parity tests belong to its extraction
milestone; the current static checklist must not be reported as completed visual
regression coverage. Production filing, Companies House test acceptance and the
full release-assurance suite belong to later gates, not to this smoke-test record.

## Verification and demonstration

See [qualification instructions](../qualification/README.md). Public checks must
work without private materials. Local-input verification must detect any changed
document or bundle. The guard must identify private files even when force-staged.
Downloaded archives must not be consumed if they differ from their approved hashes.

The intentional gate check is:

```sh
python3 -m tools.baseline.check --require-qualified
```

Its nonzero exit status currently means the milestone is unfinished. Ordinary
unit-test success does not override it. No migration, commit, push, deployment or
existing-source mutation is part of this milestone.

## Next dependency

The user authorised starting the foundation with B1–B5 assigned to the milestones
listed in the [decision](../decisions/0001-foundation-boundary.md). None of those
requirements is waived. Follow [Step 2](02-foundation.md) for implementation and
actual verification evidence.
Do not require the user to test a tagging UI before that UI exists.
