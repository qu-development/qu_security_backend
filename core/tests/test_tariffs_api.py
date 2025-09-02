import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client, Guard, GuardPropertyTariff, Property
from permissions.models import UserRole


@pytest.mark.django_db
def test_tariff_create_forbidden_for_non_owner_client():
    # Arrange: two clients, property belongs to client A, client B attempts create
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    other_user = baker.make(User)
    baker.make(Client, user=other_user)
    UserRole.objects.create(user=owner_user, role="client", is_active=True)
    UserRole.objects.create(user=other_user, role="client", is_active=True)

    prop = baker.make(
        Property, owner=owner_client, address="Tariff Site"
    )
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    api = APIClient()
    api.force_authenticate(user=other_user)

    payload = {
        "guard": guard.id,
        "property": prop.id,
        "rate": "15.50",
    }

    # Act
    url = reverse("core:guard-property-tariff-list")
    resp = api.post(url, payload, format="json")

    # Assert: should be 400/403 due to perform_create validation (not owner)
    assert resp.status_code in (400, 403)


@pytest.mark.django_db
def test_tariff_create_by_owner_succeeds_and_deactivates_previous_active():
    # Arrange: client owner creates two active tariffs -> first becomes inactive
    user = baker.make(User)
    client = baker.make(Client, user=user)
    UserRole.objects.create(user=user, role="client", is_active=True)

    prop = baker.make(Property, owner=client, address="P1")
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    # Pre-existing active tariff
    t1 = baker.make(
        GuardPropertyTariff, guard=guard, property=prop, rate="10.00", is_active=True
    )

    api = APIClient()
    api.force_authenticate(user=user)

    payload = {
        "guard": guard.id,
        "property": prop.id,
        "rate": "12.00",
    }

    url = reverse("core:guard-property-tariff-list")
    resp = api.post(url, payload, format="json")

    assert resp.status_code == 201

    # The previous tariff should be deactivated
    t1.refresh_from_db()
    assert t1.is_active is False


@pytest.mark.django_db
def test_tariff_list_filtered_for_guard_shows_only_own_tariffs():
    # Arrange: two guards, each linked to a property via tariffs
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    p = baker.make(Property, owner=owner_client, address="Site A")
    q = baker.make(Property, owner=owner_client, address="Site B")

    guser1 = baker.make(User)
    guser2 = baker.make(User)
    g1 = baker.make(Guard, user=guser1)
    g2 = baker.make(Guard, user=guser2)

    baker.make(GuardPropertyTariff, guard=g1, property=p, rate="11.00", is_active=True)
    baker.make(GuardPropertyTariff, guard=g2, property=q, rate="12.00", is_active=True)

    # Give role so PermissionManager recognizes guard role
    UserRole.objects.create(user=guser1, role="guard", is_active=True)

    api = APIClient()
    api.force_authenticate(user=guser1)

    # Act
    url = reverse("core:guard-property-tariff-list")
    resp = api.get(url)

    # Assert: only tariffs for g1
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict) and "results" in data
    guard_ids = {item["guard"] for item in data["results"]}
    assert guard_ids == {g1.id}


@pytest.mark.django_db
def test_tariff_by_guard_action_filters_correctly():
    # Arrange
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client, address="A")

    guser = baker.make(User)
    g = baker.make(Guard, user=guser)
    baker.make(GuardPropertyTariff, guard=g, property=prop, rate="9.00", is_active=True)

    api = APIClient()
    api.force_authenticate(user=owner_user)

    # Act
    url = reverse("core:guard-property-tariff-by-guard")
    resp = api.get(url, {"guard_id": g.id})

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert all(item["guard"] == g.id for item in data)


@pytest.mark.django_db
def test_tariff_by_property_action_requires_param():
    # Arrange
    user = baker.make(User)
    api = APIClient()
    api.force_authenticate(user=user)

    # Act
    url = reverse("core:guard-property-tariff-by-property")
    resp = api.get(url)

    # Assert
    assert resp.status_code == 400


@pytest.mark.django_db
def test_tariff_update_set_active_true_deactivates_others():
    # Arrange: owner client with two tariffs for same pair, second inactive; update second to active
    user = baker.make(User)
    client = baker.make(Client, user=user)
    UserRole.objects.create(user=user, role="client", is_active=True)

    prop = baker.make(Property, owner=client, address="P2")
    guser = baker.make(User)
    g = baker.make(Guard, user=guser)

    t_active = baker.make(
        GuardPropertyTariff, guard=g, property=prop, rate="10.00", is_active=True
    )
    t_inactive = baker.make(
        GuardPropertyTariff, guard=g, property=prop, rate="9.50", is_active=False
    )

    api = APIClient()
    api.force_authenticate(user=user)

    url_detail = reverse("core:guard-property-tariff-detail", args=[t_inactive.id])
    # Include inactive objects so we can update a soft-deactivated tariff
    resp = api.patch(
        url_detail + "?include_inactive=true", {"is_active": True}, format="json"
    )

    assert resp.status_code == 200

    # Now the previously active should be inactive
    t_active.refresh_from_db()
    t_inactive.refresh_from_db()
    assert t_inactive.is_active is True
    assert t_active.is_active is False


@pytest.mark.django_db
def test_tariff_retrieve_guard_cannot_access_others_tariff():
    # Arrange: two guards, tariff belongs to g1, authenticate as g2
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    prop = baker.make(Property, owner=owner_client, address="Site Z")

    guser1 = baker.make(User)
    guser2 = baker.make(User)
    g1 = baker.make(Guard, user=guser1)
    baker.make(Guard, user=guser2)

    t = baker.make(
        GuardPropertyTariff, guard=g1, property=prop, rate="10.00", is_active=True
    )

    UserRole.objects.create(user=guser2, role="guard", is_active=True)

    api = APIClient()
    api.force_authenticate(user=guser2)

    # Act
    url = reverse("core:guard-property-tariff-detail", args=[t.id])
    resp = api.get(url)

    # Assert: filtered queryset prevents access -> 404
    assert resp.status_code == 404
