"""Phase 6H.1: checkout + Stripe payments for FastAPI and Flask (SQL databases). No SQLAlchemy/web framework needed: logic runs with stubs, files are compiled."""
import hashlib
import hmac
import json
import sys
import tempfile
import time
import types
from pathlib import Path
from unittest import mock

from backend.gen import fastapi_gen, flask_gen, model
from backend.spec import compose
from gen_helpers import stack_for

STORE = "online store with products cart and orders, stripe payments, image uploads, live updates, redis cache"
GENS = {"fastapi": fastapi_gen, "flask": flask_gen}


def _gen(be, brief=STORE, db="sqlite", **extra):
    st = stack_for(db, brief, backend=be, **extra)
    spec = compose.build(brief, st)
    m = model.build(spec, st)
    return m, GENS[be].generate(spec, st, m)


def test_fastapi_and_flask_get_checkout_and_stripe():
    for be in ("fastapi", "flask"):
        m, files = _gen(be)
        assert m["checkout"] and m["integrations"]["payments"] and m["paymentProvider"] == "stripe", be
        assert {"POST /api/checkout", "POST /api/payments/intent", "POST /api/payments/webhook"} <= set(m["manifest"])
        assert not {"checkout", "payments"} & set(m["not_generated"]), m["not_generated"]
        for f in ("checkout_core.py", "payments_core.py", "routes/checkout.py", "routes/payments.py"):
            assert f"backend/app/{f}" in files, (be, f)
        assert "'checkout': True" in files["backend/app/schema.py"]
        assert "STRIPE_CURRENCY=" in files["backend/.env.example"] and "STRIPE_SECRET_KEY=" in files["backend/.env.example"]
        paths = json.loads(files["backend/openapi.json"])["paths"]
        assert "/api/checkout" in paths and "/api/payments/intent" in paths
        assert "Checkout:" in files["backend/README.md"] and "Payments (Stripe)" in files["backend/README.md"]
        for rel, txt in files.items():
            if rel.endswith(".py"):
                compile(txt, rel, "exec")


def test_other_providers_and_plain_apps_unchanged():
    m, files = _gen("fastapi", STORE.replace("stripe", "razorpay"))
    assert m["checkout"] and m["integrations"]["payments"] and m["paymentProvider"] == "razorpay"      # 6H.2: Razorpay/PayPal for Python
    assert "RAZORPAY_CURRENCY=" in files["backend/.env.example"] and "razorpay" in files["backend/app/payments_core.py"].lower()
    m, files = _gen("flask", "college management system with student login and courses")
    assert not m["checkout"] and "backend/app/checkout_core.py" not in files and "backend/app/payments_core.py" not in files


def _load(files):
    """Import the generated package with SQLAlchemy stubbed; enough for the pure logic (signature, item parsing, cents)."""
    d = tempfile.mkdtemp()
    for rel, txt in files.items():
        if rel.startswith("backend/app/"):
            p = Path(d) / rel.removeprefix("backend/")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt, encoding="utf-8")
    sa = mock.MagicMock()
    sa.exc.IntegrityError = type("IntegrityError", (Exception,), {})
    stubs = {"sqlalchemy": sa, "sqlalchemy.dialects": sa.dialects, "sqlalchemy.pool": sa.pool, "sqlalchemy.exc": sa.exc, "dotenv": types.SimpleNamespace(load_dotenv=lambda *a, **k: None)}
    sys.path.insert(0, d)
    for k in [k for k in sys.modules if k == "app" or k.startswith("app.")]:
        del sys.modules[k]
    with mock.patch.dict(sys.modules, stubs):
        import importlib
        return importlib.import_module("app.payments_core"), importlib.import_module("app.checkout_core"), importlib.import_module("app.errors")


def test_stripe_signature_items_and_cents():
    m, files = _gen("fastapi")
    pay, co, err = _load(files)
    raw, secret, now = b'{"a":1}', "whsec_x", 1_700_000_000
    sig = lambda ts, body=raw, s=secret: f"t={ts},v1=" + hmac.new(s.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    assert pay.verify_signature(raw, sig(now), secret, now=now)
    assert not pay.verify_signature(raw, sig(now), secret, now=now + 301)               # stale
    assert not pay.verify_signature(raw + b" ", sig(now), secret, now=now)             # tampered body
    assert not pay.verify_signature(raw, sig(now, s="other"), secret, now=now)         # wrong secret
    assert not pay.verify_signature(raw, "", secret, now=now) and not pay.verify_signature(raw, "t=x,v1=00", secret, now=now)
    assert co.to_cents(19.99) == 1999 and co.to_cents(0.1 + 0.2) == 30 and co.to_cents(2.675) == 268
    db = types.SimpleNamespace(parse_id=lambda v: v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None)
    assert co.parse_items(db, [{"productId": 1, "quantity": 2}, {"product_id": 1, "quantity": 3}, {"productId": 2, "quantity": 1}]) == {1: 5, 2: 1}
    for bad in (None, [], "x", [{}], [{"productId": 1, "quantity": 0}], [{"productId": 1, "quantity": 1.5}], [{"productId": 1, "quantity": True}],
                [{"productId": 1, "quantity": 99}, {"productId": 1, "quantity": 1}], [{"productId": 0, "quantity": 1}], [1], [{"productId": 1, "quantity": 1}] * 51):
        try:
            co.parse_items(db, bad)
        except err.ApiError as e:
            assert e.status == 400 and e.code == "validation_failed", bad
        else:
            raise AssertionError(f"accepted {bad!r}")
