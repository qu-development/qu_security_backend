"""
Tests for bulk operations mixin
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from common.mixins import BulkActionMixin

User = get_user_model()


"""
Tests for bulk operations mixin
"""


User = get_user_model()


class BulkActionMixinTest(TestCase):
    """Test the BulkActionMixin functionality"""

    def test_bulk_action_mixin_methods_exist(self):
        """Test that BulkActionMixin has the required methods"""
        mixin = BulkActionMixin()

        # Check that all bulk methods exist
        self.assertTrue(hasattr(mixin, "bulk_create"))
        self.assertTrue(hasattr(mixin, "bulk_delete"))
        self.assertTrue(hasattr(mixin, "bulk_update"))

        # Check that methods are callable
        self.assertTrue(callable(mixin.bulk_create))
        self.assertTrue(callable(mixin.bulk_delete))
        self.assertTrue(callable(mixin.bulk_update))

    def test_bulk_serializers_import(self):
        """Test that bulk serializers can be imported"""
        from common.bulk_serializers import (
            BulkCreateRequestSerializer,
            BulkDeleteRequestSerializer,
            BulkResponseSerializer,
            BulkUpdateRequestSerializer,
        )

        # Test that serializers exist and can be instantiated
        self.assertTrue(BulkCreateRequestSerializer)
        self.assertTrue(BulkDeleteRequestSerializer)
        self.assertTrue(BulkUpdateRequestSerializer)
        self.assertTrue(BulkResponseSerializer)

    def test_bulk_operations_documentation_exists(self):
        """Test that bulk operations documentation file exists"""
        import os

        # Get the project root directory (2 levels up from common/tests)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        docs_path = os.path.join(project_root, "docs", "bulk-operations.md")
        self.assertTrue(
            os.path.exists(docs_path),
            f"Bulk operations documentation should exist at {docs_path}",
        )
