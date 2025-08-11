"""
Common utilities for the application
"""

from decimal import Decimal
from typing import Any

from django.core.paginator import Paginator
from django.db.models import QuerySet
from rest_framework.response import Response


class PaginationHelper:
    """Helper class for consistent pagination across the application"""

    @staticmethod
    def paginate_queryset(
        queryset: QuerySet, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        """
        Paginate a queryset and return pagination info
        """
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        return {
            "results": list(page_obj),
            "pagination": {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "page": page_obj.number,
                "page_size": page_size,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "next_page": page_obj.next_page_number()
                if page_obj.has_next()
                else None,
                "previous_page": page_obj.previous_page_number()
                if page_obj.has_previous()
                else None,
            },
        }


class ResponseHelper:
    """Helper class for consistent API responses"""

    @staticmethod
    def success_response(
        data: Any = None, message: str = "Operation successful", status_code: int = 200
    ) -> Response:
        """Create a successful response"""
        response_data = {
            "success": True,
            "message": message,
        }
        if data is not None:
            response_data["data"] = data

        return Response(response_data, status=status_code)

    @staticmethod
    def error_response(
        message: str = "Operation failed", errors: Any = None, status_code: int = 400
    ) -> Response:
        """Create an error response"""
        response_data = {
            "success": False,
            "message": message,
        }
        if errors is not None:
            response_data["errors"] = errors

        return Response(response_data, status=status_code)


class ValidationHelper:
    """Helper class for common validations"""

    @staticmethod
    def validate_positive_decimal(value: Decimal, field_name: str = "Value") -> None:
        """Validate that a decimal value is positive"""
        if value <= 0:
            raise ValueError(f"{field_name} must be greater than 0")

    @staticmethod
    def validate_required_fields(data: dict, required_fields: list[str]) -> list[str]:
        """Validate required fields and return list of missing fields"""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing_fields.append(field)
        return missing_fields


class ModelHelper:
    """Helper class for common model operations"""

    @staticmethod
    def get_active_objects(model_class):
        """Get only active objects for a model"""
        return model_class.objects.filter(is_active=True)

    @staticmethod
    def soft_delete_object(obj):
        """Soft delete an object"""
        obj.is_active = False
        obj.save()
        return obj

    @staticmethod
    def restore_object(obj):
        """Restore a soft deleted object"""
        obj.is_active = True
        obj.save()
        return obj
