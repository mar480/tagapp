# Step 2 — application foundation

Status: **in progress**, 30 September 2026. Foundation implementation is available
for local preview; service integration and deployment restore remain unverified.
No conversion/tagging/export/filing feature or production profile is enabled.

The [foundation decision](../decisions/0001-foundation-boundary.md) closes the
starting architecture and assigns unresolved baseline qualification to its owning
milestones. The historical partial gates and test evidence remain intact.

## Implemented

- Django/DRF API with individual accounts, CSRF-protected session login/logout,
  owner-managed project membership and scoped project/document/job/audit endpoints.
- Initial database migrations; PostgreSQL deployment configuration and an explicitly
  separate SQLite loopback preview. Admin provisions accounts; no public signup.
- Immutable PDF upload and authorised download through private filesystem storage,
  bounded uploads, SHA-256/size metadata and transactional audit records.
- Durable job intent, per-user operation deduplication, dispatcher retry, worker
  leases, cancellation, recovery limits and a byte-integrity worker. RabbitMQ
  publication sends only the job identifier. No validation success is implied.
- React/Vite project workspace, upload/download, team management, job status and
  cancellation, recent activity, responsive layout and per-user theme/text settings.
- Versioned OpenAPI schema and generated browser types. Pinned Python hashes,
  npm lockfile and official container image digests; dependency metadata inventory.
- Loopback TLS Compose definition with PostgreSQL, RabbitMQ, API, dispatcher,
  worker and Caddy; allow-listed Docker context excludes local materials.
- CI definition for PostgreSQL concurrency, real RabbitMQ worker delivery, API
  tests, migrations, contract drift, frontend build and browser acceptance.

## Verification evidence

| Check | Local result | Limit |
|---|---|---|
| Foundation API suite | 16 passed | SQLite; not PostgreSQL locking evidence |
| PostgreSQL concurrency and RabbitMQ transport | 2 explicitly skipped | Opt-in service tests and CI supplied; not executed here |
| Real Chromium browser workflow | Passed | One integrated scenario: login, create/reopen, upload/download, worker handler, cancellation, owner/viewer/outsider isolation, revocation, keyboard skip link, persistent dark/large preferences, 390px layout, logout |
| Worker in browser test | Real handler ran in separate Python invocation | Broker transport bypassed explicitly |
| Synthetic restore rehearsal | Passed | Disposable SQLite and blobs; project access/audit/jobs/checksums preserved; not encrypted PostgreSQL restore |
| Frontend build/types | Passed | Production deployment not exercised |
| Schema generation/migration consistency | Passed: schema validates and matches; no missing migrations | No deployment database migration applied |
| Baseline and publication | 80 tests passed; worktree/index guards clear; whitespace check passed | Bounded safeguards, not a full security audit |
| Qualification separation | Foundation readiness passes; full qualification fails for five retained partial gates | No filing profile has been promoted |

Reproducible commands and limits are in [the development guide](../development/foundation.md).
Private local logs are under `.local/foundation`; no report or credential is in
this completion record. CI has been defined, not run remotely or published.

## Remaining Step 2 acceptance work

1. Build/start the pinned Compose stack and resolve any actual platform issues.
2. Execute PostgreSQL concurrency and RabbitMQ delivery tests. Exercise restart and
   outage recovery against the real services; unit mocks do not replace those checks.
3. Rehearse PostgreSQL plus blob backup/restore in an independent deployment and
   verify project access and every source checksum. Follow the [restore runbook](../operations/foundation-restore.md).
4. Verify reverse-proxy/TLS behaviour, private volume permissions, health checks and
   worker egress restrictions in the running containers. Capture actual evidence.
5. Complete the foundation acceptance record before Step 3 domain/revision work.

## Known limits and later work

- Projects have no taxonomy/fact/revision model yet (Steps 3–4). Cake extraction and
  its visual parity gate remain unchanged. Source documents only; no conversion UI.
- Upload checks identify a PDF header, not PDF correctness. No uploaded script or
  document is executed. Detailed inspection/sandboxing belongs to Step 5.
- Project list supports pagination; the workspace currently shows the first 50
  documents/jobs and 12 recent audit events. Full browsing is still needed before
  substantial report workflows. There is no full audit review UI yet.
- The login throttle uses per-process memory. Shared rate limiting, MFA, security
  review, monitoring and production hardening remain open; no public deployment.
- File/database failure compensation is tested, but a host crash between blob write
  and database commit can leave an unreferenced private blob. Reconciliation and
  retention cleanup must be designed before operational release.
- UI control labels, keyboard flow and narrow layout have browser coverage; this
  is not a WCAG audit. Screen-reader/contrast/accessibility assurance remains open.
- Production filing, report approval and editing leases are not implemented.

No user review or credential disclosure is needed to continue foundation work.
Docker Engine/Compose availability is the next local infrastructure dependency;
PostgreSQL and RabbitMQ do not need separate host installation with that route.
