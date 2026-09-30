# Foundation boundary and qualification ownership

Accepted scope: the user authorised closing foundational decisions and assigning
later qualification to its implementation milestone before starting Step 2.
Recorded 30 September 2026. This supersedes the former requirement to complete
B1–B5 before any application development. It does not qualify a filing profile.

## Decisions now fixed

- Private, single-organisation deployment with administrator-provisioned individual
  accounts. No public registration. Session authentication and CSRF protection.
- Project owner controls membership. Editors can upload and request document jobs;
  viewers, reviewers and filers currently have read access. Review/filing powers
  will be implemented in their own milestones, never inferred from role names.
- Django/DRF owns invariants and permissions on every endpoint. React uses generated
  types from a versioned OpenAPI contract. UI preferences affect the workspace only.
- PostgreSQL is the deployment database. SQLite is explicitly for disposable tests
  and loopback previews, not evidence of PostgreSQL locking or production readiness.
- Immutable source PDFs live behind a blob-store interface, outside public static
  paths. Downloads require project access. PDF signature checking at upload is an
  intake filter; isolated conversion and substantive PDF inspection belong to Step 5.
- PostgreSQL job records are authoritative. RabbitMQ carries identifiers; a dispatcher
  retries publication. Lease tokens fence stale completions, requests are deduplicated
  per user/operation, and cancellation is persisted. The initial worker verifies bytes,
  not financial correctness. Processing workers remain replaceable.
- Arelle remains behind an adapter. No second processor is required. Cake's pinned
  tree behaviour remains the Step 4 preservation contract.
- The GT illustrative accounts remain an ignored local proof-of-concept fixture.
  Reviewed synthetic fixtures and dependency redistribution review precede publication.

## Remaining work, with explicit owners

“Owner” below is the delivery milestone responsible for implementation and evidence.
No requirement has been waived or marked passed by reassignment.

| Baseline work | Owning milestone | Blocking condition retained |
|---|---|---|
| B1 exact company/LLP profile applicability | 7 validation; 13 CH test filing | No profile qualification or production enablement without reviewed eligibility and positive/negative evidence |
| B2 materialised profile examples | 4 taxonomy; 5 conversion; 6 tagging; 7 validation; 8 export; 13 transport | Relevant acceptance cases must exist and pass before the associated milestone closes |
| B3 taxonomy dependency closure/provenance | 4 taxonomy | Complete pinned packages must load without runtime network access |
| B3 transformations and later Inline errata | 7 validation; 8 export | Processor limitations and transformation selection must be resolved or explicitly handled before export qualification |
| B3 gateway prose/schema conflict | 13 CH test filing | Confirm actual transport behaviour with CH before production transport is enabled |
| B4 visual review, ActualText repairs, corpus and selection | 5 conversion; 6 tagging | No accepted conversion with unexplained text changes; repair and anchor review remain mandatory |
| B5 exact notices and redistribution terms | 14 release assurance, and before any earlier distribution of affected artefacts | No public report, converter binary, taxonomy or bundled dependency distribution without applicable review |

The evidence already recorded establishes enough feasibility to implement the
foundation. `01-status.json` retains partial qualification gates; its separate
`foundation_readiness` records permission to start Step 2. `--require-qualified`
continues to fail for unresolved qualification. `--require-foundation-ready`
checks the decision, passed intake/publication boundaries and complete reassignment.

## Foundation acceptance remains distinct

Local API/browser tests can establish behaviour, but cannot establish PostgreSQL
concurrency, RabbitMQ delivery, container isolation or a successful deployment
restore. Step 2 remains in progress until those checks have real evidence. The
foundation does not implement conversion, tagging, validation, approval or filing.
