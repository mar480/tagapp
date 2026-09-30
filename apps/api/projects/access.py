from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from .models import Project

def visible_projects(user):
    if not user.is_authenticated or not user.is_active:
        return Project.objects.none()
    return Project.objects.filter(Q(owner=user) | Q(members__user=user)).distinct()

def role_for(project, user):
    if not user.is_active:
        return None
    if project.owner_id == user.pk:
        return "owner"
    return project.members.filter(user=user).values_list("role", flat=True).first()

def accessible_project(user, project_id, *, edit=False, owner=False):
    project = get_object_or_404(visible_projects(user), pk=project_id)
    role = role_for(project, user)
    if (owner and role != "owner") or (edit and role not in ("owner", "editor")):
        raise PermissionDenied("Your project role does not allow this action.")
    return project
