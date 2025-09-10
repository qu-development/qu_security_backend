import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client, Guard, Property, Service, Shift
from permissions.models import UserRole


@pytest.mark.django_db
def test_guard_properties_shifts_endpoint_returns_correct_data():
    """Test that guard properties-shifts endpoint returns properties and shifts for a specific guard"""
    # Arrange: Create users, guard, client, properties, service, and shifts
    guard_user = baker.make(User, first_name="John", last_name="Doe")
    guard = baker.make(Guard, user=guard_user)
    UserRole.objects.create(user=guard_user, role="guard", is_active=True)

    client_user = baker.make(User)
    client = baker.make(Client, user=client_user)

    property1 = baker.make(
        Property, owner=client, name="Property 1", address="123 Main St"
    )
    property2 = baker.make(
        Property, owner=client, name="Property 2", address="456 Oak Ave"
    )

    service = baker.make(Service, name="Security Service", rate=25.00)

    # Create shifts for the guard at different properties
    baker.make(
        Shift,
        guard=guard,
        property=property1,
        service=service,
        hours_worked=8,
        planned_start_time="2025-01-01T08:00:00Z",
        planned_end_time="2025-01-01T16:00:00Z",
    )
    baker.make(
        Shift,
        guard=guard,
        property=property1,
        service=service,
        hours_worked=6,
        planned_start_time="2025-01-02T09:00:00Z",
        planned_end_time="2025-01-02T15:00:00Z",
    )
    baker.make(
        Shift,
        guard=guard,
        property=property2,
        service=service,
        hours_worked=10,
        planned_start_time="2025-01-03T07:00:00Z",
        planned_end_time="2025-01-03T17:00:00Z",
    )

    # Create admin user for authentication
    admin_user = baker.make(User, is_superuser=True)
    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:guard-properties-shifts", kwargs={"pk": guard.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()

    # Check guard basic info
    assert data["id"] == guard.id
    assert data["name"] == "John Doe"

    # Check properties and shifts structure
    properties_and_shifts = data["properties_and_shifts"]
    assert len(properties_and_shifts) == 2  # Two properties

    # Find property1 data
    prop1_data = next(
        item for item in properties_and_shifts if item["property"]["id"] == property1.id
    )
    assert prop1_data["property"]["name"] == "Property 1"
    assert len(prop1_data["shifts"]) == 2  # Two shifts for property1

    # Find property2 data
    prop2_data = next(
        item for item in properties_and_shifts if item["property"]["id"] == property2.id
    )
    assert prop2_data["property"]["name"] == "Property 2"
    assert len(prop2_data["shifts"]) == 1  # One shift for property2


@pytest.mark.django_db
def test_guard_properties_shifts_endpoint_empty_when_no_shifts():
    """Test that guard properties-shifts endpoint returns empty list when guard has no shifts"""
    # Arrange: Create guard with no shifts
    guard_user = baker.make(User, first_name="Jane", last_name="Smith")
    guard = baker.make(Guard, user=guard_user)
    UserRole.objects.create(user=guard_user, role="guard", is_active=True)

    admin_user = baker.make(User, is_superuser=True)
    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:guard-properties-shifts", kwargs={"pk": guard.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == guard.id
    assert data["name"] == "Jane Smith"
    assert data["properties_and_shifts"] == []


@pytest.mark.django_db
def test_guard_properties_shifts_endpoint_not_found():
    """Test that guard properties-shifts endpoint returns 404 for non-existent guard"""
    admin_user = baker.make(User, is_superuser=True)
    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:guard-properties-shifts", kwargs={"pk": 99999})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 404


