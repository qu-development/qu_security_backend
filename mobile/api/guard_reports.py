import logging

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from common.tasks import process_guard_report
from mobile.models import GuardReport
from mobile.serializers import GuardReportSerializer

logger = logging.getLogger(__name__)


class GuardReportViewSet(viewsets.ModelViewSet):
    """CRUD API for Guard reports.

    Supports:
    - Standard CRUD operations
    - Search (by note and guard user fields)
    - Ordering (by report_datetime, created_at, updated_at)
    - Filtering by guard via query param `?guard=<id>`
    - Custom route: `by-guard/<guard_id>/` to list reports for a specific guard
    """

    queryset = GuardReport.objects.all()
    serializer_class = GuardReportSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    # Use project-wide filter backends from settings (Search + Ordering)
    search_fields = (
        "note",
        "guard__user__username",
        "guard__user__first_name",
        "guard__user__last_name",
    )
    ordering_fields = ("report_datetime", "created_at", "updated_at")
    ordering = ("-report_datetime",)

    def get_queryset(self):
        qs = super().get_queryset()
        guard_id = self.request.query_params.get("guard")
        if guard_id:
            qs = qs.filter(guard_id=guard_id)
        date_from = self.request.query_params.get("date_from")
        if date_from:
            dt_from = parse_datetime(date_from)
            if dt_from:
                qs = qs.filter(report_datetime__gte=dt_from)
        date_to = self.request.query_params.get("date_to")
        if date_to:
            dt_to = parse_datetime(date_to)
            if dt_to:
                qs = qs.filter(report_datetime__lte=dt_to)
        return qs

    @action(
        detail=False,
        url_path=r"by-guard/(?P<guard_id>[^/.]+)",
        url_name="by-guard",
        methods=["get"],
    )
    def by_guard(self, request, guard_id=None):
        """List reports for the provided guard id.

        Example: GET /api/mobile/guard-reports/by-guard/123/
        Supports pagination, search and ordering.
        """
        # filter by created today only
        qs = self.filter_queryset(
            self.get_queryset().filter(
                guard_id=guard_id, created_at__date=timezone.now().date()
            )
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Override to add async processing after creating a guard report."""
        # Save the guard report
        report = serializer.save()

        logger.info(f"Guard report {report.id} created by {report.guard}")

        # Process the report asynchronously (file processing, notifications, etc.)
        try:
            task_result = process_guard_report(report.id)
            logger.info(f"Async processing initiated for guard report {report.id}")

            # Add task info to the response if available
            if hasattr(report, "_task_result"):
                report._task_result = task_result

        except Exception as e:
            # Log error but don't fail the request
            logger.error(
                f"Failed to initiate async processing for guard report {report.id}: {e}"
            )

    def create(self, request, *args, **kwargs):
        """Override create to include async processing status in response."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        response_data = serializer.data.copy()

        # Add async processing status if available
        if hasattr(serializer.instance, "_task_result"):
            response_data["async_processing"] = {
                "initiated": True,
                "task_result": serializer.instance._task_result,
            }
        else:
            response_data["async_processing"] = {
                "initiated": False,
                "reason": "async_tasks_disabled",
            }

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
