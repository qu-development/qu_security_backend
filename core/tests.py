"""
Complete tests for QU Security Backend system
Includes basic functionality tests and permission system tests
"""

from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

from core.models import Client, Guard, Property
from permissions.models import PropertyAccess, UserRole

# =====================================
# BASIC TESTS - Core Functionality
# =====================================


class AuthenticationTestCase(APITestCase):
    """JWT Authentication tests"""

    def setUp(self):
        self.api_client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@test.com"
        )

    def test_login_success(self):
        """Test successful login"""
        login_data = {"username": "testuser", "password": "testpass123"}
        response = self.api_client.post("/api/auth/login/", login_data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_failure(self):
        """Test failed login"""
        login_data = {"username": "testuser", "password": "wrongpassword"}
        response = self.api_client.post("/api/auth/login/", login_data, format="json")
        self.assertEqual(response.status_code, 401)


class UserEndpointTestCase(APITestCase):
    """User endpoint tests"""

    def setUp(self):
        self.api_client = APIClient()

        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123",
            email="admin@test.com",
            is_superuser=True,
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            username="regular", password="testpass123", email="regular@test.com"
        )

    def test_user_list_requires_authentication(self):
        """Test that user list requires authentication"""
        response = self.api_client.get("/api/users/")
        self.assertEqual(response.status_code, 401)

    def test_user_list_with_authentication(self):
        """Test user list with authentication"""
        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.get("/api/users/")
        self.assertEqual(response.status_code, 200)

    def test_user_creation(self):
        """Test user creation"""
        user_data = {
            "username": "newuser",
            "password": "newpass123",
            "password_confirm": "newpass123",
            "email": "newuser@test.com",
        }
        response = self.api_client.post("/api/users/", user_data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_current_user_profile(self):
        """Test current user profile"""
        self.api_client.force_authenticate(user=self.regular_user)
        response = self.api_client.get("/api/users/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "regular")


class BasicCRUDTestCase(APITestCase):
    """Basic CRUD operations tests"""

    def setUp(self):
        self.api_client = APIClient()

        # Create admin for tests
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123",
            email="admin@test.com",
            is_superuser=True,
        )

        # Create client for property tests
        self.client_user = User.objects.create_user(
            username="client", password="testpass123", email="client@test.com"
        )
        UserRole.objects.create(user=self.client_user, role="client")
        self.client = Client.objects.create(
            user=self.client_user, balance=Decimal("1000.00")
        )

    def test_property_crud_operations(self):
        """Test CRUD operations on properties"""
        self.api_client.force_authenticate(user=self.client_user)

        # CREATE - Create property
        property_data = {"address": "123 Test Street", "total_hours": 100}
        response = self.api_client.post(
            "/api/properties/", property_data, format="json"
        )
        self.assertEqual(response.status_code, 201)
        property_id = response.data["id"]

        # READ - Read property
        response = self.api_client.get(f"/api/properties/{property_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["address"], "123 Test Street")

        # UPDATE - Update property
        update_data = {"address": "456 Updated Street", "total_hours": 150}
        response = self.api_client.put(
            f"/api/properties/{property_id}/", update_data, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["address"], "456 Updated Street")

    def test_guard_crud_operations(self):
        """Test CRUD operations on guards (admin only)"""
        self.api_client.force_authenticate(user=self.admin_user)

        # Create user for guard
        guard_user = User.objects.create_user(
            username="guard1", password="testpass123", email="guard1@test.com"
        )

        # CREATE - Create guard
        guard_data = {"user": guard_user.id, "phone": "123-456-7890"}
        response = self.api_client.post("/api/guards/", guard_data, format="json")
        self.assertEqual(response.status_code, 201)

        # READ - Read guards
        response = self.api_client.get("/api/guards/")
        self.assertEqual(response.status_code, 200)

    def test_client_crud_operations(self):
        """Test CRUD operations on clients (admin only)"""
        self.api_client.force_authenticate(user=self.admin_user)

        # Create user for client
        client_user = User.objects.create_user(
            username="client1", password="testpass123", email="client1@test.com"
        )

        # CREATE - Create client
        client_data = {
            "user": client_user.id,
            "phone": "123-456-7890",
            "balance": "500.00",
        }
        response = self.api_client.post("/api/clients/", client_data, format="json")
        self.assertEqual(response.status_code, 201)

        # READ - Read clients
        response = self.api_client.get("/api/clients/")
        self.assertEqual(response.status_code, 200)


# =====================================
# PERMISSION TESTS - Advanced System
# =====================================


class AuthenticationRequiredTestCase(APITestCase):
    """Basic authentication tests"""

    def setUp(self):
        self.api_client = APIClient()

    def test_authentication_required(self):
        """Verify that authentication is required for all endpoints"""
        endpoints = [
            "/api/properties/",
            "/api/clients/",
            "/api/guards/",
            "/api/shifts/",
            "/api/expenses/",
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.api_client.get(endpoint)
                self.assertEqual(response.status_code, 401)


class RoleBasedPermissionTestCase(APITestCase):
    """Role-based permission tests"""

    def setUp(self):
        self.api_client = APIClient()

        # Create users with different roles
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123", email="admin@test.com"
        )
        self.manager_user = User.objects.create_user(
            username="manager", password="testpass123", email="manager@test.com"
        )
        self.client_user = User.objects.create_user(
            username="client", password="testpass123", email="client@test.com"
        )
        self.guard_user = User.objects.create_user(
            username="guard", password="testpass123", email="guard@test.com"
        )

        # Assign roles
        UserRole.objects.create(user=self.admin_user, role="admin")
        UserRole.objects.create(user=self.manager_user, role="manager")
        UserRole.objects.create(user=self.client_user, role="client")
        UserRole.objects.create(user=self.guard_user, role="guard")

        # Create profiles
        self.client = Client.objects.create(
            user=self.client_user, balance=Decimal("1000.00")
        )
        self.guard = Guard.objects.create(user=self.guard_user)

    def test_admin_has_full_access(self):
        """Admin should have full access to all resources"""
        self.api_client.force_authenticate(user=self.admin_user)

        endpoints = ["/api/properties/", "/api/clients/", "/api/guards/"]
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.api_client.get(endpoint)
                self.assertEqual(response.status_code, 200)

    def test_manager_has_full_access(self):
        """Manager should have full access to all resources"""
        self.api_client.force_authenticate(user=self.manager_user)

        endpoints = ["/api/properties/", "/api/clients/", "/api/guards/"]
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.api_client.get(endpoint)
                self.assertEqual(response.status_code, 200)

    def test_role_verification_functions(self):
        """Verify that role verification functions work"""
        from permissions.utils import PermissionManager

        self.assertTrue(PermissionManager.has_role(self.admin_user, "admin"))
        self.assertTrue(PermissionManager.has_role(self.manager_user, "manager"))
        self.assertTrue(PermissionManager.has_role(self.client_user, "client"))
        self.assertTrue(PermissionManager.has_role(self.guard_user, "guard"))

        # Verify that incorrect roles return False
        self.assertFalse(PermissionManager.has_role(self.client_user, "admin"))
        self.assertFalse(PermissionManager.has_role(self.guard_user, "client"))


class PropertyAccessTestCase(APITestCase):
    """Property access tests"""

    def setUp(self):
        self.api_client = APIClient()

        # Create users
        self.client1_user = User.objects.create_user(
            username="client1", password="testpass123", email="client1@test.com"
        )
        self.client2_user = User.objects.create_user(
            username="client2", password="testpass123", email="client2@test.com"
        )
        self.guard_user = User.objects.create_user(
            username="guard", password="testpass123", email="guard@test.com"
        )
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123", email="admin@test.com"
        )

        # Assign roles
        UserRole.objects.create(user=self.client1_user, role="client")
        UserRole.objects.create(user=self.client2_user, role="client")
        UserRole.objects.create(user=self.guard_user, role="guard")
        UserRole.objects.create(user=self.admin_user, role="admin")

        # Create profiles
        self.client1 = Client.objects.create(
            user=self.client1_user, balance=Decimal("1000.00")
        )
        self.client2 = Client.objects.create(
            user=self.client2_user, balance=Decimal("500.00")
        )
        self.guard = Guard.objects.create(user=self.guard_user)

        # Create properties
        self.property1 = Property.objects.create(
            owner=self.client1, address="123 Main St", total_hours=100
        )
        self.property2 = Property.objects.create(
            owner=self.client2, address="456 Oak Ave", total_hours=80
        )

        # Give guard access to property1
        PropertyAccess.objects.create(
            user=self.guard_user,
            property=self.property1,
            access_type="assigned_guard",
            can_create_shifts=True,
            can_edit_shifts=True,
            granted_by=self.admin_user,
        )

    def test_client_sees_only_own_properties(self):
        """Client should see only their own properties"""
        self.api_client.force_authenticate(user=self.client1_user)

        response = self.api_client.get("/api/properties/")
        self.assertEqual(response.status_code, 200)

        # Handle paginated response
        properties = response.data.get("results", response.data)
        property_ids = [p["id"] for p in properties]

        # Should see their property
        self.assertIn(self.property1.id, property_ids)
        # Should NOT see other client's property
        self.assertNotIn(self.property2.id, property_ids)

    def test_client_cannot_access_other_properties(self):
        """Client cannot directly access other client's properties"""
        self.api_client.force_authenticate(user=self.client1_user)

        # Try to access other client's property
        response = self.api_client.get(f"/api/properties/{self.property2.id}/")
        self.assertIn(response.status_code, [403, 404])

    def test_guard_sees_only_assigned_properties(self):
        """Guard should see only assigned properties"""
        self.api_client.force_authenticate(user=self.guard_user)

        response = self.api_client.get("/api/properties/")
        self.assertEqual(response.status_code, 200)

        # Handle paginated response
        properties = response.data.get("results", response.data)
        property_ids = [p["id"] for p in properties]

        # Should see assigned property
        self.assertIn(self.property1.id, property_ids)
        # Should NOT see unassigned property
        self.assertNotIn(self.property2.id, property_ids)

    def test_guard_cannot_access_unassigned_properties(self):
        """Guard cannot access unassigned properties"""
        self.api_client.force_authenticate(user=self.guard_user)

        # Try to access unassigned property
        response = self.api_client.get(f"/api/properties/{self.property2.id}/")
        self.assertIn(response.status_code, [403, 404])

    def test_property_access_functions(self):
        """Verify that property access functions work"""
        from permissions.utils import PermissionManager

        # Owner client
        self.assertTrue(
            PermissionManager.has_property_access(
                self.client1_user, self.property1, "owner"
            )
        )
        self.assertFalse(
            PermissionManager.has_property_access(
                self.client1_user, self.property2, "owner"
            )
        )

        # Assigned guard
        self.assertTrue(
            PermissionManager.has_property_access(
                self.guard_user, self.property1, "assigned_guard"
            )
        )
        self.assertFalse(
            PermissionManager.has_property_access(
                self.guard_user, self.property2, "assigned_guard"
            )
        )


class ResourceCreationTestCase(APITestCase):
    """Resource creation tests (shifts, expenses)"""

    def setUp(self):
        self.api_client = APIClient()

        # Create users and roles
        self.client_user = User.objects.create_user(
            username="client", password="testpass123", email="client@test.com"
        )
        self.guard_user = User.objects.create_user(
            username="guard", password="testpass123", email="guard@test.com"
        )
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123", email="admin@test.com"
        )

        # Assign roles
        UserRole.objects.create(user=self.client_user, role="client")
        UserRole.objects.create(user=self.guard_user, role="guard")
        UserRole.objects.create(user=self.admin_user, role="admin")

        # Setup groups and assign admin to correct group
        from permissions.utils import PermissionManager

        PermissionManager.setup_default_groups()
        PermissionManager.assign_user_role(self.admin_user, "admin", self.admin_user)

        # Create profiles
        self.client = Client.objects.create(
            user=self.client_user, balance=Decimal("1000.00")
        )
        self.guard = Guard.objects.create(user=self.guard_user)

        # Create property
        self.property = Property.objects.create(
            owner=self.client, address="123 Test St", total_hours=100
        )

    def test_guard_can_create_shifts(self):
        """Guard with correct role can create shifts"""
        self.api_client.force_authenticate(user=self.guard_user)

        shift_data = {
            "guard": self.guard.id,
            "property": self.property.id,
            "start_time": "2024-01-01T09:00:00Z",
            "end_time": "2024-01-01T17:00:00Z",
            "hours_worked": 8,
        }

        response = self.api_client.post("/api/shifts/", shift_data, format="json")
        # System allows guards to create shifts
        self.assertIn(response.status_code, [200, 201])

    def test_client_can_create_expenses(self):
        """Client with correct role can create expenses"""
        self.api_client.force_authenticate(user=self.client_user)

        expense_data = {
            "property": self.property.id,
            "description": "Test expense",
            "amount": "50.00",
        }

        response = self.api_client.post("/api/expenses/", expense_data, format="json")
        # System allows clients to create expenses
        self.assertIn(response.status_code, [200, 201])

    def test_admin_can_create_everything(self):
        """Admin can create any resource"""
        self.api_client.force_authenticate(user=self.admin_user)

        # Create shift
        shift_data = {
            "guard": self.guard.id,
            "property": self.property.id,
            "start_time": "2024-01-01T09:00:00Z",
            "end_time": "2024-01-01T17:00:00Z",
            "hours_worked": 8,
        }
        response = self.api_client.post("/api/shifts/", shift_data, format="json")
        self.assertIn(response.status_code, [200, 201])

        # Create expense
        expense_data = {
            "property": self.property.id,
            "description": "Admin expense",
            "amount": "75.00",
        }
        response = self.api_client.post("/api/expenses/", expense_data, format="json")
        self.assertIn(response.status_code, [200, 201])


