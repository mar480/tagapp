from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    document_id = serializers.UUIDField(read_only=True)
    class Meta:
        model = Job
        fields = ("id", "document_id", "kind", "state", "progress", "attempts", "cancel_requested",
                  "result", "error_code", "created_at", "finished_at")
        read_only_fields = fields

class JobCommandSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
