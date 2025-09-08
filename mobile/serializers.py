from rest_framework import serializers

from .models import GuardReport


class GuardReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuardReport
        fields = (
            "id",
            "guard",
            "file",
            "note",
            "report_datetime",
            "latitude",
            "longitude",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
