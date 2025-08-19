import datetime

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client, Guard, Property

# ------------------------- include_inactive tests -------------------------


@pytest.mark.django_db
def test_properties_include_inactive_toggle():
    admin = baker.make(User, is_superuser=True, is_staff=True)
    owner_user = baker.make(User)
    owner = baker.make(Client, user=owner_user)

    # Use address as searchable token to avoid alias uniqueness
    token = "ADDR-TOKEN-PROP-INACTIVE-1"
    active = baker.make(Property, owner=owner, address=token, is_active=True)
    inactive = baker.make(Property, owner=owner, address=token, is_active=False)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:property-list")

    # Default: only active
    r1 = api.get(url, {"search": token})
    ids1 = {item["id"] for item in r1.json()["results"]}
    assert ids1 == {active.id}

    # With include_inactive=true: both
    r2 = api.get(url, {"search": token, "include_inactive": "true"})
    ids2 = {item["id"] for item in r2.json()["results"]}
    assert ids2 == {active.id, inactive.id}


@pytest.mark.django_db
def test_clients_include_inactive_toggle():
    admin = baker.make(User, is_superuser=True, is_staff=True)

    token = "PHONE-CLIENT-01"
    u1 = baker.make(User)
    c_active = baker.make(Client, user=u1, phone=token, is_active=True)

    u2 = baker.make(User)
    c_inactive = baker.make(Client, user=u2, phone=token, is_active=False)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:client-list")

    # Default: only active
    r1 = api.get(url, {"search": token})
    ids1 = {item["id"] for item in r1.json()["results"]}
    assert ids1 == {c_active.id}

    # With include_inactive=true: both
    r2 = api.get(url, {"search": token, "include_inactive": "true"})
    ids2 = {item["id"] for item in r2.json()["results"]}
    assert ids2 == {c_active.id, c_inactive.id}


@pytest.mark.django_db
def test_guards_include_inactive_toggle():
    admin = baker.make(User, is_superuser=True, is_staff=True)

    token = "ADDR-TOKEN-GUARD-INACTIVE-1"
    u1 = baker.make(User)
    g_active = baker.make(Guard, user=u1, address=token, is_active=True)

    u2 = baker.make(User)
    g_inactive = baker.make(Guard, user=u2, address=token, is_active=False)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:guard-list")

    # Default: only active
    r1 = api.get(url, {"search": token})
    ids1 = {item["id"] for item in r1.json()["results"]}
    assert ids1 == {g_active.id}

    # With include_inactive=true: both
    r2 = api.get(url, {"search": token, "include_inactive": "true"})
    ids2 = {item["id"] for item in r2.json()["results"]}
    assert ids2 == {g_active.id, g_inactive.id}


# ------------------------------ ordering tests ------------------------------


@pytest.mark.django_db
def test_properties_ordering_by_name():
    admin = baker.make(User, is_superuser=True, is_staff=True)
    owner_user = baker.make(User)
    owner = baker.make(Client, user=owner_user)

    token = "ORD-PROP-FILT-1"
    baker.make(Property, owner=owner, name="AAA-NAME-ORDER", address=token)
    baker.make(Property, owner=owner, name="ZZZ-NAME-ORDER", address=token)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:property-list")

    r_asc = api.get(url, {"search": token, "ordering": "name"})
    names_asc = [item["name"] for item in r_asc.json()["results"]]
    assert names_asc == ["AAA-NAME-ORDER", "ZZZ-NAME-ORDER"]

    r_desc = api.get(url, {"search": token, "ordering": "-name"})
    names_desc = [item["name"] for item in r_desc.json()["results"]]
    assert names_desc == ["ZZZ-NAME-ORDER", "AAA-NAME-ORDER"]


@pytest.mark.django_db
def test_clients_ordering_by_user_first_name():
    admin = baker.make(User, is_superuser=True, is_staff=True)

    token = "ORD-CLIENT-FILT-1"
    ua = baker.make(User, first_name="Ana-AAA", username="ord-client-1a")
    uz = baker.make(User, first_name="Zoe-ZZZ", username="ord-client-1z")

    baker.make(Client, user=ua, phone=token)
    baker.make(Client, user=uz, phone=token)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:client-list")

    r_asc = api.get(url, {"search": token, "ordering": "user__first_name"})
    firsts_asc = [item["first_name"] for item in r_asc.json()["results"]]
    assert firsts_asc == ["Ana-AAA", "Zoe-ZZZ"]

    r_desc = api.get(url, {"search": token, "ordering": "-user__first_name"})
    firsts_desc = [item["first_name"] for item in r_desc.json()["results"]]
    assert firsts_desc == ["Zoe-ZZZ", "Ana-AAA"]


@pytest.mark.django_db
def test_guards_ordering_by_user_last_name():
    admin = baker.make(User, is_superuser=True, is_staff=True)

    token = "ORD-GUARD-FILT-1"
    ua = baker.make(User, last_name="A-Last", username="ord-guard-1a")
    uz = baker.make(User, last_name="Z-Last", username="ord-guard-1z")

    baker.make(Guard, user=ua, address=token)
    baker.make(Guard, user=uz, address=token)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:guard-list")

    r_asc = api.get(url, {"search": token, "ordering": "user__last_name"})
    lasts_asc = [item["last_name"] for item in r_asc.json()["results"]]
    assert lasts_asc == ["A-Last", "Z-Last"]

    r_desc = api.get(url, {"search": token, "ordering": "-user__last_name"})
    lasts_desc = [item["last_name"] for item in r_desc.json()["results"]]
    assert lasts_desc == ["Z-Last", "A-Last"]


