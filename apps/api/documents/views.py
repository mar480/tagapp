from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from projects.access import accessible_project
from .models import Document
from .serializers import DocumentSerializer, UploadSerializer
from .services import store_document
from .storage import blob_store

class DocumentList(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser]
    def get_queryset(self):
        return accessible_project(self.request.user, self.kwargs["project_id"]).documents.all()
    @extend_schema(request=UploadSerializer, responses={201: DocumentSerializer})
    def post(self, request, project_id):
        accessible_project(request.user, project_id, edit=True)
        upload = UploadSerializer(data=request.data); upload.is_valid(raise_exception=True)
        document = store_document(request.user, project_id, upload.validated_data["file"])
        return Response(DocumentSerializer(document).data, status=201)

class DocumentDownload(APIView):
    @extend_schema(responses={(200, "application/pdf"): bytes})
    def get(self, request, project_id, document_id):
        project = accessible_project(request.user, project_id)
        document = get_object_or_404(Document, pk=document_id, project=project)
        try:
            stream = blob_store().open(document.blob_key)
        except OSError as exc:
            raise NotFound("The stored document is unavailable.") from exc
        response = FileResponse(stream, as_attachment=True, filename=document.name, content_type="application/pdf")
        response["Content-Security-Policy"] = "sandbox; default-src 'none'"
        return response
