from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from core.models import Client, Guard, Note


@pytest.mark.django_db
class TestNoteModel:
    """Test cases for Note model"""

    def test_note_creation(self):
        """Test creating a note"""
        note = Note.objects.create(
            name="Test Note", description="Test Description", amount=Decimal("100.50")
        )

        assert note.name == "Test Note"
        assert note.description == "Test Description"
        assert note.amount == Decimal("100.50")
        assert note.is_active is True

    def test_note_str_method(self):
        """Test the string representation of note"""
        note = Note.objects.create(name="Test Note", amount=Decimal("50.00"))

        expected_str = "Test Note ($50.00) - No relations"
        assert str(note) == expected_str

    def test_note_with_relations_str(self, create_test_data):
        """Test string representation with relations"""
        client, guard, property_obj = create_test_data

        note = Note.objects.create(
            name="Related Note",
            amount=Decimal("75.25"),
            clients=[client.id],
            properties=[property_obj.id],
        )

        str_repr = str(note)
        assert "Related Note ($75.25)" in str_repr
        assert "Clients: 1" in str_repr
        assert "Properties: 1" in str_repr

    def test_amount_properties(self):
        """Test amount-related properties"""
        # Test positive amount (income)
        income_note = Note.objects.create(name="Income Note", amount=Decimal("100.00"))
        assert income_note.is_income is True
        assert income_note.is_expense is False
        assert income_note.amount_type == "Income"

        # Test negative amount (expense)
        expense_note = Note.objects.create(
            name="Expense Note", amount=Decimal("-50.00")
        )
        assert expense_note.is_income is False
        assert expense_note.is_expense is True
        assert expense_note.amount_type == "Expense"

        # Test zero amount (neutral)
        neutral_note = Note.objects.create(name="Neutral Note", amount=Decimal("0.00"))
        assert neutral_note.is_income is False
        assert neutral_note.is_expense is False
        assert neutral_note.amount_type == "Neutral"

    def test_get_related_entities(self, create_test_data):
        """Test getting related entities"""
        client, guard, property_obj = create_test_data

        note = Note.objects.create(
            name="Multi-Relation Note",
            clients=[client.id],
            guards=[guard.id],
            properties=[property_obj.id],
        )

        related_entities = note.get_related_entities()
        assert len(related_entities) == 3
        assert "clients" in related_entities
        assert "guards" in related_entities
        assert "properties" in related_entities
        assert related_entities["clients"] == [client.id]
        assert related_entities["guards"] == [guard.id]
        assert related_entities["properties"] == [property_obj.id]

    def test_note_default_values(self):
        """Test default values for note"""
        note = Note.objects.create(name="Default Note")

        assert note.description == ""
        assert note.amount == Decimal("0.00")
        assert note.clients == []
        assert note.properties == []
        assert note.guards == []


