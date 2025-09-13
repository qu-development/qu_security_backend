from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.mixins import BulkActionMixin, FilterMixin, SoftDeleteMixin
from permissions.permissions import CanCreateExpense, IsClientOwner
from permissions.utils import PermissionManager

from ..models import Expense
from ..serializers import ExpenseSerializer


class ExpenseViewSet(
    SoftDeleteMixin, FilterMixin, BulkActionMixin, viewsets.ModelViewSet
):
    """
    ViewSet for managing Expense model with full CRUD operations.

    list: Returns a list of all expenses
    create: Creates a new expense
    retrieve: Returns expense details by ID
    update: Updates expense information (PUT)
    partial_update: Partially updates expense information (PATCH)
    destroy: Deletes an expense
    """

    queryset = Expense.objects.all().order_by("-id")
    serializer_class = ExpenseSerializer

    def get_permissions(self):
        """Return the appropriate permissions based on action"""
        if self.action == "create":
            permission_classes = [permissions.IsAuthenticated, CanCreateExpense]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated, IsClientOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        # Bypass permission filtering for swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return Expense.objects.none()

        queryset = super().get_queryset()
        return PermissionManager.filter_queryset_by_permissions(
            self.request.user, queryset, "expense"
        )

    @swagger_auto_schema(
        operation_description="Get list of all expenses",
        responses={200: ExpenseSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """Get list of all expenses"""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new expense",
        request_body=ExpenseSerializer,
        responses={201: ExpenseSerializer, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        """Create a new expense"""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get expenses by property",
        responses={200: ExpenseSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def by_property(self, request):
        """Get expenses filtered by property ID"""
        property_id = request.query_params.get("property_id")
        if property_id:
            expenses = self.get_queryset().filter(property_id=property_id)
            serializer = self.get_serializer(expenses, many=True)
            return Response(serializer.data)
        return Response({"error": "property_id parameter is required"}, status=400)
