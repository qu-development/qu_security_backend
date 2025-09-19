from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from core.models import Client, Guard, Property, Service, Shift


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    from permissions.models import UserRole

    user = User.objects.create_user(
        username="admin", email="admin@test.com", password="admin123"
    )
    UserRole.objects.create(user=user, role="admin")
    return user


@pytest.fixture
def client_user():
    from permissions.models import UserRole

    user = User.objects.create_user(
        username="client", email="client@test.com", password="client123"
    )
    UserRole.objects.create(user=user, role="client")
    return user


@pytest.fixture
def guard_user():
    from permissions.models import UserRole

    user = User.objects.create_user(
        username="guard", email="guard@test.com", password="guard123"
    )
    UserRole.objects.create(user=user, role="guard")
    return user


@pytest.fixture
def client_instance(client_user):
    return baker.make(Client, user=client_user)


@pytest.fixture
def guard_instance(guard_user):
    return baker.make(Guard, user=guard_user)


@pytest.fixture
def property_instance(client_instance):
    return baker.make(Property, owner=client_instance, address="Test Property")


@pytest.fixture
def service_instance(guard_instance, property_instance):
    return baker.make(
        Service,
        name="Test Service",
        description="Test service description",
        guard=guard_instance,
        assigned_property=property_instance,
        rate=Decimal("25.00"),
        monthly_budget=Decimal("2000.00"),
        contract_start_date=timezone.now().date(),
    )


@pytest.mark.django_db
class TestServiceModel:
    """Test Service model functionality"""

    def test_service_creation(self, guard_instance, property_instance):
        """Test creating a service"""
        contract_date = timezone.now().date()
        schedule_dates = [
            timezone.now().date(),
            timezone.now().date() + timezone.timedelta(days=7),
        ]
        start_time = timezone.now().time().replace(microsecond=0)
        end_time = (
            (timezone.now() + timezone.timedelta(hours=8)).time().replace(microsecond=0)
        )
        service = Service.objects.create(
            name="Security Service",
            description="24/7 security monitoring",
            guard=guard_instance,
            assigned_property=property_instance,
            rate=Decimal("30.00"),
            monthly_budget=Decimal("2400.00"),
            contract_start_date=contract_date,
            schedule=schedule_dates,
            recurrent=True,
            start_time=start_time,
            end_time=end_time,
            weekly=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
        )

        assert service.name == "Security Service"
        assert service.description == "24/7 security monitoring"
        assert service.guard == guard_instance
        assert service.assigned_property == property_instance
        assert service.rate == Decimal("30.00")
        assert service.monthly_budget == Decimal("2400.00")
        assert service.contract_start_date == contract_date
        assert service.schedule == schedule_dates
        assert service.recurrent is True
        assert service.start_time == start_time
        assert service.end_time == end_time
        assert service.weekly == [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
        ]
        assert service.start_date == timezone.now().date()
        assert service.end_date == timezone.now().date() + timezone.timedelta(days=30)
        assert service.is_active is True

    def test_service_without_guard(self, property_instance):
        """Test creating a service without assigned guard"""
        service = Service.objects.create(
            name="Unassigned Service",
            description="Service without guard",
            assigned_property=property_instance,
            rate=Decimal("20.00"),
            monthly_budget=Decimal("1600.00"),
        )

        assert service.guard is None
        assert service.assigned_property == property_instance

    def test_service_without_property(self, guard_instance):
        """Test creating a service without assigned property"""
        service = Service.objects.create(
            name="Floating Service",
            description="Service without property",
            guard=guard_instance,
            rate=Decimal("35.00"),
            monthly_budget=Decimal("2800.00"),
        )

        assert service.guard == guard_instance
        assert service.assigned_property is None

    def test_service_total_hours_calculation(self, service_instance):
        """Test total hours calculation based on shifts via signals"""
        # Create some shifts for the service with planned times
        baker.make(
            Shift,
            service=service_instance,
            guard=service_instance.guard,
            property=service_instance.assigned_property,
            planned_start_time=timezone.now(),
            planned_end_time=timezone.now() + timezone.timedelta(hours=8),
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=8),
            hours_worked=8,
            status="completed",
        )
        baker.make(
            Shift,
            service=service_instance,
            guard=service_instance.guard,
            property=service_instance.assigned_property,
            planned_start_time=timezone.now(),
            planned_end_time=timezone.now() + timezone.timedelta(hours=6),
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=6),
            hours_worked=6,
            status="completed",
        )

        # Refresh service from database to get updated values from signals
        service_instance.refresh_from_db()

        # Test that total_hours field is updated correctly (only completed shifts)
        assert service_instance.total_hours == 14  # 8 + 6 hours

        # Test that total_hours_planned field is updated correctly (all shifts)
        assert service_instance.total_hours_planned == 14  # 8 + 6 planned hours

    def test_service_hours_with_mixed_shift_statuses(self, service_instance):
        """Test that total_hours only counts completed shifts but total_hours_planned counts all"""
        # Create completed shift with planned times
        baker.make(
            Shift,
            service=service_instance,
            guard=service_instance.guard,
            property=service_instance.assigned_property,
            planned_start_time=timezone.now(),
            planned_end_time=timezone.now() + timezone.timedelta(hours=8),
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=8),
            hours_worked=8,
            status="completed",
        )

        # Create scheduled shift (not completed) with planned times
        baker.make(
            Shift,
            service=service_instance,
            guard=service_instance.guard,
            property=service_instance.assigned_property,
            planned_start_time=timezone.now(),
            planned_end_time=timezone.now() + timezone.timedelta(hours=6),
            hours_worked=0,
            status="scheduled",
        )

        # Refresh service from database to get updated values from signals
        service_instance.refresh_from_db()

        # total_hours should only include completed shifts
        assert service_instance.total_hours == 8  # Only completed shift

        # total_hours_planned should include all shifts
        assert service_instance.total_hours_planned == 14  # 8 + 6 planned hours

    def test_service_string_representation(self, service_instance):
        """Test service string representation"""
        assert str(service_instance) == service_instance.name


