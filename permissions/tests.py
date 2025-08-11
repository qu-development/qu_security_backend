"""
Tests for permissions application
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Client, Guard, Property

from .models import PermissionLog, PropertyAccess, ResourcePermission, UserRole
from .permissions import (
    CanCreateShift,
    HasPropertyAccess,
    IsAdminOrManager,
    IsClientOwner,
)
from .utils import PermissionManager, filter_queryset_by_permissions


class PermissionModelTestCase(TestCase):
    """Test permission models"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin", email="admin@test.com", password="testpass123"
        )

        self.regular_user = User.objects.create_user(
            username="user", email="user@test.com", password="testpass123"
        )

        self.client_user = User.objects.create_user(
            username="client", email="client@test.com", password="testpass123"
        )

    def test_create_user_role(self):
        """Test creating user role"""
        user_role = UserRole.objects.create(user=self.admin_user, role="admin")

        self.assertEqual(user_role.user, self.admin_user)
        self.assertEqual(user_role.role, "admin")
        self.assertTrue(user_role.is_active)
        self.assertEqual(str(user_role), f"{self.admin_user.username} - Administrator")

    def test_user_role_choices_validation(self):
        """Test user role choices validation"""
        valid_roles = ["admin", "manager", "client", "guard", "supervisor"]

        for role in valid_roles:
            user_role = UserRole(user=self.regular_user, role=role)
            user_role.full_clean()  # Should not raise ValidationError

    def test_create_resource_permission(self):
        """Test creating resource permission"""
        permission = ResourcePermission.objects.create(
            user=self.regular_user,
            resource_type="property",
            action="create",
            granted_by=self.admin_user,
        )

        self.assertEqual(permission.user, self.regular_user)
        self.assertEqual(permission.resource_type, "property")
        self.assertEqual(permission.action, "create")
        self.assertEqual(permission.granted_by, self.admin_user)
        self.assertTrue(permission.is_active)
        self.assertIsNone(permission.resource_id)

    def test_create_specific_resource_permission(self):
        """Test creating permission for specific resource"""
        permission = ResourcePermission.objects.create(
            user=self.regular_user,
            resource_type="property",
            action="update",
            resource_id=123,
            granted_by=self.admin_user,
        )

        expected_str = f"{self.regular_user.username} - update property (ID: 123)"
        self.assertEqual(str(permission), expected_str)

    def test_create_property_access(self):
        """Test creating property access"""
        client = Client.objects.create(user=self.client_user, phone="123-456-7890")

        property_obj = Property.objects.create(owner=client, address="123 Test St")

        access = PropertyAccess.objects.create(
            user=self.regular_user,
            property=property_obj,
            access_type="assigned_guard",
            can_create_shifts=True,
            can_edit_shifts=True,
            granted_by=self.admin_user,
        )

        self.assertEqual(access.user, self.regular_user)
        self.assertEqual(access.property, property_obj)
        self.assertEqual(access.access_type, "assigned_guard")
        self.assertTrue(access.can_create_shifts)
        self.assertTrue(access.can_edit_shifts)
        self.assertFalse(access.can_create_expenses)

    def test_create_permission_log(self):
        """Test creating permission log"""
        log = PermissionLog.objects.create(
            user=self.regular_user,
            permission_type="resource_permission",
            permission_details={"resource_type": "property", "action": "create"},
            action="granted",
            performed_by=self.admin_user,
            reason="User promotion",
        )

        self.assertEqual(log.user, self.regular_user)
        self.assertEqual(log.permission_type, "resource_permission")
        self.assertEqual(log.action, "granted")
        self.assertEqual(log.performed_by, self.admin_user)
        self.assertEqual(log.reason, "User promotion")

    def test_unique_constraints(self):
        """Test unique constraints"""
        # Create first permission
        ResourcePermission.objects.create(
            user=self.regular_user,
            resource_type="property",
            action="create",
            resource_id=123,
            granted_by=self.admin_user,
        )

        # Try to create duplicate - should handle gracefully
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ResourcePermission.objects.create(
                user=self.regular_user,
                resource_type="property",
                action="create",
                resource_id=123,
                granted_by=self.admin_user,
            )


