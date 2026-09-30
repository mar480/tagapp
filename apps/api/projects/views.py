from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from .access import accessible_project, visible_projects
from .models import Membership
from .serializers import ProjectSerializer, MembershipSerializer, MemberCommandSerializer, AuditSerializer
from .services import create_project, set_member, remove_member

class ProjectList(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    def get_queryset(self):
        return visible_projects(self.request.user)
    def perform_create(self, serializer):
        serializer.instance = create_project(self.request.user, serializer.validated_data["name"])

class ProjectDetail(generics.RetrieveAPIView):
    serializer_class = ProjectSerializer
    def get_queryset(self):
        return visible_projects(self.request.user)

class MembersView(APIView):
    @extend_schema(responses=MembershipSerializer(many=True))
    def get(self, request, project_id):
        project = accessible_project(request.user, project_id)
        return Response(MembershipSerializer(project.members.select_related("user"), many=True).data)
    @extend_schema(request=MemberCommandSerializer, responses=MembershipSerializer)
    def post(self, request, project_id):
        project = accessible_project(request.user, project_id, owner=True)
        data = MemberCommandSerializer(data=request.data); data.is_valid(raise_exception=True)
        user = get_user_model().objects.filter(username=data.validated_data["username"], is_active=True).first()
        if user is None or user.pk == project.owner_id:
            raise ValidationError({"username": "Choose an existing active account other than the project owner."})
        member = set_member(project, request.user, user, data.validated_data["role"])
        return Response(MembershipSerializer(member).data, status=status.HTTP_200_OK)

class MemberDetail(APIView):
    @extend_schema(request=None, responses={204: None})
    def delete(self, request, project_id, user_id):
        project = accessible_project(request.user, project_id, owner=True)
        get_object_or_404(Membership, project=project, user_id=user_id)
        remove_member(project, request.user, user_id)
        return Response(status=204)

class AuditList(generics.ListAPIView):
    serializer_class = AuditSerializer
    def get_queryset(self):
        return accessible_project(self.request.user, self.kwargs["project_id"]).events.select_related("actor")
