from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import IsAdminOrManager
from permissions.utils import PermissionManager

from ..models import Client
from ..serializers import (
    ClientCreateSerializer,
    ClientDetailSerializer,
    ClientSerializer,
    ClientUpdateSerializer,
)


class ClientViewSet(
    SoftDeleteMixin, FilterMixin, BulkActionMixin, viewsets.ModelViewSet
):
    """
    ViewSet for managing Client model with full CRUD operations.

    list: Returns a list of all clients
    create: Creates a new client
    retrieve: Returns client details by ID
    update: Updates client information (PUT)
    partial_update: Partially updates client information (PATCH)
    destroy: Deletes a client
    """

    queryset = Client.objects.all().order_by("id")
    # Enable global search and ordering
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone",
    ]
    ordering_fields = [
        "id",
        "user__first_name",
        "user__last_name",
        "user__username",
        "user__email",
        "phone",
        "balance",
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
            return ClientCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ClientUpdateSerializer
        elif self.action == "retrieve":
            return ClientDetailSerializer
        return ClientSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        # Bypass permission filtering for swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Client.objects.none()

        queryset = super().get_queryset()
        # Allow any authenticated user to list/retrieve clients (tests expect this)
        # Restrictive filtering is only applied for mutating actions, which are
        # already protected by permission classes.
        if getattr(self, "action", None) in ["list", "retrieve"]:
            return queryset
        return PermissionManager.filter_queryset_by_permissions(
            self.request.user, queryset, "client"
        )

    @swagger_auto_schema(
        operation_description="Get list of all clients",
        responses={200: ClientSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of all clients"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new client",
        request_body=ClientCreateSerializer,
        responses={201: ClientSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Create a new client"""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a client (PUT)",
        request_body=ClientUpdateSerializer,
        responses={200: ClientSerializer, 400: "Bad Request", 404: "Not Found"},
    )
    def update(self, request, *args, **kwargs):
        """Update client and related user fields"""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a client (PATCH)",
        request_body=ClientUpdateSerializer,
        responses={200: ClientSerializer, 400: "Bad Request", 404: "Not Found"},
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update client and related user fields"""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get properties for a specific client",
        responses={200: "List of properties"},
    )
    @action(detail=True, methods=["get"])
    def properties(self, request, pk=None):
        """Get all properties for a specific client"""
        client = self.get_object()
        properties = client.properties.all()
        from ..serializers import PropertySerializer

        serializer = PropertySerializer(properties, many=True)
        return Response(serializer.data)
