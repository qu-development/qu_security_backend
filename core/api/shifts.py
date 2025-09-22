from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import IsGuardAssigned
from permissions.utils import PermissionManager

from ..models import Shift
from ..serializers import ShiftSerializer


class ShiftViewSet(
    SoftDeleteMixin, FilterMixin, BulkActionMixin, viewsets.ModelViewSet
):
    """
    ViewSet for managing Shift model with full CRUD operations.

    list: Returns a list of all shifts
    create: Creates a new shift
    retrieve: Returns shift details by ID
    update: Updates shift information (PUT)
    partial_update: Partially updates shift information (PATCH)
    destroy: Deletes a shift
    """

    queryset = (
        Shift.objects.select_related(
            "guard__user",  # To access guard.user.username, first_name, etc.
            "property__owner__user",  # To access property.owner information
            "service__guard__user",  # For service information and its guard
            "weapon",  # For weapon information if assigned
        )
        .all()
        .order_by("-start_time")
    )
    serializer_class = ShiftSerializer

    def get_permissions(self):
        """Return the appropriate permissions based on action"""
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsGuardAssigned]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        # Bypass permission filtering for swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Shift.objects.none()

        queryset = super().get_queryset()
        return PermissionManager.filter_queryset_by_permissions(
            self.request.user, queryset, "shift"
        )

    @swagger_auto_schema(
        operation_description="Get list of all shifts",
        responses={200: ShiftSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of all shifts"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new shift",
        request_body=ShiftSerializer,
        responses={201: ShiftSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Create a new shift"""
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Temporarily allow any authenticated user to create a shift."""
        serializer.save()

    @swagger_auto_schema(
        operation_description="Get shifts by guard",
        responses={200: ShiftSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def by_guard(self, request):
        """Get shifts filtered by guard ID"""
        guard_id = request.query_params.get("guard_id")
        if guard_id:
            shifts = self.get_queryset().filter(guard_id=guard_id)
            serializer = self.get_serializer(shifts, many=True)
            return Response(serializer.data)
        return Response({"error": "guard_id parameter is required"}, status=400)

    @swagger_auto_schema(
        operation_description="Get shifts by property",
        responses={200: ShiftSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def by_property(self, request):
        """Get shifts filtered by property ID"""
        property_id = request.query_params.get("property_id")
        if property_id:
            shifts = self.get_queryset().filter(property_id=property_id)
            serializer = self.get_serializer(shifts, many=True)
            return Response(serializer.data)
        return Response({"error": "property_id parameter is required"}, status=400)

    @swagger_auto_schema(
        operation_description="Get next scheduled shift for a guard",
        responses={200: ShiftSerializer, 404: "No scheduled shift found"},
    )
    @action(detail=False, methods=["get"])
    def next_shift(self, request):
        """Get the next scheduled shift for a guard"""
        guard_id = request.query_params.get("guard_id")
        if not guard_id:
            return Response({"error": "guard_id parameter is required"}, status=400)

        from django.utils import timezone

        now = timezone.now()

        # Get the next scheduled shift for the guard
        next_shift = (
            Shift.objects.filter(
                guard_id=guard_id,
                status=Shift.Status.SCHEDULED,
                planned_start_time__isnull=False,
                planned_start_time__gt=now,
            )
            .order_by("planned_start_time")
            .first()
        )

        if not next_shift:
            return Response(
                {"error": "No scheduled shifts found for this guard"},
                status=404,
            )

        serializer = self.get_serializer(next_shift)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get shifts by service",
        responses={200: ShiftSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def by_service(self, request):
        """Get shifts filtered by service ID"""
        service_id = request.query_params.get("service_id")
        if service_id:
            shifts = self.get_queryset().filter(service_id=service_id)
            serializer = self.get_serializer(shifts, many=True)
            return Response(serializer.data)
        return Response({"error": "service_id parameter is required"}, status=400)
