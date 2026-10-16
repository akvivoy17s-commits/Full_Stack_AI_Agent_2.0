import json
import os

os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ["AUTO_MIGRATE"] = "true"
os.environ["DJANGO_SETTINGS_MODULE"] = "app.settings"

from app import schema  # noqa: E402  (the environment above must be set before the app is imported)

if schema.SCHEMA["db"] == "sqlite":
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
elif os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

import pytest  # noqa: E402


def _setup():
    """Django starts inside the fixtures, so tests that are skipped (no TEST_DATABASE_URL) never need a valid configuration."""
    import django
    from django.apps import apps
    if not apps.ready:
        django.setup()


@pytest.fixture(scope="session")
def db():
    _setup()
    if not schema.SCHEMA["db"]:
        yield None
        return
    from app.db import connect
    d = connect()
    d.migrate()
    yield d
    d.close()


@pytest.fixture(scope="session")
def call(db):
    from django.test import Client
    client = Client()

    def _call(method, path, body=None, token=None, raw=None):
        extra = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
        data = raw if raw is not None else ("" if body is None else json.dumps(body))
        res = client.generic(method, path, data=data, content_type="application/json", **extra)
        try:
            return res.status_code, res.json()
        except ValueError:      # 204 has no JSON body
            return res.status_code, None

    return _call
