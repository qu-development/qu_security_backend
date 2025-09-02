from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import IsAdminOrManager
from permissions.utils import PermissionManager

from ..models import Guard
from ..serializers import (
    GuardCreateSerializer,
    GuardDetailSerializer,
    GuardPropertiesShiftsSerializer,
    GuardSerializer,
    GuardUpdateSerializer,
)


class GuardViewSet(
    SoftDeleteMixin, FilterMixin, BulkActionMixin, viewsets.ModelViewSet
):
    """
    ViewSet for managing Guard model with full CRUD operations.

    list: Returns a list of all guards
    create: Creates a new guard
    retrieve: Returns guard details by ID
    update: Updates guard information (PUT)
    partial_update: Partially updates guard information (PATCH)
    destroy: Deletes a guard
    """

    queryset = Guard.objects.all().order_by("id")
    # Enable global search and ordering
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
        "address",
    ]
    ordering_fields = [
        "id",
        "user__first_name",
        "user__last_name",
        "user__username",
        "user__email",
        "phone",
    ]

    def get_permissions(self):
        """Return the appropriate permissions based on action"""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Return the appropriate serializer class based on action"""
        if self.action == "create":
            return GuardCreateSerializer
        if self.action == "retrieve":
            return GuardDetailSerializer
        if self.action in ["update", "partial_update"]:
            return GuardUpdateSerializer
        return GuardSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        return PermissionManager.filter_queryset_by_permissions(
            self.request.user, queryset, "guard"
        )

    @swagger_auto_schema(
        operation_description="Get list of all guards",
        responses={200: GuardSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of all guards"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new guard",
        request_body=GuardCreateSerializer,
        responses={201: GuardSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Create a new guard"""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update guard information (full update)",
        request_body=GuardUpdateSerializer,
        responses={200: GuardUpdateSerializer, 400: "Bad Request", 404: "Not Found"},
    )
    def update(self, request, *args, **kwargs):
        """Update guard information (full update)"""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update guard information",
        request_body=GuardUpdateSerializer,
        responses={200: GuardUpdateSerializer, 400: "Bad Request", 404: "Not Found"},
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update guard information"""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get properties and shifts associated with a specific guard",
        responses={200: GuardPropertiesShiftsSerializer, 404: "Not Found"},
    )
    @action(detail=True, methods=["get"], url_path="properties-shifts")
    def properties_shifts(self, request, pk=None):
        """Get properties and shifts associated with a specific guard"""
        guard = self.get_object()
        serializer = GuardPropertiesShiftsSerializer(guard)
        return Response(serializer.data)
