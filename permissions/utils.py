"""
Permission utilities for QU Security Backend
"""

import logging
from functools import wraps

from django.contrib.auth.models import Group, Permission, User
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from core.models import Client, Guard, Property

from .models import PropertyAccess, ResourcePermission, UserRole

logger = logging.getLogger(__name__)


class PermissionManager:
    """Central permission manager for the application"""

    @staticmethod
    def setup_default_groups():
        """Create default user groups with appropriate permissions"""

        # Create groups
        groups_config = {
            "Administrators": {
                "permissions": ["*"],  # All permissions
                "description": "Full system access",
            },
            "Managers": {
                "permissions": [
                    "core.view_guard",
                    "core.add_guard",
                    "core.change_guard",
                    "core.delete_guard",
                    "core.view_client",
                    "core.add_client",
                    "core.change_client",
                    "core.view_property",
                    "core.add_property",
                    "core.change_property",
                    "core.delete_property",
                    "core.view_shift",
                    "core.add_shift",
                    "core.change_shift",
                    "core.delete_shift",
                    "core.view_expense",
                    "core.add_expense",
                    "core.change_expense",
                    "core.delete_expense",
                    "permissions.manage_user_roles",
                    "permissions.view_all_roles",
                ],
                "description": "Can manage guards, clients, properties, shifts and expenses",
            },
            "Clients": {
                "permissions": [
                    "core.view_property",
                    "core.add_property",
                    "core.change_property",
                    "core.view_expense",
                    "core.add_expense",
                    "core.change_expense",
                    "core.delete_expense",
                    "core.view_shift",
                ],
                "description": "Can manage own properties and related expenses",
            },
            "Guards": {
                "permissions": [
                    "core.view_shift",
                    "core.add_shift",
                    "core.change_shift",
                    "core.view_property",
                ],
                "description": "Can manage own shifts and view assigned properties",
            },
        }

        for group_name, config in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                logger.info(f"Created group: {group_name}")

            if config["permissions"] == ["*"]:
                # Assign all permissions to administrators
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)
            else:
                # Assign specific permissions
                permissions = Permission.objects.filter(
                    codename__in=[perm.split(".")[-1] for perm in config["permissions"]]
                )
                group.permissions.set(permissions)

            logger.info(f"Configured permissions for group: {group_name}")

    @staticmethod
    def assign_user_role(user: User, role: str, assigned_by: User) -> UserRole:
        """Assign a role to a user"""
        user_role, created = UserRole.objects.update_or_create(
            user=user, defaults={"role": role, "is_active": True}
        )

        # Add user to appropriate group
        group_mapping = {
            "admin": "Administrators",
            "manager": "Managers",
            "client": "Clients",
            "guard": "Guards",
        }

        if role in group_mapping:
            group = Group.objects.get(name=group_mapping[role])
            user.groups.clear()
            user.groups.add(group)

        logger.info(
            f"Assigned role {role} to user {user.username} by {assigned_by.username}"
        )
        return user_role

    @staticmethod
    def grant_resource_permission(
        user: User,
        resource_type: str,
        action: str,
        resource_id: int | None = None,
        granted_by: User | None = None,
        expires_at: str | None = None,
    ) -> ResourcePermission:
        """Grant specific resource permission to a user"""
        permission, created = ResourcePermission.objects.update_or_create(
            user=user,
            resource_type=resource_type,
            action=action,
            resource_id=resource_id,
            defaults={
                "granted_by": granted_by or user,
                "expires_at": expires_at,
                "is_active": True,
            },
        )

        logger.info(
            f"Granted {action} permission on {resource_type} to {user.username}"
        )
        return permission

    @staticmethod
    def grant_property_access(
        user: User,
        property_obj: Property,
        access_type: str,
        permissions: dict,
        granted_by: User,
    ) -> PropertyAccess:
        """Grant specific property access to a user"""
        access, created = PropertyAccess.objects.update_or_create(
            user=user,
            property=property_obj,
            defaults={
                "access_type": access_type,
                "granted_by": granted_by,
                "is_active": True,
                **permissions,
            },
        )

        logger.info(
            f"Granted {access_type} access to property {property_obj.address} for {user.username}"
        )
        return access

    @staticmethod
    def has_role(user: User, role: str) -> bool:
        """Check if user has a specific role"""
        try:
            user_role = UserRole.objects.get(user=user, is_active=True)
            return user_role.role == role
        except UserRole.DoesNotExist:
            return False

    @staticmethod
    def has_property_access(
        user: User, property_obj: Property, access_type: str
    ) -> bool:
        """Check if user has specific access to a property"""

        # Superusers and admins have all access
        if user.is_superuser or user.groups.filter(name="Administrators").exists():
            return True

        # Managers have all access
        if user.groups.filter(name="Managers").exists():
            return True

        # Check if user owns the property (for clients)
        if access_type == "owner":
            try:
                client = Client.objects.get(user=user)
                return property_obj.owner == client
            except Client.DoesNotExist:
                return False

        # Check PropertyAccess table for specific access
        access = PropertyAccess.objects.filter(
            user=user, property=property_obj, access_type=access_type, is_active=True
        ).exists()

        return access

    @staticmethod
    def has_resource_permission(
        user: User, resource_type: str, action: str, resource_id: int | None = None
    ) -> bool:
        """Check if user has permission for a specific resource action"""

        # Superusers and admins have all permissions
        if user.is_superuser or user.groups.filter(name="Administrators").exists():
            return True

        # Check user role permissions
        try:
            user_role = UserRole.objects.get(user=user, is_active=True)

            # Role-based permissions
            role_permissions = {
                "admin": {
                    "property": ["create", "read", "update", "delete", "assign"],
                    "shift": ["create", "read", "update", "delete", "approve"],
                    "expense": ["create", "read", "update", "delete", "approve"],
                    "guard": ["create", "read", "update", "delete"],
                    "client": ["create", "read", "update", "delete"],
                    "service": ["create", "read", "update", "delete"],
                },
                "manager": {
                    "property": ["create", "read", "update", "delete", "assign"],
                    "shift": ["read", "update", "approve"],
                    "expense": ["read", "approve"],
                    "guard": ["read", "update"],
                    "client": ["read", "update"],
                    "service": ["create", "read", "update", "delete"],
                },
                "client": {
                    "property": ["create", "read", "update"],
                    "expense": ["create", "read", "update", "delete"],
                    "shift": ["read"],
                    "service": ["read"],
                },
                "guard": {
                    "shift": ["create", "read", "update"], 
                    "property": ["read"],
                    "service": ["read"],
                },
            }

            if user_role.role in role_permissions:
                allowed_actions = role_permissions[user_role.role].get(
                    resource_type, []
                )
                if action in allowed_actions:
                    # For property detail-level actions, only managers auto-pass via role.
                    # Clients/guards must be owners or have explicit resource permission.
                    if resource_type == "property" and resource_id is not None:
                        if user_role.role == "manager":
                            return True
                        # fall through to owner/explicit permission checks
                    else:
                        return True

        except UserRole.DoesNotExist:
            # No explicit role; fall back to owner/explicit permission checks below
            pass

        # Owner fallback for property actions (allow owners to read/update/delete their properties)
        if resource_type == "property" and resource_id:
            # Include soft-deleted properties as well (needed for restore)
            prop = (
                getattr(Property, "all_objects", Property.objects)
                .filter(id=resource_id)
                .first()
            )
            if (
                prop
                and PermissionManager.has_property_access(user, prop, "owner")
                and action in ["read", "update", "delete"]
            ):
                return True

        # Check specific resource permissions
        resource_perm = (
            ResourcePermission.objects.filter(
                user=user, resource_type=resource_type, action=action, is_active=True
            )
            .filter(Q(resource_id=resource_id) | Q(resource_id__isnull=True))
            .first()
        )

        return resource_perm is not None

    @staticmethod
    def filter_queryset_by_permissions(user: User, queryset, resource_type: str):
        """Filter queryset based on user permissions"""

        # Superusers and admins see everything
        if user.is_superuser or user.groups.filter(name="Administrators").exists():
            return queryset

        # Managers see everything
        if user.groups.filter(name="Managers").exists():
            return queryset

        # Role-based filtering
        try:
            user_role = UserRole.objects.get(user=user, is_active=True)

            if resource_type == "property":
                if user_role.role == "client":
                    # Clients see only their properties
                    try:
                        client = Client.objects.get(user=user)
                        return queryset.filter(owner=client)
                    except Client.DoesNotExist:
                        return queryset.none()
                elif user_role.role == "guard":
                    # Guards see only assigned properties
                    property_access = PropertyAccess.objects.filter(
                        user=user, is_active=True
                    ).values_list("property_id", flat=True)
                    return queryset.filter(id__in=property_access)

            elif resource_type == "guard":
                if user_role.role == "guard":
                    # Guards see only their own Guard profile
                    return queryset.filter(user=user)
                elif user_role.role == "client":
                    # Clients see guards associated to their properties via tariffs
                    try:
                        client = Client.objects.get(user=user)
                        return queryset.filter(
                            property_tariffs__property__owner=client
                        ).distinct()
                    except Client.DoesNotExist:
                        return queryset.none()

            elif resource_type == "shift":
                if user_role.role == "guard":
                    # Guards see only their shifts
                    try:
                        guard = Guard.objects.get(user=user)
                        return queryset.filter(guard=guard)
                    except Guard.DoesNotExist:
                        return queryset.none()
                elif user_role.role == "client":
                    # Clients see shifts on their properties
                    try:
                        client = Client.objects.get(user=user)
                        return queryset.filter(property__owner=client)
                    except Client.DoesNotExist:
                        return queryset.none()

            elif resource_type == "expense" and user_role.role == "client":
                # Clients see expenses on their properties
                try:
                    client = Client.objects.get(user=user)
                    return queryset.filter(property__owner=client)
                except Client.DoesNotExist:
                    return queryset.none()

        except UserRole.DoesNotExist:
            # Fallbacks when a user has no explicit role assigned
            if resource_type == "property":
                # If the user is a Client owner, allow their own properties
                try:
                    client = Client.objects.get(user=user)
                    return queryset.filter(owner=client)
                except Client.DoesNotExist:
                    pass
            elif resource_type == "shift":
                # If the user is a Client owner, allow shifts on their properties
                try:
                    client = Client.objects.get(user=user)
                    return queryset.filter(property__owner=client)
                except Client.DoesNotExist:
                    pass
                # If the user is a Guard, allow their own shifts
                try:
                    guard = Guard.objects.get(user=user)
                    return queryset.filter(guard=guard)
                except Guard.DoesNotExist:
                    return queryset.none()
            elif resource_type == "guard":
                # If the user is a Guard, allow viewing their own guard profile
                try:
                    return queryset.filter(user=user)
                except Exception:
                    return queryset.none()

        return queryset.none()


