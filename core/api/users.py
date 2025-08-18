from django.contrib.auth.models import User
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


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
    # Enable global search and ordering
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
    ]
    ordering_fields = [
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "date_joined",
    ]

    def get_queryset(self):
        qs = super().get_queryset()
        # Restrict the list endpoint to only staff or superusers
        if getattr(self, "action", None) == "list":
            return qs.filter(Q(is_superuser=True) | Q(is_staff=True))
        return qs

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
        operation_description=(
            "Get list of users. Note: only users with is_staff=True or "
            "is_superuser=True are returned."
        ),
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
