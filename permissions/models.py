from django.contrib.auth.models import User
from django.db import models

from core.models import Property


class UserRole(models.Model):
    """Extended user roles for fine-grained permission control"""

    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("manager", "Manager"),
        ("client", "Client"),
        ("guard", "Guard"),
        ("supervisor", "Supervisor"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="role")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        permissions = [
            ("manage_user_roles", "Can manage user roles"),
            ("view_all_roles", "Can view all user roles"),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class ResourcePermission(models.Model):
    """Custom permissions for specific resources"""

    RESOURCE_TYPES = [
        ("property", "Property"),
        ("shift", "Shift"),
        ("expense", "Expense"),
        ("guard", "Guard"),
        ("client", "Client"),
    ]

    ACTION_TYPES = [
        ("create", "Create"),
        ("read", "Read"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("approve", "Approve"),
        ("assign", "Assign"),
    ]

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
    is_active = models.BooleanField(default=True)

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


class PropertyAccess(models.Model):
    """Specific property access permissions for guards and clients"""

    ACCESS_TYPES = [
        ("owner", "Owner"),
        ("assigned_guard", "Assigned Guard"),
        ("supervisor", "Supervisor"),
        ("viewer", "Viewer"),
    ]

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
    is_active = models.BooleanField(default=True)

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


class PermissionLog(models.Model):
    """Log of permission changes for auditing"""

    ACTION_TYPES = [
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
    action = models.CharField(max_length=10, choices=ACTION_TYPES)
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
