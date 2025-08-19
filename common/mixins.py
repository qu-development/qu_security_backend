"""
Common mixins for views and serializers
"""

from __future__ import annotations

import logging
from datetime import datetime, time
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from collections.abc import Callable

    from django.db.models import QuerySet

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.decorators import action

from .constants import API_MESSAGES
from .utils import ModelHelper, ResponseHelper

logger = logging.getLogger(__name__)


class SoftDeleteMixin:
    """
    Mixin to add soft delete functionality to ViewSets
    """

    @action(detail=True, methods=["post"])
    def soft_delete(self, request, pk=None):
        """Soft delete an object"""
        obj = self.get_object()
        ModelHelper.soft_delete_object(obj)
        return ResponseHelper.success_response(
            message=API_MESSAGES["deleted"], status_code=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """Restore a soft deleted object"""
        obj = self.get_object()
        ModelHelper.restore_object(obj)
        return ResponseHelper.success_response(
            message="Object restored successfully", status_code=status.HTTP_200_OK
        )

    def get_queryset(self):
        """Override to filter only active objects by default"""
        base_qs = super().get_queryset()
        model = getattr(base_qs, "model", None)
        if model and hasattr(model, "is_active"):
            include_inactive = (
                self.request.query_params.get("include_inactive", "false").lower()
                == "true"
            )
            if include_inactive and hasattr(model, "all_objects"):
                # Rebuild queryset using the unfiltered manager, preserve ordering
                queryset = model.all_objects.all()
                try:
                    order_by = list(base_qs.query.order_by)
                    if order_by:
                        queryset = queryset.order_by(*order_by)
                except Exception:
                    logger.warning(
                        "Failed to apply ordering to queryset: %s", base_qs.query
                    )
                return queryset
            # Default manager already returns only active records
            return base_qs
        return base_qs


class TimestampMixin:
    """
    Mixin to add created_at and updated_at fields to serializers
    """

    def to_representation(self, instance):
        """Add timestamp information to the representation"""
        data = super().to_representation(instance)
        if hasattr(instance, "created_at"):
            data["created_at"] = instance.created_at
        if hasattr(instance, "updated_at"):
            data["updated_at"] = instance.updated_at
        return data


class FilterMixin:
    """
    Mixin to add common filtering functionality
    """

    def filter_queryset_by_user_permissions(self, queryset: QuerySet) -> QuerySet:
        """
        Filter queryset based on user permissions.
        This is a base implementation that should be overridden in specific viewsets.
        """
        # Base implementation - can be overridden
        return queryset

    def get_filtered_queryset(self):
        """Get queryset with all filters applied"""
        queryset = self.get_queryset()

        # Apply search filter if provided
        request = getattr(self, "request", None)
        if request is None:
            return queryset
        search = request.query_params.get("search")
        if search and hasattr(self, "search_fields"):
            # Simple search implementation
            from django.db.models import Q

            search_filter = Q()
            for field in self.search_fields:
                search_filter |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(search_filter)

        # Apply date range filter
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        date_field = getattr(self, "date_filter_field", "created_at")

        def _parse_query_dt(val: str, end: bool):
            """Parse query param into aware datetime. Supports ISO datetime or YYYY-MM-DD.

            If only a date is provided (no time component), use start-of-day for date_from
            and end-of-day for date_to.
            """
            if not val:
                return None
            dt = parse_datetime(val)
            if dt is not None:
                # Detect if the input lacked a time component (common when val is YYYY-MM-DD)
                has_time = ("T" in val) or (" " in val) or (":" in val)
                if not has_time:
                    # Adjust to start/end of day accordingly
                    if end:
                        dt = dt.replace(
                            hour=23, minute=59, second=59, microsecond=999999
                        )
                    else:
                        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            d = parse_date(val)
            if d is not None:
                base = time.max if end else time.min
                dt = datetime.combine(d, base)
                return timezone.make_aware(dt)
            return None

        if date_from:
            df = _parse_query_dt(date_from, end=False) or date_from
            queryset = queryset.filter(**{f"{date_field}__gte": df})
        if date_to:
            dt = _parse_query_dt(date_to, end=True) or date_to
            queryset = queryset.filter(**{f"{date_field}__lte": dt})

        # Apply ordering
        ordering = request.query_params.get("ordering")
        if ordering:
            valid_orderings = getattr(self, "valid_orderings", [])
            if not valid_orderings or ordering.lstrip("-") in valid_orderings:
                queryset = queryset.order_by(ordering)

        return queryset

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """Apply DRF filter backends first, then apply date range filters.

        This ensures compatibility with include_inactive (SoftDeleteMixin),
        because DRF calls filter_queryset() after get_queryset().
        """
        # Apply DRF's configured filter backends (Search, Ordering, etc.)
        base_filter: Callable[[QuerySet], QuerySet] | None = getattr(
            super(), "filter_queryset", None
        )
        if callable(base_filter):
            queryset = base_filter(queryset)

        # Apply optional date range filtering
        request = getattr(self, "request", None)
        if request is None:
            return queryset
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        date_field = getattr(self, "date_filter_field", "created_at")

        def _parse_query_dt(val: str, end: bool):
            if not val:
                return None
            dt = parse_datetime(val)
            if dt is not None:
                has_time = ("T" in val) or (" " in val) or (":" in val)
                if not has_time:
                    if end:
                        dt = dt.replace(
                            hour=23, minute=59, second=59, microsecond=999999
                        )
                    else:
                        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            d = parse_date(val)
            if d is not None:
                base = time.max if end else time.min
                dt = datetime.combine(d, base)
                return timezone.make_aware(dt)
            return None

        df_parsed = _parse_query_dt(date_from, end=False) if date_from else None
        dt_parsed = _parse_query_dt(date_to, end=True) if date_to else None
        if date_from:
            queryset = queryset.filter(
                **{f"{date_field}__gte": (df_parsed or date_from)}
            )
        if date_to:
            queryset = queryset.filter(**{f"{date_field}__lte": (dt_parsed or date_to)})

        return queryset


class BulkActionMixin:
    """
    Mixin to add bulk actions to ViewSets
    """

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        """Bulk delete objects"""
        ids = request.data.get("ids", [])
        if not ids:
            return ResponseHelper.error_response(
                message="No IDs provided", status_code=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(id__in=ids)
        count = queryset.count()

        # Use soft delete if available
        if hasattr(queryset.model, "is_active"):
            queryset.update(is_active=False)
        else:
            queryset.delete()

        return ResponseHelper.success_response(
            message=f"{count} objects deleted successfully",
            data={"deleted_count": count},
        )

    @action(detail=False, methods=["post"])
    def bulk_update(self, request):
        """Bulk update objects"""
        updates = request.data.get("updates", [])
        if not updates:
            return ResponseHelper.error_response(
                message="No updates provided", status_code=status.HTTP_400_BAD_REQUEST
            )

        updated_count = 0
        errors = []

        for update in updates:
            obj_id = update.get("id")
            if not obj_id:
                errors.append("Missing ID in update data")
                continue

            try:
                obj = self.get_queryset().get(id=obj_id)
                serializer = self.get_serializer(obj, data=update, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated_count += 1
                else:
                    errors.append(f"ID {obj_id}: {serializer.errors}")
            except self.queryset.model.DoesNotExist:
                errors.append(f"Object with ID {obj_id} not found")
            except Exception as e:
                errors.append(f"ID {obj_id}: {str(e)}")

        response_data = {
            "updated_count": updated_count,
            "total_attempted": len(updates),
        }

        if errors:
            response_data["errors"] = errors

        return ResponseHelper.success_response(
            message=f"{updated_count} objects updated successfully", data=response_data
        )
