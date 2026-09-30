"""Synthetic SQLite/blob restore rehearsal. Does not qualify PostgreSQL recovery."""
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SEED = '''
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from projects.services import create_project, set_member
from documents.services import store_document
from jobs.services import request_verification, execute_verification
import uuid
user = get_user_model().objects.create_user('restore-owner')
viewer = get_user_model().objects.create_user('restore-viewer')
project = create_project(user, 'Synthetic restore rehearsal')
set_member(project, user, viewer, 'viewer')
document = store_document(user, project.pk, SimpleUploadedFile('synthetic.pdf', b'%PDF-1.7\\n% restore'))
job, _ = request_verification(user, document, uuid.uuid4())
execute_verification(job.pk)
'''
VERIFY = '''
from django.contrib.auth import get_user_model
from documents.models import Document
from documents.storage import blob_store
from projects.access import visible_projects
from projects.models import Project, AuditEvent
from jobs.models import Job
import hashlib
assert Project.objects.count() == 1
assert visible_projects(get_user_model().objects.get(username='restore-viewer')).count() == 1
assert AuditEvent.objects.count() >= 4
assert Job.objects.get().state == 'succeeded'
doc = Document.objects.get()
with blob_store().open(doc.blob_key) as stream:
    data = stream.read()
assert hashlib.sha256(data).hexdigest() == doc.sha256
assert len(data) == doc.size_bytes
assert data == b'%PDF-1.7\\n% restore'
'''

def main():
    with tempfile.TemporaryDirectory(prefix='tagger-restore-') as temporary:
        base = Path(temporary)
        source = base / 'source'; source.mkdir(mode=0o700)
        env = dict(os.environ, TAGGER_E2E_ROOT=str(source), TAGGER_SECRET_KEY=secrets.token_urlsafe(48),
                   DJANGO_SETTINGS_MODULE='config.e2e_settings')
        def run(*args):
            subprocess.run([sys.executable, str(ROOT / 'apps/api/manage.py'), *args], env=env,
                           check=True, stdout=subprocess.DEVNULL)
        run('migrate', '--noinput'); run('shell', '-c', SEED)
        # All writers have exited. Snapshot only disposable synthetic state.
        snapshot = base / 'snapshot'; shutil.copytree(source, snapshot)
        source.rename(base / 'unavailable-original')
        restored = base / 'restored'; shutil.copytree(snapshot, restored)
        env['TAGGER_E2E_ROOT'] = str(restored)
        run('shell', '-c', VERIFY)
        if any(p.stat().st_mode & 0o077 for p in (restored / 'blobs').iterdir()):
            raise RuntimeError('Restored blobs are not private')
        print('PASS: synthetic SQLite restore preserves project access, audit, jobs and exact source bytes.')
        print('PostgreSQL dump/restore and encrypted backup operations remain unverified.')

if __name__ == '__main__':
    main()
