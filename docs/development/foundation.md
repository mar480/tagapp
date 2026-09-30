# Run the foundation locally

This is a private-project preview, not a tagging or filing release. Use Python
3.12 and Node 24. Dependency installations need administrative network access;
project processing does not call an external provider.

From the repository root:

```sh
python3.12 -m venv .local/foundation/venv
.local/foundation/venv/bin/python -m pip install --require-hashes -r apps/api/requirements.txt
npm --prefix apps/web ci --ignore-scripts
npm --prefix apps/web rebuild esbuild
```

For a loopback preview without PostgreSQL or RabbitMQ:

```sh
export DJANGO_SETTINGS_MODULE=config.dev_settings
export TAGGER_DEV_SQLITE=1
.local/foundation/venv/bin/python apps/api/manage.py migrate
.local/foundation/venv/bin/python apps/api/manage.py createsuperuser
.local/foundation/venv/bin/python apps/api/manage.py runserver 127.0.0.1:8000
```

In another terminal, run `npm --prefix apps/web run dev`, then open
<http://127.0.0.1:5173>. Use the account you just created. The administrator can
provision other users through <http://127.0.0.1:5173/admin/>. Do not publish these
development servers or use the SQLite setup for concurrent deployment.

Try creating a project, reopening it, uploading a local PDF and downloading the
same bytes. Add an existing account as viewer, sign in separately, then revoke
access. Appearance settings persist per user in that browser. PDFs remain under
ignored `.local/foundation/blobs`; the database and development secret also stay
in `.local/foundation`. No source report is included in the public code.

Without RabbitMQ and a worker, “Verify stored copy” deliberately remains queued;
“Cancel check” still works. There is no fake-success fallback. The automated browser
test invokes the worker handler directly and does not claim to exercise RabbitMQ.

## Automated checks

```sh
.local/foundation/venv/bin/python apps/api/manage.py test projects jobs --settings=config.test_settings
.local/foundation/venv/bin/python apps/api/manage.py makemigrations --check --dry-run --settings=config.test_settings
.local/foundation/venv/bin/python apps/api/manage.py spectacular --file /tmp/tagger-openapi.yaml --validate --fail-on-warn --settings=config.test_settings
diff -u docs/api/openapi.yaml /tmp/tagger-openapi.yaml
npm --prefix apps/web run types
npm --prefix apps/web run build
```

Browser tests create disposable accounts, database and blobs. Install the pinned
Playwright browser with `cd apps/web && npx playwright install chromium`, then run
from the repository root:

```sh
.local/foundation/venv/bin/python tools/foundation/browser_test.py
.local/foundation/venv/bin/python tools/foundation/restore_probe.py
```

`TAGGER_BROWSER_EXECUTABLE` can point to an existing compatible Chromium executable.
The browser runner owns and stops its loopback servers on ports 8011/4173; occupied
ports fail rather than reusing an unrelated application. Test artefacts are ignored.
The restore probe uses only temporary synthetic SQLite/blob state.

## Local container integration

Docker Engine and Compose v2 are sufficient; PostgreSQL and RabbitMQ executables
are supplied by their containers. The configuration has not yet been run on this
host. Image digests were resolved from the official Docker registry on 30 September
2026. This is an integration setup, not a production security sign-off.

```sh
python3 tools/foundation/create_environment.py
docker compose --env-file .local/foundation/compose.env up --build -d
docker compose --env-file .local/foundation/compose.env exec api python manage.py createsuperuser
```

Open <https://localhost:8443>. Caddy creates a local CA; configure trust for that CA
in your development browser after checking its provenance. Database and broker have
no host ports. Never expose the API directly: production settings trust the reverse
proxy's forwarded HTTPS header. No production credentials are needed here.

The migration service runs before API/workers; database and broker health checks
control startup. See [Docker's startup-order documentation](https://docs.docker.com/compose/how-tos/startup-order/).
The internal network blocks general runtime internet access. Builds acquire pinned
dependencies separately. TLS, encrypted host volumes, backups, MFA, shared login
rate limiting and operator procedures still need deployment qualification.

To run PostgreSQL/RabbitMQ checks inside the isolated development stack:

```sh
docker compose --env-file .local/foundation/compose.env run --rm -e TAGGER_TEST_POSTGRES=1 -e TAGGER_TEST_SERVICES=1 api python manage.py test projects jobs --settings=config.test_settings
```

Only run these opt-in tests against disposable development services. They create a
Django test database and a unique RabbitMQ test queue; worker transport is real.
The CI workflow also defines these checks, but a workflow definition is not a passing
CI run. Follow the [backup/restore procedure](../operations/foundation-restore.md)
before declaring Step 2 complete. Use `docker compose ... stop` to stop services;
do not delete volumes containing projects.
