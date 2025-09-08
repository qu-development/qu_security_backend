from django.utils.dateparse import parse_datetime
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from mobile.models import GuardReport
from mobile.serializers import GuardReportSerializer


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
        qs = self.filter_queryset(self.get_queryset().filter(guard_id=guard_id))
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