class PropertyAccessPermissionTestCase(APITestCase):
    """PropertyAccess specific tests"""

    def setUp(self):
        self.api_client = APIClient()

        # Create users
        self.admin_user = User.objects.create_user(
            username="admin", password="testpass123", email="admin@test.com"
        )
        self.guard_user = User.objects.create_user(
            username="guard", password="testpass123", email="guard@test.com"
        )

        UserRole.objects.create(user=self.admin_user, role="admin")
        UserRole.objects.create(user=self.guard_user, role="guard")

        # Create client and property
        client_user = User.objects.create_user(
            username="client", password="testpass123", email="client@test.com"
        )
        UserRole.objects.create(user=client_user, role="client")
        client = Client.objects.create(user=client_user, balance=Decimal("1000.00"))

        self.property = Property.objects.create(
            owner=client, address="Test Property", total_hours=100
        )

        # Create PropertyAccess with specific permissions
        self.property_access = PropertyAccess.objects.create(
            user=self.guard_user,
            property=self.property,
            access_type="assigned_guard",
            can_create_shifts=True,
            can_edit_shifts=True,
            can_create_expenses=False,
            can_edit_expenses=False,
            granted_by=self.admin_user,
        )

    def test_property_access_permissions_are_correct(self):
        """Verify that PropertyAccess specific permissions work"""
        access = PropertyAccess.objects.get(
            user=self.guard_user, property=self.property
        )

        self.assertEqual(access.access_type, "assigned_guard")
        self.assertTrue(access.can_create_shifts)
        self.assertTrue(access.can_edit_shifts)
        self.assertFalse(access.can_create_expenses)
        self.assertFalse(access.can_edit_expenses)

    def test_no_access_for_unassigned_properties(self):
        """Verify that no access exists for unassigned properties"""
        # Create another property
        another_client = Client.objects.create(
            user=User.objects.create_user(
                username="client2", password="test", email="client2@test.com"
            ),
            balance=Decimal("500.00"),
        )
        another_property = Property.objects.create(
            owner=another_client, address="Another Property", total_hours=50
        )

        # Verify no access exists
        no_access = PropertyAccess.objects.filter(
            user=self.guard_user, property=another_property
        ).exists()
        self.assertFalse(no_access)
