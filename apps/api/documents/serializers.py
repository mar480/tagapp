from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "name", "sha256", "size_bytes", "created_at")
        read_only_fields = fields

class UploadSerializer(serializers.Serializer):
    file = serializers.FileField()
