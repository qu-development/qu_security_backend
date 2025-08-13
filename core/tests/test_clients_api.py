from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client


@pytest.mark.django_db
def test_client_list_returns_flattened_fields_without_user_details():
    # Arrange: create two clients with linked users
    u1 = baker.make(User, first_name="John", last_name="Doe", email="john1@example.com")
    u2 = baker.make(User, first_name="Jane", last_name="Roe", email="jane2@example.com")
    baker.make(Client, user=u1, phone="+10000000001")
    baker.make(Client, user=u2, phone="+10000000002")

    user = baker.make(User)  # any authenticated user can list
    client = APIClient()
    client.force_authenticate(user=user)

    # Act
    url = reverse("core:client-list")
    resp = client.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    # Paginated response
    assert isinstance(data, dict)
    assert "results" in data
    assert len(data["results"]) >= 2

    item = data["results"][0]
    expected_keys = {
        "id",
        "user",
        "first_name",
        "last_name",
        "email",
        "phone",
        "balance",
        "created_at",
        "updated_at",
        "is_active",
    }
    assert expected_keys.issubset(set(item.keys()))
    assert "user_details" not in item


@pytest.mark.django_db
def test_client_retrieve_includes_counts_and_totals():
    # Arrange
    u = baker.make(
        User, first_name="Alice", last_name="Smith", email="alice@example.com"
    )
    c = baker.make(Client, user=u, phone="+19999999999")

    user = baker.make(User)
    client = APIClient()
    client.force_authenticate(user=user)

    # Act
    url = reverse("core:client-detail", args=[c.id])
    resp = client.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "properties_count" in data
    assert "total_expenses" in data
    # Newly created client without data should have zeros
    assert data["properties_count"] == 0
    # total_expenses might be serialized as string, normalize to Decimal
    total = Decimal(str(data["total_expenses"]))
    assert total == Decimal("0") or total == Decimal("0.00")


@pytest.mark.django_db
def test_client_create_requires_admin_or_manager():
    # Arrange: authenticated but non-privileged user
    user = baker.make(User)
    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "first_name": "Carl",
        "last_name": "Sagan",
        "email": "carl@example.com",
        "phone": "+5541998709822",
    }

    # Act
    url = reverse("core:client-list")
    resp = client.post(url, payload, format="json")

    # Assert
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_client_create_success_as_superuser_creates_user_and_client():
    # Arrange: superuser bypasses role checks
    admin = baker.make(User, is_superuser=True, is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin)

    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "phone": "+5541998709822",
    }

    # Act
    url = reverse("core:client-list")
    resp = client.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 201
    data = resp.json()

    # Response shape assertions
    assert data["first_name"] == payload["first_name"]
    assert data["last_name"] == payload["last_name"]
    assert data["email"] == payload["email"]
    assert data["phone"] == payload["phone"]
    for key in ("created_at", "updated_at", "is_active", "user"):
        assert key in data
    assert "user_details" not in data

    # Verify created User has unusable password and no elevated flags
    created_client = Client.objects.get(id=data["id"])  # type: ignore[index]
    created_user = created_client.user
    assert not created_user.has_usable_password()
    assert created_user.is_staff is False
    assert created_user.is_superuser is False


@pytest.mark.django_db
def test_client_create_duplicate_email_returns_400():
    # Arrange
    admin = baker.make(User, is_superuser=True, is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin)

    # Existing user with the same email
    baker.make(User, email="dup@example.com")

    payload = {
        "first_name": "Dupe",
        "last_name": "Case",
        "email": "dup@example.com",
        "phone": "+1111111111",
    }

    url = reverse("core:client-list")
    resp = client.post(url, payload, format="json")

    assert resp.status_code == 400
    data = resp.json()
    assert "email" in data


@pytest.mark.django_db
def test_client_update_successfully_updates_user_and_client_fields():
    # Arrange
    admin = baker.make(User, is_superuser=True, is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin)

    # Existing client
    old_user = baker.make(
        User, first_name="Old", last_name="Name", email="old@example.com"
    )
    c = baker.make(Client, user=old_user, phone="+1000")

    payload = {
        "email": "new@example.com",
        "phone": "+2000",
        "first_name": "New",
        "last_name": "Name",
    }

    # Act
    url = reverse("core:client-detail", args=[c.id])
    resp = client.patch(url, payload, format="json")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["phone"] == "+2000"
    # Refresh from DB and verify
    c.refresh_from_db()
    assert c.phone == "+2000"
    c.user.refresh_from_db()
    assert c.user.email == "new@example.com"
    assert c.user.first_name == "New"


@pytest.mark.django_db
def test_client_update_email_conflict_returns_400():
    # Arrange
    admin = baker.make(User, is_superuser=True, is_staff=True)
    client = APIClient()
    client.force_authenticate(user=admin)

    # Target client
    target_user = baker.make(User, email="target@example.com")
    c = baker.make(Client, user=target_user, phone="+1000")

    # Another user with conflicting email
    baker.make(User, email="conflict@example.com")

    payload = {"email": "conflict@example.com"}

    # Act
    url = reverse("core:client-detail", args=[c.id])
    resp = client.patch(url, payload, format="json")

    # Assert
    assert resp.status_code == 400
    data = resp.json()
    assert "email" in data
