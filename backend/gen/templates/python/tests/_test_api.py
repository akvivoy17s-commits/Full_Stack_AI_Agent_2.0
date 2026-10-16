"""Generated tests: they read app/schema.py, so they cover every entity and access rule of THIS app.
SQLite runs in memory. For PostgreSQL / MySQL / MongoDB set TEST_DATABASE_URL to a disposable database."""
import itertools
import os

import pytest

from app import schema

S = schema.SCHEMA
ENTITIES = [e for e in S["entities"].values() if not e["internal"] and not e["isUser"] and e["ops"]]
PW = "Passw0rd!long"
_seq = itertools.count(1)

pytestmark = pytest.mark.skipif(S["db"] not in (None, "sqlite") and not os.environ.get("TEST_DATABASE_URL"),
                                reason="set TEST_DATABASE_URL to run the database tests")


def sample(f):
    n = next(_seq)
    return {"string": f"s{n}", "text": f"text {n}", "email": f"e{n}@example.com", "url": f"https://example.com/{n}",
            "int": n, "float": 1.5, "bool": True, "datetime": "2030-01-01T00:00:00Z"}[f["type"]]


def values(db, e, api):
    """Required values for an entity. api=True leaves out what the server sets itself."""
    o = {}
    for f in e["fields"]:
        if not f["required"]:
            continue
        if api and (f["name"] == e["ownerField"] or f["name"] in e["sensitive"] or f["name"] == "created_at"):
            continue
        if f["type"] == "ref":
            o[f["name"]] = db.create(f["ref"], values(db, S["entities"][f["ref"]], False))["id"]
        elif f["type"] == "enum":
            o[f["name"]] = f["values"][0]
        elif f["name"] == "password_hash":
            from app.security import hash_password
            o[f["name"]] = hash_password(PW)
        elif f["name"] == "created_at":
            o[f["name"]] = "2030-01-01T00:00:00Z"
        else:
            o[f["name"]] = sample(f)
    return o


def make_user(db, call, role=None):
    email = f"u{next(_seq)}@example.com"
    if role:
        from app.security import hash_password
        db.create("User", {"email": email, "name": "Seeded", "password_hash": hash_password(PW), "role": role,
                           **({"created_at": "2030-01-01T00:00:00Z"} if any(f["name"] == "created_at" for f in S["entities"]["User"]["fields"]) else {})})
    else:
        assert call("POST", "/api/auth/register", {"email": email, "name": "Test User", "password": PW})[0] == 201
    status, body = call("POST", "/api/auth/login", {"email": email, "password": PW})
    assert status == 200
    return {"token": body["accessToken"], "id": body["user"]["id"], "email": email}


def test_health(call):
    status, body = call("GET", "/api/health")
    assert status == 200 and body["status"] == "ok"


def test_unknown_route_is_json_404(call):
    status, body = call("GET", "/api/does-not-exist")
    assert status == 404 and body["error"]["code"] == "not_found"


def test_invalid_json_is_a_client_error(call):
    status, body = call("POST", "/api/auth/login" if S["auth"] else "/api/health", raw=b"{not json")
    assert status in (400, 405) and "error" in body


