"""App spec: every kind x stack combination builds, is internally consistent, never leaks secrets, and honours overrides."""
import itertools
import json
import re

import pytest

from backend.spec import compose as B
from backend.spec import templates as T
from backend.stack import catalog as C
from backend.stack import resolve

BRIEFS = {
    "portfolio": "personal portfolio website", "landing": "startup landing page", "site": "college website",
    "dashboard": "analytics dashboard for a saas team with login", "ecommerce": "online store with login, razorpay payments and image uploads",
    "chat": "real-time chat app with login", "chatbot": "AI chatbot with openai", "management": "college management system with student attendance",
    "cms": "blog platform with an editor", "social": "social network with a news feed", "local": "personal to-do app, offline",
    "generic": "something",
}


def stack_for(brief, mode="automatic", prefs=None):
    r = resolve(mode, prefs or {}, brief)
    assert r["ok"], r["errors"]
    return r["stack"]


@pytest.mark.parametrize("kind", sorted(BRIEFS))
def test_every_kind_builds_and_is_consistent(kind):
    brief = BRIEFS[kind]
    spec = B.build(brief, stack_for(brief))
    assert spec["kind"] == kind
    assert B.integrity(spec["data"]["entities"]) == []
    assert spec["pages"] and spec["features"] and spec["plan"][0]["id"] == "spec"
    names = {e["name"] for e in spec["data"]["entities"]}
    for r in spec["api"]["routes"]:                                  # every route points at a real entity
        assert r["entity"] is None or r["entity"] in names
    if not spec["auth"]["enabled"]:
        assert all(p["auth"] is False for p in spec["pages"])


def test_stacks_matrix_never_crashes_and_env_is_safe():
    fronts = ["html", "react", "angular", "next", "vue", "svelte"]
    backs = ["express", "nestjs", "fastapi", "flask", "django", "spring", "aspnet", "laravel", "go"]
    n = 0
    for kind, be in itertools.product(["ecommerce", "management", "chatbot", "social"], backs):
        brief = BRIEFS[kind]
        r = resolve("hybrid", {"backend": be}, brief)
        if not r["ok"]:
            continue
        spec = B.build(brief, r["stack"])
        n += 1
        for v in spec["env"]:
            if v["scope"] == "public":
                assert not v["secret"], v
                assert not re.search(r"SECRET|PASSWORD|PRIVATE", v["name"]), v
            if v["secret"]:
                assert not re.search(r"[A-Za-z0-9]{32,}", v["placeholder"]), v      # placeholders only, never a real-looking value
        assert len({v["name"] for v in spec["env"]}) == len(spec["env"])
    assert n > 20
    for fe in fronts:
        r = resolve("hybrid", {"frontend": fe, "frontend_lang": "ts" if fe == "angular" else "js"}, BRIEFS["dashboard"])
        if r["ok"]:
            B.build(BRIEFS["dashboard"], r["stack"])


def test_ecommerce_contract():
    spec = B.build(BRIEFS["ecommerce"], stack_for(BRIEFS["ecommerce"]))
    names = {e["name"] for e in spec["data"]["entities"]}
    assert {"User", "Product", "Order", "OrderItem", "Payment", "FileAsset"} <= names
    routes = {(r["method"], r["path"]): r for r in spec["api"]["routes"]}
    assert ("POST", "/api/checkout") in routes and ("POST", "/api/payments/webhook") in routes and ("GET", "/api/health") in routes
    assert routes[("GET", "/api/products")]["access"] == "public" and routes[("POST", "/api/products")]["access"] == "admin"
    assert routes[("PUT", "/api/orders/{id}")]["access"] == "admin"
    assert not any(r["path"].startswith("/api/order-items") for r in spec["api"]["routes"])       # created via the order
    assert any(v["name"] == "RAZORPAY_KEY_SECRET" and v["secret"] for v in spec["env"])
    user = next(e for e in spec["data"]["entities"] if e["name"] == "User")
    assert "password_hash" in user["sensitive"]


def test_management_variants():
    edu = B.build(BRIEFS["management"], stack_for(BRIEFS["management"]))
    assert {"Student", "Course", "Enrollment", "Attendance"} <= {e["name"] for e in edu["data"]["entities"]} and edu["variant"] == "education"
    hos = B.build("hospital management system with appointments", stack_for("hospital management system with appointments"))
    assert {"Patient", "Doctor", "Appointment"} <= {e["name"] for e in hos["data"]["entities"]}
    gen = B.build("crm management system", stack_for("crm management system"))
    assert any("generic" in a.lower() for a in gen["assumptions"])


def test_no_backend_is_honest():
    spec = B.build(BRIEFS["portfolio"], stack_for(BRIEFS["portfolio"]))
    assert spec["api"]["routes"] == [] and spec["data"]["entities"] == [] and spec["env"] == []
    assert any("mailto" in f for f in spec["features"]) and not any("form" in f.lower() for f in spec["features"])
    legacy = B.build("shop with login and payments", {"frontend": "html", "frontend_lang": "js", "backend": "none", "database": "none", "auth": "none"})
    assert legacy["gaps"] and "no backend" in legacy["gaps"][0]
    assert all(s["status"] in ("done", "ready") for s in legacy["plan"])


def test_portfolio_with_backend_gets_a_working_contact_endpoint():
    spec = B.build(BRIEFS["portfolio"] + " with a contact form", stack_for("portfolio with a contact form and database", "hybrid", {"backend": "express"}))
    r = next(r for r in spec["api"]["routes"] if r["path"] == "/api/enquiries" and r["method"] == "POST")
    assert r["access"] == "public" and r["rate_limited"]


