from django.db import transaction
from .models import AuditEvent, Project, Membership

def audit(project, actor, operation, **metadata):
    AuditEvent.objects.create(project=project, actor=actor, operation=operation, metadata=metadata)

@transaction.atomic
def create_project(actor, name):
    project = Project.objects.create(owner=actor, name=name)
    audit(project, actor, "project.created")
    return project

@transaction.atomic
def set_member(project, actor, user, role):
    Project.objects.select_for_update().get(pk=project.pk)
    membership, _ = Membership.objects.update_or_create(project=project, user=user, defaults={"role": role})
    audit(project, actor, "membership.set", user_id=str(user.pk), role=role)
    return membership

@transaction.atomic
def remove_member(project, actor, user_id):
    Project.objects.select_for_update().get(pk=project.pk)
    deleted, _ = Membership.objects.filter(project=project, user_id=user_id).delete()
    if deleted:
        audit(project, actor, "membership.removed", user_id=str(user_id))
