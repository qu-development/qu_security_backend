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

    queryset = Shift.objects.all().order_by("-start_time")
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
