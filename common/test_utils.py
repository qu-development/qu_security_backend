"""
Base test classes and utilities for testing
"""

from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

from core.models import Client, Guard, Property
from permissions.models import PropertyAccess, UserRole


class BaseAPITestCase(APITestCase):
    """Base test case with common setup"""

    def setUp(self):
        self.client = APIClient()
        self.setup_users()
        self.setup_test_data()

    def setup_users(self):
        """Create test users with different roles"""
        # Admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123",
            email="admin@test.com",
            is_superuser=True,
        )
        UserRole.objects.create(user=self.admin_user, role="admin")

        # Manager user
        self.manager_user = User.objects.create_user(
            username="manager", password="testpass123", email="manager@test.com"
        )
        UserRole.objects.create(user=self.manager_user, role="manager")

        # Client user
        self.client_user = User.objects.create_user(
            username="client", password="testpass123", email="client@test.com"
        )
        UserRole.objects.create(user=self.client_user, role="client")

        # Guard user
        self.guard_user = User.objects.create_user(
            username="guard", password="testpass123", email="guard@test.com"
        )
        UserRole.objects.create(user=self.guard_user, role="guard")

    def setup_test_data(self):
        """Create test business objects"""
        # Create client profile
        self.client_profile = Client.objects.create(
            user=self.client_user, phone="123-456-7890", balance=Decimal("1000.00")
        )

        # Create guard profile
        self.guard_profile = Guard.objects.create(
            user=self.guard_user, phone="098-765-4321"
        )

        # Create property
        self.property = Property.objects.create(
            owner=self.client_profile, address="123 Test Street", total_hours=100
        )

    def authenticate_as(self, user):
        """Helper method to authenticate as a specific user"""
        self.client.force_authenticate(user=user)

    def create_property_access(
        self, user, property_obj, access_type="viewer", **permissions
    ):
        """Helper method to create property access"""
        return PropertyAccess.objects.create(
            user=user,
            property=property_obj,
            access_type=access_type,
            granted_by=self.admin_user,
            **permissions,
        )

    def assert_response_success(self, response, expected_status=200):
        """Assert response is successful"""
        self.assertEqual(response.status_code, expected_status)

    def assert_response_error(self, response, expected_status=400):
        """Assert response is error"""
        self.assertEqual(response.status_code, expected_status)


class TestDataFactory:
    """Factory for creating test data"""

    @staticmethod
    def create_user(username, email=None, **kwargs):
        """Create a test user"""
        if not email:
            email = f"{username}@test.com"
        return User.objects.create_user(
            username=username, email=email, password="testpass123", **kwargs
        )

    @staticmethod
    def create_property(owner, address=None, **kwargs):
        """Create a test property"""
        if not address:
            address = f"Test Address {owner.user.username}"
        return Property.objects.create(
            owner=owner, address=address, total_hours=100, **kwargs
        )

    @staticmethod
    def create_client(user=None, **kwargs):
        """Create a test client"""
        if not user:
            user = TestDataFactory.create_user("test_client")
        return Client.objects.create(
            user=user, phone="123-456-7890", balance=Decimal("1000.00"), **kwargs
        )

    @staticmethod
    def create_guard(user=None, **kwargs):
        """Create a test guard"""
        if not user:
            user = TestDataFactory.create_user("test_guard")
        return Guard.objects.create(user=user, phone="098-765-4321", **kwargs)