@pytest.mark.django_db
class TestNoteAPI:
    """Test cases for Note API endpoints"""

    def test_create_note(self, api_client, admin_user):
        """Test creating a note via API"""
        api_client.force_authenticate(user=admin_user)

        url = reverse("core:note-list")
        data = {
            "name": "API Test Note",
            "description": "Created via API",
            "amount": "150.75",
        }

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        note = Note.objects.get(id=response.data["id"])
        assert note.name == "API Test Note"
        assert note.amount == Decimal("150.75")
        assert note.created_by == admin_user  # Verify created_by is set

    def test_created_by_field_in_response(self, api_client, admin_user):
        """Test that created_by field is included in API responses"""
        api_client.force_authenticate(user=admin_user)

        # Create a note
        url = reverse("core:note-list")
        data = {
            "name": "Created By Test Note",
            "description": "Testing created_by field",
            "amount": "50.00",
        }

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "created_by" in response.data
        assert response.data["created_by"] == admin_user.id

        # Retrieve the note and verify created_by info
        note_id = response.data["id"]
        url = reverse("core:note-detail", kwargs={"pk": note_id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "created_by" in response.data
        assert "created_by_name" in response.data
        assert response.data["created_by"] == admin_user.id
        expected_name = admin_user.get_full_name() or admin_user.username
        assert response.data["created_by_name"] == expected_name

    def test_list_notes(self, api_client, admin_user):
        """Test listing notes via API"""
        api_client.force_authenticate(user=admin_user)

        # Create test notes
        Note.objects.create(name="Note 1", amount=Decimal("100.00"))
        Note.objects.create(name="Note 2", amount=Decimal("-50.00"))

        url = reverse("core:note-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_retrieve_note(self, api_client, admin_user):
        """Test retrieving a specific note"""
        api_client.force_authenticate(user=admin_user)

        note = Note.objects.create(name="Retrieve Test", amount=Decimal("25.50"))

        url = reverse("core:note-detail", kwargs={"pk": note.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Retrieve Test"
        assert response.data["amount"] == "25.50"

    def test_update_note(self, api_client, admin_user):
        """Test updating a note"""
        api_client.force_authenticate(user=admin_user)

        note = Note.objects.create(name="Original Name", amount=Decimal("100.00"))

        url = reverse("core:note-detail", kwargs={"pk": note.pk})
        data = {"name": "Updated Name", "amount": "200.00"}

        response = api_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK

        note.refresh_from_db()
        assert note.name == "Updated Name"
        assert note.amount == Decimal("200.00")

    def test_delete_note(self, api_client, admin_user):
        """Test deleting a note (soft delete)"""
        api_client.force_authenticate(user=admin_user)

        note = Note.objects.create(name="To Delete")

        url = reverse("core:note-detail", kwargs={"pk": note.pk})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        note.refresh_from_db()
        assert note.is_active is False

    def test_note_with_relations(self, api_client, admin_user, create_test_data):
        """Test creating note with relations"""
        api_client.force_authenticate(user=admin_user)
        client, guard, property_obj = create_test_data

        url = reverse("core:note-list")
        data = {
            "name": "Related Note",
            "description": "Note with relations",
            "amount": "75.00",
            "clients": [client.id],
            "properties": [property_obj.id],
            "guards": [guard.id],
        }

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        note = Note.objects.get(id=response.data["id"])
        assert client.id in note.clients
        assert property_obj.id in note.properties
        assert guard.id in note.guards

    def test_note_filtering(self, api_client, admin_user):
        """Test filtering notes using search functionality"""
        api_client.force_authenticate(user=admin_user)

        # Create test notes
        Note.objects.create(name="Income Note", amount=Decimal("100.00"))
        Note.objects.create(name="Expense Note", amount=Decimal("-50.00"))
        Note.objects.create(name="Search Note", amount=Decimal("25.00"))

        url = reverse("core:note-list")

        # Test basic list - should return all notes
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

        # Test name search (should find notes containing "Note")
        response = api_client.get(url, {"search": "Income"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Income Note"

        # Test search by description/name
        response = api_client.get(url, {"search": "Search"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Search Note"

    def test_note_statistics_endpoint(self, api_client, admin_user):
        """Test the statistics endpoint"""
        api_client.force_authenticate(user=admin_user)

        # Create test notes
        Note.objects.create(name="Income 1", amount=Decimal("100.00"))
        Note.objects.create(name="Income 2", amount=Decimal("50.00"))
        Note.objects.create(name="Expense 1", amount=Decimal("-30.00"))
        Note.objects.create(name="Neutral", amount=Decimal("0.00"))

        url = reverse("core:note-statistics")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_notes"] == 4
        assert response.data["total_amount"] == Decimal("120.00")
        assert response.data["income_amount"] == Decimal("150.00")
        assert response.data["expense_amount"] == Decimal("-30.00")
        assert response.data["income_count"] == 2
        assert response.data["expense_count"] == 1
        assert response.data["neutral_count"] == 1

    def test_note_duplicate_endpoint(self, api_client, admin_user):
        """Test the duplicate endpoint"""
        api_client.force_authenticate(user=admin_user)

        note = Note.objects.create(
            name="Original Note",
            description="Original description",
            amount=Decimal("100.00"),
        )

        url = reverse("core:note-duplicate", kwargs={"pk": note.pk})
        data = {"name": "Duplicated Note"}

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # Check that new note was created
        new_note = Note.objects.get(id=response.data["id"])
        assert new_note.name == "Duplicated Note"
        assert new_note.description == "Original description"  # Should copy
        assert new_note.amount == Decimal("100.00")  # Should copy
        assert new_note.id != note.id  # Should be different

    def test_note_summary_endpoint(self, api_client, admin_user):
        """Test the summary endpoint"""
        api_client.force_authenticate(user=admin_user)

        # Create test notes
        Note.objects.create(name="Note 1", amount=Decimal("100.00"))
        Note.objects.create(name="Note 2", amount=Decimal("-50.00"))

        url = reverse("core:note-summary")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

        # Check that summary fields are present
        note_data = response.data["results"][0]
        required_fields = ["id", "name", "amount", "amount_type", "created_at"]
        for field in required_fields:
            assert field in note_data

    def test_unauthorized_access(self, api_client):
        """Test that unauthorized users cannot access notes"""
        url = reverse("core:note-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestNotePermissions:
    """Test cases for Note permissions and filtering"""

    def test_client_sees_own_notes(self, api_client, create_test_data):
        """Test that clients only see their own notes"""
        client, guard, property_obj = create_test_data

        # Create notes for this client and another
        client_note = Note.objects.create(
            name="Client Note", clients=[client.id], amount=Decimal("100.00")
        )

        other_client = Client.objects.create(
            user=User.objects.create_user(username="other", password="pass"),
            phone="999999999",
        )
        Note.objects.create(
            name="Other Client Note", clients=[other_client.id], amount=Decimal("50.00")
        )

        api_client.force_authenticate(user=client.user)

        url = reverse("core:note-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == client_note.id

    def test_guard_sees_own_notes(self, api_client, create_test_data):
        """Test that guards only see their own notes"""
        client, guard, property_obj = create_test_data

        # Create note for this guard
        guard_note = Note.objects.create(
            name="Guard Note", guards=[guard.id], amount=Decimal("75.00")
        )

        # Create note for another guard
        other_guard = Guard.objects.create(
            user=User.objects.create_user(username="other_guard", password="pass"),
            phone="888888888",
        )
        Note.objects.create(
            name="Other Guard Note", guards=[other_guard.id], amount=Decimal("25.00")
        )

        api_client.force_authenticate(user=guard.user)

        url = reverse("core:note-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == guard_note.id

    def test_user_without_profile_sees_no_notes(self, api_client):
        """Test that users without client/guard profile see no notes"""
        user = User.objects.create_user(username="noProfile", password="pass")

        # Create some notes
        Note.objects.create(name="Some Note", amount=Decimal("100.00"))

        api_client.force_authenticate(user=user)

        url = reverse("core:note-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_duplicate_note_sets_created_by(self, api_client, admin_user):
        """Test that duplicating a note sets created_by to current user"""
        # Create a different user who will be the original creator
        original_user = User.objects.create_user(
            username="original_creator", password="pass123"
        )

        # Create a note with original user as creator
        original_note = Note.objects.create(
            name="Original Note",
            description="Original description",
            amount=Decimal("100.00"),
            created_by=original_user,
        )

        # Authenticate as admin user (different from original creator)
        api_client.force_authenticate(user=admin_user)

        # Duplicate the note
        url = reverse("core:note-duplicate", kwargs={"pk": original_note.pk})
        response = api_client.post(url, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        # Verify the duplicate note has admin_user as created_by
        duplicated_note = Note.objects.get(id=response.data["id"])
        assert duplicated_note.created_by == admin_user
        assert duplicated_note.name == "Original Note (Copy)"
        assert duplicated_note.amount == Decimal("100.00")

        # Verify original note is unchanged
        original_note.refresh_from_db()
        assert original_note.created_by == original_user


@pytest.mark.django_db
class TestNoteValidation:
    """Test cases for Note validation"""

    def test_empty_name_validation(self, api_client, admin_user):
        """Test that empty name is not allowed"""
        api_client.force_authenticate(user=admin_user)

        url = reverse("core:note-list")
        data = {
            "name": "",  # Empty name
            "amount": "100.00",
        }

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data

    def test_invalid_amount_validation(self, api_client, admin_user):
        """Test amount validation"""
        api_client.force_authenticate(user=admin_user)

        url = reverse("core:note-list")
        data = {"name": "Test Note", "amount": "invalid_amount"}

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "amount" in response.data

    def test_none_amount_becomes_zero(self, api_client, admin_user):
        """Test that None amount becomes 0.00"""
        api_client.force_authenticate(user=admin_user)

        url = reverse("core:note-list")
        data = {
            "name": "Zero Amount Note"
            # No amount provided
        }

        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        note = Note.objects.get(id=response.data["id"])
        assert note.amount == Decimal("0.00")
