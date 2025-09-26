import tempfile
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.core.files.storage import FileSystemStorage


# Mock MediaStorage to avoid S3 during tests
class TestMediaStorage(FileSystemStorage):
    """Test-only storage that mimics MediaStorage without S3."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location = settings.MEDIA_ROOT

    def get_signed_url(self, name, expiration=3600):
        """Mock implementation that returns a local URL."""
        return f"/media/{name}"

    def save(self, name, content, max_length=None):
        """Override save to use local filesystem."""
        return super().save(name, content, max_length)

    def url(self, name):
        """Return local URL for files."""
        return f"/media/{name}"


@pytest.fixture(scope="session", autouse=True)
def django_db_setup():
    # Mirror core/tests/conftest.py to use in-memory SQLite for test suite
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        # Add defaults expected by Django's DB wrapper to avoid KeyError
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
        "OPTIONS": {},
        "TIME_ZONE": None,
        "TEST": {
            "NAME": None,
            "MIRROR": None,
            "CHARSET": None,
            "COLLATION": None,
        },
    }

    # Force disable S3 storage for tests to prevent AWS credentials issues
    settings.USE_S3 = False

    # Configure local file storage for tests
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    settings.MEDIA_ROOT = tempfile.mkdtemp()

    # Mock AWS settings to avoid errors
    settings.AWS_ACCESS_KEY_ID = "test"
    settings.AWS_SECRET_ACCESS_KEY = "test"
    settings.AWS_STORAGE_BUCKET_NAME = "test-bucket"
    settings.AWS_S3_REGION_NAME = "us-east-1"


@pytest.fixture(scope="session", autouse=True)
def setup_test_storage():
    """Setup storage mocking before Django apps are loaded."""
    # This must happen before Django loads models
    from unittest.mock import patch

    # Mock MediaStorage at import time
    with patch("core.storages.MediaStorage", TestMediaStorage):
        yield


@pytest.fixture(autouse=True)
def mock_media_storage():
    """Mock MediaStorage class to use local filesystem storage."""
    # Import the model to modify its field storage
    from mobile.models import GuardReport

    # Store original storage to restore later
    original_storage = GuardReport._meta.get_field("file").storage

    # Replace the storage with test storage
    GuardReport._meta.get_field("file").storage = TestMediaStorage()

    # Mock the main import paths
    with (
        patch("core.storages.MediaStorage", TestMediaStorage),
        patch("mobile.models.MediaStorage", TestMediaStorage),
    ):
        yield

    # Restore original storage after test
    GuardReport._meta.get_field("file").storage = original_storage


@pytest.fixture(autouse=True)
def mock_boto3():
    """Mock boto3 and botocore to prevent AWS credential errors."""
    mock_s3_client = MagicMock()
    mock_s3_resource = MagicMock()

    with (
        patch("boto3.client", return_value=mock_s3_client),
        patch("boto3.resource", return_value=mock_s3_resource),
        patch("botocore.session.Session"),
        patch("botocore.credentials.Credentials"),
    ):
        yield
