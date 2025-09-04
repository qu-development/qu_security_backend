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

    payload = {
        "guard": guard.id,
        "property": prop.id,
        "start_time": "2025-01-01T10:00:00Z",
        "end_time": "2025-01-01T12:00:00Z",
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

    payload = {
        "guard": guard.id,
        "property": prop.id,
        "start_time": "2025-02-01T08:00:00Z",
        "end_time": "2025-02-01T16:00:00Z",
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

    payload = {
        "guard": guard.id,
        "property": prop.id,
        "start_time": "2025-03-01T09:00:00Z",
        "end_time": "2025-03-01T13:00:00Z",
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

    # Create a shift for the armed guard
    shift = baker.make(
        "Shift",
        guard=guard,
        property=prop,
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
