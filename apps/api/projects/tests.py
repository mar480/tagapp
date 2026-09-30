from datetime import timedelta
import hashlib
import io
import os
from pathlib import Path
import secrets
import tempfile
import uuid
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from documents.models import Document
from documents.storage import FileSystemBlobStore
from jobs.models import Job
from jobs.services import claim, dispatch_pending, execute_verification, finish
from .models import Project, Membership, AuditEvent

PDF = b"%PDF-1.7\n% Synthetic intake-only test bytes; not a conversion fixture.\n"

class FoundationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = secrets.token_urlsafe(24)
        User = get_user_model()
        cls.owner = User.objects.create_user("owner", password=cls.password)
        cls.other = User.objects.create_user("other", password=cls.password)
        cls.viewer = User.objects.create_user("viewer", password=cls.password)

    def setUp(self):
        cache.clear()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(BLOB_ROOT=Path(self.directory.name))
        self.settings_override.enable(); self.addCleanup(self.settings_override.disable)
        self.client = APIClient(enforce_csrf_checks=True)
        self.login(self.owner)
        response = self.client.post("/api/v1/projects/", {"name": "Synthetic accounts"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.project = Project.objects.get(pk=response.data["id"])
        self.url = f"/api/v1/projects/{self.project.pk}/"

    def login(self, user):
        csrf = self.client.get("/api/v1/auth/session/").data["csrf_token"]
        self.client.credentials(HTTP_X_CSRFTOKEN=csrf)
        response = self.client.post("/api/v1/auth/login/", {"username": user.username, "password": self.password}, format="json")
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_X_CSRFTOKEN=response.data["csrf_token"])

    def upload(self, content=PDF):
        return self.client.post(self.url + "documents/", {"file": SimpleUploadedFile("report.pdf", content, "application/pdf")}, format="multipart")

    def document(self):
        response = self.upload(); self.assertEqual(response.status_code, 201)
        return Document.objects.get(pk=response.data["id"])

    def queue(self, document=None, operation=None):
        document = document or self.document()
        response = self.client.post(self.url + f"documents/{document.pk}/verify/",
                                    {"operation_id": str(operation or uuid.uuid4())}, format="json")
        self.assertIn(response.status_code, (200, 201))
        return Job.objects.get(pk=response.data["id"])

    def test_anonymous_access_and_login_csrf_are_enforced(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.get("/api/v1/projects/").status_code, 403)
        self.assertEqual(client.post("/api/v1/auth/login/", {"username": "owner", "password": self.password}).status_code, 403)
        self.client.credentials()
        self.assertEqual(self.client.post("/api/v1/projects/", {"name": "No CSRF"}).status_code, 403)

    def test_logout_ends_session_and_project_reopens_after_login(self):
        self.assertEqual(self.client.post("/api/v1/auth/logout/").status_code, 200)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.login(self.owner)
        self.assertEqual(self.client.get(self.url).data["name"], self.project.name)

    def test_outsider_cannot_enumerate_project_documents_jobs_or_events(self):
        document = self.document(); job = self.queue(document)
        self.login(self.other)
        self.assertEqual(self.client.get("/api/v1/projects/").data["count"], 0)
        for suffix in ("", "documents/", f"documents/{document.pk}/download/", "jobs/", f"jobs/{job.pk}/", "members/", "audit/"):
            with self.subTest(suffix=suffix):
                self.assertEqual(self.client.get(self.url + suffix).status_code, 404)

    def test_project_owner_is_server_assigned(self):
        response = self.client.post("/api/v1/projects/", {"name": "Owned", "owner": str(self.other.pk), "role": "viewer"}, format="json")
        self.assertEqual(Project.objects.get(pk=response.data["id"]).owner, self.owner)

    def test_viewer_cannot_upload_queue_or_grant_permissions(self):
        document = self.document()
        Membership.objects.create(project=self.project, user=self.viewer, role="viewer")
        self.login(self.viewer)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.upload().status_code, 403)
        self.assertEqual(self.client.post(self.url + f"documents/{document.pk}/verify/", {"operation_id": str(uuid.uuid4())}, format="json").status_code, 403)
        self.assertEqual(self.client.post(self.url + "members/", {"username": "other", "role": "editor"}, format="json").status_code, 403)

    def test_owner_can_grant_and_revoke_access_with_audit(self):
        response = self.client.post(self.url + "members/", {"username": "other", "role": "editor"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.login(self.other); self.assertEqual(self.upload().status_code, 201)
        self.login(self.owner)
        self.assertEqual(self.client.delete(self.url + f"members/{self.other.pk}/").status_code, 204)
        self.login(self.other); self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertTrue(AuditEvent.objects.filter(project=self.project, operation="membership.removed").exists())

    def test_immutable_upload_download_preserves_bytes_and_hides_storage_key(self):
        document = self.document()
        response = self.client.get(self.url + "documents/")
        self.assertNotIn("blob_key", response.data["results"][0])
        self.assertEqual(document.sha256, hashlib.sha256(PDF).hexdigest())
        download = self.client.get(self.url + f"documents/{document.pk}/download/")
        self.assertEqual(b"".join(download.streaming_content), PDF)
        self.assertIn("attachment", download["Content-Disposition"])
        self.assertEqual(download["Cache-Control"], "no-store")
        self.assertEqual(download["X-Content-Type-Options"], "nosniff")
        self.assertEqual(self.client.patch(self.url + "documents/", {}, format="json").status_code, 405)
        self.assertEqual(os.stat(Path(self.directory.name) / document.blob_key).st_mode & 0o777, 0o600)

    def test_invalid_or_oversized_upload_leaves_no_document(self):
        self.assertEqual(self.upload(b"<script>not PDF</script>").status_code, 400)
        with override_settings(MAX_DOCUMENT_BYTES=10): self.assertEqual(self.upload().status_code, 400)
        self.assertEqual(Document.objects.count(), 0)
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])

    def test_database_failure_rolls_back_document_and_removes_blob(self):
        with patch("documents.services.audit", side_effect=RuntimeError("synthetic failure")):
            with self.assertRaises(RuntimeError): self.upload()
        self.assertEqual(Document.objects.count(), 0)
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])

    def test_storage_rejects_traversal_symlinks_and_collision_deletion(self):
        store = FileSystemBlobStore()
        with self.assertRaises(ValueError): store.open("../../secret")
        stored = store.put(io.BytesIO(PDF))
        with patch("documents.storage.uuid.uuid4", return_value=uuid.UUID(stored.key)):
            with self.assertRaises(FileExistsError): store.put(io.BytesIO(b"overwrite"))
        with store.open(stored.key) as stream: self.assertEqual(stream.read(), PDF)
        link = uuid.uuid4().hex
        (Path(self.directory.name) / link).symlink_to(Path(self.directory.name) / stored.key)
        with self.assertRaises(OSError): store.open(link)

    def test_job_intent_deduplicates_and_rejects_conflicting_operation(self):
        document = self.document(); operation = uuid.uuid4()
        self.assertEqual(self.queue(document, operation).pk, self.queue(document, operation).pk)
        other = self.document()
        response = self.client.post(self.url + f"documents/{other.pk}/verify/", {"operation_id": str(operation)}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_broker_outage_keeps_intent_and_duplicate_delivery_is_safe(self):
        job = self.queue()
        def unavailable(_): raise OSError("broker unavailable")
        self.assertEqual(dispatch_pending(unavailable), 0)
        job.refresh_from_db(); self.assertEqual(job.state, "queued")
        Job.objects.filter(pk=job.pk).update(last_enqueued_at=timezone.now() - timedelta(minutes=1))
        messages = []; self.assertEqual(dispatch_pending(messages.append), 1)
        self.assertEqual(messages, [str(job.pk)])
        execute_verification(job.pk); execute_verification(job.pk)
        job.refresh_from_db(); self.assertEqual(job.state, "succeeded")
        self.assertEqual(job.attempts, 1)
        self.assertEqual(AuditEvent.objects.filter(project=self.project, operation="job.succeeded").count(), 1)

    def test_expired_worker_lease_recovers_and_stale_worker_cannot_finish(self):
        job = self.queue(); old = claim(job.pk)
        self.assertIsNone(claim(job.pk))
        Job.objects.filter(pk=job.pk).update(lease_until=timezone.now() - timedelta(seconds=1))
        self.assertEqual(dispatch_pending(lambda _: None), 1)
        new = claim(job.pk)
        self.assertNotEqual(old.lease_token, new.lease_token)
        self.assertFalse(finish(job.pk, old.lease_token, Job.State.SUCCEEDED))
        self.assertTrue(finish(job.pk, new.lease_token, Job.State.SUCCEEDED))

    def test_cancelled_or_revoked_jobs_do_not_run(self):
        job = self.queue()
        self.assertEqual(self.client.post(self.url + f"jobs/{job.pk}/cancel/").status_code, 200)
        execute_verification(job.pk)
        job.refresh_from_db(); self.assertEqual(job.state, "cancelled")
        Membership.objects.create(project=self.project, user=self.other, role="editor")
        document = self.document(); self.login(self.other); revoked = self.queue(document)
        Membership.objects.filter(project=self.project, user=self.other).delete()
        execute_verification(revoked.pk)
        revoked.refresh_from_db(); self.assertEqual(revoked.state, "cancelled")

    def test_integrity_failure_is_explicit_and_contains_no_report_content(self):
        job = self.queue()
        (Path(self.directory.name) / job.document.blob_key).write_bytes(b"modified")
        execute_verification(job.pk)
        job.refresh_from_db(); self.assertEqual(job.state, "failed")
        self.assertEqual(job.error_code, "source_integrity_failed")
        self.assertEqual(job.result, {})

    def test_recovery_attempts_are_bounded(self):
        job = self.queue(); Job.objects.filter(pk=job.pk).update(attempts=3)
        self.assertIsNone(claim(job.pk))
        job.refresh_from_db(); self.assertEqual(job.error_code, "worker_recovery_limit")
