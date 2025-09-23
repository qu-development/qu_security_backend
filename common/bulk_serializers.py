"""
Serializers for bulk operations
"""

from rest_framework import serializers


class BulkCreateRequestSerializer(serializers.Serializer):
    """Serializer for bulk create request"""

    items = serializers.ListField(
        child=serializers.DictField(), help_text="List of objects to create"
    )


class BulkDeleteRequestSerializer(serializers.Serializer):
    """Serializer for bulk delete request"""

    ids = serializers.ListField(
        child=serializers.IntegerField(), help_text="List of object IDs to delete"
    )


class BulkUpdateRequestSerializer(serializers.Serializer):
    """Serializer for bulk update request"""

    updates = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of objects with their updates (must include 'id' field)",
    )


class BulkResponseSerializer(serializers.Serializer):
    """Base serializer for bulk operation responses"""

    success = serializers.BooleanField(help_text="Whether the operation was successful")
    message = serializers.CharField(help_text="Response message")
    data = serializers.DictField(help_text="Response data")  # type: ignore[assignment]


class BulkCreateResponseDataSerializer(serializers.Serializer):
    """Data part of bulk create response"""

    created_count = serializers.IntegerField(help_text="Number of objects created")
    total_attempted = serializers.IntegerField(
        help_text="Total number of objects attempted"
    )
    created_objects = serializers.ListField(  # type: ignore[assignment]
        child=serializers.DictField(),
        required=False,
        help_text="List of created objects",
    )
    errors = serializers.ListField(  # type: ignore[assignment]
        child=serializers.CharField(),
        required=False,
        help_text="List of errors encountered",
    )


class BulkDeleteResponseDataSerializer(serializers.Serializer):
    """Data part of bulk delete response"""

    deleted_count = serializers.IntegerField(help_text="Number of objects deleted")


class BulkUpdateResponseDataSerializer(serializers.Serializer):
    """Data part of bulk update response"""

    updated_count = serializers.IntegerField(help_text="Number of objects updated")
    total_attempted = serializers.IntegerField(
        help_text="Total number of objects attempted"
    )
    errors = serializers.ListField(  # type: ignore[assignment]
        child=serializers.CharField(),
        required=False,
        help_text="List of errors encountered",
    )
