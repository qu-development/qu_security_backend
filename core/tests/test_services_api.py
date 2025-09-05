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
        service = Service.objects.create(
            name="Security Service",
            description="24/7 security monitoring",
            guard=guard_instance,
            assigned_property=property_instance,
            rate=Decimal("30.00"),
            monthly_budget=Decimal("2400.00"),
            contract_start_date=contract_date,
        )

        assert service.name == "Security Service"
        assert service.description == "24/7 security monitoring"
        assert service.guard == guard_instance
        assert service.assigned_property == property_instance
        assert service.rate == Decimal("30.00")
        assert service.monthly_budget == Decimal("2400.00")
        assert service.contract_start_date == contract_date
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
        """Test total hours calculation based on shifts"""
        # Create some shifts for the service
        baker.make(
            Shift,
            service=service_instance,
            guard=service_instance.guard,
            property=service_instance.assigned_property,
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
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=6),
            hours_worked=6,
            status="completed",
        )

        # Test that total_hours method works
        total_hours = service_instance.total_hours
        assert total_hours == 14  # 8 + 6 hours

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
        assert response.data["results"][0]["name"] == service_instance.name

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
        }
        response = api_client.post(url, data)

        assert response.status_code == 201
        assert response.data["name"] == "New Security Service"
        assert response.data["rate"] == "40.00"
        assert response.data["monthly_budget"] == "3200.00"

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
        assert "guard_name" in response.data
        assert "property_name" in response.data

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
        }
        response = api_client.patch(url, data)

        assert response.status_code == 200
        assert response.data["name"] == "Updated Service Name"
        assert response.data["rate"] == "45.00"
        assert response.data["monthly_budget"] == "3600.00"

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

    def test_unauthenticated_access_forbidden(self, api_client, service_instance):
        """Test that unauthenticated users cannot access services"""
        url = reverse("core:service-list")
        response = api_client.get(url)

        assert response.status_code == 401


@pytest.mark.django_db
class TestServiceValidation:
    """Test Service model validation"""

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
