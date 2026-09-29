# Cake preservation contract

Baseline: `cake/vps` commit `9251b790faa65b78d80dbe4528fcdd3aefef1238`.
The source is available in the local bare mirror `cake.git`; it is not copied into
the public application at this milestone. A citation such as `path:60–169` refers
to the lines returned by `git --git-dir=cake.git show <commit>:<path>`.

## Behavioural acceptance checklist

All rows are **pending migration and verification**. Static inspection establishes
the behaviours to preserve; it does not establish browser accessibility or a
visual regression baseline.

| ID | Behaviour to preserve | Evidence / future acceptance |
|---|---|---|
| CAKE-01 | Nesting, relationship order, expansion/collapse and repeated occurrences | `frontend/src/components/taxonomy/explorer/tree_utils.ts:173` onwards; compare path identities/order, not only concept sets |
| CAKE-02 | Primary, secondary and tertiary concept icons | `tree_utils.ts:60–169`; exercise every mapping and precedence case |
| CAKE-03 | Colour meaning, selected state and search highlighting | `TaxonomyTreeView.tsx:190–255`; light/dark/high-contrast visual review with text labels |
| CAKE-04 | Presentation and definition-network tabs | `XBRLTaxonomyExplorerContainer.tsx:22–44`; hypercube-dimension, dimension-domain, defaults, domain-member and all networks |
| CAKE-05 | Search/filter, automatic expansion, occurrence navigation | `TaxonomyTreeView.tsx` and search utilities; repeated concept at different paths remains navigable |
| CAKE-06 | Labels, references, concept properties and dimensions/members | `backend/xbrl/concept_extractor.py:114–265`; compare structured outputs |
| CAKE-07 | Hypercube exploration | `backend/xbrl/hypercube_extractor.py:20–24,138–164,198–254`; preserve viewer while qualifying dimensional validity separately |
| CAKE-08 | Contextual help and deep links | `TaxonomyTreeView.tsx`; copy/open links retains selected package, entry point, network and occurrence |
| CAKE-09 | Filtered-tree JSON, CSV, HTML and PNG exports | `TaxonomyTreeView.tsx`; retain filter/order/labels, accessible export controls |
| CAKE-10 | Panel resizing and modern responsive use | Desktop three-panel workspace; smaller screens use accessible panel switching without losing selections |
| CAKE-11 | Equivalent keyboard and click-only tagging | New functionality; tree interaction must coexist with screen-reader/keyboard navigation and never require dragging |
| CAKE-12 | Project-specific taxonomy state | Parallel requests for two pinned taxonomies yield independent trees; no global active taxonomy |

Paths abbreviated in this table are relative to
`frontend/src/components/taxonomy/explorer/` unless otherwise specified.

## Visual vocabulary

Preserve meanings and glyphs; contrast-safe theme tokens may alter colour values
with explicit review. Baseline values below come from `tree_utils.ts:71–169`.

| Meaning | Icon | Baseline colour |
|---|---|---|
| Guidance | Warning triangle | `#ef4444` |
| Heading / ELR group | Folder | `#1f2937` / `#334155` |
| Cross-reference | Opposing arrows | `#f87171` |
| Domain member | Globe / bars for Q2 domain type | `#ec4899` |
| Energy / mass / percent | Sun / gauge / percentage | `#f97316` / `#22c55e` / `#14b8a6` |
| Fixed item | Align-left plus red star | `#06b6d4`, `#ef4444` |
| Grouping item | Base type plus blue star | `#3b82f6` secondary |
| Syndicate number / non-negative decimal | Hash / numeric sort | `#22c55e` / `#ef4444` |
| GHG emissions | Gauge | `#22c55e` |
| URI / Boolean / date | Link / check-square / calendar-clock | `#60a5fa` / `#22c55e` / `#d946ef` |
| Decimal / monetary / shares / string | Numeric sort / pound / chart-line / align-left | `#737373` / `#f59e0b` / `#a855f7` / `#06b6d4` |
| Country | Globe | `#22c55e` |
| Dimension / hypercube | Sort-amount / table | `#6366f1` / `#fb7185` |
| Unknown concept | Home | `#6b7280` |

ELR groups and countries take precedence; then dimension/hypercube, specific type,
base type and fallback. Dimension and domain types may carry a tertiary type icon.
Do not copy the prefix-dependent type checks into the domain layer: resolve
expanded QNames at the adapter boundary while retaining equivalent presentation.
The existing country class and explicit colour are not identical; capture actual
rendering before deciding which token reproduces it.

## Extraction boundary

`TaxonomyExplorer` accepts a pinned selection, relationship-network data, occurrence
IDs, selection and search state, and emits navigation/apply-concept commands.
PrimeReact is an implementation detail. The host application owns project state,
permissions, fact commands, preferences and source selection. No tree component
owns active server taxonomy state or Arelle model objects.

Taxonomy labels/references are untrusted display content. Package identity includes
checksum, entry point and dependency closure. Viewer relationships do not prove
dimensional validity: target roles, defaults, typed domains, closed cubes, `notAll`
and prohibited arcs require qualified processor behaviour.

## Visual baseline capture procedure

Before migration, create a reviewed static Cake build in isolated local tooling,
using only approved synthetic/cached taxonomy data. Capture desktop and narrow
viewports at fixed fonts/browser/device scale; store package/commit/browser hashes
with screenshots. Include each icon, a deeply nested tree, repeated concepts,
filter results, expanded dimensions, help and each export dialog. Compare migrated
screens and interaction traces against these. Have the product owner review
intentional differences, particularly dark-mode contrast.

**No screenshots or browser parity tests have been captured yet.** Do not mark
CAKE-01–12 complete on the strength of this checklist.
