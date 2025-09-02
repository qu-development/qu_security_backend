import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client, Guard, Property, Shift
from permissions.utils import PermissionManager


@pytest.mark.django_db
def test_shift_list_guard_sees_only_own_shifts():
    # Arrange: two guards, one client/property, two shifts (one per guard)
    owner_user = baker.make(User)
    client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=client, address="Alpha Site")

    guard_user_1 = baker.make(User)
    guard_1 = baker.make(Guard, user=guard_user_1)
    guard_user_2 = baker.make(User)
    guard_2 = baker.make(Guard, user=guard_user_2)

    baker.make(
        Shift,
        guard=guard_1,
        property=prop,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=4),
    )
    baker.make(
        Shift,
        guard=guard_2,
        property=prop,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )

    # Assign roles
    PermissionManager.assign_user_role(guard_user_1, "guard", assigned_by=owner_user)

    # Act: list as guard 1
    api = APIClient()
    api.force_authenticate(user=guard_user_1)
    url = reverse("core:shift-list")
    resp = api.get(url)

    # Assert: only own shifts returned
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict) and "results" in data  # paginated
    assert len(data["results"]) == 1
    assert data["results"][0]["guard"] == guard_1.id


@pytest.mark.django_db
def test_shift_list_client_sees_only_shifts_on_their_properties():
    # Arrange: two clients, one property each, shared guard
    client_user_1 = baker.make(User)
    client_1 = baker.make(Client, user=client_user_1)
    prop_1 = baker.make(Property, owner=client_1, address="P1")

    client_user_2 = baker.make(User)
    client_2 = baker.make(Client, user=client_user_2)
    prop_2 = baker.make(Property, owner=client_2, address="P2")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    baker.make(
        Shift,
        guard=guard,
        property=prop_1,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=6),
    )
    baker.make(
        Shift,
        guard=guard,
        property=prop_2,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=5),
    )

    # Assign role to client 1
    PermissionManager.assign_user_role(
        client_user_1, "client", assigned_by=client_user_1
    )

    # Act: list as client 1
    api = APIClient()
    api.force_authenticate(user=client_user_1)
    url = reverse("core:shift-list")
    resp = api.get(url)

    # Assert: only shifts on client's properties
    assert resp.status_code == 200
    data = resp.json()
    ids = [item["property"] for item in data.get("results", [])]
    assert set(ids) == {prop_1.id}


@pytest.mark.django_db
def test_shift_update_assigned_guard_ok_and_other_guard_forbidden():
    # Arrange
    owner_user = baker.make(User)
    client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=client, address="Gamma")

    guard_user_1 = baker.make(User)
    guard_1 = baker.make(Guard, user=guard_user_1)
    guard_user_2 = baker.make(User)
    baker.make(Guard, user=guard_user_2)

    shift = baker.make(
        Shift,
        guard=guard_1,
        property=prop,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=8),
    )

    PermissionManager.assign_user_role(guard_user_1, "guard", assigned_by=owner_user)
    PermissionManager.assign_user_role(guard_user_2, "guard", assigned_by=owner_user)

    # Act: assigned guard can update
    api = APIClient()
    api.force_authenticate(user=guard_user_1)
    url = reverse("core:shift-detail", args=[shift.id])
    resp = api.patch(url, {"status": "completed"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    # Act: other guard cannot update (403 or 404 due to queryset filtering)
    api2 = APIClient()
    api2.force_authenticate(user=guard_user_2)
    resp2 = api2.patch(url, {"status": "voided"}, format="json")
    assert resp2.status_code in (403, 404)


@pytest.mark.django_db
def test_shift_update_manager_ok():
    # Arrange
    manager_user = baker.make(User)
    owner_user = baker.make(User)
    client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=client, address="Delta")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    shift = baker.make(
        Shift,
        guard=guard,
        property=prop,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=8),
    )

    PermissionManager.assign_user_role(
        manager_user, "manager", assigned_by=manager_user
    )

    # Act
    api = APIClient()
    api.force_authenticate(user=manager_user)
    url = reverse("core:shift-detail", args=[shift.id])
    resp = api.patch(url, {"status": "completed"}, format="json")

    # Assert
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


@pytest.mark.django_db
def test_shift_soft_delete_and_restore():
    # Arrange
    manager_user = baker.make(User)
    PermissionManager.assign_user_role(
        manager_user, "manager", assigned_by=manager_user
    )

    owner_user = baker.make(User)
    client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=client, address="Omega")
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)
    shift = baker.make(
        Shift,
        guard=guard,
        property=prop,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=4),
    )

    api = APIClient()
    api.force_authenticate(user=manager_user)

    # Soft delete
    url_soft = reverse("core:shift-soft-delete", args=[shift.id])
    resp_soft = api.post(url_soft)
    assert resp_soft.status_code in (200, 204)

    # List should exclude inactive by default
    url_list = reverse("core:shift-list")
    resp_list = api.get(url_list)
    assert resp_list.status_code == 200
    assert all(item["id"] != shift.id for item in resp_list.json().get("results", []))

    # Include inactive should return it
    resp_list_inactive = api.get(url_list + "?include_inactive=true")
    assert resp_list_inactive.status_code == 200
    ids = [item["id"] for item in resp_list_inactive.json().get("results", [])]
    assert shift.id in ids

    # Restore
    url_restore = reverse("core:shift-restore", args=[shift.id])
    resp_restore = api.post(url_restore)
    assert resp_restore.status_code == 200


@pytest.mark.django_db
def test_shift_by_guard_and_by_property_filters():
    # Arrange
    owner_user = baker.make(User)
    client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=client, address="Lambda")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    baker.make(
        Shift,
        guard=guard,
        property=prop,
        start_time=timezone.now(),
        end_time=timezone.now() + timezone.timedelta(hours=2),
    )

    api = APIClient()
    api.force_authenticate(user=owner_user)

    # by_guard
    url_by_guard = reverse("core:shift-by-guard") + f"?guard_id={guard.id}"
    resp_guard = api.get(url_by_guard)
    assert resp_guard.status_code == 200
    assert len(resp_guard.json()) >= 1

    # by_property
    url_by_prop = reverse("core:shift-by-property") + f"?property_id={prop.id}"
    resp_prop = api.get(url_by_prop)
    assert resp_prop.status_code == 200
    assert len(resp_prop.json()) >= 1


@pytest.mark.django_db
def test_shift_validation_end_time_after_start_time():
    # Arrange
    owner_user = baker.make(User)
    client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=client, address="Kappa")

    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    api = APIClient()
    api.force_authenticate(user=owner_user)

    payload = {
        "guard": guard.id,
        "property": prop.id,
        "start_time": "2025-01-01T10:00:00Z",
        "end_time": "2025-01-01T09:00:00Z",  # invalid: end before start
    }

    # Act
    url = reverse("core:shift-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 400
    assert "end_time" in resp.json()
