from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import IsAdminOrManager
from permissions.utils import PermissionManager

from ..models import Guard
from ..serializers import GuardCreateSerializer, GuardDetailSerializer, GuardSerializer


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
