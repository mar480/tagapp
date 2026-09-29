# Publication boundary

The Tagger repository is public. Supplied materials and historical repositories
are local reference inputs, not distributable source by default.

`.gitignore` excludes `materials/`, `tagapp-materials/`, root bare mirrors,
bundles, private `.local/` tools/evidence, runtime storage, common credentials,
databases, models and dependency directories. It does not remove already tracked
files and does not prevent `git add -f`.

Run the publication guard against the worktree before staging and against the
index before committing. It checks index object bytes rather than trusting the
working copy, rejects symlinks/gitlinks, blocks known private paths, and reports
only filenames and risk categories. Unreviewed binary and oversized files fail
closed. To introduce public binary fixtures later, add a narrowly scoped,
checksum-based review mechanism; do not broadly allow PDFs or archives.

This guard catches selected token formats and private-key markers. It does not
prove absence of credentials, personal data, confidential prose, encoded secrets
or licence restrictions. An independent historical scan remains required before
any old repository is republished. CI runs after upload, so it cannot prevent
initial disclosure to a remote host. Local review remains necessary.

## Intake findings

| Input | Risk | Containment |
|---|---|---|
| Soft | Uploaded accounts, generated reports, SQLite databases/journals, historical test databases | Keep complete bundle/mirror local. Use newly generated synthetic fixtures. Do not migrate storage contents. |
| Charles | Tracked dependencies, compiled files and account fixtures with unverified provenance | Extract reviewed first-party source only; replace fixture content. |
| Cake | Archived Supabase client contains a JWT identifying an anonymous/public role | Exclude the obsolete integration. Review live service permissions if still deployed; rotate/revoke if exposure exceeds intended access. No privileged credential was established by the role alone. |
| Soft | Hard-coded development Flask session secret | Replace with deployment-managed credentials; do not port configuration. |
| FRC PDFs/packages | Publicly accessible copyrighted materials | Keep originals local until redistribution rights are established. |

The Cake finding is at `cake@9251b790:archive/pr-d-2026-04-07/dead-code/frontend/src/integrations/supabase/client.ts:7`,
blob `b7d93bf4d9b04a3a763f58237cf91bcf1eb8413a`.
The Soft finding is at `soft@6693b812:backend/webapp/__init__.py:15`.
No suspected value is included here.

Historical intake scanning covered reachable refs, using local pattern matching;
large and binary blobs were not comprehensively inspected. Report/DB contents were
not semantically reviewed. This is a finding register, **not a clean security bill**.

## Future runtime boundary

Unpublished reports stay within the controlled deployment. Conversion, Arelle and
AI workers must deny general outbound traffic and render documents without scripts
or uncontrolled external assets. Acquisition of software, models and taxonomy
packages is a separate administrative operation. Only an explicit authorised
Companies House validation/submission action may send report contents out.

Operational logs contain IDs and error codes, not report text, credentials or full
processor messages. Restricted evidence can contain report material and belongs in
private project storage. Volume encryption, key management, backups and deletion
semantics remain deployment acceptance requirements; `.gitignore` implements none
of these runtime controls.
