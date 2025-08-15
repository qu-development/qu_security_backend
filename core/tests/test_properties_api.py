import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client, Property
from permissions.models import UserRole


@pytest.mark.django_db
def test_property_create_by_client_sets_owner():
    # Arrange
    user = baker.make(User)
    client_profile = baker.make(Client, user=user)
    api = APIClient()
    api.force_authenticate(user=user)

    payload = {
        "address": "456 New Street",
        "total_hours": 120,
        "alias": "HQ",
    }

    # Act
    url = reverse("core:property-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert data["owner"] == client_profile.id
    assert data["alias"] == "HQ"


@pytest.mark.django_db
def test_property_create_non_client_returns_400():
    # Arrange: authenticated user without Client profile
    user = baker.make(User)
    api = APIClient()
    api.force_authenticate(user=user)

    payload = {
        "address": "789 Lone Street",
        "total_hours": 80,
    }

    # Act
    url = reverse("core:property-list")
    resp = api.post(url, payload, format="json")

    # Assert
    assert resp.status_code == 400
    # Error message raised in perform_create
    assert "Only clients can create properties" in str(resp.json())


@pytest.mark.django_db
def test_alias_uniqueness_per_owner_on_create_returns_400():
    # Arrange
    user = baker.make(User)
    baker.make(Client, user=user)
    api = APIClient()
    api.force_authenticate(user=user)

    # First create succeeds
    url = reverse("core:property-list")
    resp1 = api.post(
        url,
        {"address": "A St", "total_hours": 10, "alias": "Alpha"},
        format="json",
    )
    assert resp1.status_code == 201

    # Second with same alias for same owner fails
    resp2 = api.post(
        url,
        {"address": "B St", "total_hours": 20, "alias": "Alpha"},
        format="json",
    )
    assert resp2.status_code == 400
    assert "alias" in resp2.json()


@pytest.mark.django_db
def test_alias_can_repeat_for_different_owners():
    # Arrange two clients
    u1 = baker.make(User)
    baker.make(Client, user=u1)
    u2 = baker.make(User)
    baker.make(Client, user=u2)

    api1 = APIClient()
    api1.force_authenticate(user=u1)
    api2 = APIClient()
    api2.force_authenticate(user=u2)

    url = reverse("core:property-list")

    # Same alias for different owners should both succeed
    r1 = api1.post(
        url, {"address": "One", "total_hours": 10, "alias": "Shared"}, format="json"
    )
    r2 = api2.post(
        url, {"address": "Two", "total_hours": 20, "alias": "Shared"}, format="json"
    )

    assert r1.status_code == 201
    assert r2.status_code == 201


@pytest.mark.django_db
def test_blank_alias_normalized_to_none_and_no_conflict():
    # Arrange
    user = baker.make(User)
    baker.make(Client, user=user)
    api = APIClient()
    api.force_authenticate(user=user)
    url = reverse("core:property-list")

    # First with blank alias -> normalized to None
    r1 = api.post(
        url, {"address": "A", "total_hours": 10, "alias": "   "}, format="json"
    )
    assert r1.status_code == 201
    assert r1.json()["alias"] is None

    # Second with blank alias should also succeed (NULLs don't conflict)
    r2 = api.post(url, {"address": "B", "total_hours": 20, "alias": ""}, format="json")
    assert r2.status_code == 201
    assert r2.json()["alias"] is None


@pytest.mark.django_db
def test_alias_uniqueness_is_case_sensitive_allows_different_case():
    # Arrange
    user = baker.make(User)
    baker.make(Client, user=user)
    api = APIClient()
    api.force_authenticate(user=user)
    url = reverse("core:property-list")

    r1 = api.post(
        url, {"address": "C1", "total_hours": 10, "alias": "Alpha"}, format="json"
    )
    assert r1.status_code == 201
    r2 = api.post(
        url, {"address": "C2", "total_hours": 10, "alias": "alpha"}, format="json"
    )
    assert r2.status_code == 201


@pytest.mark.django_db
def test_client_list_scoped_to_owner():
    # Arrange two owners, assign role to ensure filtering path
    u1 = baker.make(User)
    c1 = baker.make(Client, user=u1)
    UserRole.objects.create(user=u1, role="client", is_active=True)

    u2 = baker.make(User)
    c2 = baker.make(Client, user=u2)
    UserRole.objects.create(user=u2, role="client", is_active=True)

    # Properties for both
    baker.make(Property, owner=c1, address="Owner1 St", total_hours=5)
    baker.make(Property, owner=c2, address="Owner2 St", total_hours=6)

    api = APIClient()
    api.force_authenticate(user=u1)

    # Act
    url = reverse("core:property-list")
    resp = api.get(url)

    # Assert: only owner's properties are returned
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict) and "results" in data
    returned_owner_ids = {item["owner"] for item in data["results"]}
    assert returned_owner_ids == {c1.id}


