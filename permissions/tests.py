"""
Permissions app tests
"""

from common.test_utils import BaseAPITestCase
from permissions.models import UserRole


class UserRoleTestCase(BaseAPITestCase):
    """Test user roles functionality"""

    def test_user_role_creation(self):
        """Test creating user roles"""
        # Roles should already be created in setUp
        admin_role = UserRole.objects.get(user=self.admin_user)
        self.assertEqual(admin_role.role, "admin")

        client_role = UserRole.objects.get(user=self.client_user)
        self.assertEqual(client_role.role, "client")

    def test_role_string_representation(self):
        """Test string representation of roles"""
        admin_role = UserRole.objects.get(user=self.admin_user)
        expected = f"{self.admin_user.username} - Administrator"
        self.assertEqual(str(admin_role), expected)


class PropertyAccessTestCase(BaseAPITestCase):
    """Test property access functionality"""

    def test_property_access_creation(self):
        """Test creating property access"""
        access = self.create_property_access(
            user=self.guard_user,
            property_obj=self.property,
            access_type="assigned_guard",
            can_create_shifts=True,
        )

        self.assertEqual(access.user, self.guard_user)
        self.assertEqual(access.property, self.property)
        self.assertTrue(access.can_create_shifts)

    def test_property_access_string_representation(self):
        """Test string representation of property access"""
        access = self.create_property_access(
            user=self.guard_user, property_obj=self.property, access_type="viewer"
        )

        expected = (
            f"{self.guard_user.username} - viewer access to {self.property.address}"
        )
        self.assertEqual(str(access), expected)


class PermissionAPITestCase(BaseAPITestCase):
    """Test permission management API"""

    def test_admin_can_access_permission_api(self):
        """Test that admin can access permission management API"""
        self.authenticate_as(self.admin_user)
        response = self.client.get("/api/v1/permissions/admin/")
        self.assert_response_success(response)

    def test_non_admin_cannot_access_permission_api(self):
        """Test that non-admin cannot access permission management API"""
        self.authenticate_as(self.client_user)
        response = self.client.get("/api/v1/permissions/admin/")
        self.assert_response_error(response, 403)

    def test_permission_api_requires_authentication(self):
        """Test that permission API requires authentication"""
        response = self.client.get("/api/v1/permissions/admin/")
        self.assert_response_error(response, 401)
