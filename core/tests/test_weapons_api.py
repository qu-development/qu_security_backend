import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Guard, Weapon
from permissions.models import UserRole


@pytest.mark.django_db
def test_weapon_list_requires_authentication():
    """Test that weapon list endpoint requires authentication"""
    api = APIClient()
    url = reverse("core:weapon-list")
    resp = api.get(url)
    assert resp.status_code == 401


@pytest.mark.django_db
def test_weapon_list_as_authenticated_user():
    """Test weapon list endpoint with authenticated user"""
    # Arrange
    admin_user = baker.make(
        User, is_superuser=True
    )  # Use superuser to avoid permission issues
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)
    baker.make(Weapon, guard=guard, serial_number="ABC123", model="Glock 17")

    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:weapon-list")
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) >= 1  # At least one weapon should be returned
    # Find our weapon in the results
    our_weapon = next(
        (w for w in data["results"] if w["serial_number"] == "ABC123"), None
    )
    assert our_weapon is not None
    assert our_weapon["model"] == "Glock 17"


@pytest.mark.django_db
def test_weapon_create_requires_admin_or_manager():
    """Test that weapon creation requires admin or manager role"""
    # Arrange
    user = baker.make(User)
    guard = baker.make(Guard, user=user)
    UserRole.objects.create(user=user, role="guard", is_active=True)

    api = APIClient()
    api.force_authenticate(user=user)

    # Act
    url = reverse("core:weapon-list")
    data = {"guard": guard.id, "serial_number": "XYZ789", "model": "Smith & Wesson"}
    resp = api.post(url, data)

    # Assert
    assert resp.status_code == 403


@pytest.mark.django_db
def test_weapon_create_as_admin_succeeds():
    """Test weapon creation as admin user"""
    # Arrange
    admin_user = baker.make(User, is_superuser=True)
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:weapon-list")
    data = {"guard": guard.id, "serial_number": "XYZ789", "model": "Smith & Wesson"}
    resp = api.post(url, data)

    # Assert
    assert resp.status_code == 201
    weapon = Weapon.objects.get(serial_number="XYZ789")
    assert weapon.guard == guard
    assert weapon.model == "Smith & Wesson"


@pytest.mark.django_db
def test_weapon_create_duplicate_serial_number_for_same_guard_fails():
    """Test that creating a weapon with duplicate serial number for same guard fails"""
    # Arrange
    admin_user = baker.make(User, is_superuser=True)
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    # Create existing weapon
    baker.make(Weapon, guard=guard, serial_number="ABC123", model="Existing Model")

    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:weapon-list")
    data = {
        "guard": guard.id,
        "serial_number": "ABC123",  # Same serial number
        "model": "New Model",
    }
    resp = api.post(url, data)

    # Assert
    assert resp.status_code == 400
    # The error comes from the unique_together constraint
    assert "must make a unique set" in str(
        resp.data
    ) or "already has a weapon with this serial number" in str(resp.data)


@pytest.mark.django_db
def test_weapon_create_same_serial_number_different_guards_succeeds():
    """Test that creating weapons with same serial number for different guards succeeds"""
    # Arrange
    admin_user = baker.make(User, is_superuser=True)
    guard_user1 = baker.make(User, username="guard1")
    guard_user2 = baker.make(User, username="guard2")
    guard1 = baker.make(Guard, user=guard_user1)
    guard2 = baker.make(Guard, user=guard_user2)

    # Create weapon for first guard
    baker.make(Weapon, guard=guard1, serial_number="ABC123", model="Model 1")

    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act - create weapon with same serial number for different guard
    url = reverse("core:weapon-list")
    data = {
        "guard": guard2.id,
        "serial_number": "ABC123",  # Same serial number but different guard
        "model": "Model 2",
    }
    resp = api.post(url, data)

    # Assert
    assert resp.status_code == 201
    assert Weapon.objects.filter(serial_number="ABC123").count() == 2


