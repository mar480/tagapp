"""Run real-browser acceptance tests with disposable synthetic accounts and storage."""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]

def main():
    with tempfile.TemporaryDirectory(prefix='tagger-e2e-') as directory:
        os.environ.update(TAGGER_E2E_ROOT=directory, TAGGER_SECRET_KEY=secrets.token_urlsafe(48),
                          TAGGER_E2E_PASSWORD=secrets.token_urlsafe(24),
                          DJANGO_SETTINGS_MODULE='config.e2e_settings', TAGGER_TEST_PYTHON=sys.executable)
        sys.path.insert(0, str(ROOT / 'apps/api'))
        import django
        django.setup()
        from django.core.management import call_command
        from django.contrib.auth import get_user_model
        call_command('migrate', verbosity=0)
        for name in ('browser-owner', 'browser-viewer', 'browser-outsider'):
            get_user_model().objects.create_user(name, password=os.environ['TAGGER_E2E_PASSWORD'])
        return subprocess.run(['npm', 'run', 'test:e2e'], cwd=ROOT / 'apps/web').returncode

if __name__ == '__main__':
    raise SystemExit(main())