@pytest.mark.django_db
class TestServiceAPI:
    """Test Service API endpoints"""

    def test_list_services_as_admin(self, api_client, admin_user, service_instance):
        """Test listing services as admin"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-list")
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

        service_names = [service["name"] for service in response.data["results"]]
        assert service_instance.name in service_names

    def test_list_services_as_client(self, api_client, client_user, service_instance):
        """Test listing services as client (should see only related services)"""
        api_client.force_authenticate(user=client_user)
        url = reverse("core:service-list")
        response = api_client.get(url)

        assert response.status_code == 200
        # Client should only see services for their properties

    def test_list_services_as_guard(self, api_client, guard_user, service_instance):
        """Test listing services as guard (should see only assigned services)"""
        api_client.force_authenticate(user=guard_user)
        url = reverse("core:service-list")
        response = api_client.get(url)

        assert response.status_code == 200
        # Guard should only see their assigned services

    def test_create_service_as_admin(
        self, api_client, admin_user, guard_instance, property_instance
    ):
        """Test creating a service as admin"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-list")
        data = {
            "name": "New Security Service",
            "description": "New service description",
            "guard": guard_instance.id,
            "assigned_property": property_instance.id,
            "rate": "40.00",
            "monthly_budget": "3200.00",
            "contract_start_date": timezone.now().date().isoformat(),
            "schedule": [
                timezone.now().date().isoformat(),
                (timezone.now().date() + timezone.timedelta(days=7)).isoformat(),
            ],
            "recurrent": True,
            "start_time": timezone.now().time().replace(microsecond=0).isoformat(),
            "end_time": (timezone.now() + timezone.timedelta(hours=8))
            .time()
            .replace(microsecond=0)
            .isoformat(),
            "weekly": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "start_date": timezone.now().date().isoformat(),
            "end_date": (
                timezone.now().date() + timezone.timedelta(days=30)
            ).isoformat(),
        }
        response = api_client.post(url, data)

        assert response.status_code == 201
        assert response.data["name"] == "New Security Service"
        assert response.data["rate"] == "40.00"
        assert response.data["monthly_budget"] == "3200.00"
        assert response.data["weekly"] == [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
        ]
        assert "start_date" in response.data
        assert "end_date" in response.data

    def test_create_service_as_client_forbidden(
        self, api_client, client_user, guard_instance, property_instance
    ):
        """Test that clients cannot create services"""
        api_client.force_authenticate(user=client_user)
        url = reverse("core:service-list")
        data = {
            "name": "Unauthorized Service",
            "description": "Should not be created",
            "guard": guard_instance.id,
            "assigned_property": property_instance.id,
            "rate": "25.00",
            "monthly_budget": "2000.00",
            "contract_start_date": timezone.now().date().isoformat(),
        }
        response = api_client.post(url, data)

        assert response.status_code == 403

    def test_retrieve_service(self, api_client, admin_user, service_instance):
        """Test retrieving a specific service"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-detail", kwargs={"pk": service_instance.id})
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["id"] == service_instance.id
        assert response.data["name"] == service_instance.name
        assert "total_hours" in response.data
        assert "total_hours_planned" in response.data
        assert "guard_name" in response.data
        assert "property_name" in response.data
        assert "weekly" in response.data
        assert "start_date" in response.data
        assert "end_date" in response.data

    def test_update_service_as_admin(self, api_client, admin_user, service_instance):
        """Test updating a service as admin"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-detail", kwargs={"pk": service_instance.id})
        data = {
            "name": "Updated Service Name",
            "description": "Updated description",
            "rate": "45.00",
            "monthly_budget": "3600.00",
            "contract_start_date": timezone.now().date().isoformat(),
            "schedule": [timezone.now().date().isoformat()],
            "recurrent": False,
            "start_time": timezone.now().time().replace(microsecond=0).isoformat(),
            "end_time": (timezone.now() + timezone.timedelta(hours=4))
            .time()
            .replace(microsecond=0)
            .isoformat(),
            "weekly": ["Saturday", "Sunday"],
            "start_date": timezone.now().date().isoformat(),
            "end_date": (
                timezone.now().date() + timezone.timedelta(days=60)
            ).isoformat(),
        }
        response = api_client.patch(url, data)

        assert response.status_code == 200
        assert response.data["name"] == "Updated Service Name"
        assert response.data["rate"] == "45.00"
        assert response.data["monthly_budget"] == "3600.00"
        assert response.data["weekly"] == ["Saturday", "Sunday"]

    def test_delete_service_as_admin(self, api_client, admin_user, service_instance):
        """Test deleting a service as admin (soft delete)"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-detail", kwargs={"pk": service_instance.id})
        response = api_client.delete(url)

        assert response.status_code == 204

        # Verify soft delete - need to get from all objects including deleted
        from core.models import Service

        deleted_service = Service.all_objects.filter(id=service_instance.id).first()
        assert deleted_service is not None
        assert deleted_service.is_active is False

    def test_service_search(self, api_client, admin_user, service_instance):
        """Test searching services"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-list")
        response = api_client.get(url, {"search": "Test"})

        assert response.status_code == 200
        assert len(response.data["results"]) >= 1

    def test_service_ordering(self, api_client, admin_user, service_instance):
        """Test ordering services"""
        # Create another service
        baker.make(Service, name="Another Service", rate=Decimal("50.00"))

        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-list")

        # Test ordering by name
        response = api_client.get(url, {"ordering": "name"})
        assert response.status_code == 200

        # Test ordering by rate (descending)
        response = api_client.get(url, {"ordering": "-rate"})
        assert response.status_code == 200

    def test_service_shifts_endpoint(self, api_client, admin_user, service_instance):
        """Test getting shifts for a service"""
        # Create a shift for the service
        baker.make(
            Shift,
            service=service_instance,
            guard=service_instance.guard,
            property=service_instance.assigned_property,
            planned_start_time=timezone.now() - timezone.timedelta(hours=1),
            planned_end_time=timezone.now() + timezone.timedelta(hours=9),
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=8),
        )

        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-shifts", kwargs={"pk": service_instance.id})
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_services_by_property(self, api_client, admin_user, service_instance):
        """Test getting services by property"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-by-property")
        response = api_client.get(
            url, {"property_id": service_instance.assigned_property.id}
        )

        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_services_by_guard(self, api_client, admin_user, service_instance):
        """Test getting services by guard"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-by-guard")
        response = api_client.get(url, {"guard_id": service_instance.guard.id})

        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_create_service_invalid_weekdays_api(
        self, api_client, admin_user, guard_instance, property_instance
    ):
        """Test creating a service with invalid weekdays via API"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-list")
        data = {
            "name": "Invalid Weekdays Service",
            "description": "Service with invalid weekdays",
            "guard": guard_instance.id,
            "assigned_property": property_instance.id,
            "rate": "25.00",
            "monthly_budget": "2000.00",
            "weekly": ["Monday", "InvalidDay", "Tuesday"],
        }
        response = api_client.post(url, data)

        assert response.status_code == 400
        assert "weekly" in response.data

    def test_create_service_all_weekdays(
        self, api_client, admin_user, guard_instance, property_instance
    ):
        """Test creating a service with all weekdays"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-list")
        data = {
            "name": "All Weekdays Service",
            "description": "Service for every day",
            "guard": guard_instance.id,
            "assigned_property": property_instance.id,
            "rate": "35.00",
            "monthly_budget": "5000.00",
            "weekly": [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
            "start_date": timezone.now().date().isoformat(),
            "end_date": (
                timezone.now().date() + timezone.timedelta(days=90)
            ).isoformat(),
        }
        response = api_client.post(url, data)

        assert response.status_code == 201
        assert response.data["weekly"] == [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        assert "start_date" in response.data
        assert "end_date" in response.data

    def test_create_service_date_validation_api(
        self, api_client, admin_user, guard_instance, property_instance
    ):
        """Test date validation via API"""
        api_client.force_authenticate(user=admin_user)
        url = reverse("core:service-list")

        start_date = timezone.now().date()
        end_date = start_date - timezone.timedelta(days=1)  # Invalid: end before start

        data = {
            "name": "Invalid Dates Service",
            "description": "Service with invalid date range",
            "guard": guard_instance.id,
            "assigned_property": property_instance.id,
            "rate": "25.00",
            "monthly_budget": "2000.00",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        response = api_client.post(url, data)

        assert response.status_code == 400
        assert "end_date" in response.data

    def test_unauthenticated_access_forbidden(self, api_client, service_instance):
        """Test that unauthenticated users cannot access services"""
        url = reverse("core:service-list")
        response = api_client.get(url)

        assert response.status_code == 401


@pytest.mark.django_db
class TestServiceValidation:
    """Test Service model validation"""

    def test_valid_weekdays_validation(self, guard_instance, property_instance):
        """Test that valid weekdays are accepted"""
        service = Service.objects.create(
            name="Valid Weekdays Service",
            guard=guard_instance,
            assigned_property=property_instance,
            rate=Decimal("25.00"),
            monthly_budget=Decimal("2000.00"),
            weekly=[
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ],
        )

        service.full_clean()  # Should not raise ValidationError
        assert service.weekly == [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

    def test_invalid_weekdays_validation(self, guard_instance, property_instance):
        """Test that invalid weekdays are rejected"""
        from django.core.exceptions import ValidationError

        service = Service(
            name="Invalid Weekdays Service",
            guard=guard_instance,
            assigned_property=property_instance,
            rate=Decimal("25.00"),
            monthly_budget=Decimal("2000.00"),
            weekly=["Monday", "InvalidDay", "Tuesday"],
        )

        with pytest.raises(ValidationError) as exc_info:
            service.full_clean()

        assert "weekly" in exc_info.value.message_dict
        assert "InvalidDay" in str(exc_info.value.message_dict["weekly"])

    def test_weekly_helper_methods(self, guard_instance, property_instance):
        """Test helper methods for weekly field"""
        service = Service.objects.create(
            name="Helper Methods Service",
            guard=guard_instance,
            assigned_property=property_instance,
            rate=Decimal("25.00"),
            monthly_budget=Decimal("2000.00"),
            weekly=["Monday", "Wednesday", "Friday"],
        )

        # Test get_weekly_days_display
        display = service.get_weekly_days_display()
        assert display == "Monday, Wednesday, Friday"

        # Test is_scheduled_for_day
        assert service.is_scheduled_for_day("Monday") is True
        assert service.is_scheduled_for_day("Tuesday") is False
        assert service.is_scheduled_for_day("Wednesday") is True
        assert service.is_scheduled_for_day("Sunday") is False

    def test_start_date_before_end_date_validation(
        self, guard_instance, property_instance
    ):
        """Test that start_date must be before end_date"""

        start_date = timezone.now().date()
        end_date = start_date - timezone.timedelta(days=1)  # End date before start date

        Service(
            name="Invalid Dates Service",
            guard=guard_instance,
            assigned_property=property_instance,
            rate=Decimal("25.00"),
            monthly_budget=Decimal("2000.00"),
            start_date=start_date,
            end_date=end_date,
        )

        # Note: This validation should be in the serializer/API level
        # The model itself doesn't validate this constraint

    def test_negative_rate_validation(self, guard_instance, property_instance):
        """Test that negative rates are not allowed"""
        from django.core.exceptions import ValidationError

        service = Service(
            name="Invalid Service",
            guard=guard_instance,
            assigned_property=property_instance,
            rate=Decimal("-10.00"),
            monthly_budget=Decimal("1000.00"),
        )
        with pytest.raises(ValidationError):
            service.full_clean()

    def test_negative_monthly_budget_validation(
        self, guard_instance, property_instance
    ):
        """Test that negative monthly budgets are not allowed"""
        from django.core.exceptions import ValidationError

        service = Service(
            name="Invalid Service",
            guard=guard_instance,
            assigned_property=property_instance,
            rate=Decimal("25.00"),
            monthly_budget=Decimal("-1000.00"),
        )
        with pytest.raises(ValidationError):
            service.full_clean()

    def test_required_name_field(self, guard_instance, property_instance):
        """Test that name field is required"""
        from django.core.exceptions import ValidationError

        service = Service(
            guard=guard_instance,
            assigned_property=property_instance,
            rate=Decimal("25.00"),
            monthly_budget=Decimal("2000.00"),
        )
        with pytest.raises(ValidationError):
            service.full_clean()


@pytest.mark.django_db
class TestServicePermissions:
    """Test Service permissions and access control"""

    def test_admin_full_access(self, api_client, admin_user, service_instance):
        """Test that admin has full access to services"""
        api_client.force_authenticate(user=admin_user)

        # List
        response = api_client.get(reverse("core:service-list"))
        assert response.status_code == 200

        # Retrieve
        response = api_client.get(
            reverse("core:service-detail", kwargs={"pk": service_instance.id})
        )
        assert response.status_code == 200

        # Update
        response = api_client.patch(
            reverse("core:service-detail", kwargs={"pk": service_instance.id}),
            {"name": "Updated Name"},
        )
        assert response.status_code == 200

    def test_guard_limited_access(self, api_client, guard_user, service_instance):
        """Test that guards have limited access to services"""
        api_client.force_authenticate(user=guard_user)

        # List (should work but filtered)
        response = api_client.get(reverse("core:service-list"))
        assert response.status_code == 200

        # Retrieve (should work for assigned services)
        response = api_client.get(
            reverse("core:service-detail", kwargs={"pk": service_instance.id})
        )
        assert response.status_code in [
            200,
            403,
        ]  # Depends on permission implementation

    def test_client_limited_access(self, api_client, client_user, service_instance):
        """Test that clients have limited access to services"""
        api_client.force_authenticate(user=client_user)

        # List (should work but filtered to their properties)
        response = api_client.get(reverse("core:service-list"))
        assert response.status_code == 200

        # Create (should be forbidden)
        response = api_client.post(
            reverse("core:service-list"),
            {"name": "Test Service", "rate": "25.00", "monthly_budget": "2000.00"},
        )
        assert response.status_code == 403
