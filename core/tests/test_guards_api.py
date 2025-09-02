import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client, Guard, GuardPropertyTariff, Property
from permissions.models import UserRole


@pytest.mark.django_db
def test_guard_list_as_guard_shows_only_self():
    # Arrange: two guards with roles
    guard_user1 = baker.make(User, first_name="G1")
    guard_user2 = baker.make(User, first_name="G2")
    g1 = baker.make(Guard, user=guard_user1)
    baker.make(Guard, user=guard_user2)
    UserRole.objects.create(user=guard_user1, role="guard", is_active=True)
    UserRole.objects.create(user=guard_user2, role="guard", is_active=True)

    api = APIClient()
    api.force_authenticate(user=guard_user1)

    # Act
    url = reverse("core:guard-list")
    resp = api.get(url)

    # Assert: only own guard profile returned
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict) and "results" in data
    returned_ids = {item["id"] for item in data["results"]}
    assert returned_ids == {g1.id}


@pytest.mark.django_db
def test_guard_list_as_client_shows_only_guards_on_owned_properties():
    # Arrange: two clients with properties and tariffs to guards
    client_user1 = baker.make(User)
    client_user2 = baker.make(User)
    client1 = baker.make(Client, user=client_user1)
    client2 = baker.make(Client, user=client_user2)
    UserRole.objects.create(user=client_user1, role="client", is_active=True)
    UserRole.objects.create(user=client_user2, role="client", is_active=True)

    p1 = baker.make(Property, owner=client1, address="P1")
    p2 = baker.make(Property, owner=client2, address="P2")

    gu1 = baker.make(User)
    gu2 = baker.make(User)
    g1 = baker.make(Guard, user=gu1)
    g2 = baker.make(Guard, user=gu2)

    # Tariffs linking guards to properties (client1 should only see g1)
    baker.make(GuardPropertyTariff, guard=g1, property=p1, rate="10.00", is_active=True)
    baker.make(GuardPropertyTariff, guard=g2, property=p2, rate="12.00", is_active=True)

    api = APIClient()
    api.force_authenticate(user=client_user1)

    # Act
    url = reverse("core:guard-list")
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict) and "results" in data
    returned_ids = {item["id"] for item in data["results"]}
    assert returned_ids == {g1.id}


@pytest.mark.django_db
def test_guard_create_requires_admin_or_manager():
    # Arrange: authenticated non-privileged user
    acting = baker.make(User)
    target_user = baker.make(User)

    api = APIClient()
    api.force_authenticate(user=acting)

    payload = {
        "user": target_user.id,
        "phone": "+1111111111",
        "ssn": "SSN123",
        "address": "Addr",
    }

    # Act
    url = reverse("core:guard-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_guard_create_as_superuser_succeeds():
    # Arrange: superuser can create guard
    admin = baker.make(User, is_superuser=True, is_staff=True)
    target_user = baker.make(User)

    api = APIClient()
    api.force_authenticate(user=admin)

    payload = {
        "user": target_user.id,
        "phone": "+12223334444",
        "address": "Somewhere",
    }

    # Act
    url = reverse("core:guard-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"] == target_user.id
    assert data["phone"] == "+12223334444"


@pytest.mark.django_db
def test_guard_update_forbidden_for_non_admin():
    # Arrange: guard attempts to update (should be forbidden)
    g_user = baker.make(User)
    UserRole.objects.create(user=g_user, role="guard", is_active=True)
    g = baker.make(Guard, user=g_user, phone="+1000")

    api = APIClient()
    api.force_authenticate(user=g_user)

    # Act
    url = reverse("core:guard-detail", args=[g.id])
    resp = api.patch(url, {"phone": "+2000"}, format="json")

    # Assert
    assert resp.status_code in (401, 403)
