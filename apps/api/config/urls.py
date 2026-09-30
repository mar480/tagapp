from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import path
from drf_spectacular.views import SpectacularAPIView
from accounts.views import SessionView, LoginView, LogoutView
from projects.views import ProjectList, ProjectDetail, MembersView, MemberDetail, AuditList
from documents.views import DocumentList, DocumentDownload
from jobs.views import JobList, JobDetail, VerifyDocument, CancelJob

def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "ok"})
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)

urlpatterns = [
    path("admin/", admin.site.urls), path("health/", health),
    path("api/v1/schema/", SpectacularAPIView.as_view()),
    path("api/v1/auth/session/", SessionView.as_view()), path("api/v1/auth/login/", LoginView.as_view()),
    path("api/v1/auth/logout/", LogoutView.as_view()),
    path("api/v1/projects/", ProjectList.as_view()), path("api/v1/projects/<uuid:pk>/", ProjectDetail.as_view()),
    path("api/v1/projects/<uuid:project_id>/members/", MembersView.as_view()),
    path("api/v1/projects/<uuid:project_id>/members/<uuid:user_id>/", MemberDetail.as_view()),
    path("api/v1/projects/<uuid:project_id>/audit/", AuditList.as_view()),
    path("api/v1/projects/<uuid:project_id>/documents/", DocumentList.as_view()),
    path("api/v1/projects/<uuid:project_id>/documents/<uuid:document_id>/download/", DocumentDownload.as_view()),
    path("api/v1/projects/<uuid:project_id>/documents/<uuid:document_id>/verify/", VerifyDocument.as_view()),
    path("api/v1/projects/<uuid:project_id>/jobs/", JobList.as_view()),
    path("api/v1/projects/<uuid:project_id>/jobs/<uuid:pk>/", JobDetail.as_view()),
    path("api/v1/projects/<uuid:project_id>/jobs/<uuid:job_id>/cancel/", CancelJob.as_view()),
]
