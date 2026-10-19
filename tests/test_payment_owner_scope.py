from backend.gen import model as backend_model
from backend.spec import compose as B
from backend.stack import resolve


def stack_for(brief):
    resolved = resolve("automatic", {}, brief)
    assert resolved["ok"], resolved.get("errors")
    return resolved["stack"]


def test_payment_owner_scope_has_user_relation_when_auth_is_enabled():
    brief = "online store with login, razorpay payments and image uploads"
    st = stack_for(brief)
    spec = B.build(brief, st)
    payment_spec = next(e for e in spec["data"]["entities"] if e["name"] == "Payment")
    assert any(f["name"] == "user_id" and f.get("ref") == "User" for f in payment_spec["fields"])
    model = backend_model.build(spec, st)
    payment = next(e for e in model["entities"] if e["name"] == "Payment")
    assert payment["ownerField"] == "user_id"
    assert not any("Payment is owner-scoped but has no reference to User" in warning for warning in model["warnings"])


def test_payment_owner_relation_is_removed_for_public_no_auth_app():
    brief = "online store with razorpay payments and no login"
    st = resolve("automatic", {}, brief)["stack"]
    spec = B.build(brief, st)
    payment = next(e for e in spec["data"]["entities"] if e["name"] == "Payment")
    assert not any(f.get("ref") == "User" for f in payment["fields"])
