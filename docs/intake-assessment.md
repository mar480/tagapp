# Intake and reuse assessment

Assessed 28 September 2026. Static review of the supplied Git histories and
documents; existing applications, setup scripts, migrations and tests were not
executed. Separately recorded synthetic qualification probes execute installed
Arelle and an official converter, not supplied repository code.

Source citations below are **local Git object citations**, not working-copy paths.
`C:path:lines` means `git --git-dir=charles.git show 822051c304abc07f2cc00345e5a60b15f5fe2369:path`;
`K:` uses `cake.git` at `9251b790faa65b78d80dbe4528fcdd3aefef1238`;
`S:` uses `soft.git` at `6693b812dc73fd7c66b47a1d894c8300a377e602`.
The line numbers refer to that immutable content. No confidential working copy
has been placed in distributable application code.

## 1. Executive summary

Cake is the strongest starting point for taxonomy navigation and its visual
vocabulary should be preserved. Its process-global taxonomy state must be replaced
before a multi-project service uses it (`K:backend/state.py:6–13`). Charles offers a
micro-entity regression workflow, not a general fact model
(`C:tagger/backend/tagger/models.py:17–32`). Soft contributes rule-management and
validation-presentation ideas, but its narrow report parser and float arithmetic
are unsuitable for the new core (`S:backend/validation_rules/testing/report_loader_core.py:26–87`,
`S:backend/validation_rules/testing/report_model.py:41–55`).

Keep all three bundles and their histories local. No existing project establishes
general Companies House filing conformance, production submission recovery, or
the requested free-tagging workflow. Static evidence supports targeted extraction,
not wholesale migration. The accepted delivery plan remains the implementation
authority; the baseline gate is still open.

## 2. Materials received

Actual root: `/home/robert-marks/Documents/tagapp`, branch `main`. Before changes,
only `init.txt` was tracked and its deletion was already present. That deletion is
preserved. No applicable non-empty `AGENTS.md` was found in the project, parent or
home instructions inspected during intake.

| Material | Size / state |
|---|---|
| `tagapp-materials/repos/charles.bundle` | 128,051,318 bytes |
| `tagapp-materials/repos/cake.bundle` | 147,801,827 bytes |
| `tagapp-materials/repos/soft.bundle` | 34,501,213 bytes |
| `charles.git/`, `cake.git/`, `soft.git/` | Existing local bare mirrors |
| Five guidance documents under `materials/inbox/` | Two ODTs and three PDFs; see section 10 |
| `materials/README.md`, `materials/repos/README.md` | Internal intake descriptions |
| `tagapp-materials/PLAN.md` | Saved accepted plan; copied to `docs/implementation-plan.md` |

Expected bundles are present under a different directory from the handoff. The
root README was absent and is now created for the new project. Bundle sizes make
them unsuitable public source assets independently of their confidentiality.
No principal substantial synthetic report or complete qualified taxonomy package
was supplied as a standalone development fixture. Full filename/size/checksum
inventories are in [materials-manifest.json](qualification/materials-manifest.json)
and [repository-pins.json](qualification/repository-pins.json).

## 3. Confidentiality and public-repository risks

See [the containment register](security/publication.md). Soft includes uploaded
accounts, report outputs and live-looking database files, including
`instance/soft_validation.db`, `instance/soft_validation_local.db` and historical
test databases. Do not copy these into fixtures or public releases. Uploaded
documents and DB records were not semantically inspected.

Charles's selected tree has 26,177 tracked files, predominantly 26,077 dependency
files under `node_modules` plus compiled Python caches. Soft has 57,864 tracked
files, including 56,486 rule snapshots, 152 reports and 50 uploads. These are tree
inventory counts, not evidence that every file is unique or confidential.

An archived Cake Supabase JWT indicates an anonymous role
(`K:archive/pr-d-2026-04-07/dead-code/frontend/src/integrations/supabase/client.ts:7`).
Soft hard-codes a development session secret (`S:backend/webapp/__init__.py:15`).
Values are intentionally omitted. Anonymous role metadata alone does not prove
privileged access; exclude the dead integration and review deployed permissions.

Local history-pattern scanning examined reachable objects across refs. Unique
blob inventories were Charles 23,728, Cake 2,203 and Soft 2,498; respectively
142/303/69 blobs exceeded the 4 MB scan threshold, and binary coverage was limited.
Initial provider-pattern matches in taxonomy names were false positives. No
confirmed privileged provider credential was established by the refined scan.
This is not exhaustive secret, PII, malware or copyright clearance. Before
republishing any historical source, perform a dedicated history scan and review
the exact files selected for extraction.

