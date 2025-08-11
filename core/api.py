from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import (
    CanCreateExpense,
    CanCreateShift,
    IsAdminOrManager,
    IsClientOwner,
    IsGuardAssigned,
)
from permissions.utils import PermissionManager

from .models import Client, Expense, Guard, Property, Shift
from .serializers import (
    ClientDetailSerializer,
    ClientSerializer,
    ExpenseSerializer,
    GuardDetailSerializer,
    GuardSerializer,
    PropertyDetailSerializer,
    PropertySerializer,
    ShiftSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes user information"""

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user information to the response
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        return data


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
        if self.action == "retrieve":
            return ClientDetailSerializer
        return ClientSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
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
        request_body=ClientSerializer,
        responses={201: ClientSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Create a new client"""
        return super().create(request, *args, **kwargs)

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
        """Return the appropriate permissions based on action"""
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated]
        elif (
            self.action in ["update", "partial_update", "destroy"]
            or self.action == "retrieve"
        ):
            permission_classes = [permissions.IsAuthenticated, IsClientOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Return the appropriate serializer class based on action"""
        if self.action == "retrieve":
            return PropertyDetailSerializer
        return PropertySerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        return PermissionManager.filter_queryset_by_permissions(
            self.request.user, queryset, "property"
        )

    def perform_create(self, serializer):
        """Set the owner to the current user's client profile"""
        try:
            client = self.request.user.client
            serializer.save(owner=client)
        except Exception:
            # If the user doesn't have a client profile, raise an error
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Only clients can create properties")

    @swagger_auto_schema(
        operation_description="Get list of all properties",
        responses={200: PropertySerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of all properties"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new property",
        request_body=PropertySerializer,
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
            permission_classes = [permissions.IsAuthenticated, CanCreateShift]
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
