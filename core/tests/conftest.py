import pytest
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models import Client, Guard, Property


@pytest.fixture(scope="session", autouse=True)
def django_db_setup():
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        # Add defaults expected by Django's DB wrapper to avoid KeyError
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
        "OPTIONS": {},
        "TIME_ZONE": None,
        "TEST": {
            "NAME": None,
            "MIRROR": None,
            "CHARSET": None,
            "COLLATION": None,
        },
    }


@pytest.fixture
def api_client():
    """Create an API client for testing"""
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def create_test_data():
    """Create test data for use in tests"""
    # Create users
    client_user = User.objects.create_user(
        username="testclient", email="client@test.com", password="testpass123"
    )
    guard_user = User.objects.create_user(
        username="testguard", email="guard@test.com", password="testpass123"
    )

    # Create client and guard profiles
    client = Client.objects.create(user=client_user, phone="1234567890")
    guard = Guard.objects.create(user=guard_user, phone="0987654321")

    # Create property
    property_obj = Property.objects.create(
        owner=client, name="Test Property", address="123 Test Street"
    )

    return client, guard, property_obj
