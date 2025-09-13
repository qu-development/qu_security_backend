from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import IsAdminOrManager
from permissions.utils import PermissionManager

from ..models import Weapon
from ..serializers import (
    WeaponCreateSerializer,
    WeaponSerializer,
    WeaponUpdateSerializer,
)


class WeaponViewSet(
    SoftDeleteMixin, FilterMixin, BulkActionMixin, viewsets.ModelViewSet
):
    """
    ViewSet for managing Weapon model with full CRUD operations.

    list: Returns a list of all weapons
    create: Creates a new weapon
    retrieve: Returns weapon details by ID
    update: Updates weapon information (PUT)
    partial_update: Partially updates weapon information (PATCH)
    destroy: Soft deletes a weapon
    """

    queryset = Weapon.objects.all().order_by("id")
    serializer_class = WeaponSerializer
    search_fields = [
        "serial_number",
        "model",
        "guard__user__username",
        "guard__user__first_name",
        "guard__user__last_name",
    ]
    ordering_fields = [
        "id",
        "serial_number",
        "model",
        "guard__user__username",
        "created_at",
        "updated_at",
    ]

    def get_permissions(self):
        """Return the list of permissions that this view requires."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAdminOrManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Return the class to use for the serializer."""
        if self.action == "create":
            return WeaponCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return WeaponUpdateSerializer
        return WeaponSerializer

    def get_queryset(self):
        """Return the queryset for this view."""
        # Bypass permission filtering for swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Weapon.objects.none()

        queryset = super().get_queryset()
        return PermissionManager.filter_queryset_by_permissions(
            self.request.user, queryset, "weapon"
        )

    @swagger_auto_schema(
        operation_description="Get list of all weapons",
        responses={200: WeaponSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """List all weapons."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new weapon",
        request_body=WeaponCreateSerializer,
        responses={201: WeaponSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Create a new weapon."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update weapon information (full update)",
        request_body=WeaponUpdateSerializer,
        responses={200: WeaponUpdateSerializer, 400: "Bad Request", 404: "Not Found"},
    )
    def update(self, request, *args, **kwargs):
        """Update weapon information."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update weapon information",
        request_body=WeaponUpdateSerializer,
        responses={200: WeaponUpdateSerializer, 400: "Bad Request", 404: "Not Found"},
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update weapon information."""
        return super().partial_update(request, *args, **kwargs)
