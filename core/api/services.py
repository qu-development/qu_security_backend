from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import create_resource_permission

from ..models import Service
from ..serializers import (
    ServiceCreateSerializer,
    ServiceSerializer,
    ServiceUpdateSerializer,
)
from ..serializers.shifts import ShiftSerializer


class ServiceViewSet(
    SoftDeleteMixin, FilterMixin, BulkActionMixin, viewsets.ModelViewSet
):
    """
    ViewSet for managing Service model with full CRUD operations.

    list: Returns a list of all services
    create: Creates a new service
    retrieve: Returns service details by ID
    update: Updates service information (PUT)
    partial_update: Partially updates service information (PATCH)
    destroy: Deletes a service
    """

    queryset = (
        Service.objects.select_related("guard__user", "assigned_property__owner__user")
        .prefetch_related("shifts")
        .all()
        .order_by("id")
    )
    serializer_class = ServiceSerializer
    search_fields = [
        "name",
        "description",
        "guard__user__username",
        "assigned_property__name",
    ]
    ordering_fields = ["id", "name", "rate", "monthly_budget"]

    def get_permissions(self):
        """Return permissions based on action using resource permissions."""
        base = [permissions.IsAuthenticated]

        # Map actions to resource permission actions
        if self.action == "create":
            Perm = create_resource_permission("service", action="create")
            base.append(Perm)
        elif self.action in ["update", "partial_update"]:
            Perm = create_resource_permission("service", action="update")
            base.append(Perm)
        elif self.action == "destroy":
            Perm = create_resource_permission("service", action="delete")
            base.append(Perm)
        elif self.action in ["retrieve", "list"]:
            Perm = create_resource_permission("service", action="read")
            base.append(Perm)
        else:
            # Default to read for any other actions
            Perm = create_resource_permission("service", action="read")
            base.append(Perm)

        return [p() for p in base]

    def get_serializer_class(self):
        if self.action == "create":
            return ServiceCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ServiceUpdateSerializer
        return ServiceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    @swagger_auto_schema(
        operation_description="Get list of all services",
        responses={200: ServiceSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new service",
        request_body=ServiceCreateSerializer,
        responses={201: ServiceSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return the created instance using ServiceSerializer to include total_hours
        response_serializer = ServiceSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update service information (full update)",
        request_body=ServiceUpdateSerializer,
        responses={200: ServiceSerializer, 400: "Bad Request", 404: "Not Found"},
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        # Return the updated instance using ServiceSerializer to include total_hours
        response_serializer = ServiceSerializer(updated_instance)
        return Response(response_serializer.data)

    @swagger_auto_schema(
        operation_description="Partially update service information",
        request_body=ServiceUpdateSerializer,
        responses={200: ServiceSerializer, 400: "Bad Request"},
    )
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        # Return the updated instance using ServiceSerializer to include total_hours
        response_serializer = ServiceSerializer(updated_instance)
        return Response(response_serializer.data)

    @swagger_auto_schema(
        operation_description="Delete a service (soft delete)",
        responses={204: "No Content"},
    )
    def destroy(self, request, *args, **kwargs):
        """Soft delete a service instead of hard delete"""
        from common.utils import ModelHelper

        obj = self.get_object()
        ModelHelper.soft_delete_object(obj)
        return Response(status=204)

    @swagger_auto_schema(
        operation_description="Get shifts for a specific service",
        responses={200: ShiftSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def shifts(self, request, pk=None):
        """Get all shifts for a specific service"""
        service = self.get_object()
        # Optimizar la consulta de shifts con select_related
        shifts = (
            service.shifts.select_related(
                "guard__user",
                "property",  # Corregido: es 'property', no 'assigned_property'
                "service",
            )
            .all()
            .order_by("-start_time")
        )

        serializer = ShiftSerializer(shifts, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get services by property",
        responses={200: ServiceSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def by_property(self, request):
        """Filter services by property"""
        property_id = request.query_params.get("property_id")
        if not property_id:
            return Response({"error": "property_id parameter is required"}, status=400)

        services = self.get_queryset().filter(assigned_property_id=property_id)
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get services by guard",
        responses={200: ServiceSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def by_guard(self, request):
        """Filter services by guard"""
        guard_id = request.query_params.get("guard_id")
        if not guard_id:
            return Response({"error": "guard_id parameter is required"}, status=400)

        services = self.get_queryset().filter(guard_id=guard_id)
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)
