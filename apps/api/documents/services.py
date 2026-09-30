from pathlib import PurePosixPath
from django.db import transaction
from rest_framework.exceptions import ValidationError
from projects.access import accessible_project
from projects.services import audit
from projects.models import Project
from .models import Document
from .storage import blob_store

def store_document(actor, project_id, upload):
    # Header check is intake only, not PDF conversion or conformance validation.
    if upload.read(5) != b"%PDF-":
        raise ValidationError({"file": "Select a PDF document."})
    upload.seek(0)
    name = PurePosixPath(upload.name.replace("\\", "/")).name
    if not name or len(name) > 255 or any(ord(c) < 32 for c in name):
        raise ValidationError({"file": "Invalid document filename."})
    store = blob_store(); stored = None
    try:
        with transaction.atomic():
            Project.objects.select_for_update().get(pk=project_id)
            project = accessible_project(actor, project_id, edit=True)
            stored = store.put(upload)
            document = Document.objects.create(project=project, uploaded_by=actor, name=name,
                blob_key=stored.key, sha256=stored.sha256, size_bytes=stored.size_bytes)
            audit(project, actor, "document.uploaded", document_id=str(document.pk), sha256=stored.sha256,
                  size_bytes=stored.size_bytes)
        return document
    except BaseException as exc:
        if stored:
            store.delete(stored.key)
        if isinstance(exc, ValueError):
            raise ValidationError({"file": str(exc)}) from exc
        raise
