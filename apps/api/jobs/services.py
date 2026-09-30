"""Durable job intent, duplicate delivery protection and lease recovery."""
from datetime import timedelta
import hashlib
import uuid
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException
from projects.access import accessible_project, role_for
from projects.services import audit
from documents.storage import blob_store
from .models import Job

class Conflict(APIException):
    status_code = 409
    default_detail = "This operation conflicts with existing state."

@transaction.atomic
def request_verification(actor, document, operation_id):
    # Serialize this user's idempotency namespace, including requests for different projects.
    get_user_model().objects.select_for_update().get(pk=actor.pk)
    accessible_project(actor, document.project_id, edit=True)
    existing = Job.objects.filter(requested_by=actor, operation_id=operation_id).first()
    if existing:
        if existing.document_id != document.pk or existing.kind != "verify_document":
            raise Conflict("Operation identifier was already used for a different request.")
        return existing, False
    job = Job.objects.create(project=document.project, document=document, requested_by=actor, operation_id=operation_id)
    audit(document.project, actor, "job.queued", job_id=str(job.pk), kind=job.kind)
    return job, True

@transaction.atomic
def cancel_job(actor, job_id):
    job = Job.objects.select_for_update().select_related("project").get(pk=job_id)
    accessible_project(actor, job.project_id, edit=True)
    if job.state == Job.State.CANCELLED:
        return job
    if job.state not in (Job.State.QUEUED, Job.State.RUNNING):
        raise Conflict("This job has already finished.")
    job.cancel_requested = True
    if job.state == Job.State.QUEUED:
        job.state = Job.State.CANCELLED
        job.finished_at = timezone.now()
    job.save()
    audit(job.project, actor, "job.cancellation_requested", job_id=str(job.pk))
    return job

@transaction.atomic
def claim(job_id):
    job = Job.objects.select_for_update().select_related("project", "document", "requested_by").filter(pk=job_id).first()
    if job is None or job.state not in (Job.State.QUEUED, Job.State.RUNNING):
        return None
    now = timezone.now()
    if job.state == Job.State.RUNNING and job.lease_until and job.lease_until > now:
        return None
    if job.cancel_requested or role_for(job.project, job.requested_by) not in ("owner", "editor"):
        job.state = Job.State.CANCELLED
        job.finished_at = now
        job.save()
        audit(job.project, job.requested_by, "job.cancelled", job_id=str(job.pk))
        return None
    if job.attempts >= 3:
        job.state = Job.State.FAILED
        job.error_code = "worker_recovery_limit"
        job.finished_at = now
        job.save()
        audit(job.project, job.requested_by, "job.failed", job_id=str(job.pk), code=job.error_code)
        return None
    job.state = Job.State.RUNNING
    job.attempts += 1
    job.progress = 0
    job.lease_token = uuid.uuid4()
    job.lease_until = now + timedelta(seconds=120)
    job.save()
    return job

@transaction.atomic
def finish(job_id, token, state, *, result=None, error_code=""):
    job = Job.objects.select_for_update().select_related("project", "requested_by").get(pk=job_id)
    if job.state != Job.State.RUNNING or job.lease_token != token:
        return False
    job.state = Job.State.CANCELLED if job.cancel_requested else state
    job.result = result or {} if job.state == Job.State.SUCCEEDED else {}
    job.error_code = error_code if job.state == Job.State.FAILED else ""
    job.progress = 100 if job.state == Job.State.SUCCEEDED else job.progress
    job.finished_at = timezone.now()
    job.lease_token = None; job.lease_until = None
    job.save()
    audit(job.project, job.requested_by, "job." + job.state, job_id=str(job.pk), code=job.error_code)
    return True

def execute_verification(job_id):
    job = claim(job_id)
    if job is None:
        return
    try:
        if job.kind != "verify_document":
            raise ValueError("Unsupported job type")
        digest = hashlib.sha256(); size = 0
        with blob_store().open(job.document.blob_key) as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk); size += len(chunk)
                if Job.objects.filter(pk=job.pk, cancel_requested=True).exists():
                    finish(job.pk, job.lease_token, Job.State.CANCELLED)
                    return
                if size > job.document.size_bytes:
                    raise ValueError("Stored size differs")
                Job.objects.filter(pk=job.pk, lease_token=job.lease_token, state=Job.State.RUNNING).update(
                    progress=min(99, size * 100 // max(1, job.document.size_bytes)))
        if digest.hexdigest() != job.document.sha256 or size != job.document.size_bytes:
            raise ValueError("Stored checksum differs")
        finish(job.pk, job.lease_token, Job.State.SUCCEEDED,
               result={"document_id": str(job.document_id), "sha256": digest.hexdigest(), "size_bytes": size})
    except FileNotFoundError:
        finish(job.pk, job.lease_token, Job.State.FAILED, error_code="source_unavailable")
    except ValueError:
        finish(job.pk, job.lease_token, Job.State.FAILED, error_code="source_integrity_failed")
    except Exception:
        # Do not expose exception messages, report contents or storage paths through the API.
        finish(job.pk, job.lease_token, Job.State.FAILED, error_code="worker_failed")

def dispatch_pending(publish, *, limit=20):
    now = timezone.now(); due = now - timedelta(seconds=30)
    candidates = list(Job.objects.filter(
        Q(state=Job.State.QUEUED) & (Q(last_enqueued_at__isnull=True) | Q(last_enqueued_at__lte=due)) |
        Q(state=Job.State.RUNNING, lease_until__lte=now)
    ).order_by("created_at").values_list("pk", flat=True)[:limit])
    sent = 0
    for job_id in candidates:
        with transaction.atomic():
            job = Job.objects.select_for_update().get(pk=job_id)
            expired = job.state == Job.State.RUNNING and job.lease_until and job.lease_until <= now
            queued = job.state == Job.State.QUEUED and (not job.last_enqueued_at or job.last_enqueued_at <= due)
            if not (expired or queued):
                continue
            if expired:
                job.state = Job.State.QUEUED
                job.lease_token = None; job.lease_until = None
            job.last_enqueued_at = now
            job.save()
        # Broker publication happens after commit. A crash/lost publish is retried after 30s.
        # Duplicate publication is safe: claim/finish fence worker state with a lease token.
        try:
            publish(str(job_id))
        except Exception:
            break  # Durable intent remains queued; no exception/credential text is logged.
        sent += 1
    return sent
