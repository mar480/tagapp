# Foundation backup and restore qualification

Status: procedure supplied; PostgreSQL/container execution pending. A disposable
SQLite rehearsal checks logical associations and exact blob bytes only. It is not
evidence for PostgreSQL recovery, encryption, retention or disaster recovery.

The database references immutable blobs. A database-only backup is incomplete.
Preserve the private environment/keys separately with restricted access; backups
must be encrypted on storage and transport. Never add any of these files to Git.

## Consistent development snapshot

Use an encrypted local destination with mode 700. Stop all writers before copying
both database and blobs. Keep the API, dispatcher and worker stopped until both
copies and their checksums have completed. These commands assume the local Compose
stack and produce restricted backup files under the ignored `backups` directory.

```sh
umask 077
mkdir -p backups/foundation
docker compose --env-file .local/foundation/compose.env stop web dispatcher worker api
docker compose --env-file .local/foundation/compose.env exec -T db pg_dump -U tagger -d tagger --format=custom > backups/foundation/database.dump
docker compose --env-file .local/foundation/compose.env run --rm --no-deps -T api tar -C /data/blobs -cf - . > backups/foundation/blobs.tar
sha256sum backups/foundation/database.dump backups/foundation/blobs.tar > backups/foundation/SHA256SUMS
docker compose --env-file .local/foundation/compose.env start api worker dispatcher web
```

Do not overwrite a previous snapshot; select a fresh directory for each real backup.
Stop and investigate any failed command before restarting writers or treating a
snapshot as valid. `umask` restricts permissions but does not provide encryption.
Use the organisation's encrypted backup destination and key-management procedure.
A broker backup is not authoritative: durable job intent resides in PostgreSQL.

## Restore rehearsal

Restore only into a **new** isolated Compose project with empty volumes and an
independent private environment file. Keep its web/API/workers stopped, and avoid
port collisions with the original deployment. Verify backup checksums first.

1. Start only the new project's database with `docker compose -p tagger-restore
   --env-file <private-restore-env> up -d db` and wait for database readiness.
2. Restore with `docker compose -p tagger-restore --env-file <private-restore-env>
   exec -T db pg_restore -U tagger -d tagger --exit-on-error --single-transaction
   --no-owner < backups/foundation/database.dump`. The target must be empty.
3. Restore blobs with `docker compose -p tagger-restore --env-file
   <private-restore-env> run --rm --no-deps -T api tar --no-same-owner
   -C /data/blobs -xf - < backups/foundation/blobs.tar`. Use only trusted backups.
4. Start migration and application services. Confirm schema version, account login,
   owner/viewer isolation, audit events, queued-job recovery, and original downloads.
   Recompute every restored blob's size and SHA-256 against its Document row; any
   missing or changed blob fails the rehearsal. Check owner-only storage permissions.
5. Record source versions, snapshot hashes, restore timings and acceptance results
   without including reports, keys or credentials. Keep the original deployment
   and backup intact until the rehearsal is accepted.

The custom-format dump requires `pg_restore`; database roles and external files
need separate treatment. Source: [PostgreSQL 17 backup documentation](https://www.postgresql.org/docs/17/backup-dump.html).

Before production: automate encrypted backup rotation and integrity checks, rehearse
restoration on another host, set retention/deletion and recovery objectives, test
key loss and capacity failures, and provide an operator runbook. No production
filing may rely on this unqualified development procedure.