def require_permission(
    resource_type: str, action: str, resource_id_param: str | None = None
):
    """Decorator to require specific permissions for view methods"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]

            if not PermissionManager.has_resource_permission(
                request.user, resource_type, action, resource_id
            ):
                raise PermissionDenied(
                    f"You don't have permission to {action} {resource_type}"
                )

            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def require_property_access(access_type: str, permission_field: str | None = None):
    """Decorator to require specific property access"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            property_id = kwargs.get("property_id") or kwargs.get("pk")
            if not property_id:
                raise PermissionDenied("Property ID required")

            try:
                property_obj = Property.objects.get(id=property_id)
            except Property.DoesNotExist:
                raise PermissionDenied("Property not found")

            # Check if user has access to this property
            access = PropertyAccess.objects.filter(
                user=request.user,
                property=property_obj,
                access_type=access_type,
                is_active=True,
            ).first()

            if not access:
                raise PermissionDenied(
                    f"You don't have {access_type} access to this property"
                )

            # Check specific permission if required
            if permission_field and not getattr(access, permission_field, False):
                raise PermissionDenied(
                    f"You don't have {permission_field} permission for this property"
                )

            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def permission_required(
    resource_type: str, action: str, resource_id_param: str | None = None
):
    """Alias for require_permission decorator for DRF compatibility"""
    return require_permission(resource_type, action, resource_id_param)


def filter_queryset_by_permissions(user: User, queryset, resource_type: str):
    """Standalone function to filter querysets by permissions"""
    return PermissionManager.filter_queryset_by_permissions(
        user, queryset, resource_type
    )
