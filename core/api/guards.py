from django.core.cache import cache
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
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
        # Bypass permission filtering for swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Guard.objects.none()

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

    @swagger_auto_schema(
        operation_description="Update guard real-time location and status",
        methods=["post"],
        manual_parameters=[
            openapi.Parameter(
                "guard_id",
                openapi.IN_QUERY,
                description="ID of the guard to update",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["lat", "lon", "is_on_shift"],
            properties={
                "lat": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Latitude coordinate",
                    example="40.7128",
                ),
                "lon": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Longitude coordinate",
                    example="-74.0060",
                ),
                "is_on_shift": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Whether the guard is currently on shift",
                    example=True,
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Location updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "guard_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "last_updated": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Bad Request - Invalid data or missing guard_id",
            404: "Guard not found",
        },
    )
    @action(detail=False, methods=["post"], url_path="update-location")
    def update_location(self, request):
        """Update guard real-time location and shift status"""
        try:
            # Get guard_id from query parameters
            guard_id = request.query_params.get("guard_id")
            if not guard_id:
                return Response(
                    {"error": "guard_id query parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate guard exists
            try:
                Guard.objects.get(id=guard_id)
            except Guard.DoesNotExist:
                return Response(
                    {"error": f"Guard with id {guard_id} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validate request data
            required_fields = ["lat", "lon", "is_on_shift"]
            for field in required_fields:
                if field not in request.data:
                    return Response(
                        {"error": f"Field '{field}' is required"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Validate latitude and longitude
            try:
                lat = float(request.data["lat"])
                lon = float(request.data["lon"])
                if not (-90 <= lat <= 90):
                    raise ValueError("Latitude must be between -90 and 90")
                if not (-180 <= lon <= 180):
                    raise ValueError("Longitude must be between -180 and 180")
            except (ValueError, TypeError) as e:
                return Response(
                    {"error": f"Invalid coordinates: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate is_on_shift
            is_on_shift = request.data["is_on_shift"]
            if not isinstance(is_on_shift, bool):
                return Response(
                    {"error": "is_on_shift must be a boolean"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prepare data for cache
            now = timezone.now()
            cache_data = {
                "lat": request.data["lat"],
                "lon": request.data["lon"],
                "is_on_shift": is_on_shift,
                "last_updated": now.isoformat(),
            }

            # Store in cache with the specified structure: guards_rts:{guard_id: data}
            cache_key = f"guards_rts:{guard_id}"

            # Set cache with maximum timeout (30 days = 2592000 seconds)
            # This is typically the maximum allowed by most cache backends
            cache.set(cache_key, cache_data, timeout=2592000)

            return Response(
                {
                    "success": True,
                    "message": "Guard location updated successfully",
                    "guard_id": int(guard_id),
                    "last_updated": now.isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_description="Get cached guard location data",
        methods=["get"],
        manual_parameters=[
            openapi.Parameter(
                "guard_id",
                openapi.IN_QUERY,
                description="ID of specific guard to get location for (optional - if not provided, returns all guards)",
                type=openapi.TYPE_INTEGER,
                required=False,
            )
        ],
        responses={
            200: openapi.Response(
                description="Cached location data retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Guard location data from cache",
                            additional_properties=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "lat": openapi.Schema(type=openapi.TYPE_STRING),
                                    "lon": openapi.Schema(type=openapi.TYPE_STRING),
                                    "is_on_shift": openapi.Schema(
                                        type=openapi.TYPE_BOOLEAN
                                    ),
                                    "last_updated": openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                },
                            ),
                        ),
                        "total_guards": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            404: "Guard not found or no cached data",
        },
    )
    @action(detail=False, methods=["get"], url_path="cached-locations")
    def cached_locations(self, request):
        """Get cached guard location data from Valkey"""
        try:
            guard_id = request.query_params.get("guard_id")

            if guard_id:
                # Get specific guard's cached location
                try:
                    # Validate guard exists
                    Guard.objects.get(id=guard_id)
                except Guard.DoesNotExist:
                    return Response(
                        {"error": f"Guard with id {guard_id} not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                cache_key = f"guards_rts:{guard_id}"
                cached_data = cache.get(cache_key)

                if not cached_data:
                    return Response(
                        {
                            "error": f"No cached location data found for guard {guard_id}"
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

                return Response(
                    {
                        "success": True,
                        "data": {guard_id: cached_data},
                        "total_guards": 1,
                    },
                    status=status.HTTP_200_OK,
                )

            else:
                # Get all guards' cached locations
                # First, get all guard IDs from the database
                all_guard_ids = list(Guard.objects.values_list("id", flat=True))

                cached_locations = {}
                for gid in all_guard_ids:
                    cache_key = f"guards_rts:{gid}"
                    cached_data = cache.get(cache_key)
                    if cached_data:
                        cached_locations[str(gid)] = cached_data

                return Response(
                    {
                        "success": True,
                        "data": cached_locations,
                        "total_guards": len(cached_locations),
                        "total_guards_in_db": len(all_guard_ids),
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
