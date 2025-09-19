import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client, Guard, Property, Weapon


@pytest.mark.django_db
def test_shift_create_by_any_authenticated_user_succeeds():
    # Arrange: create a property (owned by a client) and a guard
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client, address="Site A")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    acting_user = baker.make(User)  # plain authenticated user
    api = APIClient()
    api.force_authenticate(user=acting_user)

    # Create a weapon for the guard
    weapon = baker.make(
        Weapon, guard=guard, serial_number="TEST123", model="Test Model"
    )

    payload = {
        "guard": guard.id,
        "property": prop.id,
        "planned_start_time": "2025-01-01T09:00:00Z",
        "planned_end_time": "2025-01-01T13:00:00Z",
        "start_time": "2025-01-01T10:00:00Z",
        "end_time": "2025-01-01T12:00:00Z",
        "is_armed": True,
        "weapon": weapon.id,
    }

    # Act
    url = reverse("core:shift-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert data["guard"] == guard.id
    assert data["property"] == prop.id


@pytest.mark.django_db
def test_shift_create_by_guard_for_self_succeeds():
    # Arrange: create a property and authenticate as a guard user
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client, address="Site B")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    api = APIClient()
    api.force_authenticate(user=guard_user)

    # Create a weapon for the guard
    weapon = baker.make(
        Weapon, guard=guard, serial_number="GUARD456", model="Guard Model"
    )

    payload = {
        "guard": guard.id,
        "property": prop.id,
        "planned_start_time": "2025-02-01T07:00:00Z",
        "planned_end_time": "2025-02-01T17:00:00Z",
        "start_time": "2025-02-01T08:00:00Z",
        "end_time": "2025-02-01T16:00:00Z",
        "is_armed": True,
        "weapon": weapon.id,
    }

    # Act
    url = reverse("core:shift-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert data["guard"] == guard.id
    assert data["property"] == prop.id


@pytest.mark.django_db
def test_shift_create_unauthenticated_returns_401():
    # Arrange: create a property and a guard
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client, address="Site C")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    api = APIClient()  # no authentication

    # Create a weapon for the guard
    weapon = baker.make(
        Weapon, guard=guard, serial_number="UNAUTH789", model="Unauth Model"
    )

    payload = {
        "guard": guard.id,
        "property": prop.id,
        "planned_start_time": "2025-03-01T08:00:00Z",
        "planned_end_time": "2025-03-01T14:00:00Z",
        "start_time": "2025-03-01T09:00:00Z",
        "end_time": "2025-03-01T13:00:00Z",
        "is_armed": True,
        "weapon": weapon.id,
    }

    # Act
    url = reverse("core:shift-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_shift_with_armed_guard_returns_weapon_details():
    # Arrange: create a property, an armed guard with a weapon, and a shift
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client, address="Site D")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user, is_armed=True)
    baker.make(Weapon, guard=guard, serial_number="ABC123", model="Glock 17")

    # Create a weapon for the guard (use the one already created)
    weapon = Weapon.objects.get(guard=guard, serial_number="ABC123")

    # Create a shift for the armed guard with the weapon assigned
    shift = baker.make(
        "Shift",
        guard=guard,
        property=prop,
        is_armed=True,
        weapon=weapon,
        planned_start_time="2025-04-01T08:00:00Z",
        planned_end_time="2025-04-01T18:00:00Z",
        start_time="2025-04-01T09:00:00Z",
        end_time="2025-04-01T17:00:00Z",
    )

    api = APIClient()
    api.force_authenticate(user=guard_user)

    # Act
    url = reverse("core:shift-detail", kwargs={"pk": shift.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "weapon_details" in data
    assert data["weapon_details"] is not None
    assert data["weapon_details"]["serial_number"] == "ABC123"
    assert data["weapon_details"]["model"] == "Glock 17"


@pytest.mark.django_db
def test_shift_with_unarmed_guard_returns_no_weapon_details():
    # Arrange: create a property, an unarmed guard, and a shift
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client, address="Site E")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user, is_armed=False)

    # Create a shift for the unarmed guard
    shift = baker.make(
        "Shift",
        guard=guard,
        property=prop,
        is_armed=False,
        weapon=None,
        planned_start_time="2025-05-01T08:00:00Z",
        planned_end_time="2025-05-01T18:00:00Z",
        start_time="2025-05-01T09:00:00Z",
        end_time="2025-05-01T17:00:00Z",
    )

    api = APIClient()
    api.force_authenticate(user=guard_user)

    # Act
    url = reverse("core:shift-detail", kwargs={"pk": shift.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "weapon_details" in data
    assert data["weapon_details"] is None


@pytest.mark.django_db
def test_shift_with_specific_weapon_returns_correct_weapon_details():
    # Arrange: create a property, an armed guard with multiple weapons, and a shift with a specific weapon
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client, address="Site F")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user, is_armed=True)

    # Create multiple weapons for the guard
    baker.make(Weapon, guard=guard, serial_number="XYZ789", model="Beretta 92")
    weapon2 = baker.make(
        Weapon, guard=guard, serial_number="DEF456", model="Sig Sauer P320"
    )

    # Create a shift with a specific weapon assigned
    shift = baker.make(
        "Shift",
        guard=guard,
        property=prop,
        is_armed=True,
        weapon=weapon2,  # Assign the second weapon specifically
        planned_start_time="2025-06-01T08:00:00Z",
        planned_end_time="2025-06-01T18:00:00Z",
        start_time="2025-06-01T09:00:00Z",
        end_time="2025-06-01T17:00:00Z",
    )

    api = APIClient()
    api.force_authenticate(user=guard_user)

    # Act
    url = reverse("core:shift-detail", kwargs={"pk": shift.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "weapon_details" in data
    assert data["weapon_details"] is not None
    assert data["weapon_details"]["serial_number"] == "DEF456"
    assert data["weapon_details"]["model"] == "Sig Sauer P320"


@pytest.mark.django_db
def test_shift_planned_hours_worked_calculation():
    """Test that planned_hours_worked is calculated correctly"""
    # Arrange: create guard and property
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client)

    acting_user = baker.make(User)
    api = APIClient()
    api.force_authenticate(user=acting_user)

    # Test case 1: 4 hour shift (9:00 AM to 1:00 PM)
    payload = {
        "guard": guard.id,
        "property": prop.id,
        "planned_start_time": "2025-01-01T09:00:00Z",
        "planned_end_time": "2025-01-01T13:00:00Z",
        "is_armed": False,
    }

    # Act
    url = reverse("core:shift-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert float(data["planned_hours_worked"]) == 4.0


@pytest.mark.django_db
def test_shift_planned_hours_worked_half_hours():
    """Test planned_hours_worked with half hours"""
    # Arrange: create guard and property
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client)

    acting_user = baker.make(User)
    api = APIClient()
    api.force_authenticate(user=acting_user)

    # Test case: 2.5 hour shift (9:00 AM to 11:30 AM)
    payload = {
        "guard": guard.id,
        "property": prop.id,
        "planned_start_time": "2025-01-01T09:00:00Z",
        "planned_end_time": "2025-01-01T11:30:00Z",
        "is_armed": False,
    }

    # Act
    url = reverse("core:shift-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert float(data["planned_hours_worked"]) == 2.5


@pytest.mark.django_db
def test_shift_planned_hours_worked_no_planned_times():
    """Test planned_hours_worked when planned times are not set"""
    # Arrange: create guard and property
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client)

    acting_user = baker.make(User)
    api = APIClient()
    api.force_authenticate(user=acting_user)

    # Test case: No planned times
    payload = {
        "guard": guard.id,
        "property": prop.id,
        "is_armed": False,
    }

    # Act
    url = reverse("core:shift-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert float(data["planned_hours_worked"]) == 0.0


@pytest.mark.django_db
def test_shift_planned_hours_worked_update():
    """Test that planned_hours_worked updates when planned times change"""
    # Arrange: create shift
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client)

    shift = baker.make(
        "Shift",
        guard=guard,
        property=prop,
        planned_start_time="2025-01-01T09:00:00Z",
        planned_end_time="2025-01-01T13:00:00Z",  # 4 hours initially
    )

    api = APIClient()
    api.force_authenticate(user=guard_user)  # Authenticate as the guard user

    # Act: Update to 8 hours
    url = reverse("core:shift-detail", kwargs={"pk": shift.id})
    payload = {
        "planned_start_time": "2025-01-01T08:00:00Z",
        "planned_end_time": "2025-01-01T16:00:00Z",
    }
    resp = api.patch(url, payload, format="json")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["planned_hours_worked"]) == 8.0