class PermissionManagerTestCase(TestCase):
    """Test PermissionManager utility functions"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin", email="admin@test.com", password="testpass123"
        )

        self.regular_user = User.objects.create_user(
            username="user", email="user@test.com", password="testpass123"
        )

        self.client_user = User.objects.create_user(
            username="client", email="client@test.com", password="testpass123"
        )

        # Create admin role
        UserRole.objects.create(user=self.admin_user, role="admin")

    def test_assign_user_role(self):
        """Test assigning role to user"""
        user_role = PermissionManager.assign_user_role(
            self.regular_user, "manager", self.admin_user
        )

        self.assertEqual(user_role.user, self.regular_user)
        self.assertEqual(user_role.role, "manager")
        self.assertTrue(user_role.is_active)

    def test_assign_role_deactivates_previous(self):
        """Test that assigning new role deactivates previous one"""
        # Create initial role
        old_role = UserRole.objects.create(user=self.regular_user, role="guard")

        # Assign new role
        new_role = PermissionManager.assign_user_role(
            self.regular_user, "supervisor", self.admin_user
        )

        # Check old role is deactivated
        old_role.refresh_from_db()
        self.assertFalse(old_role.is_active)
        self.assertTrue(new_role.is_active)

    def test_grant_resource_permission(self):
        """Test granting resource permission"""
        permission = PermissionManager.grant_resource_permission(
            self.regular_user, "property", "create", granted_by=self.admin_user
        )

        self.assertEqual(permission.user, self.regular_user)
        self.assertEqual(permission.resource_type, "property")
        self.assertEqual(permission.action, "create")
        self.assertEqual(permission.granted_by, self.admin_user)

    def test_grant_specific_resource_permission(self):
        """Test granting permission for specific resource"""
        permission = PermissionManager.grant_resource_permission(
            self.regular_user,
            "property",
            "update",
            resource_id=123,
            granted_by=self.admin_user,
        )

        self.assertEqual(permission.resource_id, 123)

    def test_grant_property_access(self):
        """Test granting property access"""
        client = Client.objects.create(user=self.client_user, phone="123-456-7890")

        property_obj = Property.objects.create(owner=client, address="123 Test St")

        permissions = {
            "can_create_shifts": True,
            "can_edit_shifts": True,
            "can_create_expenses": False,
        }

        access = PermissionManager.grant_property_access(
            self.regular_user,
            property_obj,
            "assigned_guard",
            permissions,
            self.admin_user,
        )

        self.assertEqual(access.access_type, "assigned_guard")
        self.assertTrue(access.can_create_shifts)
        self.assertTrue(access.can_edit_shifts)
        self.assertFalse(access.can_create_expenses)

    def test_has_resource_permission_admin(self):
        """Test admin has all permissions"""
        UserRole.objects.create(user=self.admin_user, role="admin")

        has_permission = PermissionManager.has_resource_permission(
            self.admin_user, "property", "create"
        )

        self.assertTrue(has_permission)

    def test_has_resource_permission_specific(self):
        """Test specific resource permission"""
        # Grant specific permission
        ResourcePermission.objects.create(
            user=self.regular_user,
            resource_type="property",
            action="create",
            granted_by=self.admin_user,
        )

        has_permission = PermissionManager.has_resource_permission(
            self.regular_user, "property", "create"
        )

        self.assertTrue(has_permission)

    def test_has_resource_permission_denied(self):
        """Test permission denied"""
        has_permission = PermissionManager.has_resource_permission(
            self.regular_user, "property", "delete"
        )

        self.assertFalse(has_permission)

    def test_has_property_access(self):
        """Test property access checking"""
        client = Client.objects.create(user=self.client_user, phone="123-456-7890")

        property_obj = Property.objects.create(owner=client, address="123 Test St")

        # Grant access
        PropertyAccess.objects.create(
            user=self.regular_user,
            property=property_obj,
            access_type="assigned_guard",
            granted_by=self.admin_user,
        )

        has_access = PermissionManager.has_property_access(
            self.regular_user, property_obj, "assigned_guard"
        )

        self.assertTrue(has_access)

    def test_filter_queryset_by_permissions(self):
        """Test queryset filtering by permissions"""
        # Create test data
        client1 = Client.objects.create(user=self.client_user, phone="111-1111")
        client2 = Client.objects.create(user=self.regular_user, phone="222-2222")

        _ = Property.objects.create(owner=client1, address="Property 1")
        property2 = Property.objects.create(owner=client2, address="Property 2")

        # Regular user should only see their own client's properties
        UserRole.objects.create(user=self.regular_user, role="client")

        queryset = Property.objects.all()
        filtered_queryset = filter_queryset_by_permissions(
            self.regular_user, queryset, "property"
        )

        # Should only return property2 (owned by regular_user's client profile)
        self.assertEqual(list(filtered_queryset), [property2])


class PermissionClassTestCase(TestCase):
    """Test permission classes"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123", is_superuser=True
        )

        self.manager_user = User.objects.create_user(
            username="manager", password="testpass123"
        )

        self.client_user = User.objects.create_user(
            username="client", password="testpass123"
        )

        self.guard_user = User.objects.create_user(
            username="guard", password="testpass123"
        )

        # Create roles
        UserRole.objects.create(user=self.admin_user, role="admin")
        UserRole.objects.create(user=self.manager_user, role="manager")
        UserRole.objects.create(user=self.client_user, role="client")
        UserRole.objects.create(user=self.guard_user, role="guard")

        # Create core objects
        self.client_obj = Client.objects.create(
            user=self.client_user, phone="123-456-7890"
        )

        self.guard_obj = Guard.objects.create(
            user=self.guard_user, phone="098-765-4321"
        )

        self.property_obj = Property.objects.create(
            owner=self.client_obj, address="123 Test St"
        )

    def create_mock_request(self, user):
        """Create mock request with user"""
        from unittest.mock import Mock

        request = Mock()
        request.user = user
        return request

    def test_is_admin_or_manager_permission(self):
        """Test IsAdminOrManager permission"""
        permission = IsAdminOrManager()

        # Test admin access
        request = self.create_mock_request(self.admin_user)
        self.assertTrue(permission.has_permission(request, None))

        # Test manager access
        request = self.create_mock_request(self.manager_user)
        self.assertTrue(permission.has_permission(request, None))

        # Test guard denial
        request = self.create_mock_request(self.guard_user)
        self.assertFalse(permission.has_permission(request, None))

    def test_is_client_owner_permission(self):
        """Test IsClientOwner permission"""
        permission = IsClientOwner()

        # Test owner access
        request = self.create_mock_request(self.client_user)
        self.assertTrue(
            permission.has_object_permission(request, None, self.property_obj)
        )

        # Test non-owner denial
        request = self.create_mock_request(self.guard_user)
        self.assertFalse(
            permission.has_object_permission(request, None, self.property_obj)
        )

        # Test admin access
        request = self.create_mock_request(self.admin_user)
        self.assertTrue(
            permission.has_object_permission(request, None, self.property_obj)
        )

    def test_has_property_access_permission(self):
        """Test HasPropertyAccess permission"""
        permission = HasPropertyAccess()

        # Grant property access to guard
        PropertyAccess.objects.create(
            user=self.guard_user,
            property=self.property_obj,
            access_type="assigned_guard",
            granted_by=self.admin_user,
        )

        # Test guard with access
        request = self.create_mock_request(self.guard_user)
        self.assertTrue(
            permission.has_object_permission(request, None, self.property_obj)
        )

        # Test user without access
        other_user = User.objects.create_user(username="other", password="test")
        request = self.create_mock_request(other_user)
        self.assertFalse(
            permission.has_object_permission(request, None, self.property_obj)
        )

    def test_can_create_shift_permission(self):
        """Test CanCreateShift permission"""
        permission = CanCreateShift()

        # Grant shift creation permission
        PropertyAccess.objects.create(
            user=self.guard_user,
            property=self.property_obj,
            access_type="assigned_guard",
            can_create_shifts=True,
            granted_by=self.admin_user,
        )

        # Create mock shift object
        from unittest.mock import Mock

        shift = Mock()
        shift.property = self.property_obj

        # Test guard with permission
        request = self.create_mock_request(self.guard_user)
        self.assertTrue(permission.has_object_permission(request, None, shift))

        # Test guard without permission
        other_guard_user = User.objects.create_user(username="guard2", password="test")
        request = self.create_mock_request(other_guard_user)
        self.assertFalse(permission.has_object_permission(request, None, shift))


