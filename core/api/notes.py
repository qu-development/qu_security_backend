from decimal import Decimal

from django.db.models import Q, Sum
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from common.pagination import SettingsPageNumberPagination
from core.models import Note
from core.serializers import (
    NoteCreateSerializer,
    NoteSerializer,
    NoteSummarySerializer,
    NoteUpdateSerializer,
)


class NoteViewSet(ModelViewSet):
    """
    ViewSet for managing Notes with full CRUD operations.

    Notes can be related to any entity in the system and track
    financial information (positive/negative amounts).
    """

    queryset = Note.objects.select_related("created_by").order_by("-created_at")

    permission_classes = [IsAuthenticated]
    pagination_class = SettingsPageNumberPagination
    # No custom filterset, use default DRF search/order

    search_fields = ["name", "description"]
    ordering_fields = ["name", "amount", "created_at", "updated_at"]
    ordering = ["-created_at"]  # Default ordering

    def get_serializer_class(self):
        """Return the appropriate serializer class"""
        if self.action == "create":
            return NoteCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return NoteUpdateSerializer
        elif self.action == "summary":
            return NoteSummarySerializer
        return NoteSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()

        # If user is not superuser or staff, filter by user's related data
        if not (self.request.user.is_superuser or self.request.user.is_staff):
            user = self.request.user

            # Filter to show only notes related to user's entities
            user_filter = Q()

            # Include notes related to user as client
            if hasattr(user, "client"):
                user_filter |= Q(clients__contains=[user.client.id])
                # Include notes for user's properties (get properties owned by user's client)
                from core.models import Property

                user_properties = Property.objects.filter(
                    owner_id=user.client.id
                ).values_list("id", flat=True)
                if user_properties:
                    user_filter |= Q(properties__overlap=list(user_properties))

            # Include notes related to user as guard
            if hasattr(user, "guard"):
                user_filter |= Q(guards__contains=[user.guard.id])
                # Include notes for guard's services and shifts
                from core.models import Service, Shift

                user_services = Service.objects.filter(
                    guard_id=user.guard.id
                ).values_list("id", flat=True)
                if user_services:
                    user_filter |= Q(services__overlap=list(user_services))
                user_shifts = Shift.objects.filter(guard_id=user.guard.id).values_list(
                    "id", flat=True
                )
                if user_shifts:
                    user_filter |= Q(shifts__overlap=list(user_shifts))

            # Apply filter if any conditions exist
            queryset = queryset.filter(user_filter) if user_filter else queryset.none()

        return queryset

    def perform_create(self, serializer):
        """Set created_by field when creating a note"""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Perform soft delete by setting is_active=False"""
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get a summary of notes with lightweight data.
        Useful for dashboards or quick overviews.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Get pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        Get statistics about notes including totals and counts.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Calculate statistics
        total_notes = queryset.count()
        total_amount = queryset.aggregate(total=Sum("amount"))["total"] or Decimal(
            "0.00"
        )

        positive_amount = queryset.filter(amount__gt=0).aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")

        negative_amount = queryset.filter(amount__lt=0).aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")

        # Count by amount type
        income_count = queryset.filter(amount__gt=0).count()
        expense_count = queryset.filter(amount__lt=0).count()
        neutral_count = queryset.filter(amount=0).count()

        # Count by relations (now using array fields)
        relations_stats = {}
        array_fields = [
            "clients",
            "properties",
            "guards",
            "services",
            "shifts",
            "weapons",
            "type_of_services",
        ]

        for field in array_fields:
            # Count notes that have non-empty arrays for each field
            relations_stats[f"{field}_count"] = queryset.exclude(**{field: []}).count()

        return Response(
            {
                "total_notes": total_notes,
                "total_amount": total_amount,
                "income_amount": positive_amount,
                "expense_amount": negative_amount,
                "net_amount": total_amount,
                "income_count": income_count,
                "expense_count": expense_count,
                "neutral_count": neutral_count,
                "relations_statistics": relations_stats,
            }
        )

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """
        Create a duplicate of an existing note.
        Optionally modify some fields in the request data.
        """
        note = self.get_object()

        # Get the original data
        serializer = NoteCreateSerializer(note)
        original_data = serializer.data.copy()

        # Update with any provided data from request
        update_data = request.data
        for key, value in update_data.items():
            if key in original_data:
                original_data[key] = value

        # Remove the ID and timestamps for duplication
        original_data.pop("id", None)

        # Modify name to indicate it's a duplicate if not overridden
        if "name" not in update_data:
            original_data["name"] = f"{original_data['name']} (Copy)"

        # Create the new note
        create_serializer = NoteCreateSerializer(
            data=original_data, context={"request": request}
        )
        if create_serializer.is_valid():
            new_note = create_serializer.save(created_by=request.user)
            response_serializer = NoteSerializer(new_note)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                create_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