## 4. Bundle and branch verification

All three bundles passed `git bundle verify`; they contain complete histories.
`git fsck --full --no-reflogs` succeeded for each mirror. Bundles and mirror refs
matched apart from the bundle's `HEAD` entry. No tags were present.

| Repository | Default branch | Selected branch and commit | Ref inventory |
|---|---|---|---|
| Charles | `oneshot` | `oneshot`, `822051c304abc07f2cc00345e5a60b15f5fe2369` | One branch |
| Cake | `main` | `vps`, `9251b790faa65b78d80dbe4528fcdd3aefef1238` | 64 branches, 45 pull refs |
| Soft | `main` | `frontend`, `6693b812dc73fd7c66b47a1d894c8300a377e602` | Three branches, one pull ref; `next` shares selected commit |

The full ref names, commits, SHA-256 bundle hashes and symbolic default refs are
recorded in [repository-pins.json](qualification/repository-pins.json). No branch
was guessed from a remote, and no existing source ref was modified.

## 5. Charles assessment

**Purpose and stack.** Flask API, SQLite/JSON project persistence, React/TypeScript
Vite frontend, npm dependencies. Python requirements pin Flask 3.1.0, Gunicorn 23,
lxml 5.3.0, Arelle 2.36.40 and openpyxl 3.1.5
(`C:tagger/backend/requirements.txt:1–5`). API setup is
`C:tagger/backend/app.py:1–79`; frontend scripts/dependencies are in
`C:tagger/frontend/package.json:1–103`. Current selected commit is dated
2026-06-16; that is evidence of recent activity, not ongoing maintenance assurance.

**Domain and generation.** Projects default to a micro-entity profile with
dict-heavy state (`C:tagger/backend/tagger/models.py:17–32`). Context/unit registries
are limited (`context_registry.py:7–17`, `unit_registry.py:6–16` in the same package).
Generation maps template fields and uses fixed current/prior contexts
(`ixbrl_generator.py:134–176,216–268`). It is useful as a behaviour fixture, not a
general source-anchored tagging engine. Persistence stores mutable JSON in SQLite
(`storage.py:39–60,80–121`); immutable revisions, permissions and durable jobs need
new implementation.

**Validation and filing.** Arelle is invoked through a subprocess and messages are
classified by textual log content (`validation.py:705–765`). Fixture-signature
comparison covers a limited subset and does not compare all fact values
(`validation.py:653–702`). External test validation posts the report and polls/
scrapes results (`companies_house_validator.py:40–103`). Company/officer lookup
calls are separate from filing (`companies_house_client.py:10–11,31–77`). A passing
test-validator report is not evidence of production submission.

**UI/accessibility.** Template-based canvas and concept override controls, rather
than a free taxonomy drag/drop workspace. The canvas prevents default Tab handling
at its boundary and injects HTML (`C:tagger/frontend/src/components/tagger/TemplateCanvas.tsx:62–78,107`).
Concept override accepts textual QNames (`ConceptOverridePanel.tsx:31–67`), with
local workspace state (`C:tagger/frontend/src/pages/TaggerWorkspace.tsx:32–42`). These behaviours need review
before reuse; static inspection cannot establish keyboard accessibility.

**Security/tests/docs.** Optional authentication and blacklist-style HTML filtering
are insufficient for the new private-team deployment
(`C:tagger/backend/tagger/security.py:12–39,55–73`). Backend tests exercise the
micro-entity workflow and mock external validation
(`C:tagger/tests/test_tagger_microentity.py:187–505`). The frontend test
script refers to `src/all-tests.ts`, which was absent in the selected tree.
`C:docs/tagger-completion-audit.md:3–52` contains dated claims and stale paths;
these were not rerun or accepted as conformance evidence. No active local AI/MCP
provider integration was established by the reviewed code. No first-party licence
file was found at the repository root.

## 6. Cake/vps assessment

**Purpose and stack.** A substantial taxonomy explorer using Flask, direct Arelle
loading, React/TypeScript, Vite and PrimeReact. API entry:
`K:backend/app.py:1–70`; dependency/build evidence:
`K:backend/requirements.txt:1–4`, `K:frontend/package.json:1–103`, `K:backend/Dockerfile`.
The Dockerfile uses Python 3.12 slim and one Gunicorn worker with four threads.
Selected commit date: 2026-09-21. Seven frontend test files, two backend test files
and smoke scripts were found; no supplied tests were executed in intake.