@pytest.mark.django_db
def test_users_ordering_by_username():
    admin = baker.make(User, is_superuser=True, is_staff=True)

    token = "ORD-USER-FILT-1"
    # Only staff/superusers are returned by list; mark both as staff
    u_a = baker.make(User, username="aaa-" + token, is_staff=True)
    u_z = baker.make(User, username="zzz-" + token, is_staff=True)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:user-list")

    r_asc = api.get(url, {"search": token, "ordering": "username"})
    usernames_asc = [item["username"] for item in r_asc.json()["results"]]
    assert usernames_asc == [u_a.username, u_z.username]

    r_desc = api.get(url, {"search": token, "ordering": "-username"})
    usernames_desc = [item["username"] for item in r_desc.json()["results"]]
    assert usernames_desc == [u_z.username, u_a.username]


# --------------------------- date range (created_at) ---------------------------


@pytest.mark.django_db
def test_properties_date_range_created_at_filters():
    admin = baker.make(User, is_superuser=True, is_staff=True)
    owner_user = baker.make(User)
    owner = baker.make(Client, user=owner_user)

    token = "DATE-PROP-FILT-1"

    t1 = timezone.make_aware(datetime.datetime(2024, 1, 1, 12, 0, 0))
    t2 = timezone.make_aware(datetime.datetime(2024, 1, 5, 12, 0, 0))
    t3 = timezone.make_aware(datetime.datetime(2024, 1, 10, 12, 0, 0))

    baker.make(Property, owner=owner, address=token, created_at=t1)
    p2 = baker.make(Property, owner=owner, address=token, created_at=t2)
    baker.make(Property, owner=owner, address=token, created_at=t3)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:property-list")

    r = api.get(
        url, {"search": token, "date_from": "2024-01-05", "date_to": "2024-01-08"}
    )
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {p2.id}


@pytest.mark.django_db
def test_clients_date_range_created_at_filters():
    admin = baker.make(User, is_superuser=True, is_staff=True)

    token = "DATE-CLIENT-FILT-1"

    t1 = timezone.make_aware(datetime.datetime(2024, 2, 1, 12, 0, 0))
    t2 = timezone.make_aware(datetime.datetime(2024, 2, 5, 12, 0, 0))
    t3 = timezone.make_aware(datetime.datetime(2024, 2, 10, 12, 0, 0))

    u1 = baker.make(User)
    u2 = baker.make(User)
    u3 = baker.make(User)

    baker.make(Client, user=u1, phone=token, created_at=t1)
    c2 = baker.make(Client, user=u2, phone=token, created_at=t2)
    c3 = baker.make(Client, user=u3, phone=token, created_at=t3)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:client-list")

    r = api.get(
        url, {"search": token, "date_from": "2024-02-05", "date_to": "2024-02-10"}
    )
    ids = {item["id"] for item in r.json()["results"]}
    # Inclusive bounds: should include Feb 5 and Feb 10
    assert ids == {c2.id, c3.id}


@pytest.mark.django_db
def test_guards_date_range_created_at_filters():
    admin = baker.make(User, is_superuser=True, is_staff=True)

    token = "DATE-GUARD-FILT-1"

    t1 = timezone.make_aware(datetime.datetime(2024, 3, 1, 12, 0, 0))
    t2 = timezone.make_aware(datetime.datetime(2024, 3, 5, 12, 0, 0))
    t3 = timezone.make_aware(datetime.datetime(2024, 3, 10, 12, 0, 0))

    ua = baker.make(User, username="date-guard-a")
    ub = baker.make(User, username="date-guard-b")
    uc = baker.make(User, username="date-guard-c")

    baker.make(Guard, user=ua, address=token, created_at=t1)
    g2 = baker.make(Guard, user=ub, address=token, created_at=t2)
    baker.make(Guard, user=uc, address=token, created_at=t3)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:guard-list")

    r = api.get(
        url, {"search": token, "date_from": "2024-03-02", "date_to": "2024-03-09"}
    )
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {g2.id}


@pytest.mark.django_db
def test_users_date_range_date_joined_filters():
    admin = baker.make(User, is_superuser=True, is_staff=True)

    token = "DATE-USER-FILT-1"

    t1 = timezone.make_aware(datetime.datetime(2024, 4, 1, 8, 0, 0))
    t2 = timezone.make_aware(datetime.datetime(2024, 4, 5, 8, 0, 0))
    t3 = timezone.make_aware(datetime.datetime(2024, 4, 10, 8, 0, 0))

    baker.make(User, username=f"a-{token}", is_staff=True, date_joined=t1)
    u2 = baker.make(User, username=f"b-{token}", is_staff=True, date_joined=t2)
    u3 = baker.make(User, username=f"c-{token}", is_staff=True, date_joined=t3)

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:user-list")

    r = api.get(
        url, {"search": token, "date_from": "2024-04-05", "date_to": "2024-04-10"}
    )
    usernames = {item["username"] for item in r.json()["results"]}
    assert usernames == {u2.username, u3.username}
