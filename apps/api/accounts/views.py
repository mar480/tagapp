from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from .serializers import LoginSerializer, SessionSerializer, UserSerializer

def csrf_failure(request, reason=""):
    return JsonResponse({"detail": "Session verification failed. Refresh and try again."}, status=403)

def session_data(request):
    return {"user": UserSerializer(request.user).data if request.user.is_authenticated else None,
            "csrf_token": get_token(request)}

class SessionView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(responses=SessionSerializer)
    def get(self, request):
        response = Response(session_data(request))
        response["Cache-Control"] = "no-store"
        return response

class LoginThrottle(AnonRateThrottle):
    scope = "login"

@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginThrottle]
    @extend_schema(request=LoginSerializer, responses=SessionSerializer)
    def post(self, request):
        data = LoginSerializer(data=request.data); data.is_valid(raise_exception=True)
        user = authenticate(request, **data.validated_data)
        if user is None:
            return Response({"detail": "Username or password was not recognised."}, status=400)
        login(request, user)
        return Response(session_data(request))

class LogoutView(APIView):
    @extend_schema(request=None, responses=SessionSerializer)
    def post(self, request):
        logout(request)
        return Response(session_data(request))
