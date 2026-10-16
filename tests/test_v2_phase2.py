"""V2 phase 2: wizard overrides reach project creation; editing an entity keeps its access rules."""
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
BRIEF = "online store with login and checkout"


def _entity(spec, name):
    return next(e for e in spec["data"]["entities"] if e["name"] == name)


def test_create_applies_overrides_and_keeps_access_rules():
    base = client.post("/spec/preview", json={"brief": BRIEF, "mode": "automatic"}).json()["spec"]
    old = _entity(base, "Product")
    ov = {"entities": {"Product": ["name:string!", "price:float!", "badge:string"]}, "features": ["Wishlist", "Gift cards"]}
    r = client.post("/projects", json={"brief": BRIEF, "mode": "automatic", "overrides": ov})
    assert r.status_code == 200, r.text
    spec = client.get(f"/projects/{r.json()['project_id']}/spec").json()
    new = _entity(spec, "Product")
    assert [f["name"] for f in new["fields"]] == ["name", "price", "badge"]
    assert (new["read"], new["write"]) == (old["read"], old["write"])
    assert spec["features"] == ["Wishlist", "Gift cards"] and spec["overrides"]["features"] == ["Wishlist", "Gift cards"]


def test_create_rejects_bad_overrides_without_leaving_a_project():
    before = len(client.get("/projects").json())
    assert client.post("/projects", json={"brief": BRIEF, "mode": "automatic", "overrides": {"nope": 1}}).status_code == 422
    assert client.post("/projects", json={"brief": BRIEF, "mode": "automatic", "overrides": {"entities": {"bad name": ["x:string"]}}}).status_code == 422
    assert client.post("/projects", json={"brief": BRIEF, "mode": "automatic", "overrides": {"drop_entities": ["Product"]}}).status_code == 422   # OrderItem still references it
    assert len(client.get("/projects").json()) == before


def test_create_without_overrides_is_unchanged():
    r = client.post("/projects", json={"brief": BRIEF, "mode": "automatic"})
    assert r.status_code == 200 and client.get(f"/projects/{r.json()['project_id']}/spec").json()["overrides"] == {}