@pytest.mark.django_db
def test_weapon_update_requires_admin_or_manager():
    """Test that weapon update requires admin or manager role"""
    # Arrange
    user = baker.make(User)
    guard = baker.make(Guard, user=user)
    weapon = baker.make(Weapon, guard=guard, serial_number="ABC123", model="Old Model")
    UserRole.objects.create(user=user, role="guard", is_active=True)

    api = APIClient()
    api.force_authenticate(user=user)

    # Act
    url = reverse("core:weapon-detail", kwargs={"pk": weapon.id})
    data = {"model": "New Model"}
    resp = api.patch(url, data)

    # Assert
    assert resp.status_code == 403


@pytest.mark.django_db
def test_weapon_update_as_admin_succeeds():
    """Test weapon update as admin user"""
    # Arrange
    admin_user = baker.make(User, is_superuser=True)
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)
    weapon = baker.make(Weapon, guard=guard, serial_number="ABC123", model="Old Model")

    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:weapon-detail", kwargs={"pk": weapon.id})
    data = {"model": "New Model"}
    resp = api.patch(url, data)

    # Assert
    assert resp.status_code == 200
    weapon.refresh_from_db()
    assert weapon.model == "New Model"


@pytest.mark.django_db
def test_weapon_update_duplicate_serial_number_fails():
    """Test that updating weapon with duplicate serial number for same guard fails"""
    # Arrange
    admin_user = baker.make(User, is_superuser=True)
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    baker.make(Weapon, guard=guard, serial_number="ABC123", model="Model 1")
    weapon2 = baker.make(Weapon, guard=guard, serial_number="XYZ789", model="Model 2")

    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act - try to update weapon2 with weapon1's serial number
    url = reverse("core:weapon-detail", kwargs={"pk": weapon2.id})
    data = {"serial_number": "ABC123"}  # Same as weapon1
    resp = api.patch(url, data)

    # Assert
    assert resp.status_code == 400
    # The error comes from the unique_together constraint or custom validation
    assert "must make a unique set" in str(
        resp.data
    ) or "already has another weapon with this serial number" in str(resp.data)


@pytest.mark.django_db
def test_weapon_delete_requires_admin_or_manager():
    """Test that weapon deletion requires admin or manager role"""
    # Arrange
    user = baker.make(User)
    guard = baker.make(Guard, user=user)
    weapon = baker.make(Weapon, guard=guard, serial_number="ABC123", model="Model")
    UserRole.objects.create(user=user, role="guard", is_active=True)

    api = APIClient()
    api.force_authenticate(user=user)

    # Act
    url = reverse("core:weapon-detail", kwargs={"pk": weapon.id})
    resp = api.delete(url)

    # Assert
    assert resp.status_code == 403


@pytest.mark.django_db
def test_weapon_delete_as_admin_succeeds():
    """Test weapon deletion as admin user"""
    # Arrange
    admin_user = baker.make(User, is_superuser=True)
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)
    weapon = baker.make(Weapon, guard=guard, serial_number="ABC123", model="Model")

    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:weapon-detail", kwargs={"pk": weapon.id})
    resp = api.delete(url)

    # Assert
    assert resp.status_code == 204
    # Check that weapon is soft deleted (if using soft delete) or actually deleted
    try:
        weapon.refresh_from_db()
        assert not weapon.is_active  # Soft delete
    except Weapon.DoesNotExist:
        # Hard delete is also acceptable
        pass


@pytest.mark.django_db
def test_weapon_retrieve_includes_guard_details():
    """Test that weapon retrieve endpoint includes guard details"""
    # Arrange
    admin_user = baker.make(User, is_superuser=True)
    guard_user = baker.make(User, first_name="John", last_name="Doe")
    guard = baker.make(Guard, user=guard_user)
    weapon = baker.make(Weapon, guard=guard, serial_number="ABC123", model="Glock 17")

    api = APIClient()
    api.force_authenticate(user=admin_user)

    # Act
    url = reverse("core:weapon-detail", kwargs={"pk": weapon.id})
    resp = api.get(url)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["serial_number"] == "ABC123"
    assert data["model"] == "Glock 17"
    assert data["guard_details"]["user_details"]["first_name"] == "John"
    assert data["guard_details"]["user_details"]["last_name"] == "Doe"
