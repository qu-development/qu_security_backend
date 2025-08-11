"""
Permission-enabled ViewSets for QU Security Backend
"""

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Client, Expense, Guard, Property, Shift
from core.serializers import (
    ClientSerializer,
    ExpenseSerializer,
    GuardSerializer,
    PropertySerializer,
    ShiftSerializer,
    UserSerializer,
)

from .models import PermissionLog, PropertyAccess, UserRole
from .permissions import (
    CanCreateExpense,
    CanCreateShift,
    IsAdminOrManager,
    IsClientOwner,
    IsGuardAssigned,
    IsOwnerOrManager,
)
from .utils import (
    PermissionManager,
    filter_queryset_by_permissions,
    permission_required,
)


class PermissionAwareViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet with permission checking and queryset filtering
    """

    def get_permissions(self):
        """
        Get permissions based on action
        """
        permission_classes = [permissions.IsAuthenticated]

        # Add specific permissions based on action
        if self.action == "create":
            permission_classes.extend(self.get_create_permissions())
        elif self.action in ["update", "partial_update"]:
            permission_classes.extend(self.get_update_permissions())
        elif self.action == "destroy":
            permission_classes.extend(self.get_delete_permissions())
        else:
            permission_classes.extend(self.get_read_permissions())

        return [permission() for permission in permission_classes]

    def get_create_permissions(self):
        return []

    def get_read_permissions(self):
        return []

    def get_update_permissions(self):
        return []

    def get_delete_permissions(self):
        return []

    def get_queryset(self):
        """
        Filter queryset based on user permissions
        """
        queryset = super().get_queryset()
        return filter_queryset_by_permissions(
            self.request.user, queryset, self.get_model_name()
        )

    def get_model_name(self):
        """
        Get model name for permission checking
        """
        return self.queryset.model.__name__.lower()

    def perform_create(self, serializer):
        """
        Log permission usage when creating objects
        """
        instance = serializer.save()
        PermissionLog.objects.create(
            user=self.request.user,
            permission_type=f"{self.get_model_name()}_create",
            permission_details={
                "action": "create",
                "resource_type": self.get_model_name(),
                "resource_id": instance.id,
            },
            action="granted",
            performed_by=self.request.user,
            timestamp=timezone.now(),
        )

    def perform_update(self, serializer):
        """
        Log permission usage when updating objects
        """
        instance = serializer.save()
        PermissionLog.objects.create(
            user=self.request.user,
            permission_type=f"{self.get_model_name()}_update",
            permission_details={
                "action": "update",
                "resource_type": self.get_model_name(),
                "resource_id": instance.id,
            },
            action="granted",
            performed_by=self.request.user,
            timestamp=timezone.now(),
        )

    def perform_destroy(self, instance):
        """
        Log permission usage when deleting objects
        """
        PermissionLog.objects.create(
            user=self.request.user,
            permission_type=f"{self.get_model_name()}_delete",
            permission_details={
                "action": "delete",
                "resource_type": self.get_model_name(),
                "resource_id": instance.id,
            },
            action="granted",
            performed_by=self.request.user,
            timestamp=timezone.now(),
        )
        super().perform_destroy(instance)


class UserViewSetWithPermissions(PermissionAwareViewSet):
    """
    ViewSet for User model with permission controls
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_create_permissions(self):
        return [IsAdminOrManager]

    def get_read_permissions(self):
        return []  # All authenticated users can read

    def get_update_permissions(self):
        return [IsOwnerOrManager]

    def get_delete_permissions(self):
        return [IsAdminOrManager]

    @action(detail=True, methods=["post"])
    @permission_required("user", "update")
    def assign_role(self, request, pk=None):
        """
        Assign role to user (Admin/Manager only)
        """
        user = self.get_object()
        role = request.data.get("role")

        if not role or role not in [choice[0] for choice in UserRole.ROLE_CHOICES]:
            return Response(
                {"error": "Valid role is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        user_role = PermissionManager.assign_user_role(user, role, request.user)

        return Response(
            {
                "message": f"Role {role} assigned to user {user.username}",
                "role": user_role.role,
                "role_display": user_role.get_role_display(),
            }
        )

    @action(detail=True, methods=["get"])
    def permissions(self, request, pk=None):
        """
        Get user permissions
        """
        user = self.get_object()

        # Only allow users to see their own permissions or admins/managers
        if (
            user != request.user
            and not request.user.groups.filter(
                name__in=["Administrators", "Managers"]
            ).exists()
        ):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Get user permissions summary
        permissions_data = {
            "user_id": user.id,
            "username": user.username,
            "role": None,
            "resource_permissions": [],
            "property_access": [],
        }

        # Get user role
        try:
            user_role = UserRole.objects.get(user=user, is_active=True)
            permissions_data["role"] = {
                "role": user_role.role,
                "display": user_role.get_role_display(),
            }
        except UserRole.DoesNotExist:
            pass

        # Get resource permissions
        for perm in user.resource_permissions.filter(is_active=True):
            permissions_data["resource_permissions"].append(
                {
                    "resource_type": perm.resource_type,
                    "action": perm.action,
                    "resource_id": perm.resource_id,
                }
            )

        # Get property access
        for access in user.property_access.filter(is_active=True):
            permissions_data["property_access"].append(
                {
                    "property_id": access.property.id,
                    "property_address": access.property.address,
                    "access_type": access.access_type,
                }
            )

        return Response(permissions_data)


class GuardViewSetWithPermissions(PermissionAwareViewSet):
    """
    ViewSet for Guard model with permission controls
    """

    queryset = Guard.objects.all()
    serializer_class = GuardSerializer

    def get_create_permissions(self):
        return [IsAdminOrManager]

    def get_read_permissions(self):
        return []  # Filtered by queryset

    def get_update_permissions(self):
        return [IsOwnerOrManager]

    def get_delete_permissions(self):
        return [IsAdminOrManager]

    def get_queryset(self):
        """
        Filter guards based on user role
        """
        queryset = super().get_queryset()

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(
                name__in=["Administrators", "Managers"]
            ).exists()
        ):
            return queryset

        # Guards can only see themselves
        try:
            guard = Guard.objects.get(user=self.request.user)
            return queryset.filter(id=guard.id)
        except Guard.DoesNotExist:
            return queryset.none()


class ClientViewSetWithPermissions(PermissionAwareViewSet):
    """
    ViewSet for Client model with permission controls
    """

    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def get_create_permissions(self):
        return [IsAdminOrManager]

    def get_read_permissions(self):
        return []  # Filtered by queryset

    def get_update_permissions(self):
        return [IsOwnerOrManager]

    def get_delete_permissions(self):
        return [IsAdminOrManager]

    def get_queryset(self):
        """
        Filter clients based on user role
        """
        queryset = super().get_queryset()

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(
                name__in=["Administrators", "Managers"]
            ).exists()
        ):
            return queryset

        # Clients can only see themselves
        try:
            client = Client.objects.get(user=self.request.user)
            return queryset.filter(id=client.id)
        except Client.DoesNotExist:
            return queryset.none()


