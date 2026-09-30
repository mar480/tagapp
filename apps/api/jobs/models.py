import uuid
from django.conf import settings
from django.db import models
from projects.models import Project
from documents.models import Document

class Job(models.Model):
    class State(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="jobs")
    document = models.ForeignKey(Document, on_delete=models.PROTECT)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    operation_id = models.UUIDField()
    kind = models.CharField(max_length=32, default="verify_document", editable=False)
    state = models.CharField(max_length=16, choices=State.choices, default=State.QUEUED)
    progress = models.PositiveSmallIntegerField(default=0)
    attempts = models.PositiveSmallIntegerField(default=0)
    lease_token = models.UUIDField(null=True, editable=False)
    lease_until = models.DateTimeField(null=True, editable=False)
    last_enqueued_at = models.DateTimeField(null=True)
    cancel_requested = models.BooleanField(default=False)
    result = models.JSONField(default=dict)
    error_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [models.UniqueConstraint(fields=["requested_by", "operation_id"], name="one_job_operation_per_user"),
            models.CheckConstraint(condition=models.Q(progress__lte=100), name="job_progress_percent")]
        indexes = [models.Index(fields=["state", "last_enqueued_at"], name="job_dispatch_due")]