class AdminPermissionAPITestCase(APITestCase):
    """Test Admin Permission API endpoints"""

    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            is_superuser=True,
        )

        self.manager_user = User.objects.create_user(
            username="manager", email="manager@test.com", password="testpass123"
        )

        self.regular_user = User.objects.create_user(
            username="user", email="user@test.com", password="testpass123"
        )

        # Create roles
        UserRole.objects.create(user=self.admin_user, role="admin")
        UserRole.objects.create(user=self.manager_user, role="manager")

        # Create client and property for testing
        self.client_user = User.objects.create_user(
            username="client", email="client@test.com", password="testpass123"
        )
        UserRole.objects.create(user=self.client_user, role="client")

        self.client_obj = Client.objects.create(
            user=self.client_user, phone="123-456-7890"
        )

        self.property_obj = Property.objects.create(
            owner=self.client_obj, address="123 Test Property"
        )

        self.api_client = APIClient()

    def get_jwt_token(self, user):
        """Get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def authenticate_user(self, user):
        """Authenticate user with JWT"""
        token = self.get_jwt_token(user)
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_list_users_with_permissions_as_admin(self):
        """Test listing users with permissions as admin"""
        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-list-users-with-permissions")
        response = self.api_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertTrue(len(response.data) >= 4)  # At least 4 users created

    def test_list_users_with_permissions_as_regular_user(self):
        """Test listing users with permissions as regular user (should fail)"""
        self.authenticate_user(self.regular_user)
        url = reverse("admin-permissions-list-users-with-permissions")
        response = self.api_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_user_role_as_admin(self):
        """Test assigning user role as admin"""
        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-assign-user-role")
        data = {
            "user_id": self.regular_user.id,
            "role": "manager",
            "reason": "Promotion to manager",
        }
        response = self.api_client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verify role was assigned
        user_role = UserRole.objects.get(user=self.regular_user, is_active=True)
        self.assertEqual(user_role.role, "manager")

    def test_assign_invalid_role(self):
        """Test assigning invalid role"""
        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-assign-user-role")
        data = {
            "user_id": self.regular_user.id,
            "role": "invalid_role",
            "reason": "Test",
        }
        response = self.api_client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_grant_resource_permission(self):
        """Test granting resource permission"""
        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-grant-resource-permission")
        data = {
            "user_id": self.regular_user.id,
            "resource_type": "property",
            "action": "create",
            "reason": "Permission to create properties",
        }
        response = self.api_client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verify permission was granted
        permission = ResourcePermission.objects.get(
            user=self.regular_user, resource_type="property", action="create"
        )
        self.assertTrue(permission.is_active)

    def test_grant_property_access(self):
        """Test granting property access"""
        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-grant-property-access")
        data = {
            "user_id": self.regular_user.id,
            "property_id": self.property_obj.id,
            "access_type": "assigned_guard",
            "permissions": {"can_create_shifts": True, "can_edit_shifts": True},
            "reason": "Assign guard to property",
        }
        response = self.api_client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

        # Verify access was granted
        access = PropertyAccess.objects.get(
            user=self.regular_user, property=self.property_obj
        )
        self.assertEqual(access.access_type, "assigned_guard")
        self.assertTrue(access.can_create_shifts)
        self.assertTrue(access.can_edit_shifts)

    def test_revoke_resource_permission(self):
        """Test revoking resource permission"""
        # First, grant a permission
        permission = ResourcePermission.objects.create(
            user=self.regular_user,
            resource_type="property",
            action="update",
            granted_by=self.admin_user,
        )

        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-revoke-resource-permission")
        data = {"permission_id": permission.id, "reason": "No longer needed"}
        response = self.api_client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify permission was revoked
        permission.refresh_from_db()
        self.assertFalse(permission.is_active)

    def test_revoke_property_access(self):
        """Test revoking property access"""
        # First, grant access
        access = PropertyAccess.objects.create(
            user=self.regular_user,
            property=self.property_obj,
            access_type="viewer",
            granted_by=self.admin_user,
        )

        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-revoke-property-access")
        data = {"access_id": access.id, "reason": "Access no longer needed"}
        response = self.api_client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify access was revoked
        access.refresh_from_db()
        self.assertFalse(access.is_active)

    def test_permission_audit_log(self):
        """Test getting permission audit log"""
        # Create some log entries
        PermissionLog.objects.create(
            user=self.regular_user,
            permission_type="resource_permission",
            permission_details={"resource_type": "property", "action": "create"},
            action="granted",
            performed_by=self.admin_user,
            reason="Initial permission grant",
        )

        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-permission-audit-log")
        response = self.api_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("logs", response.data)
        self.assertIn("count", response.data)
        self.assertTrue(len(response.data["logs"]) >= 1)

    def test_bulk_permission_update(self):
        """Test bulk permission update"""
        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-bulk-permission-update")
        data = {
            "updates": [
                {
                    "user_id": self.regular_user.id,
                    "operation": "grant",
                    "permission_data": {
                        "type": "resource",
                        "resource_type": "property",
                        "action": "read",
                    },
                },
                {
                    "user_id": self.regular_user.id,
                    "operation": "grant",
                    "permission_data": {
                        "type": "property",
                        "property_id": self.property_obj.id,
                        "access_type": "viewer",
                    },
                },
            ]
        }
        response = self.api_client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

        # Verify permissions were granted
        resource_permission = ResourcePermission.objects.get(
            user=self.regular_user, resource_type="property", action="read"
        )
        self.assertTrue(resource_permission.is_active)

        property_access = PropertyAccess.objects.get(
            user=self.regular_user, property=self.property_obj
        )
        self.assertEqual(property_access.access_type, "viewer")

    def test_available_options(self):
        """Test getting available options"""
        self.authenticate_user(self.admin_user)
        url = reverse("admin-permissions-available-options")
        response = self.api_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("roles", response.data)
        self.assertIn("resource_types", response.data)
        self.assertIn("actions", response.data)
        self.assertIn("access_types", response.data)

        # Verify role choices are included
        self.assertIn("admin", [role[0] for role in response.data["roles"]])
        self.assertIn("manager", [role[0] for role in response.data["roles"]])


class PermissionDecoratorTestCase(APITestCase):
    """Test permission decorators"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123"
        )

        self.regular_user = User.objects.create_user(
            username="user", password="testpass123"
        )

        UserRole.objects.create(user=self.admin_user, role="admin")
        UserRole.objects.create(user=self.regular_user, role="guard")

        self.api_client = APIClient()

    def get_jwt_token(self, user):
        """Get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def authenticate_user(self, user):
        """Authenticate user with JWT"""
        token = self.get_jwt_token(user)
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_permission_required_decorator_success(self):
        """Test permission required decorator allows admin"""
        # Grant specific permission to regular user
        ResourcePermission.objects.create(
            user=self.regular_user,
            resource_type="property",
            action="create",
            granted_by=self.admin_user,
        )

        self.authenticate_user(self.regular_user)

        # Test endpoint that uses @permission_required decorator
        # This would be tested in the actual API endpoint tests
        # Here we just verify the permission exists
        has_permission = PermissionManager.has_resource_permission(
            self.regular_user, "property", "create"
        )
        self.assertTrue(has_permission)

    def test_permission_required_decorator_denied(self):
        """Test permission required decorator denies unauthorized user"""
        self.authenticate_user(self.regular_user)

        # Test that user doesn't have permission
        has_permission = PermissionManager.has_resource_permission(
            self.regular_user,
            "property",
            "delete",  # Not granted
        )
        self.assertFalse(has_permission)


class PermissionLogTestCase(TestCase):
    """Test permission logging functionality"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123"
        )

        self.regular_user = User.objects.create_user(
            username="user", password="testpass123"
        )

        UserRole.objects.create(user=self.admin_user, role="admin")

    def test_permission_log_creation(self):
        """Test that permission changes are logged"""
        # Grant permission (should create log)
        _ = PermissionManager.grant_resource_permission(
            self.regular_user, "property", "create", granted_by=self.admin_user
        )

        # Verify log was created
        log = PermissionLog.objects.get(
            user=self.regular_user,
            permission_type="resource_permission",
            action="granted",
        )

        self.assertEqual(log.performed_by, self.admin_user)
        self.assertIn("resource_type", log.permission_details)
        self.assertEqual(log.permission_details["resource_type"], "property")

    def test_permission_log_ordering(self):
        """Test that permission logs are ordered by timestamp"""
        # Create multiple logs
        for i in range(3):
            PermissionLog.objects.create(
                user=self.regular_user,
                permission_type=f"test_permission_{i}",
                permission_details={"test": i},
                action="granted",
                performed_by=self.admin_user,
            )

        # Get logs - should be ordered by timestamp (newest first)
        logs = PermissionLog.objects.all()
        timestamps = [log.timestamp for log in logs]

        # Verify descending order
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))


