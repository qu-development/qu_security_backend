import logging

from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import IsClientOwner

from ..models import GuardPropertyTariff
from ..serializers import (
    GuardPropertyTariffCreateSerializer,
    GuardPropertyTariffSerializer,
)

logger = logging.getLogger(__name__)


class GuardPropertyTariffViewSet(
    SoftDeleteMixin, FilterMixin, BulkActionMixin, viewsets.ModelViewSet
):
    """
    ViewSet for managing GuardPropertyTariff with full CRUD operations.

    list: Returns a list of tariffs filtered by user role
    create: Creates a new tariff for a guard at a property
    retrieve: Returns tariff details by ID
    update: Updates tariff information (PUT)
    partial_update: Partially updates tariff information (PATCH)
    destroy: Deletes a tariff
    by_guard: Returns tariffs filtered by guard_id
    by_property: Returns tariffs filtered by property_id
    """

    queryset = (
        GuardPropertyTariff.objects.select_related(
            "guard__user",  # To access guard information
            "property__owner__user",  # To access property owner client information
        )
        .all()
        .order_by("-id")
    )
    serializer_class = GuardPropertyTariffSerializer

    def get_serializer_class(self):
        # Use a minimal serializer on create to only accept guard, property, and rate
        if self.action == "create":
            return GuardPropertyTariffCreateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        """Return permissions based on action"""
        if self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsClientOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user role and ownership"""
        # Bypass permission filtering for swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return GuardPropertyTariff.objects.none()

        qs = super().get_queryset()
        user = self.request.user

        # Admins and managers see everything
        if (
            user.is_superuser
            or user.groups.filter(name__in=["Administrators", "Managers"]).exists()
        ):
            return qs

        # Clients: tariffs for their properties only
        from core.models import Client as ClientModel
        from core.models import Guard as GuardModel

        client = ClientModel.objects.filter(user=user).first()
        if client:
            return qs.filter(property__owner=client)

        # Guards: tariffs assigned to them
        guard = GuardModel.objects.filter(user=user).first()
        if guard:
            return qs.filter(guard=guard)

        # Others: none
        return qs.none()

    def perform_create(self, serializer):
        """Ensure only property owners or admins/managers can create tariffs.

        Also maintain history: only one active tariff per (guard, property).
        When creating a new tariff for the same pair, deactivate the previous
        active tariff instead of raising an error.
        """
        user = self.request.user
        is_admin_mgr = (
            user.is_superuser
            or user.groups.filter(name__in=["Administrators", "Managers"]).exists()
        )

        # Clients must own the property
        from rest_framework.exceptions import ValidationError

        from core.models import Client as ClientModel

        if not is_admin_mgr:
            client = ClientModel.objects.filter(user=user).first()
            if not client:
                raise ValidationError("Only clients or managers can create tariffs")

            prop = serializer.validated_data.get("property")
            if not prop or prop.owner != client:
                raise ValidationError(
                    "You can only create tariffs for your own properties"
                )
        else:
            # Admin/manager path: just use provided property
            prop = serializer.validated_data.get("property")

        # Maintain a single active tariff per guard+property.
        # Deactivate any existing active tariff only if the new one is active.
        guard = serializer.validated_data.get("guard")
        new_active = serializer.validated_data.get("is_active", True)
        if guard and prop and new_active:
            GuardPropertyTariff.objects.filter(
                guard=guard, property=prop, is_active=True
            ).update(is_active=False)

        serializer.save()

    def perform_update(self, serializer):
        """Ensure only one active tariff exists per (guard, property) on update."""
        instance = self.get_object()
        validated = serializer.validated_data

        guard = validated.get("guard", instance.guard)
        prop = validated.get("property", instance.property)
        # If explicitly provided, use it; otherwise keep current
        new_active = validated.get("is_active", instance.is_active)

        # If the updated record should be active, deactivate other active ones for the pair
        if guard and prop and new_active:
            GuardPropertyTariff.objects.filter(
                guard=guard,
                property=prop,
                is_active=True,
            ).exclude(pk=instance.pk).update(is_active=False)

        serializer.save()

    @swagger_auto_schema(
        operation_description="Get list of all guard-property tariffs",
        responses={200: GuardPropertyTariffSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description=(
            "Create a new guard-property tariff. Preferred keys: guard_id, property_id, rate. "
            "Legacy keys 'guard' and 'property' are accepted (deprecated) while "
            "TARIFFS_ALLOW_LEGACY_KEYS=True."
        ),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            oneOf=[
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    required=["guard_id", "property_id", "rate"],
                    properties={
                        "guard_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="ID of the guard (preferred)",
                        ),
                        "property_id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="ID of the property (preferred)",
                        ),
                        "rate": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Decimal as string, e.g. '12.50'",
                        ),
                    },
                ),
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    required=["guard", "property", "rate"],
                    properties={
                        "guard": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="DEPRECATED. Use guard_id.",
                        ),
                        "property": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="DEPRECATED. Use property_id.",
                        ),
                        "rate": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Decimal as string, e.g. '12.50'",
                        ),
                    },
                    description="Deprecated legacy payload shape",
                ),
            ],
        ),
        responses={201: GuardPropertyTariffSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        # Accept legacy payload keys by mapping to the new schema
        # legacy: {"guard": <id>, "property": <id>, "rate": ".."}
        # new:    {"guard_id": <id>, "property_id": <id>, "rate": ".."}
        data = request.data.copy()
        used_legacy = False
        if getattr(settings, "TARIFFS_ALLOW_LEGACY_KEYS", True):
            if "guard" in data and "guard_id" not in data:
                data["guard_id"] = data["guard"]
                del data["guard"]
                used_legacy = True
            if "property" in data and "property_id" not in data:
                data["property_id"] = data["property"]
                del data["property"]
                used_legacy = True
            if used_legacy:
                logger.warning(
                    "Deprecated payload keys 'guard'/'property' used on tariffs create; "
                    "migrate to 'guard_id'/'property_id'. This compatibility will be removed in a future release."
                )
        else:
            # Explicitly reject legacy keys when feature flag is disabled
            if "guard" in data or "property" in data:
                raise ValidationError(
                    {
                        "non_field_errors": [
                            "Legacy payload keys 'guard'/'property' are not accepted. "
                            "Use 'guard_id' and 'property_id'."
                        ]
                    }
                )

        # Validate and create with the minimal create serializer
        create_serializer = self.get_serializer(data=data)
        create_serializer.is_valid(raise_exception=True)
        # Use perform_create to preserve business rules
        self.perform_create(create_serializer)
        instance = create_serializer.instance

        # Respond with the full read serializer
        read_serializer = GuardPropertyTariffSerializer(
            instance, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=201, headers=headers)

    @swagger_auto_schema(
        operation_description="Get tariffs by guard",
        responses={200: GuardPropertyTariffSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def by_guard(self, request):
        guard_id = request.query_params.get("guard_id")
        if guard_id:
            tariffs = self.get_queryset().filter(guard_id=guard_id)
            serializer = self.get_serializer(tariffs, many=True)
            return Response(serializer.data)
        return Response({"error": "guard_id parameter is required"}, status=400)

    @swagger_auto_schema(
        operation_description="Get tariffs by property",
        responses={200: GuardPropertyTariffSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def by_property(self, request):
        property_id = request.query_params.get("property_id")
        if property_id:
            tariffs = self.get_queryset().filter(property_id=property_id)
            serializer = self.get_serializer(tariffs, many=True)
            return Response(serializer.data)
        return Response({"error": "property_id parameter is required"}, status=400)
