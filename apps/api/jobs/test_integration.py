"""Opt-in checks requiring a disposable PostgreSQL database and RabbitMQ vhost."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from unittest import skipUnless
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, connections
from django.test import TransactionTestCase, override_settings
from documents.services import store_document
from projects.services import create_project
from .models import Job
from .services import request_verification, dispatch_pending
from .tasks import verify_document

@skipUnless(os.environ.get('TAGGER_TEST_SERVICES') == '1', 'PostgreSQL/RabbitMQ integration not enabled')
class ServiceIntegrationTests(TransactionTestCase):
    def setUp(self):
        self.assertEqual(connection.vendor, 'postgresql', 'SQLite cannot qualify this integration gate')
        self.directory = tempfile.TemporaryDirectory(prefix='tagger-services-')
        self.addCleanup(self.directory.cleanup)
        settings = override_settings(BLOB_ROOT=Path(self.directory.name))
        settings.enable(); self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_user('service-test', password=secrets.token_urlsafe(24))
        self.project = create_project(self.user, 'Synthetic service check')
        self.document = store_document(self.user, self.project.pk, SimpleUploadedFile('synthetic.pdf', b'%PDF-1.7\n% test'))

    def test_concurrent_duplicate_commands_create_one_intent(self):
        barrier = threading.Barrier(2)
        operation = uuid.uuid4()
        def request():
            try:
                barrier.wait(timeout=10)
                return request_verification(self.user, self.document, operation)[0].pk
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: request(), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(Job.objects.count(), 1)

    def test_real_broker_delivers_to_a_separate_worker(self):
        queue = 'tagger-test-' + uuid.uuid4().hex
        env = dict(os.environ, DJANGO_SETTINGS_MODULE='config.test_settings',
                   POSTGRES_DB=connection.settings_dict['NAME'], TAGGER_BLOB_ROOT=self.directory.name)
        process = subprocess.Popen([sys.executable, '-m', 'celery', '-A', 'config', 'worker',
                                    '--pool=solo', '--concurrency=1', '--loglevel=WARNING',
                                    '--queues=' + queue, '--hostname=' + queue + '@%h'],
                                   cwd=Path(__file__).resolve().parents[1], env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        def cleanup():
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=5)
            from config.celery import app
            with app.connection_for_write() as broker:
                broker.default_channel.queue_delete(queue=queue)
        self.addCleanup(cleanup)
        job, _ = request_verification(self.user, self.document, uuid.uuid4())
        self.assertEqual(dispatch_pending(lambda value: verify_document.apply_async(args=[value], queue=queue)), 1)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            job.refresh_from_db()
            if job.state in (Job.State.SUCCEEDED, Job.State.FAILED):
                break
            if process.poll() is not None:
                self.fail('Separate Celery worker exited before completing the job')
            time.sleep(0.2)
        self.assertEqual(job.state, Job.State.SUCCEEDED)
        self.assertEqual(job.result['sha256'], self.document.sha256)
        self.assertEqual(job.attempts, 1)