**Taxonomies.** Loader exposes Arelle model objects directly
(`K:backend/xbrl/loader.py:27–37`). Selection is process-global behind an RLock
(`K:backend/state.py:6–13`), incompatible with independent project selections.
Entry-point discovery and remote-first loading appear in
`K:backend/services/taxonomy_service.py:44–62,106–198`. The selected tree contains
cached JSON and package metadata but no XSD files. It cannot establish complete
offline DTS loading. Some 2027 metadata is version 0.1.0; one charities metadata
directory uses `META_INF`, inconsistent with expected `META-INF` handling.

**Capabilities.** Concept extraction includes labels/references and relationships
(`K:backend/xbrl/concept_extractor.py:114–265`); search/filter/ranking is separated
(`K:backend/search/query_engine.py:33–138`). Dimensional indexes and resolution
helpers are useful viewer services
(`K:backend/services/dimensional_relationships.py:130–482`). Hypercube traversal
does not establish full dimensional validity; typed dimensions return no explicit
member list (`K:backend/xbrl/hypercube_extractor.py:20–24,138–164,198–254`). Do not
treat that list as a typed-value editor or a validator.

**UI.** Preserve visual mapping and rendering
(`K:frontend/src/components/taxonomy/explorer/tree_utils.ts:60–169`,
`TaxonomyTreeView.tsx:190–255`). Network tabs include presentation and multiple
definition/custom relationships, without a dedicated calculation tab in the
reviewed tab definition (`XBRLTaxonomyExplorerContainer.tsx:22–44`). Tree filtering,
highlighting, context menus and filtered exports are concentrated in
`TaxonomyTreeView.tsx`. [The preservation checklist](architecture/cake-preservation.md)
defines the migration boundary; no browser visual baseline has yet been captured.

**Gaps.** This is not a report editor, iXBRL generator or filing lifecycle service.
Cached taxonomy JSON does not replace pinned complete packages. No active AI/MCP
provider integration was found in the reviewed active source. Documentation
includes help-mode and refactoring handovers, but those claims are not independent
test evidence. Root first-party licensing is unspecified. Frontend lockfile
metadata covers 486 dependency entries; see the licence inventory.

## 7. Soft/frontend assessment

**Purpose and stack.** Flask/Jinja rule-management and report-validation prototype,
not the React taxonomy viewer described in an earlier handoff. The supplied
materials README correctly describes it as soft validation/data quality.
`S:requirements.txt:1–2` declares Flask and Gunicorn but omits imported Arelle
(`S:backend/validation_rules/taxonomy/taxonomy_loader.py:6,34–58`). Application configuration fixes a 2026 FRS102
path (`S:backend/webapp/__init__.py:11–35`). Selected commit date: 2026-05-05.

**Rules and validation.** Candidate rules have severity, confidence and review
metadata (`S:backend/validation_rules/rule_generation/rule_schema.py:6–20`); generation is heuristic, not evidence of a
generative model (`S:backend/validation_rules/rule_generation/generator.py:443–691`). Draft/publish/archive
ideas are reusable, but publication copies files and updates DB state separately,
and validation of draft payloads is limited
(`S:backend/webapp/services/rule_admin_service.py:198–274,507–528`). Validation stores per-run snapshots
(`S:backend/webapp/services/validation_service.py:283–284,470` onwards). The new rule language needs bounded
semantics, immutable versions and reproducible evaluation.

**Parser limits.** Explicit dimensions only, simple units, narrow Inline XBRL fact
extraction, missing continuation/descendant/transformation handling
(`S:backend/validation_rules/testing/report_loader_core.py:26–87`); numeric operations use float
(`S:backend/validation_rules/testing/report_model.py:41–55`). Replace these with a canonical model and processor
adapter. Arelle-backed taxonomy loading does not establish full report validation.

**Operations/UI.** SQLite tables for runs/jobs/rules
(`S:backend/webapp/db.py:12–80`); daemon-thread jobs are not restart-safe
(`S:backend/webapp/services/job_service.py:88–96,181` onwards). Reviewed validation/admin routes do not show
the required per-project access checks (`S:backend/webapp/routes.py:58–100,165–244`). Responsive
CSS exists (`S:backend/webapp/static/styles.css:718` onwards); screen-reader and
keyboard behaviour remain untested. No conventional automated suite was found;
synthetic generators and batch outputs are behavioural evidence only. No active
LLM/MCP integration or local inference boundary was established. Root first-party
licensing is unspecified.

