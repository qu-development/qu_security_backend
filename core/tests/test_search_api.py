import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client, Guard, Property


@pytest.mark.django_db
def test_properties_search_by_fields():
    # Arrange: admin can view everything
    admin = baker.make(User, is_superuser=True, is_staff=True)

    # Owners and properties
    owner1_user = baker.make(
        User,
        username="user-UNIQ-carlos-1",
        first_name="FNAME-UNIQ-CARLOS-1",
        last_name="LNAME-UNIQ-LOPEZ-1",
        email="carlos-uniq1@example.com",
    )
    owner1 = baker.make(Client, user=owner1_user)
    prop1 = baker.make(
        Property,
        owner=owner1,
        name="NAME-UNIQ-PROP-1",
        alias="ALIAS-UNIQ-PROP-1",
        address="ADDR-UNIQ-PROP-1",
        total_hours=10,
    )

    owner2_user = baker.make(
        User,
        username="user-UNIQ-maria-2",
        first_name="FNAME-UNIQ-MARIA-2",
        last_name="LNAME-UNIQ-GOMEZ-2",
        email="maria-uniq2@example.com",
    )
    owner2 = baker.make(Client, user=owner2_user)
    prop2 = baker.make(
        Property,
        owner=owner2,
        name="NAME-UNIQ-PROP-2",
        alias="ALIAS-UNIQ-PROP-2",
        address="ADDR-UNIQ-PROP-2",
        total_hours=12,
    )

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:property-list")

    # By name (unique token)
    r = api.get(url, {"search": "NAME-UNIQ-PROP-1"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {prop1.id}

    # By alias (unique token)
    r = api.get(url, {"search": "ALIAS-UNIQ-PROP-1"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {prop1.id}

    # By address (unique token)
    r = api.get(url, {"search": "ADDR-UNIQ-PROP-1"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {prop1.id}

    # By owner user fields (unique token)
    r = api.get(url, {"search": "FNAME-UNIQ-CARLOS-1"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {prop1.id}

    r = api.get(url, {"search": "FNAME-UNIQ-MARIA-2"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {prop2.id}


@pytest.mark.django_db
def test_clients_search_by_user_and_phone():
    # Arrange
    admin = baker.make(User, is_superuser=True, is_staff=True)

    u1 = baker.make(
        User,
        username="user-UNIQ-lucia-1",
        first_name="Lucia-UNIQ-1",
        last_name="Perez-UNIQ-1",
        email="lucia-uniq1@example.com",
    )
    c1 = baker.make(Client, user=u1, phone="PHONE-UNIQ-51-123")

    u2 = baker.make(
        User,
        username="user-UNIQ-diego-2",
        first_name="Diego-UNIQ-2",
        last_name="Lopez-UNIQ-2",
        email="diego-uniq2@example.com",
    )
    c2 = baker.make(Client, user=u2, phone="PHONE-UNIQ-777-999")

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:client-list")

    # By first_name (unique token)
    r = api.get(url, {"search": "Lucia-UNIQ-1"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {c1.id}

    # By phone (unique token)
    r = api.get(url, {"search": "PHONE-UNIQ-777"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {c2.id}

    # By email (unique token)
    r = api.get(url, {"search": "lucia-uniq1@"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {c1.id}


@pytest.mark.django_db
def test_guards_search_by_user_phone_address():
    # Arrange
    admin = baker.make(User, is_superuser=True, is_staff=True)

    u1 = baker.make(
        User,
        username="user-UNIQ-juan-1",
        first_name="Juan-UNIQ-1",
        last_name="Perez-UNIQ-1",
        email="juan-uniq1@example.com",
    )
    g1 = baker.make(
        Guard, user=u1, phone="PHONE-UNIQ-555-1000", address="ADDR-UNIQ-FALSA-123"
    )

    u2 = baker.make(
        User,
        username="user-UNIQ-roberto-2",
        first_name="Roberto-UNIQ-2",
        last_name="Gomez-UNIQ-2",
        email="roberto-uniq2@example.com",
    )
    baker.make(
        Guard, user=u2, phone="PHONE-UNIQ-444-2000", address="ADDR-UNIQ-REAL-456"
    )

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:guard-list")

    # By address (unique token)
    r = api.get(url, {"search": "ADDR-UNIQ-FALSA"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {g1.id}

    # By phone (unique token)
    r = api.get(url, {"search": "PHONE-UNIQ-555-1"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {g1.id}

    # By user name (unique token)
    r = api.get(url, {"search": "Juan-UNIQ-1"})
    ids = {item["id"] for item in r.json()["results"]}
    assert ids == {g1.id}


@pytest.mark.django_db
def test_users_search_by_username_and_name():
    # Arrange: list endpoint returns only staff/superusers
    admin = baker.make(User, is_superuser=True, is_staff=True)

    baker.make(
        User,
        username="alice",
        first_name="Alice",
        last_name="Liddell",
        email="alice@example.com",
        is_staff=True,
    )
    baker.make(
        User,
        username="bob",
        first_name="Bob",
        last_name="Builder",
        email="bob@example.com",
        is_staff=True,
    )

    api = APIClient()
    api.force_authenticate(user=admin)
    url = reverse("core:user-list")

    # By username substring
    r = api.get(url, {"search": "ali"})
    usernames = {item["username"] for item in r.json()["results"]}
    assert usernames == {"alice"}

    # By last name
    r = api.get(url, {"search": "Build"})
    usernames = {item["username"] for item in r.json()["results"]}
    assert usernames == {"bob"}
