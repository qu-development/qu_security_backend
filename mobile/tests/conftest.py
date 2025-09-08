import pytest
from django.conf import settings


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
