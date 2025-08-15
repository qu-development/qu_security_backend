"""
Custom DRF permissions for QU Security Backend
"""

from rest_framework.permissions import BasePermission

from core.models import Client, Guard, Property

from .models import PropertyAccess, UserRole
from .utils import PermissionManager


class IsOwnerOrManager(BasePermission):
    """
    Custom permission to only allow owners of an object or managers to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Superusers and managers have full access
        if (
            request.user.is_superuser
            or request.user.groups.filter(
                name__in=["Administrators", "Managers"]
            ).exists()
        ):
            return True

        # Check if user owns the object
        if hasattr(obj, "user") and obj.user == request.user:
            return True

        return (
            hasattr(obj, "owner")
            and hasattr(obj.owner, "user")
            and obj.owner.user == request.user
        )


class HasResourcePermission(BasePermission):
    """
    Permission class that checks resource-specific permissions
    """

    def __init__(self, resource_type, action=None):
        self.resource_type = resource_type
        self.action = action

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # For detail actions, rely on object-level checks to allow owner-specific access
        detail_actions = {
            "retrieve",
            "update",
            "partial_update",
            "destroy",
            "soft_delete",
            "restore",
        }
        if getattr(view, "action", None) in detail_actions or "pk" in getattr(
            view, "kwargs", {}
        ):
            return True

        # Determine action from HTTP method if not specified
        action = self.action
        if not action:
            action_mapping = {
                "GET": "read",
                "POST": "create",
                "PUT": "update",
                "PATCH": "update",
                "DELETE": "delete",
            }
            action = action_mapping.get(request.method, "read")

        return PermissionManager.has_resource_permission(
            request.user, self.resource_type, action
        )

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Determine action: prefer explicit action defined for this permission (for custom actions)
        action = self.action
        if not action:
            # Fallback to HTTP method mapping
            action_mapping = {
                "GET": "read",
                "PUT": "update",
                "PATCH": "update",
                "POST": "create",
                "DELETE": "delete",
            }
            action = action_mapping.get(request.method, "read")

        return PermissionManager.has_resource_permission(
            request.user, self.resource_type, action, obj.id
        )


class IsClientOwner(BasePermission):
    """
    Permission that allows access only to client owners of properties/expenses
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and managers have full access
        if (
            request.user.is_superuser
            or request.user.groups.filter(
                name__in=["Administrators", "Managers"]
            ).exists()
        ):
            return True

        try:
            client = Client.objects.get(user=request.user)

            # For properties
            if hasattr(obj, "owner"):
                return obj.owner == client

            # For expenses (check property owner)
            if hasattr(obj, "property"):
                return obj.property.owner == client

            # For shifts (check property owner)
            if hasattr(obj, "property"):
                return obj.property.owner == client

        except Client.DoesNotExist:
            pass

        return False


class IsGuardAssigned(BasePermission):
    """
    Permission that allows access only to guards assigned to shifts/properties
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and managers have full access
        if (
            request.user.is_superuser
            or request.user.groups.filter(
                name__in=["Administrators", "Managers"]
            ).exists()
        ):
            return True

        try:
            guard = Guard.objects.get(user=request.user)

            # For shifts
            if hasattr(obj, "guard"):
                return obj.guard == guard

            # For properties (check if guard has access)
            if hasattr(obj, "id"):
                property_access = PropertyAccess.objects.filter(
                    user=request.user, property=obj, is_active=True
                ).exists()
                return property_access

        except Guard.DoesNotExist:
            pass

        return False


class HasPropertyAccess(BasePermission):
    """
    Permission that checks specific property access rights
    """

    def __init__(self, access_type=None, permission_field=None):
        self.access_type = access_type
        self.permission_field = permission_field

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and managers have full access
        if (
            request.user.is_superuser
            or request.user.groups.filter(
                name__in=["Administrators", "Managers"]
            ).exists()
        ):
            return True

        # Get property from object
        property_obj = None
        if hasattr(obj, "property"):
            property_obj = obj.property
        elif isinstance(obj, Property):
            property_obj = obj

        if not property_obj:
            return False

        # Check property access
        access_filter = {
            "user": request.user,
            "property": property_obj,
            "is_active": True,
        }

        if self.access_type:
            access_filter["access_type"] = self.access_type

        access = PropertyAccess.objects.filter(**access_filter).first()

        if not access:
            return False

        # Check specific permission field if required
        if self.permission_field:
            return getattr(access, self.permission_field, False)

        return True


class CanCreateShift(BasePermission):
    """
    Permission for creating shifts
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and managers can always create shifts
        if (
            request.user.is_superuser
            or request.user.groups.filter(
                name__in=["Administrators", "Managers"]
            ).exists()
        ):
            return True

        # Guards can create their own shifts
        try:
            UserRole.objects.get(user=request.user, role="guard", is_active=True)
            return True
        except UserRole.DoesNotExist:
            pass

        return False


class CanCreateExpense(BasePermission):
    """
    Permission for creating expenses
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and managers can always create expenses
        if (
            request.user.is_superuser
            or request.user.groups.filter(
                name__in=["Administrators", "Managers"]
            ).exists()
        ):
            return True

        # Clients can create expenses for their properties
        try:
            UserRole.objects.get(user=request.user, role="client", is_active=True)
            return True
        except UserRole.DoesNotExist:
            pass

        return False


class RoleBasedPermission(BasePermission):
    """
    Permission based on user roles
    """

    def __init__(self, allowed_roles):
        self.allowed_roles = (
            allowed_roles if isinstance(allowed_roles, list) else [allowed_roles]
        )

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers always have permission
        if request.user.is_superuser:
            return True

        try:
            user_role = UserRole.objects.get(user=request.user, is_active=True)
            return user_role.role in self.allowed_roles
        except UserRole.DoesNotExist:
            return False


# Predefined permission classes for common use cases
class IsAdminOrManager(RoleBasedPermission):
    def __init__(self):
        super().__init__(["admin", "manager"])


class IsClientUser(RoleBasedPermission):
    def __init__(self):
        super().__init__(["client"])


class IsGuardUser(RoleBasedPermission):
    def __init__(self):
        super().__init__(["guard"])


# Permission class factories for DRF ViewSets
def create_resource_permission(resource_type, action=None):
    """Factory function to create resource permission classes"""

    class ResourcePermission(HasResourcePermission):
        def __init__(self):
            super().__init__(resource_type, action)

    return ResourcePermission


def create_property_access_permission(access_type=None, permission_field=None):
    """Factory function to create property access permission classes"""

    class PropertyAccessPermission(HasPropertyAccess):
        def __init__(self):
            super().__init__(access_type, permission_field)

    return PropertyAccessPermission