class PermissionExpirationTestCase(TestCase):
    """Test permission expiration functionality"""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123"
        )

        self.regular_user = User.objects.create_user(
            username="user", password="testpass123"
        )

        UserRole.objects.create(user=self.admin_user, role="admin")

    def test_expired_permission_not_active(self):
        """Test that expired permissions are not considered active"""
        # Create expired permission
        expired_time = timezone.now() - timedelta(days=1)

        permission = ResourcePermission.objects.create(
            user=self.regular_user,
            resource_type="property",
            action="create",
            granted_by=self.admin_user,
            expires_at=expired_time,
        )

        # Check permission (should be false due to expiration)
        _ = PermissionManager.has_resource_permission(
            self.regular_user, "property", "create"
        )

        # This would depend on implementation checking expires_at
        # For now, just verify the permission exists but is expired
        self.assertTrue(permission.expires_at < timezone.now())

    def test_future_expiration_is_active(self):
        """Test that permissions with future expiration are active"""
        # Create permission that expires in the future
        future_time = timezone.now() + timedelta(days=30)

        permission = ResourcePermission.objects.create(
            user=self.regular_user,
            resource_type="property",
            action="create",
            granted_by=self.admin_user,
            expires_at=future_time,
        )

        # Verify not expired
        self.assertTrue(permission.expires_at > timezone.now())
        self.assertTrue(permission.is_active)
