from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import IsClientOwner

from ..models import GuardPropertyTariff
from ..serializers import GuardPropertyTariffSerializer


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

    queryset = GuardPropertyTariff.objects.all().order_by("-id")
    serializer_class = GuardPropertyTariffSerializer

    def get_permissions(self):
        """Return permissions based on action"""
        if self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsClientOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user role and ownership"""
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
        operation_description="Create a new guard-property tariff",
        request_body=GuardPropertyTariffSerializer,
        responses={201: GuardPropertyTariffSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

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