@pytest.mark.django_db
def test_property_guards_shifts_endpoint_returns_correct_data():
    """Test that property guards-shifts endpoint returns guards and shifts for a specific property"""
    # Arrange: Create users, guards, client, property, service, and shifts
    client_user = baker.make(User)
    client = baker.make(Client, user=client_user)
    property_obj = baker.make(
        Property, owner=client, name="Test Property", address="789 Pine St"
    )

    guard_user1 = baker.make(User, first_name="Guard", last_name="One")
    guard_user2 = baker.make(User, first_name="Guard", last_name="Two")
    guard1 = baker.make(Guard, user=guard_user1)
    guard2 = baker.make(Guard, user=guard_user2)

    UserRole.objects.create(user=guard_user1, role="guard", is_active=True)
    UserRole.objects.create(user=guard_user2, role="guard", is_active=True)

    service = baker.make(Service, name="Night Security", rate=30.00)

    # Create shifts for different guards at the same property
    baker.make(
        Shift,
        guard=guard1,
        property=property_obj,
        service=service,
        hours_worked=8,
        planned_start_time="2025-02-01T08:00:00Z",
        planned_end_time="2025-02-01T16:00:00Z",
    )
    baker.make(
        Shift,
        guard=guard1,
        property=property_obj,
        service=service,
        hours_worked=6,
        planned_start_time="2025-02-02T09:00:00Z",
        planned_end_time="2025-02-02T15:00:00Z",
    )
    baker.make(
        Shift,
        guard=guard2,
        property=property_obj,
        service=service,
        hours_worked=12,
        planned_start_time="2025-02-03T08:00:00Z",
        planned_end_time="2025-02-03T20:00:00Z",
    )

    # Create admin user for authentication
    admin_user = baker.make(User, is_superuser=True)
    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:property-guards-shifts", kwargs={"pk": property_obj.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()

    # Check property basic info
    assert data["id"] == property_obj.id
    assert data["name"] == "Test Property"

    # Check guards and shifts structure
    guards_and_shifts = data["guards_and_shifts"]
    assert len(guards_and_shifts) == 2  # Two guards

    # Find guard1 data
    guard1_data = next(
        item for item in guards_and_shifts if item["guard"]["id"] == guard1.id
    )
    assert guard1_data["guard"]["name"] == "Guard One"
    assert len(guard1_data["shifts"]) == 2  # Two shifts for guard1

    # Find guard2 data
    guard2_data = next(
        item for item in guards_and_shifts if item["guard"]["id"] == guard2.id
    )
    assert guard2_data["guard"]["name"] == "Guard Two"
    assert len(guard2_data["shifts"]) == 1  # One shift for guard2


@pytest.mark.django_db
def test_property_guards_shifts_endpoint_empty_when_no_shifts():
    """Test that property guards-shifts endpoint returns empty list when property has no shifts"""
    # Arrange: Create property with no shifts
    client_user = baker.make(User)
    client = baker.make(Client, user=client_user)
    property_obj = baker.make(
        Property, owner=client, name="Empty Property", address="000 Empty St"
    )

    admin_user = baker.make(User, is_superuser=True)
    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:property-guards-shifts", kwargs={"pk": property_obj.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == property_obj.id
    assert data["name"] == "Empty Property"
    assert data["guards_and_shifts"] == []


@pytest.mark.django_db
def test_property_guards_shifts_endpoint_not_found():
    """Test that property guards-shifts endpoint returns 404 for non-existent property"""
    admin_user = baker.make(User, is_superuser=True)
    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:property-guards-shifts", kwargs={"pk": 99999})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 404


@pytest.mark.django_db
def test_guard_properties_shifts_endpoint_permissions():
    """Test that guard properties-shifts endpoint respects permissions"""
    # Arrange: Create guard and unauthenticated client
    guard_user = baker.make(User, first_name="Test", last_name="Guard")
    guard = baker.make(Guard, user=guard_user)
    UserRole.objects.create(user=guard_user, role="guard", is_active=True)

    api = APIClient()
    # No authentication

    # Act
    url = reverse("core:guard-properties-shifts", kwargs={"pk": guard.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 401  # Unauthorized


@pytest.mark.django_db
def test_property_guards_shifts_endpoint_permissions():
    """Test that property guards-shifts endpoint respects permissions"""
    # Arrange: Create property and unauthenticated client
    client_user = baker.make(User)
    client = baker.make(Client, user=client_user)
    property_obj = baker.make(Property, owner=client, name="Test Property")

    api = APIClient()
    # No authentication

    # Act
    url = reverse("core:property-guards-shifts", kwargs={"pk": property_obj.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 401  # Unauthorized
