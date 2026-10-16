import os

os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET"] = "test-secret-" + "x" * 40
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ["AUTO_MIGRATE"] = "true"

from app import schema  # noqa: E402  (the environment above must be set before the app is imported)

if schema.SCHEMA["db"] == "sqlite":
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
elif os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["MONGODB_URI"] = os.environ["TEST_DATABASE_URL"]

import pytest  # noqa: E402

from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def db():
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
    client = create_app(db).test_client()

    def _call(method, path, body=None, token=None, raw=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        if raw is not None:
            res = client.open(path, method=method, data=raw, headers={**headers, "Content-Type": "application/json"})
        else:
            res = client.open(path, method=method, json=body, headers=headers)
        return res.status_code, res.get_json(silent=True)

    return _call
