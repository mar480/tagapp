from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import Project, Membership, AuditEvent
from .access import role_for

class ProjectSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    @extend_schema_field(serializers.CharField())
    def get_role(self, obj):
        return role_for(obj, self.context["request"].user)
    class Meta:
        model = Project
        fields = ("id", "name", "created_at", "role")
        read_only_fields = ("id", "created_at", "role")

class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    class Meta:
        model = Membership
        fields = ("user_id", "username", "role")

class MemberCommandSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=Membership.Role.choices)

class AuditSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.username", allow_null=True)
    class Meta:
        model = AuditEvent
        fields = ("id", "actor", "operation", "metadata", "created_at")
