"""
Simple JWT utilities for token validation
"""

import jwt
from django.conf import settings


class JWTPermissionHelper:
    """Simple helper class for JWT token operations"""

    @staticmethod
    def decode_token(token):
        """Decode JWT token and return payload"""
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return decoded
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    @staticmethod
    def has_property_access(token, property_id):
        """Check if user has access to specific property"""
        decoded = JWTPermissionHelper.decode_token(token)
        if not decoded:
            return False

        accessible_properties = decoded.get("accessible_properties", [])
        return property_id in accessible_properties

    @staticmethod
    def has_resource_permission(token, resource_type, action):
        """Check if user has permission for specific resource action"""
        decoded = JWTPermissionHelper.decode_token(token)
        if not decoded:
            return False

        resource_permissions = decoded.get("resource_permissions", {})
        actions = resource_permissions.get(resource_type, [])
        return action in actions

    @staticmethod
    def can_create_clients(token):
        """Check if user can create clients"""
        return JWTPermissionHelper.has_resource_permission(token, "client", "create")

    @staticmethod
    def can_delete_clients(token):
        """Check if user can delete clients"""
        return JWTPermissionHelper.has_resource_permission(token, "client", "delete")

    @staticmethod
    def can_manage_guards(token):
        """Check if user can manage guards"""
        decoded = JWTPermissionHelper.decode_token(token)
        if not decoded:
            return False

        resource_permissions = decoded.get("resource_permissions", {})
        guard_actions = resource_permissions.get("guard", [])
        return (
            "create" in guard_actions
            or "update" in guard_actions
            or "delete" in guard_actions
        )

    @staticmethod
    def is_admin(token):
        """Check if user is admin"""
        decoded = JWTPermissionHelper.decode_token(token)
        if not decoded:
            return False

        return decoded.get("is_admin", False) or decoded.get("is_superuser", False)
