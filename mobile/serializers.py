from rest_framework import serializers

from .models import GuardReport


class GuardReportSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = GuardReport
        fields = (
            "id",
            "guard",
            "file",
            "file_url",
            "note",
            "report_datetime",
            "latitude",
            "longitude",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "file_url")

    def get_file_url(self, obj):
        """Return a signed URL for accessing the file."""
        return obj.get_file_url()
