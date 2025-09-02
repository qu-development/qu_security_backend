"""
Base test classes and utilities for testing
"""

import secrets
import string
from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase

from core.models import Client, Guard, Property
from permissions.models import PropertyAccess, UserRole


def generate_test_password(length=12):
    """Generate a random password for testing"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class BaseAPITestCase(APITestCase):
    """Base test case with common setup"""

    def setUp(self):
        self.client = APIClient()
        # Store passwords for potential use in tests
        self.test_passwords = {}
        self.setup_users()
        self.setup_test_data()

    def setup_users(self):
        """Create test users with different roles"""
        # Generate unique passwords for each user
        admin_password = generate_test_password()
        manager_password = generate_test_password()
        client_password = generate_test_password()
        guard_password = generate_test_password()

        # Store passwords in case tests need them
        self.test_passwords = {
            "admin": admin_password,
            "manager": manager_password,
            "client": client_password,
            "guard": guard_password,
        }

        # Admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            password=admin_password,
            email="admin@test.com",
            is_superuser=True,
        )
        UserRole.objects.create(user=self.admin_user, role="admin")

        # Manager user
        self.manager_user = User.objects.create_user(
            username="manager", password=manager_password, email="manager@test.com"
        )
        UserRole.objects.create(user=self.manager_user, role="manager")

        # Client user
        self.client_user = User.objects.create_user(
            username="client", password=client_password, email="client@test.com"
        )
        UserRole.objects.create(user=self.client_user, role="client")

        # Guard user
        self.guard_user = User.objects.create_user(
            username="guard", password=guard_password, email="guard@test.com"
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
            owner=self.client_profile, address="123 Test Street"
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
    def create_user(username, email=None, password=None, **kwargs):
        """Create a test user"""
        if not email:
            email = f"{username}@test.com"
        if not password:
            password = generate_test_password()
        return User.objects.create_user(
            username=username, email=email, password=password, **kwargs
        )

    @staticmethod
    def create_property(owner, address=None, **kwargs):
        """Create a test property"""
        if not address:
            address = f"Test Address {owner.user.username}"
        return Property.objects.create(
            owner=owner, address=address, **kwargs
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