def test_firebase_has_no_custom_api():
    st = stack_for("notes sync app using firebase firestore")
    spec = B.build("notes sync app using firebase firestore", st)
    assert spec["data"]["access"] == "security-rules" and spec["api"]["routes"] == []
    assert any("security rules" in s.lower() for s in spec["security"])


def test_plan_statuses_follow_the_catalog():
    st = stack_for("college management system", "hybrid", {"backend": "spring", "database": "mysql", "frontend": "angular", "frontend_lang": "ts"})
    plan = {s["id"]: s["status"] for s in B.build("college management system", st)["plan"]}
    assert plan["pages"] == "planned:5" and plan["api"] == "ready" and plan["wiring"] == "planned:5" and plan["verify"] == "ready"
    react = {s["id"]: s["status"] for s in B.build("analytics dashboard", {"frontend": "react", "frontend_lang": "ts", "backend": "none", "database": "none"})["plan"]}
    assert react["pages"] == "ready"


def test_open_questions_only_when_essential():
    assert B.build("website", stack_for("website"))["open_questions"][0]["id"] == "purpose"
    assert B.build(BRIEFS["ecommerce"], stack_for(BRIEFS["ecommerce"]))["open_questions"] == []
    q = B.build("store with login and checkout but no backend", {"frontend": "html", "frontend_lang": "js", "backend": "none"})["open_questions"]
    assert q and q[0]["id"] == "backend-conflict"


def test_overrides_and_validation():
    st = stack_for(BRIEFS["ecommerce"])
    ov = {"pages": [{"slug": "home", "title": "Home"}, {"slug": "deals", "title": "Deals", "auth": False}],
          "features": ["Wishlist"], "entities": {"Wishlist": ["user_id:ref(User)!", "product_id:ref(Product)!"]}, "drop_entities": ["FileAsset"]}
    spec = B.build(BRIEFS["ecommerce"], st, ov)
    assert [p["slug"] for p in spec["pages"]] == ["home", "deals"] and spec["features"] == ["Wishlist"]
    names = {e["name"] for e in spec["data"]["entities"]}
    assert "Wishlist" in names and "FileAsset" not in names
    assert any(r["path"] == "/api/wishlists" for r in spec["api"]["routes"])
    assert spec["hash"] != B.build(BRIEFS["ecommerce"], st)["hash"]
    for bad in ({"pages": []}, {"pages": [{"slug": "Bad Slug", "title": "x"}]}, {"features": "x"}, {"nope": 1},
                {"entities": {"lower": ["a:string"]}}, {"entities": {"Thing": ["bad token"]}}, {"drop_entities": ["x"]}):
        with pytest.raises(ValueError):
            B.validate_overrides(bad)
    with pytest.raises(ValueError, match="unknown entity"):                           # dangling relation is refused
        B.build(BRIEFS["ecommerce"], st, {"entities": {"Thing": ["owner:ref(Ghost)!"]}})
    with pytest.raises(ValueError, match="unknown entity"):                           # dropping what others reference is refused
        B.build(BRIEFS["ecommerce"], st, {"drop_entities": ["Product"]})


def test_deterministic_and_json_safe():
    st = stack_for(BRIEFS["social"])
    a, b = B.build(BRIEFS["social"], st), B.build(BRIEFS["social"], st)
    assert a == b and json.loads(json.dumps(a)) == a
    assert len(B.digest(a)) <= 320


def test_plural_and_fields():
    assert [B.plural(n) for n in ("Category", "Product", "OrderItem", "Address", "Batch")] == ["categories", "products", "order-items", "addresses", "batches"]
    f = B.parse_field("status:enum(a|b)!")
    assert f["values"] == ["a", "b"] and f["required"]
    assert B.parse_field("owner:ref(User)")["ref"] == "User" and B.parse_field("email:email!@")["unique"]
    with pytest.raises(ValueError):
        B.parse_field("Bad:string")


def test_ecommerce_reference_pages_and_personal_data_are_scoped():
    brief = "online shopping store with login, catalog, wishlist, address book, checkout and admin order management"
    st = stack_for(brief)
    spec = B.build(brief, st)
    pages = {p["slug"]: p for p in spec["pages"]}
    assert {"catalog", "category", "product", "cart", "wishlist", "checkout", "addresses", "orders", "admin-products", "admin-orders"} <= set(pages)
    entities = {e["name"]: e for e in spec["data"]["entities"]}
    assert {"CartItem", "WishlistItem", "Address"} <= set(entities)
    for name in ("CartItem", "WishlistItem", "Address"):
        e = entities[name]
        assert e["read"] == "owner" and e["write"] == "owner"
        assert any(f.get("ref") == "User" for f in e["fields"])
    routes = {(r["method"], r["path"]): r for r in spec["api"]["routes"]}
    assert routes[("PUT", "/api/orders/{id}")]["access"] == "admin"


def test_no_auth_ecommerce_does_not_publish_personal_cart_wishlist_or_addresses():
    st = {"frontend": "react", "frontend_lang": "ts", "backend": "express", "database": "mysql", "auth": "none", "cache": "none", "storage": "none", "ai": "none", "testing": "none", "deploy": "local"}
    spec = B.build("public online shop with catalog but no login", st)
    names = {e["name"] for e in spec["data"]["entities"]}
    assert not ({"CartItem", "WishlistItem", "Address"} & names)