@pytest.mark.django_db
def test_owner_can_retrieve_and_update_property():
    # Arrange
    user = baker.make(User)
    client_profile = baker.make(Client, user=user)
    UserRole.objects.create(user=user, role="client", is_active=True)
    prop = baker.make(
        Property, owner=client_profile, address="Old Addr", total_hours=10, alias="Old"
    )

    api = APIClient()
    api.force_authenticate(user=user)

    # Retrieve
    url_detail = reverse("core:property-detail", args=[prop.id])
    r_get = api.get(url_detail)
    assert r_get.status_code == 200

    # Update
    r_patch = api.patch(
        url_detail, {"alias": "New", "address": "New Addr"}, format="json"
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["alias"] == "New"


@pytest.mark.django_db
def test_update_to_duplicate_alias_returns_400():
    # Arrange
    user = baker.make(User)
    client_profile = baker.make(Client, user=user)
    UserRole.objects.create(user=user, role="client", is_active=True)

    baker.make(
        Property, owner=client_profile, alias="ALPHA", address="X", total_hours=1
    )
    p2 = baker.make(
        Property, owner=client_profile, alias="BETA", address="Y", total_hours=1
    )

    api = APIClient()
    api.force_authenticate(user=user)

    # Act: try to change p2 alias to ALPHA
    url_detail = reverse("core:property-detail", args=[p2.id])
    resp = api.patch(url_detail, {"alias": "ALPHA"}, format="json")

    # Assert
    assert resp.status_code == 400
    assert "alias" in resp.json()


@pytest.mark.django_db
def test_non_owner_cannot_retrieve_or_update_or_soft_delete():
    # Arrange
    owner_user = baker.make(User)
    owner_client = baker.make(Client, user=owner_user)
    UserRole.objects.create(user=owner_user, role="client", is_active=True)
    prop = baker.make(Property, owner=owner_client, address="Secured", total_hours=10)

    other_user = baker.make(User)
    baker.make(Client, user=other_user)
    UserRole.objects.create(user=other_user, role="client", is_active=True)

    api = APIClient()
    api.force_authenticate(user=other_user)

    # Retrieve should be forbidden or not found due to filtering
    url_detail = reverse("core:property-detail", args=[prop.id])
    r_get = api.get(url_detail)
    assert r_get.status_code in (403, 404)

    # Update should be forbidden or not found
    r_patch = api.patch(url_detail, {"address": "Hack"}, format="json")
    assert r_patch.status_code in (403, 404)

    # Soft delete should be forbidden/not found (access controlled via filtered queryset)
    soft_url = f"/en/api/properties/{prop.id}/soft_delete/"
    r_soft = api.post(soft_url)
    assert r_soft.status_code in (403, 404)


@pytest.mark.django_db
def test_soft_delete_and_restore_flow():
    # Arrange
    user = baker.make(User)
    client_profile = baker.make(Client, user=user)
    UserRole.objects.create(user=user, role="client", is_active=True)
    prop = baker.make(
        Property, owner=client_profile, address="ToRemove", total_hours=10
    )

    api = APIClient()
    api.force_authenticate(user=user)

    url_detail = reverse("core:property-detail", args=[prop.id])

    # Soft delete
    soft_url = f"/en/api/properties/{prop.id}/soft_delete/"
    r_soft = api.post(soft_url)
    assert r_soft.status_code == 204

    # After soft delete, detail should not be accessible (404)
    r_after_soft = api.get(url_detail)
    assert r_after_soft.status_code == 404

    # Restore
    restore_url = f"/en/api/properties/{prop.id}/restore/?include_inactive=true"
    r_restore = api.post(restore_url)
    assert r_restore.status_code == 200

    # After restore, detail should be accessible again (200)
    r_after_restore = api.get(url_detail)
    assert r_after_restore.status_code == 200