## 8. Cross-project capability comparison

| Capability | Charles | Cake | Soft | New application |
|---|---|---|---|---|
| General taxonomy exploration | Limited concept override | Strong reuse candidate | Loader for rule generation | Cake extraction with project isolation |
| PDF conversion/free source tagging | Not established | Not a report editor | Reads existing reports | New conversion, anchor and tagging services |
| Contexts/units/dimensions | Template-oriented | Viewer/index support | Narrow parser | Explicit canonical domain |
| iXBRL generation | Micro fixture workflow | Not established | Not established | New deterministic generator |
| Validation | Arelle subprocess + fixture/test-validator paths | Taxonomy exploration | Heuristic business rules | Layered structured validation |
| Approval/submission recovery | Not established | Not established | Not established | New audited lifecycle |
| Rules lifecycle | Limited | Not primary purpose | Useful workflow ideas | Bounded DSL and immutable packs |
| Local AI | Not established | Not established | Heuristic confidence only | Replaceable private inference |

Evidence is the cited source in sections 5–7. “Not established” means not proven
by static review, not an exhaustive mathematical proof of absence.

## 9. Recommended reuse

| Component | Classification | Reason |
|---|---|---|
| Cake icon meanings, labels and colour vocabulary | Reuse largely unchanged | Explicit product requirement; adapt contrast/prefix resolution without losing meaning (`tree_utils.ts:60–169`) |
| Cake search and relationship query helpers | Extract into shared taxonomy package | Useful separation exists; replace global selection/raw model coupling (`query_engine.py:33–138`, `state.py:6–13`) |
| Cake React explorer | Adapt with significant changes | Preserve PrimeReact initially; inject pinned query state, accessible tagging commands and theme tokens (`TaxonomyTreeView.tsx:190–255`) |
| Cake hypercube viewer | Adapt with significant changes | Useful exploration, incomplete typed/default/relationship validity authority (`hypercube_extractor.py:138–254`) |
| Cake Flask entry/state | Replace | New Django/session/project architecture; shared active taxonomy cannot survive (`backend/app.py:1–70`, `state.py:6–13`) |
| Charles template/generation flow | Retain as behavioural reference | Template assumptions must not constrain free tagging (`ixbrl_generator.py:134–268`) |
| Charles tests/fixtures | Adapt with significant changes | Replace unverified report content; convert intended behaviours into general domain regression tests (`test_tagger_microentity.py:187–505`) |
| Charles validation/auth/sanitiser | Replace | Text-classified processor errors, optional access and blacklist sanitisation are insufficient (`validation.py:705–765`, `security.py:12–73`) |
| Soft rule lifecycle and findings presentation | Retain as behavioural reference | Useful drafts/review/evidence UX; new bounded engine and atomic publish required (`rule_admin_service.py:198–274`) |
| Soft numeric/parser/job code | Replace | Float and partial parsing; daemon jobs lose durability (`report_model.py:41–55`, `report_loader_core.py:26–87`, `job_service.py:88–96`) |
| All databases/uploads/generated snapshots/dependencies | Do not reuse as public assets | Confidentiality, provenance, volume and deployment coupling |

## 10. Documentation inventory

| Supplied document | Authority/date/version | Requirement supported | Publication/outdatedness |
|---|---|---|---|
| `materials/README.md` | Internal, undated | Intake map | Derived summary safe; preserve original locally; spelling/path errors |
| `materials/repos/README.md` | Internal, undated | Reuse priorities | Claims such as validator success require independent reproduction |
| `Companies_House_TIS for accounts.odt` | Companies House; v6.0; cover 29 Sep 2026; published 25 Sep | Account categories, mandatory facts, entry points, rendering/profile constraints | Official source bytes matched; date discrepancy recorded; not legal eligibility advice |
| `Companies_House_TIS for filing_v5.3.odt` | Companies House; filename 5.3, cover 5.2/7 Apr 2022, change log 5.03/Jun 2024 | XML transport, envelopes, receipts | Official source bytes matched; conflicting version labels; pin schema separately |
| `FRC_Accounts_Taxonomies_Design_2026.pdf` | FRC, v13.0, 18 Nov 2025; 28 pages | Taxonomy architecture and dimensional use | Authoritative technical guidance; copyright review before redistribution |
| `FRC_Taoxnomies_Developer_Guide_2026.pdf` | FRC, v13.0, 18 Nov 2025; 61 pages | Package and processor integration | Remote byte identity unverified; read with release notes |
| `XBRL_Tagging_Guide_-_FRC_Taxonomies_2026.pdf` | FRC, v13.0, 18 Nov 2025; 76 pages | Tagging semantics and guidance | Same publication restriction; later taxonomy changes may supersede examples |
| `tagapp-materials/PLAN.md` | Internal accepted product/implementation plan | Scope, architecture, gates | Copied into public derived documentation; requirements are not verification evidence |

