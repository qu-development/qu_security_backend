from django.contrib.auth.models import User
from django.db import models

from common.constants import ACCESS_TYPES, ACTION_TYPES, RESOURCE_TYPES, USER_ROLES
from common.models import BaseModel
from core.models import Property


class UserRole(BaseModel):
    """Extended user roles for fine-grained permission control"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="role")
    role = models.CharField(max_length=20, choices=USER_ROLES)

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        permissions = [
            ("manage_user_roles", "Can manage user roles"),
            ("view_all_roles", "Can view all user roles"),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class ResourcePermission(BaseModel):
    """Custom permissions for specific resources"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="resource_permissions"
    )
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    action = models.CharField(max_length=10, choices=ACTION_TYPES)
    resource_id = models.PositiveIntegerField(
        null=True, blank=True
    )  # Specific resource ID or None for all
    granted_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="granted_permissions"
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Resource Permission"
        verbose_name_plural = "Resource Permissions"
        unique_together = ["user", "resource_type", "action", "resource_id"]
        indexes = [
            models.Index(fields=["user", "resource_type", "action"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        resource_info = f" (ID: {self.resource_id})" if self.resource_id else " (All)"
        return (
            f"{self.user.username} - {self.action} {self.resource_type}{resource_info}"
        )


class PropertyAccess(BaseModel):
    """Specific property access permissions for guards and clients"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_access"
    )
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="user_access"
    )
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    can_create_shifts = models.BooleanField(default=False)
    can_edit_shifts = models.BooleanField(default=False)
    can_create_expenses = models.BooleanField(default=False)
    can_edit_expenses = models.BooleanField(default=False)
    can_approve_expenses = models.BooleanField(default=False)
    granted_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="granted_property_access"
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Property Access"
        verbose_name_plural = "Property Access"
        unique_together = ["user", "property"]
        indexes = [
            models.Index(fields=["user", "property"]),
            models.Index(fields=["property", "access_type"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.access_type} access to {self.property.address}"


class PermissionLog(BaseModel):
    """Log of permission changes for auditing"""

    LOG_ACTION_TYPES = [
        ("granted", "Permission Granted"),
        ("revoked", "Permission Revoked"),
        ("modified", "Permission Modified"),
        ("expired", "Permission Expired"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="permission_logs"
    )
    permission_type = models.CharField(max_length=50)
    permission_details = models.JSONField()
    action = models.CharField(max_length=10, choices=LOG_ACTION_TYPES)
    performed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="performed_permission_changes"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name = "Permission Log"
        verbose_name_plural = "Permission Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["performed_by", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.permission_type} {self.action} for {self.user.username} at {self.timestamp}"