class PropertyViewSetWithPermissions(PermissionAwareViewSet):
    """
    ViewSet for Property model with permission controls
    """

    queryset = Property.objects.all()
    serializer_class = PropertySerializer

    def get_create_permissions(self):
        return [IsAdminOrManager]

    def get_read_permissions(self):
        return []  # Filtered by queryset

    def get_update_permissions(self):
        return [IsClientOwner]

    def get_delete_permissions(self):
        return [IsAdminOrManager]

    def get_queryset(self):
        """
        Filter properties based on user role and access
        """
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_superuser
            or user.groups.filter(name__in=["Administrators", "Managers"]).exists()
        ):
            return queryset

        # Clients see their own properties
        try:
            client = Client.objects.get(user=user)
            return queryset.filter(owner=client)
        except Client.DoesNotExist:
            pass

        # Guards see properties they have access to
        try:
            Guard.objects.get(user=user)
            accessible_properties = PropertyAccess.objects.filter(
                user=user, is_active=True
            ).values_list("property", flat=True)
            return queryset.filter(id__in=accessible_properties)
        except Guard.DoesNotExist:
            pass

        return queryset.none()

    @action(detail=True, methods=["post"])
    @permission_required("property", "update")
    def grant_access(self, request, pk=None):
        """
        Grant property access to a user (Client/Admin/Manager only)
        """
        property_obj = self.get_object()
        user_id = request.data.get("user_id")
        access_type = request.data.get("access_type", "viewer")
        permissions = request.data.get("permissions", {})

        if not user_id:
            return Response(
                {"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if requester can grant access to this property
        if not IsClientOwner().has_object_permission(request, self, property_obj):
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        # Create property access
        property_access = PermissionManager.grant_property_access(
            target_user, property_obj, access_type, permissions, request.user
        )

        return Response(
            {
                "message": f"Access granted to {target_user.username}",
                "access_type": access_type,
                "access_id": property_access.id,
            }
        )


class ShiftViewSetWithPermissions(PermissionAwareViewSet):
    """
    ViewSet for Shift model with permission controls
    """

    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer

    def get_create_permissions(self):
        return [CanCreateShift]

    def get_read_permissions(self):
        return []  # Filtered by queryset

    def get_update_permissions(self):
        return [IsGuardAssigned]

    def get_delete_permissions(self):
        return [IsAdminOrManager]

    def get_queryset(self):
        """
        Filter shifts based on user role
        """
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_superuser
            or user.groups.filter(name__in=["Administrators", "Managers"]).exists()
        ):
            return queryset

        # Guards see their own shifts
        try:
            guard = Guard.objects.get(user=user)
            return queryset.filter(guard=guard)
        except Guard.DoesNotExist:
            pass

        # Clients see shifts for their properties
        try:
            client = Client.objects.get(user=user)
            return queryset.filter(property__owner=client)
        except Client.DoesNotExist:
            pass

        return queryset.none()


class ExpenseViewSetWithPermissions(PermissionAwareViewSet):
    """
    ViewSet for Expense model with permission controls
    """

    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def get_create_permissions(self):
        return [CanCreateExpense]

    def get_read_permissions(self):
        return []  # Filtered by queryset

    def get_update_permissions(self):
        return [IsClientOwner]

    def get_delete_permissions(self):
        return [IsClientOwner]

    def get_queryset(self):
        """
        Filter expenses based on user role
        """
        queryset = super().get_queryset()
        user = self.request.user

        if (
            user.is_superuser
            or user.groups.filter(name__in=["Administrators", "Managers"]).exists()
        ):
            return queryset

        # Clients see expenses for their properties
        try:
            client = Client.objects.get(user=user)
            return queryset.filter(property__owner=client)
        except Client.DoesNotExist:
            pass

        return queryset.none()


# Simplified permission management for general use
class PermissionManagementViewSet(viewsets.ViewSet):
    """
    Basic permission management (Admin/Manager only)
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminOrManager]

    @action(detail=False, methods=["get"])
    def audit_log(self, request):
        """
        Get permission audit log (simplified)
        """
        logs = PermissionLog.objects.all().order_by("-timestamp")[:50]

        log_data = []
        for log in logs:
            log_data.append(
                {
                    "user": log.user.username,
                    "permission_type": log.permission_type,
                    "action": log.action,
                    "timestamp": log.timestamp,
                    "performed_by": log.performed_by.username,
                    "reason": log.reason,
                }
            )

        return Response(log_data)