The five regulatory source documents remain unchanged and excluded from Git.
Names are preserved, including spelling differences. The FRC documents support
taxonomies generally, not automatic approval of every Companies House profile.
The selected repositories' plans/handovers/fixture READMEs are historical internal
design evidence, not regulatory sources; see sections 5–7. Generated private rule
snapshots and uploaded reports were not reclassified as documentation.

## 11. Verified facts

- Supplied bundle integrity, refs, selected commits and document checksums were
  checked locally; input verification is reproducible with `--local-materials`.
- Cake visual mappings are centralised at the required commit and paths.
- Charles/Soft do not provide a suitable general canonical fact model as reviewed.
- pdf2htmlEX and Arelle synthetic probes have separate machine-readable results;
  they do not demonstrate FRC/Companies House conformance.
- The user confirms an existing Companies House test account. No credentials were
  requested, read or stored, and no report was sent externally.

## 12. Assumptions requiring confirmation

Statutory eligibility and exceptions for each framework/entity/account category
need review before candidate profiles are enabled. First-party reuse is authorised
by the user, but third-party licences and bundled assets still need review.
The substantial synthetic fixture must represent agreed accounting semantics;
typed-dimension processor fixtures may use a separate synthetic extension when
the selected filing profile does not permit such constructs.

## 13. Contradictions or outdated material

Soft is a validation/rules MVP, not Cake's taxonomy viewer. Materials paths differ
from the handoff. Cake cached exports are not a complete offline taxonomy package.
Charles's test-validator success claims do not prove legal filing acceptance.
CH version/date labels conflict, generic auditor requirements need version-aware
reconciliation, and historical abbreviated accounts must not become current
default journeys. See [sources.json](compliance/sources.json).

## 14. Gaps

Complete taxonomy/schema/dependency closure; qualified converter build and font/
Unicode corpus; principal synthetic accounts and profile fixtures; statutory
eligibility matrix; full distribution licence review; independent processor access;
Cake visual baselines. Authentication, revisions, source anchors, general tagging,
generation, rules, local assistance, approval and filing are future implementation
milestones, not delivered functionality.

## 15. Recommended next steps

Complete [milestone 1](milestones/01-baseline.md) in its recorded order: acquire and
pin taxonomy/schema assets; resolve profile exceptions; generate positive/negative
fixtures; qualify conversion and independent-validation tooling; capture licence
obligations. Then build the application foundation, domain/revisions and Cake
extraction. Do not flatten the agreed staged gates into simultaneous scaffolding.

## 16. Questions for the user

Companies House test account availability is resolved: available. Independent
RaptorXML+XBRL access remains outstanding. The official FRC 2026 package has now been acquired and its three principal
entry points validated offline; see `qualification/taxonomy-result.json`. No credentials,
private client accounts or production-filing authority are needed for this intake.

## Subsequent local fixture intake — 28 September 2026

The user supplied `materials/inbox/illustrative accounts/fy26-illustrative-accounts-magnificent-cuisine-limited.pdf`
and selected it as the principal local PoC fixture. Grant Thornton's FY26 FRS 102
illustrative accounts are advisory examples with publisher guidance, not normative
filing rules. The report is dated for the year ending 31 December 2026 according to
[the publisher](https://www.grantthornton.co.uk/insights/annual-financial-reporting-illustrative-accounts/).
The local input is 29,855,944 bytes and 108 pages; it is unencrypted and has text
on every page, but lacks tagged-PDF structure. Its hash and publication boundary
are recorded in [the registry](qualification/fixture-registry.json).

This supports realistic conversion and later tagging development. It does not
supply expected XBRL facts, a qualified Companies House profile, or permission to
redistribute the original. No reuse-terms decision is needed for continuing the
user-authorised local proof of concept. The PDF, extracts, conversion outputs and
detailed diagnostics remain excluded from the public source tree; representative
public synthetic accounts will follow. The earlier synthetic fixture is retained
for arithmetic/conversion regressions. The user's material inventory note changed
to list this addition; its previous hash is preserved in the manifest.
