"""
API endpoints for permissions app
"""

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.constants import ACCESS_TYPES, ACTION_TYPES, RESOURCE_TYPES, USER_ROLES
from core.models import Property

from .models import PermissionLog, PropertyAccess, ResourcePermission, UserRole


class AdminPermissionAPI(viewsets.ViewSet):
    """
    Admin-only API for managing user permissions
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """Only superusers and admin role users can access"""
        permission_classes = [permissions.IsAuthenticated]

        # If user is authenticated, check for admin privileges
        if self.request.user.is_authenticated and not (
            self.request.user.is_superuser
            or UserRole.objects.filter(
                user=self.request.user, role="admin", is_active=True
            ).exists()
        ):
            self.permission_denied(self.request, message="Admin privileges required")

        return [permission() for permission in permission_classes]

    def check_admin_permission(self):
        """Check if user has admin permissions"""
        if not self.request.user.is_authenticated:
            return False

        return (
            self.request.user.is_superuser
            or UserRole.objects.filter(
                user=self.request.user, role="admin", is_active=True
            ).exists()
        )

    def list(self, request):
        """Default list endpoint for admin permissions API"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "message": "Admin Permission Management API",
                "available_endpoints": [
                    "list-users-with-permissions/",
                    "assign-user-role/",
                    "grant-resource-permission/",
                    "revoke-resource-permission/",
                    "grant-property-access/",
                    "revoke-property-access/",
                    "permission-audit-log/",
                    "bulk-permission-update/",
                    "available-options/",
                ],
                "description": "API for managing user permissions, roles, and access controls",
            }
        )

    @action(detail=False, methods=["get"])
    def list_users_with_permissions(self, request):
        """List all users with their current permissions"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        users_data = []
        users = (
            User.objects.all()
            .select_related("role")
            .prefetch_related("resource_permissions", "property_access")
        )

        for user in users:
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
                "role": None,
                "resource_permissions": [],
                "property_access": [],
            }

            # Get user role
            try:
                user_role = UserRole.objects.get(user=user, is_active=True)
                user_data["role"] = {
                    "role": user_role.role,
                    "display": user_role.get_role_display(),
                    "created_at": user_role.created_at,
                    "updated_at": user_role.updated_at,
                }
            except UserRole.DoesNotExist:
                pass

            # Get resource permissions
            for perm in user.resource_permissions.filter(is_active=True):
                user_data["resource_permissions"].append(
                    {
                        "id": perm.id,
                        "resource_type": perm.resource_type,
                        "action": perm.action,
                        "resource_id": perm.resource_id,
                        "granted_by": perm.granted_by.username,
                        "granted_at": perm.granted_at,
                        "expires_at": perm.expires_at,
                    }
                )

            # Get property access
            for access in user.property_access.filter(is_active=True):
                user_data["property_access"].append(
                    {
                        "id": access.id,
                        "property_id": access.property.id,
                        "property_address": access.property.address,
                        "property_name": access.property.name,
                        "access_type": access.access_type,
                        "can_create_shifts": access.can_create_shifts,
                        "can_edit_shifts": access.can_edit_shifts,
                        "can_create_expenses": access.can_create_expenses,
                        "can_edit_expenses": access.can_edit_expenses,
                        "can_approve_expenses": access.can_approve_expenses,
                        "granted_by": access.granted_by.username,
                        "granted_at": access.granted_at,
                    }
                )

            users_data.append(user_data)

        return Response({"count": len(users_data), "users": users_data})

    @action(detail=False, methods=["post"])
    def assign_user_role(self, request):
        """Assign or change user role"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get("user_id")
        role = request.data.get("role")
        reason = request.data.get("reason", "")

        if not user_id or not role:
            return Response(
                {"error": "user_id and role are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role not in dict(USER_ROLES):
            return Response(
                {
                    "error": "Invalid role",
                    "valid_roles": [choice[0] for choice in USER_ROLES],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            # Deactivate existing role
            UserRole.objects.filter(user=user).update(is_active=False)

            # Create new role
            user_role, created = UserRole.objects.get_or_create(
                user=user, role=role, defaults={"is_active": True}
            )

            if not created:
                user_role.is_active = True
                user_role.save()

            # Log the change
            PermissionLog.objects.create(
                user=user,
                permission_type="user_role",
                permission_details={"role": role, "action": "assigned"},
                action="granted",
                performed_by=request.user,
                reason=reason,
            )

        return Response(
            {
                "message": f"Role {role} assigned to user {user.username}",
                "user_id": user.id,
                "username": user.username,
                "role": role,
                "role_display": user_role.get_role_display(),
                "created": created,
            }
        )

    @action(detail=False, methods=["post"])
    def grant_resource_permission(self, request):
        """Grant resource permission to a user"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get("user_id")
        resource_type = request.data.get("resource_type")
        action = request.data.get("action")
        resource_id = request.data.get("resource_id")  # Optional
        expires_at = request.data.get("expires_at")  # Optional
        reason = request.data.get("reason", "")

        if not all([user_id, resource_type, action]):
            return Response(
                {"error": "user_id, resource_type, and action are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if resource_type not in dict(RESOURCE_TYPES):
            return Response(
                {
                    "error": "Invalid resource_type",
                    "valid_types": [choice[0] for choice in RESOURCE_TYPES],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action not in dict(ACTION_TYPES):
            return Response(
                {
                    "error": "Invalid action",
                    "valid_actions": [choice[0] for choice in ACTION_TYPES],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Parse expires_at if provided
        expires_at_parsed = None
        if expires_at:
            from django.utils.dateparse import parse_datetime

            expires_at_parsed = parse_datetime(expires_at)
            if not expires_at_parsed:
                return Response(
                    {
                        "error": "Invalid expires_at format. Use ISO format: YYYY-MM-DDTHH:MM:SSZ"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            permission, created = ResourcePermission.objects.get_or_create(
                user=user,
                resource_type=resource_type,
                action=action,
                resource_id=resource_id,
                defaults={
                    "granted_by": request.user,
                    "expires_at": expires_at_parsed,
                    "is_active": True,
                },
            )

            if not created:
                permission.granted_by = request.user
                permission.expires_at = expires_at_parsed
                permission.is_active = True
                permission.save()

            # Log the change
            PermissionLog.objects.create(
                user=user,
                permission_type="resource_permission",
                permission_details={
                    "resource_type": resource_type,
                    "action": action,
                    "resource_id": resource_id,
                    "expires_at": expires_at,
                },
                action="granted",
                performed_by=request.user,
                reason=reason,
            )

        return Response(
            {
                "message": f"{action.title()} permission for {resource_type} granted to {user.username}",
                "permission_id": permission.id,
                "user_id": user.id,
                "username": user.username,
                "resource_type": resource_type,
                "action": action,
                "resource_id": resource_id,
                "expires_at": expires_at_parsed,
                "created": created,
            }
        )

    @action(detail=False, methods=["post"])
    def revoke_resource_permission(self, request):
        """Revoke resource permission from a user"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        permission_id = request.data.get("permission_id")
        reason = request.data.get("reason", "")

        if not permission_id:
            return Response(
                {"error": "permission_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            permission = ResourcePermission.objects.get(id=permission_id)
        except ResourcePermission.DoesNotExist:
            return Response(
                {"error": "Permission not found"}, status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            permission.is_active = False
            permission.save()

            # Log the change
            PermissionLog.objects.create(
                user=permission.user,
                permission_type="resource_permission",
                permission_details={
                    "resource_type": permission.resource_type,
                    "action": permission.action,
                    "resource_id": permission.resource_id,
                },
                action="revoked",
                performed_by=request.user,
                reason=reason,
            )

        return Response(
            {
                "message": f"{permission.action.title()} permission for {permission.resource_type} revoked from {permission.user.username}",
                "permission_id": permission.id,
                "user_id": permission.user.id,
                "username": permission.user.username,
                "resource_type": permission.resource_type,
                "action": permission.action,
            }
        )

    @action(detail=False, methods=["post"])
    def grant_property_access(self, request):
        """Grant property access to a user"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get("user_id")
        property_id = request.data.get("property_id")
        access_type = request.data.get("access_type", "viewer")
        permissions = request.data.get("permissions", {})
        reason = request.data.get("reason", "")

        if not all([user_id, property_id]):
            return Response(
                {"error": "user_id and property_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if access_type not in dict(ACCESS_TYPES):
            return Response(
                {
                    "error": "Invalid access_type",
                    "valid_types": [choice[0] for choice in ACCESS_TYPES],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
            property_obj = Property.objects.get(id=property_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            property_access, created = PropertyAccess.objects.get_or_create(
                user=user,
                property=property_obj,
                defaults={
                    "access_type": access_type,
                    "granted_by": request.user,
                    "is_active": True,
                    "can_create_shifts": permissions.get("can_create_shifts", False),
                    "can_edit_shifts": permissions.get("can_edit_shifts", False),
                    "can_create_expenses": permissions.get(
                        "can_create_expenses", False
                    ),
                    "can_edit_expenses": permissions.get("can_edit_expenses", False),
                    "can_approve_expenses": permissions.get(
                        "can_approve_expenses", False
                    ),
                },
            )

            if not created:
                property_access.access_type = access_type
                property_access.granted_by = request.user
                property_access.is_active = True
                property_access.can_create_shifts = permissions.get(
                    "can_create_shifts", property_access.can_create_shifts
                )
                property_access.can_edit_shifts = permissions.get(
                    "can_edit_shifts", property_access.can_edit_shifts
                )
                property_access.can_create_expenses = permissions.get(
                    "can_create_expenses", property_access.can_create_expenses
                )
                property_access.can_edit_expenses = permissions.get(
                    "can_edit_expenses", property_access.can_edit_expenses
                )
                property_access.can_approve_expenses = permissions.get(
                    "can_approve_expenses", property_access.can_approve_expenses
                )
                property_access.save()

            # Log the change
            PermissionLog.objects.create(
                user=user,
                permission_type="property_access",
                permission_details={
                    "property_id": property_id,
                    "property_address": property_obj.address,
                    "property_name": property_obj.name,
                    "access_type": access_type,
                    "permissions": permissions,
                },
                action="granted",
                performed_by=request.user,
                reason=reason,
            )

        return Response(
            {
                "message": f"{access_type.title()} access to {property_obj.name} granted to {user.username}",
                "access_id": property_access.id,
                "user_id": user.id,
                "username": user.username,
                "property_id": property_id,
                "property_name": property_obj.name,
                "property_address": property_obj.address,
                "access_type": access_type,
                "permissions": {
                    "can_create_shifts": property_access.can_create_shifts,
                    "can_edit_shifts": property_access.can_edit_shifts,
                    "can_create_expenses": property_access.can_create_expenses,
                    "can_edit_expenses": property_access.can_edit_expenses,
                    "can_approve_expenses": property_access.can_approve_expenses,
                },
                "created": created,
            }
        )

    @action(detail=False, methods=["post"])
    def revoke_property_access(self, request):
        """Revoke property access from a user"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        access_id = request.data.get("access_id")
        reason = request.data.get("reason", "")

        if not access_id:
            return Response(
                {"error": "access_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            property_access = PropertyAccess.objects.get(id=access_id)
        except PropertyAccess.DoesNotExist:
            return Response(
                {"error": "Property access not found"}, status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            property_access.is_active = False
            property_access.save()

            # Log the change
            PermissionLog.objects.create(
                user=property_access.user,
                permission_type="property_access",
                permission_details={
                    "property_id": property_access.property.id,
                    "property_address": property_access.property.address,
                    "property_name": property_access.property.name,
                    "access_type": property_access.access_type,
                },
                action="revoked",
                performed_by=request.user,
                reason=reason,
            )

        return Response(
            {
                "message": f"{property_access.access_type.title()} access to {property_access.property.name} revoked from {property_access.user.username}",
                "access_id": access_id,
                "user_id": property_access.user.id,
                "username": property_access.user.username,
                "property_id": property_access.property.id,
                "property_name": property_access.property.name,
            }
        )

    @action(detail=False, methods=["get"])
    def permission_audit_log(self, request):
        """Get detailed permission audit log"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.query_params.get("user_id")
        permission_type = request.query_params.get("permission_type")
        action = request.query_params.get("action")
        limit = int(request.query_params.get("limit", 100))

        logs = PermissionLog.objects.all().select_related("user", "performed_by")

        if user_id:
            logs = logs.filter(user_id=user_id)
        if permission_type:
            logs = logs.filter(permission_type=permission_type)
        if action:
            logs = logs.filter(action=action)

        logs = logs.order_by("-timestamp")[:limit]

        log_data = []
        for log in logs:
            log_data.append(
                {
                    "id": log.id,
                    "user": {
                        "id": log.user.id,
                        "username": log.user.username,
                        "email": log.user.email,
                        "full_name": f"{log.user.first_name} {log.user.last_name}".strip(),
                    },
                    "permission_type": log.permission_type,
                    "permission_details": log.permission_details,
                    "action": log.action,
                    "performed_by": {
                        "id": log.performed_by.id,
                        "username": log.performed_by.username,
                        "email": log.performed_by.email,
                        "full_name": f"{log.performed_by.first_name} {log.performed_by.last_name}".strip(),
                    },
                    "timestamp": log.timestamp,
                    "reason": log.reason,
                }
            )

        return Response(
            {
                "count": len(log_data),
                "logs": log_data,
                "filters": {
                    "user_id": user_id,
                    "permission_type": permission_type,
                    "action": action,
                    "limit": limit,
                },
            }
        )

    @action(detail=False, methods=["post"])
    def bulk_permission_update(self, request):
        """Bulk update permissions for multiple users"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        updates = request.data.get("updates", [])
        if not updates:
            return Response(
                {"error": "updates array is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = []
        successful_count = 0
        failed_count = 0

        with transaction.atomic():
            for update in updates:
                user_id = update.get("user_id")
                operation = update.get("operation")  # 'grant' or 'revoke'
                permission_data = update.get("permission_data", {})

                if operation not in ["grant", "revoke"]:
                    results.append(
                        {
                            "user_id": user_id,
                            "operation": operation,
                            "success": False,
                            "error": 'Invalid operation. Must be "grant" or "revoke"',
                        }
                    )
                    failed_count += 1
                    continue

                try:
                    user = User.objects.get(id=user_id)

                    if operation == "grant":
                        if permission_data.get("type") == "resource":
                            permission, created = (
                                ResourcePermission.objects.get_or_create(
                                    user=user,
                                    resource_type=permission_data["resource_type"],
                                    action=permission_data["action"],
                                    resource_id=permission_data.get("resource_id"),
                                    defaults={
                                        "granted_by": request.user,
                                        "is_active": True,
                                    },
                                )
                            )
                            results.append(
                                {
                                    "user_id": user_id,
                                    "username": user.username,
                                    "operation": operation,
                                    "success": True,
                                    "permission_id": permission.id,
                                    "resource_type": permission_data["resource_type"],
                                    "action": permission_data["action"],
                                    "created": created,
                                }
                            )
                            successful_count += 1

                        elif permission_data.get("type") == "property":
                            property_obj = Property.objects.get(
                                id=permission_data["property_id"]
                            )
                            access, created = PropertyAccess.objects.get_or_create(
                                user=user,
                                property=property_obj,
                                defaults={
                                    "access_type": permission_data.get(
                                        "access_type", "viewer"
                                    ),
                                    "granted_by": request.user,
                                    "is_active": True,
                                },
                            )
                            results.append(
                                {
                                    "user_id": user_id,
                                    "username": user.username,
                                    "operation": operation,
                                    "success": True,
                                    "access_id": access.id,
                                    "property_id": permission_data["property_id"],
                                    "access_type": permission_data.get(
                                        "access_type", "viewer"
                                    ),
                                    "created": created,
                                }
                            )
                            successful_count += 1

                        else:
                            results.append(
                                {
                                    "user_id": user_id,
                                    "operation": operation,
                                    "success": False,
                                    "error": 'Invalid permission type. Must be "resource" or "property"',
                                }
                            )
                            failed_count += 1

                    elif operation == "revoke":
                        if permission_data.get("type") == "resource":
                            updated = ResourcePermission.objects.filter(
                                id=permission_data["permission_id"]
                            ).update(is_active=False)

                            results.append(
                                {
                                    "user_id": user_id,
                                    "username": user.username,
                                    "operation": operation,
                                    "success": updated > 0,
                                    "permission_id": permission_data["permission_id"],
                                }
                            )
                            if updated > 0:
                                successful_count += 1
                            else:
                                failed_count += 1

                        elif permission_data.get("type") == "property":
                            updated = PropertyAccess.objects.filter(
                                id=permission_data["access_id"]
                            ).update(is_active=False)

                            results.append(
                                {
                                    "user_id": user_id,
                                    "username": user.username,
                                    "operation": operation,
                                    "success": updated > 0,
                                    "access_id": permission_data["access_id"],
                                }
                            )
                            if updated > 0:
                                successful_count += 1
                            else:
                                failed_count += 1

                        else:
                            results.append(
                                {
                                    "user_id": user_id,
                                    "operation": operation,
                                    "success": False,
                                    "error": 'Invalid permission type. Must be "resource" or "property"',
                                }
                            )
                            failed_count += 1

                except User.DoesNotExist:
                    results.append(
                        {
                            "user_id": user_id,
                            "operation": operation,
                            "success": False,
                            "error": "User not found",
                        }
                    )
                    failed_count += 1
                except Property.DoesNotExist:
                    results.append(
                        {
                            "user_id": user_id,
                            "operation": operation,
                            "success": False,
                            "error": "Property not found",
                        }
                    )
                    failed_count += 1
                except Exception as e:
                    results.append(
                        {
                            "user_id": user_id,
                            "operation": operation,
                            "success": False,
                            "error": str(e),
                        }
                    )
                    failed_count += 1

        return Response(
            {
                "message": f"Bulk update completed. {successful_count} successful, {failed_count} failed.",
                "summary": {
                    "total": len(updates),
                    "successful": successful_count,
                    "failed": failed_count,
                },
                "results": results,
            }
        )

    @action(detail=False, methods=["get"])
    def available_options(self, request):
        """Get available options for permissions"""
        if not self.check_admin_permission():
            return Response(
                {"error": "Admin privileges required"}, status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "user_roles": [
                    {"value": choice[0], "label": choice[1]} for choice in USER_ROLES
                ],
                "resource_types": [
                    {"value": choice[0], "label": choice[1]}
                    for choice in RESOURCE_TYPES
                ],
                "actions": [
                    {"value": choice[0], "label": choice[1]} for choice in ACTION_TYPES
                ],
                "access_types": [
                    {"value": choice[0], "label": choice[1]} for choice in ACCESS_TYPES
                ],
                "permission_types": [
                    {"value": "user_role", "label": "User Role"},
                    {"value": "resource_permission", "label": "Resource Permission"},
                    {"value": "property_access", "label": "Property Access"},
                ],
                "log_actions": [
                    {"value": "granted", "label": "Granted"},
                    {"value": "revoked", "label": "Revoked"},
                    {"value": "modified", "label": "Modified"},
                    {"value": "expired", "label": "Expired"},
                ],
            }
        )
