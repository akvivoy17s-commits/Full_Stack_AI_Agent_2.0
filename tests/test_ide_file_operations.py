"""Tests for safe create/delete operations exposed by the IDE Explorer."""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _new_project() -> str:
    response = client.post(
        "/projects",
        json={"brief": "A small demo website with a home page and contact form"},
    )
    assert response.status_code == 200, response.text
    return response.json()["project_id"]


def test_create_nested_source_file_and_delete_it():
    pid = _new_project()
    path = "src/components/CreatedFromIDE.tsx"

    created = client.post(f"/projects/{pid}/file", json={"path": path, "content": "export default function CreatedFromIDE() { return null }"})
    assert created.status_code == 200, created.text
    assert created.json()["path"] == path
    assert path in client.get(f"/projects/{pid}/files").json()
    assert client.get(f"/projects/{pid}/file", params={"path": path}).json()["content"].startswith("export default")

    deleted = client.delete(f"/projects/{pid}/file", params={"path": path})
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["deleted"] == path
    assert path not in client.get(f"/projects/{pid}/files").json()


def test_create_file_does_not_overwrite_existing_file():
    pid = _new_project()
    path = "src/new-file.ts"
    assert client.post(f"/projects/{pid}/file", json={"path": path, "content": "old"}).status_code == 200
    response = client.post(f"/projects/{pid}/file", json={"path": path, "content": "new"})
    assert response.status_code == 409
    assert client.get(f"/projects/{pid}/file", params={"path": path}).json()["content"] == "old"


def test_create_delete_reject_traversal_and_agent_private_paths():
    pid = _new_project()
    for path in ("../outside.ts", ".agent/private.ts", "src/../../outside.ts"):
        created = client.post(f"/projects/{pid}/file", json={"path": path, "content": "x"})
        assert created.status_code == 400, (path, created.text)
    deleted = client.delete(f"/projects/{pid}/file", params={"path": ".agent/private.ts"})
    assert deleted.status_code == 400, deleted.text
