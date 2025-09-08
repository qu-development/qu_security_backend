import datetime

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Guard
from mobile.models import GuardReport


@pytest.mark.django_db
def test_guard_report_create_authenticated_succeeds():
    # Arrange: create a guard and authenticate as any user
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    acting_user = baker.make(User)
    api = APIClient()
    api.force_authenticate(user=acting_user)

    upload = SimpleUploadedFile("report.txt", b"hello world", content_type="text/plain")
    payload = {
        "guard": guard.id,
        "file": upload,
        "note": "Routine check ok",
        "latitude": 10.123456,
        "longitude": -70.654321,
    }

    # Act
    url = reverse("mobile:guard-report-list")
    resp = api.post(url, data=payload, format="multipart")

    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert data["guard"] == guard.id
    assert data["note"] == "Routine check ok"
    assert data["file"]  # file URL/path should be present


@pytest.mark.django_db
def test_guard_report_create_unauthenticated_returns_401():
    guard_user = baker.make(User)
    guard = baker.make(Guard, user=guard_user)

    api = APIClient()  # no auth

    upload = SimpleUploadedFile("report2.txt", b"unauth", content_type="text/plain")
    payload = {"guard": guard.id, "file": upload}

    url = reverse("mobile:guard-report-list")
    resp = api.post(url, data=payload, format="multipart")

    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_guard_reports_list_filter_by_guard_query_param():
    # Arrange
    g1_user = baker.make(User)
    g2_user = baker.make(User)
    g1 = baker.make(Guard, user=g1_user)
    g2 = baker.make(Guard, user=g2_user)

    # Create reports for two different guards
    f1 = SimpleUploadedFile("g1a.txt", b"g1a", content_type="text/plain")
    f2 = SimpleUploadedFile("g1b.txt", b"g1b", content_type="text/plain")
    f3 = SimpleUploadedFile("g2a.txt", b"g2a", content_type="text/plain")

    r1 = baker.make(GuardReport, guard=g1, file=f1)
    r2 = baker.make(GuardReport, guard=g1, file=f2)
    baker.make(GuardReport, guard=g2, file=f3)

    api = APIClient()
    api.force_authenticate(user=baker.make(User))

    # Act: filter by guard g1
    url = reverse("mobile:guard-report-list")
    resp = api.get(url, {"guard": g1.id})

    # Assert: only g1 reports returned
    assert resp.status_code == 200
    data = resp.json()
    ids = {item["id"] for item in data["results"]}
    assert ids == {r1.id, r2.id}


@pytest.mark.django_db
def test_guard_reports_by_guard_custom_action():
    g1_user = baker.make(User)
    g2_user = baker.make(User)
    g1 = baker.make(Guard, user=g1_user)
    g2 = baker.make(Guard, user=g2_user)

    f1 = SimpleUploadedFile("g1a2.txt", b"g1a2", content_type="text/plain")
    f2 = SimpleUploadedFile("g1b2.txt", b"g1b2", content_type="text/plain")
    f3 = SimpleUploadedFile("g2a2.txt", b"g2a2", content_type="text/plain")

    r1 = baker.make(GuardReport, guard=g1, file=f1)
    r2 = baker.make(GuardReport, guard=g1, file=f2)
    baker.make(GuardReport, guard=g2, file=f3)

    api = APIClient()
    api.force_authenticate(user=baker.make(User))

    url = reverse("mobile:guard-report-by-guard", kwargs={"guard_id": g1.id})
    resp = api.get(url)

    assert resp.status_code == 200
    data = resp.json()
    ids = {item["id"] for item in data["results"]}
    assert ids == {r1.id, r2.id}


@pytest.mark.django_db
def test_guard_reports_date_range_filters():
    guard = baker.make(Guard, user=baker.make(User))

    f1 = SimpleUploadedFile("d1.txt", b"d1", content_type="text/plain")
    f2 = SimpleUploadedFile("d2.txt", b"d2", content_type="text/plain")
    f3 = SimpleUploadedFile("d3.txt", b"d3", content_type="text/plain")

    t1 = timezone.make_aware(datetime.datetime(2025, 1, 1, 12, 0, 0))
    t2 = timezone.make_aware(datetime.datetime(2025, 1, 5, 12, 0, 0))
    t3 = timezone.make_aware(datetime.datetime(2025, 1, 10, 12, 0, 0))

    r1 = baker.make(GuardReport, guard=guard, file=f1, report_datetime=t1)
    r2 = baker.make(GuardReport, guard=guard, file=f2, report_datetime=t2)
    r3 = baker.make(GuardReport, guard=guard, file=f3, report_datetime=t3)

    api = APIClient()
    api.force_authenticate(user=baker.make(User))

    url = reverse("mobile:guard-report-list")

    # date_from only
    r_from = api.get(url, {"date_from": "2025-01-05T00:00:00Z"})
    ids_from = {item["id"] for item in r_from.json()["results"]}
    assert ids_from == {r2.id, r3.id}

    # date_to only
    r_to = api.get(url, {"date_to": "2025-01-05T23:59:59Z"})
    ids_to = {item["id"] for item in r_to.json()["results"]}
    assert ids_to == {r1.id, r2.id}

    # both
    r_between = api.get(
        url,
        {"date_from": "2025-01-05T00:00:00Z", "date_to": "2025-01-07T00:00:00Z"},
    )
    ids_between = {item["id"] for item in r_between.json()["results"]}
    assert ids_between == {r2.id}


@pytest.mark.django_db
def test_guard_reports_search_and_ordering():
    guard = baker.make(Guard, user=baker.make(User))

    fa = SimpleUploadedFile("a.txt", b"a", content_type="text/plain")
    fz = SimpleUploadedFile("z.txt", b"z", content_type="text/plain")

    t_early = timezone.make_aware(datetime.datetime(2025, 2, 1, 9, 0, 0))
    t_late = timezone.make_aware(datetime.datetime(2025, 2, 1, 12, 0, 0))

    r_early = baker.make(
        GuardReport,
        guard=guard,
        file=fa,
        note="CHECK-NOTE-ORD-TOKEN early",
        report_datetime=t_early,
    )
    r_late = baker.make(
        GuardReport,
        guard=guard,
        file=fz,
        note="CHECK-NOTE-ORD-TOKEN late",
        report_datetime=t_late,
    )

    api = APIClient()
    api.force_authenticate(user=baker.make(User))

    url = reverse("mobile:guard-report-list")

    # Ascending
    r1 = api.get(url, {"search": "CHECK-NOTE-ORD-TOKEN", "ordering": "report_datetime"})
    ordered_ids_asc = [item["id"] for item in r1.json()["results"]]
    assert ordered_ids_asc == [r_early.id, r_late.id]

    # Descending
    r2 = api.get(
        url, {"search": "CHECK-NOTE-ORD-TOKEN", "ordering": "-report_datetime"}
    )
    ordered_ids_desc = [item["id"] for item in r2.json()["results"]]
    assert ordered_ids_desc == [r_late.id, r_early.id]
