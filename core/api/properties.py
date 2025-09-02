from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.models import ResourcePermission
from permissions.permissions import create_resource_permission
from permissions.utils import PermissionManager

from ..models import Client, Property
from ..serializers import (
    PropertyDetailSerializer,
    PropertyGuardsShiftsSerializer,
    PropertySerializer,
)


class PropertyViewSet(
    SoftDeleteMixin, FilterMixin, BulkActionMixin, viewsets.ModelViewSet
):
    """
    ViewSet for managing Property model with full CRUD operations.

    list: Returns a list of all properties
    create: Creates a new property
    retrieve: Returns property details by ID
    update: Updates property information (PUT)
    partial_update: Partially updates property information (PATCH)
    destroy: Deletes a property
    """

    queryset = Property.objects.all().order_by("id")
    # Enable global search and ordering
    search_fields = [
        "name",
        "alias",
        "address",
        "owner__user__username",
        "owner__user__first_name",
        "owner__user__last_name",
        "owner__user__email",
    ]
    ordering_fields = [
        "id",
        "name",
        "alias",
        "contract_start_date",
    ]

    def get_permissions(self):
        """Return permissions based on action using resource permissions."""
        base = [permissions.IsAuthenticated]

        # Map actions to resource permission actions
        if self.action == "create":
            # Creation remains allowed for authenticated users with a Client profile.
            # Owner is set in perform_create(). No explicit resource permission required here.
            return [p() for p in base]
        elif self.action in ["update", "partial_update", "restore"]:
            Perm = create_resource_permission("property", action="update")
            base.append(Perm)
        elif self.action in ["destroy", "soft_delete"]:
            Perm = create_resource_permission("property", action="delete")
            base.append(Perm)
        elif self.action == "retrieve" or self.action == "list":
            Perm = create_resource_permission("property", action="read")
            base.append(Perm)
        else:
            # Default to read for any other actions
            Perm = create_resource_permission("property", action="read")
            base.append(Perm)

        return [p() for p in base]

    def get_serializer_class(self):
        """Return the appropriate serializer class based on action"""
        if self.action == "retrieve":
            return PropertyDetailSerializer
        return PropertySerializer

    def get_queryset(self):
        """Filter queryset based on role-based permissions and explicit resource grants.

        - Keeps SoftDeleteMixin behavior (include_inactive toggle).
        - Expands access for detail actions if user has explicit ResourcePermission
          on specific properties (read/update/delete).
        """
        base_qs = super().get_queryset()
        qs = PermissionManager.filter_queryset_by_permissions(
            self.request.user, base_qs, "property"
        )

        # For detail-type actions, include objects the user has explicit resource permission for
        action = getattr(self, "action", None)
        if action in {
            "retrieve",
            "update",
            "partial_update",
            "destroy",
            "soft_delete",
            "restore",
        }:
            if action == "retrieve":
                needed_actions = ["read"]
            elif action in {"update", "partial_update", "restore"}:
                needed_actions = ["update"]
            else:  # destroy, soft_delete
                needed_actions = ["delete"]

            rp = ResourcePermission.objects.filter(
                user=self.request.user,
                is_active=True,
                resource_type="property",
                action__in=needed_actions,
            )

            # If user has a global permission (resource_id is null), allow all
            if rp.filter(resource_id__isnull=True).exists():
                qs = (qs | base_qs).distinct()
            else:
                ids = list(
                    rp.filter(resource_id__isnull=False).values_list(
                        "resource_id", flat=True
                    )
                )
                if ids:
                    include_inactive = (
                        self.request.query_params.get(
                            "include_inactive", "false"
                        ).lower()
                        == "true"
                    )
                    manager = (
                        Property.all_objects if include_inactive else Property.objects
                    )
                    extra_qs = manager.filter(id__in=ids)
                    qs = (qs | extra_qs).distinct()

        return qs

    def perform_create(self, serializer):
        """
        Create property owned by:
        - The authenticated user's Client profile, if it exists; otherwise
        - The Client specified by 'owner' when the user has Django add permission.
        """
        user = self.request.user

        # Case 1: authenticated user is a Client -> force owner to self
        client = getattr(user, "client", None)
        if client:
            serializer.save(owner=client)
            return

        # Case 2: user has Django model add permission -> require owner in payload
        if user.has_perm("core.add_property"):
            owner_id = self.request.data.get("owner")
            if not owner_id:
                raise ValidationError({"owner": "Owner (Client id) is required."})
            # Validate owner exists
            target_client = Client.objects.filter(pk=owner_id).first()
            if not target_client:
                raise ValidationError({"owner": "Owner not found."})

            # Enforce alias uniqueness per owner early to return 400 instead of DB error
            alias = serializer.validated_data.get("alias")
            if alias:
                exists = Property.objects.filter(
                    owner=target_client, alias=alias
                ).exists()
                if exists:
                    raise ValidationError(
                        {"alias": "Alias must be unique for this owner."}
                    )

            serializer.save(owner=target_client)
            return

        # Otherwise, reject
        raise ValidationError(
            "Only clients or users with add permission can create properties"
        )

    @swagger_auto_schema(
        operation_description="Get list of all properties",
        responses={200: PropertySerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of all properties"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description=(
            "Create a new property. If the authenticated user is not a Client but has "
            "Django permission 'core.add_property', you must include 'owner' (Client id)."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["address"],
            properties={
                "owner": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description=(
                        "Client id. Required for non-client users with 'core.add_property'. "
                        "Ignored when the caller is a Client (owner is forced to self)."
                    ),
                ),
                "address": openapi.Schema(type=openapi.TYPE_STRING),
                "alias": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    nullable=True,
                    description=(
                        "Unique per owner; blank/empty values are normalized to null."
                    ),
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                "contract_start_date": openapi.Schema(
                    type=openapi.TYPE_STRING, format="date"
                ),
            },
        ),
        responses={201: PropertySerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Create a new property"""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get shifts for a specific property",
        responses={200: "List of shifts"},
    )
    @action(detail=True, methods=["get"])
    def shifts(self, request, pk=None):
        """Get all shifts for a specific property"""
        property_obj = self.get_object()
        shifts = property_obj.shifts.all()
        from ..serializers import ShiftSerializer

        serializer = ShiftSerializer(shifts, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get expenses for a specific property",
        responses={200: "List of expenses"},
    )
    @action(detail=True, methods=["get"])
    def expenses(self, request, pk=None):
        """Get all expenses for a specific property"""
        property_obj = self.get_object()
        expenses = property_obj.expenses.all()
        from ..serializers import ExpenseSerializer

        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get guards and shifts associated with a specific property",
        responses={200: PropertyGuardsShiftsSerializer, 404: "Not Found"},
    )
    @action(detail=True, methods=["get"], url_path="guards-shifts")
    def guards_shifts(self, request, pk=None):
        """Get guards and shifts associated with a specific property"""
        property_obj = self.get_object()
        serializer = PropertyGuardsShiftsSerializer(property_obj)
        return Response(serializer.data)