if S["auth"]:
    def test_register_login_me_refresh_logout(call):
        email = f"a{next(_seq)}@example.com"
        status, body = call("POST", "/api/auth/register", {"email": email, "name": "Test", "password": PW})
        assert status == 201 and body["user"]["role"] == S["defaultRole"] and "password_hash" not in body["user"]
        assert S["defaultRole"] != S["adminRole"] and body["user"]["role"] != S["adminRole"]   # sign-up never creates an administrator
        assert call("POST", "/api/auth/register", {"email": email, "name": "Test", "password": PW})[0] == 409
        assert call("POST", "/api/auth/register", {"email": "bad", "name": "", "password": "x"})[0] == 400
        assert call("POST", "/api/auth/register", {"email": f"b{next(_seq)}@example.com", "name": "X", "password": PW, "role": S["adminRole"]})[0] == 400
        assert call("POST", "/api/auth/login", {"email": email, "password": "wrong-password"})[0] == 401
        status, body = call("POST", "/api/auth/login", {"email": email, "password": PW})
        assert status == 200
        access, refresh = body["accessToken"], body.get("refreshToken")
        assert call("GET", "/api/auth/me")[0] == 401
        assert call("GET", "/api/auth/me", token="not-a-token")[0] == 401
        assert call("GET", "/api/auth/me", token=access)[1]["user"]["email"] == email
        if S["refresh"]:
            status, body = call("POST", "/api/auth/refresh", {"refreshToken": refresh})
            assert status == 200 and body["refreshToken"] != refresh
            assert call("POST", "/api/auth/refresh", {"refreshToken": refresh})[0] == 401  # single use
        assert call("POST", "/api/auth/logout", {}, token=access)[0] == 204

    def test_login_rejects_non_string_credentials(call):
        assert call("POST", "/api/auth/login", {"email": {"$ne": "x"}, "password": {"$ne": "x"}})[0] == 400

    if "list" in S["entities"]["User"]["ops"]:
        def test_user_list_is_admin_only_and_hides_password_hashes(db, call):
            admin, user = make_user(db, call, S["adminRole"]), make_user(db, call)
            assert call("GET", "/api/users")[0] == 401
            assert call("GET", "/api/users", token=user["token"])[0] == 403
            status, body = call("GET", "/api/users", token=admin["token"])
            assert status == 200 and len(body["data"]) >= 2 and all("password_hash" not in u for u in body["data"])


@pytest.mark.parametrize("e", ENTITIES, ids=[e["name"] for e in ENTITIES])
def test_entity_access_rules_and_crud(db, call, e):
    p, ops = f"/api/{e['path']}", e["ops"]
    admin = make_user(db, call, S["adminRole"]) if S["auth"] else {"token": None}
    user = make_user(db, call) if S["auth"] else {"token": None}
    fresh = lambda: values(db, e, True)  # every request gets its own values (unique fields)
    body = fresh()

    if "list" in ops:
        assert call("GET", p)[0] == (200 if e["read"] == "public" else 401)
        if e["read"] == "admin":
            assert call("GET", p, token=user["token"])[0] == 403
    if "create" not in ops:
        return
    assert call("POST", p, fresh())[0] == (201 if e["write"] == "public" else 401)
    if e["write"] == "admin":
        assert call("POST", p, fresh(), token=user["token"])[0] == 403
    assert call("POST", p, {**fresh(), "bogus": 1}, token=admin["token"])[0] == 400  # unknown fields are rejected
    if body:
        assert call("POST", p, {}, token=admin["token"])[0] == 400  # required fields
    status, made = call("POST", p, fresh(), token=admin["token"])
    assert status == 201 and "id" in made
    rid = made["id"]
    if e["ownerField"] and S["auth"]:
        assert str(made[e["ownerField"]]) == str(admin["id"])
    assert all(s not in made for s in e["sensitive"])

    if "get" in ops:
        assert call("GET", f"{p}/{rid}", token=admin["token"])[0] == 200
        assert call("GET", f"{p}/{'0' * 24 if S['db'] == 'mongodb' else 999999999}", token=admin["token"])[0] == 404
        assert call("GET", f"{p}/abc", token=admin["token"])[0] == 404
    if "list" in ops:
        status, lst = call("GET", f"{p}?limit=5", token=admin["token"])
        assert status == 200 and isinstance(lst["data"], list) and lst["total"] >= 1 and lst["page"] == 1 and lst["limit"] == 5
        assert call("GET", f"{p}?limit=0", token=admin["token"])[0] == 400
    if "update" in ops and body:
        assert call("PUT", f"{p}/{rid}", fresh(), token=admin["token"])[0] == 200
        if S["auth"]:
            assert call("PUT", f"{p}/{rid}", fresh())[0] == (200 if e["write"] == "public" else 401)
    if "get" in ops and e["ownerField"] and e["write"] == "owner" and S["auth"]:
        status, mine = call("POST", p, fresh(), token=user["token"])
        assert status == 201
        other = make_user(db, call)
        assert call("GET", f"{p}/{mine['id']}", token=user["token"])[0] == 200
        assert call("GET", f"{p}/{mine['id']}", token=other["token"])[0] == 404  # other users cannot see it
        assert call("GET", f"{p}/{mine['id']}", token=admin["token"])[0] == 200
    if "delete" in ops:
        assert call("DELETE", f"{p}/{rid}", token=admin["token"])[0] == 204
        if "get" in ops:
            assert call("GET", f"{p}/{rid}", token=admin["token"])[0] == 404
