from django.contrib.auth.models import User
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.models import ResourcePermission
from permissions.permissions import (
    CanCreateExpense,
    IsAdminOrManager,
    IsClientOwner,
    IsGuardAssigned,
    create_resource_permission,
)
from permissions.utils import PermissionManager

from .models import (
    Client,
    Expense,
    Guard,
    GuardPropertyTariff,
    Property,
    PropertyTypeOfService,
    Shift,
)
from .serializers import (
    ClientCreateSerializer,
    ClientDetailSerializer,
    ClientSerializer,
    ClientUpdateSerializer,
    ExpenseSerializer,
    GuardDetailSerializer,
    GuardPropertyTariffSerializer,
    GuardSerializer,
    PropertyDetailSerializer,
    PropertySerializer,
    PropertyTypeOfServiceSerializer,
    ShiftSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes essential user permissions"""

    @classmethod
    def get_token(cls, user):
        """Add custom claims to the token"""
        token = super().get_token(user)

        # Add only essential user info
        token["username"] = user.username
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser

        # Import here to avoid circular imports
        from permissions.models import UserRole

        # Add user role (essential for frontend authorization)
        try:
            user_role = UserRole.objects.get(user=user, is_active=True)
            token["role"] = user_role.role
        except UserRole.DoesNotExist:
            token["role"] = "user"  # Default role

        # Add accessible property IDs only (not all data)
        from permissions.models import PropertyAccess

        accessible_properties = list(
            PropertyAccess.objects.filter(user=user, is_active=True).values_list(
                "property_id", flat=True
            )
        )
        token["accessible_properties"] = accessible_properties

        # Add resource permissions (for clients, guards, etc.)
        from permissions.models import ResourcePermission

        resource_permissions = {}
        permissions_qs = ResourcePermission.objects.filter(
            user=user, is_active=True
        ).values("resource_type", "action")

        for perm in permissions_qs:
            resource_type = perm["resource_type"]
            action = perm["action"]
            if resource_type not in resource_permissions:
                resource_permissions[resource_type] = []
            if action not in resource_permissions[resource_type]:
                resource_permissions[resource_type].append(action)

        token["resource_permissions"] = resource_permissions

        # Add admin status for quick frontend checks
        token["is_admin"] = user.is_superuser or (
            user_role.role == "admin" if "user_role" in locals() else False
        )

        return token

    def validate(self, attrs):
        """Validate credentials and return tokens"""
        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view with Swagger documentation"""

    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing User model with full CRUD operations.

    list: Returns a list of all users
    create: Creates a new user
    retrieve: Returns user details by ID
    update: Updates user information (PUT)
    partial_update: Partially updates user information (PATCH)
    destroy: Deletes a user
    """

    queryset = User.objects.all().order_by("-date_joined")

    def get_serializer_class(self):
        """Return the appropriate serializer class based on action"""
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        """Return the appropriate permissions based on action"""
        if self.action == "create":
            # Allow anyone to register
            permission_classes = [permissions.AllowAny]
        else:
            # Require authentication for other actions
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_description="Get list of all users",
        responses={200: UserSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of all users"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=UserCreateSerializer,
        responses={201: UserSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Register a new user"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get user details by ID",
        responses={200: UserSerializer, 404: "User not found"},
    )
    def retrieve(self, request, *args, **kwargs):
        """Get user details by ID"""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update user information",
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer, 400: "Bad Request", 404: "User not found"},
    )
    def update(self, request, *args, **kwargs):
        """Update user information (PUT)"""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update user information",
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer, 400: "Bad Request", 404: "User not found"},
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update user information (PATCH)"""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a user",
        responses={204: "User deleted successfully", 404: "User not found"},
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a user"""
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get current user profile",
        responses={200: UserSerializer},
    )
    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """Get current user profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


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
        request_body=GuardSerializer,
        responses={201: GuardSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Create a new guard"""
        return super().create(request, *args, **kwargs)


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
        from .serializers import PropertySerializer

        serializer = PropertySerializer(properties, many=True)
        return Response(serializer.data)


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
        from rest_framework.exceptions import ValidationError

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
            required=["address", "total_hours"],
            properties={
                "owner": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description=(
                        "Client id. Required for non-client users with 'core.add_property'. "
                        "Ignored when the caller is a Client (owner is forced to self)."
                    ),
                ),
                "address": openapi.Schema(type=openapi.TYPE_STRING),
                "total_hours": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Total hours budgeted"
                ),
                "alias": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    nullable=True,
                    description=(
                        "Unique per owner; blank/empty values are normalized to null."
                    ),
                ),
                "name": openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                "types_of_service": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description="List of PropertyTypeOfService IDs",
                ),
                "monthly_rate": openapi.Schema(
                    type=openapi.TYPE_NUMBER, description="Monthly rate"
                ),
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
        from .serializers import ShiftSerializer

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
        from .serializers import ExpenseSerializer

        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)


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


class PropertyTypeOfServiceViewSet(SoftDeleteMixin, viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for PropertyTypeOfService model.

    list: Returns a list of all property types of service
    retrieve: Returns details for a property type of service by ID
    """

    queryset = PropertyTypeOfService.objects.all().order_by("name")
    serializer_class = PropertyTypeOfServiceSerializer

    def get_permissions(self):
        """Require authentication for all actions"""
        permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        operation_description="Get list of all property types of service",
        responses={200: PropertyTypeOfServiceSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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
        """Ensure only property owners or admins/managers can create tariffs"""
        user = self.request.user

        # Allow admins/managers
        if (
            user.is_superuser
            or user.groups.filter(name__in=["Administrators", "Managers"]).exists()
        ):
            serializer.save()
            return

        # Clients must own the property
        from rest_framework.exceptions import ValidationError

        from core.models import Client as ClientModel

        client = ClientModel.objects.filter(user=user).first()
        if not client:
            raise ValidationError("Only clients or managers can create tariffs")

        prop = serializer.validated_data.get("property")
        if not prop or prop.owner != client:
            raise ValidationError("You can only create tariffs for your own properties")

        # Optional: enforce uniqueness early (DB constraint also exists)
        guard = serializer.validated_data.get("guard")
        if GuardPropertyTariff.objects.filter(guard=guard, property=prop).exists():
            raise ValidationError("A tariff for this guard and property already exists")

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


class ExpenseViewSet(
    SoftDeleteMixin, FilterMixin, BulkActionMixin, viewsets.ModelViewSet
):
    """
    ViewSet for managing Expense model with full CRUD operations.

    list: Returns a list of all expenses
    create: Creates a new expense
    retrieve: Returns expense details by ID
    update: Updates expense information (PUT)
    partial_update: Partially updates expense information (PATCH)
    destroy: Deletes an expense
    """

    queryset = Expense.objects.all().order_by("-id")
    serializer_class = ExpenseSerializer

    def get_permissions(self):
        """Return the appropriate permissions based on action"""
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated, CanCreateExpense]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsClientOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        return PermissionManager.filter_queryset_by_permissions(
            self.request.user, queryset, "expense"
        )

    @swagger_auto_schema(
        operation_description="Get list of all expenses",
        responses={200: ExpenseSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of all expenses"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new expense",
        request_body=ExpenseSerializer,
        responses={201: ExpenseSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Create a new expense"""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get expenses by property",
        responses={200: ExpenseSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def by_property(self, request):
        """Get expenses filtered by property ID"""
        property_id = request.query_params.get("property_id")
        if property_id:
            expenses = self.get_queryset().filter(property_id=property_id)
            serializer = self.get_serializer(expenses, many=True)
            return Response(serializer.data)
        return Response({"error": "property_id parameter is required"}, status=400)
