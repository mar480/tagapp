from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from projects.access import accessible_project
from documents.models import Document
from .models import Job
from .serializers import JobSerializer, JobCommandSerializer
from .services import request_verification, cancel_job

class JobList(generics.ListAPIView):
    serializer_class = JobSerializer
    def get_queryset(self):
        return accessible_project(self.request.user, self.kwargs["project_id"]).jobs.all()

class JobDetail(generics.RetrieveAPIView):
    serializer_class = JobSerializer
    def get_queryset(self):
        return accessible_project(self.request.user, self.kwargs["project_id"]).jobs.all()

class VerifyDocument(APIView):
    @extend_schema(request=JobCommandSerializer, responses={200: JobSerializer, 201: JobSerializer})
    def post(self, request, project_id, document_id):
        project = accessible_project(request.user, project_id, edit=True)
        document = get_object_or_404(Document, project=project, pk=document_id)
        data = JobCommandSerializer(data=request.data); data.is_valid(raise_exception=True)
        job, created = request_verification(request.user, document, data.validated_data["operation_id"])
        return Response(JobSerializer(job).data, status=201 if created else 200)

class CancelJob(APIView):
    @extend_schema(request=None, responses=JobSerializer)
    def post(self, request, project_id, job_id):
        project = accessible_project(request.user, project_id, edit=True)
        get_object_or_404(Job, project=project, pk=job_id)
        return Response(JobSerializer(cancel_job(request.user, job_id)).data)
