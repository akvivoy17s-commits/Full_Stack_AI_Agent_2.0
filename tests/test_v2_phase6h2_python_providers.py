"""Phase 6H.2: Razorpay and PayPal for FastAPI and Flask. SQLAlchemy is stubbed; provider logic runs against fakes."""
import hashlib
import hmac
import json
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

from backend.gen import fastapi_gen, flask_gen, model
from backend.spec import compose
from gen_helpers import stack_for

BRIEF = "online store with products cart and orders, {p} payments, image uploads"
GENS = {"fastapi": fastapi_gen, "flask": flask_gen}


def _gen(be, prov):
    brief = BRIEF.format(p=prov)
    st = stack_for("sqlite", brief, backend=be)
    spec = compose.build(brief, st)
    m = model.build(spec, st)
    return m, GENS[be].generate(spec, st, m)


def test_provider_files_env_and_docs():
    for be in ("fastapi", "flask"):
        for prov, env, doc in (("razorpay", "RAZORPAY_CURRENCY=", "Payments (Razorpay)"), ("paypal", "PAYPAL_CURRENCY=", "Payments (PayPal)"), ("stripe", "STRIPE_CURRENCY=", "Payments (Stripe)")):
            m, files = _gen(be, prov)
            assert m["paymentProvider"] == prov and m["integrations"]["payments"] and "payments" not in m["not_generated"], (be, prov)
            assert f"backend/app/pay_shared.py" in files and f"backend/app/payments_{prov}.py" not in files    # template is copied over payments_core.py
            core = files["backend/app/payments_core.py"]
            assert (prov == "stripe") == ("api.stripe.com" in core) and (prov == "razorpay") == ("api.razorpay.com" in core) and (prov == "paypal") == ("paypal.com" in core), (be, prov)
            assert env in files["backend/.env.example"] and doc in files["backend/README.md"]
            for rel, txt in files.items():
                if rel.endswith(".py"):
                    compile(txt, rel, "exec")


def _load(files, mods):
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
        return [importlib.import_module(m) for m in mods]


DB = types.SimpleNamespace(parse_id=lambda v: int(v) if isinstance(v, (int, str)) and not isinstance(v, bool) and str(v).isdigit() and int(v) > 0 else None)


def test_razorpay_signature_and_webhook():
    m, files = _gen("fastapi", "razorpay")
    rz, shared, err = _load(files, ["app.payments_core", "app.pay_shared", "app.errors"])
    raw, secret = b'{"event":"payment.captured"}', "whsec"
    good = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    assert rz.verify_signature(raw, good, secret) and rz.verify_signature(raw, good.upper(), secret)
    assert not rz.verify_signature(raw + b"x", good, secret) and not rz.verify_signature(raw, "zz", secret) and not rz.verify_signature(raw, good, "")
    rz.cfg.razorpay_webhook_secret, rz.cfg.razorpay_currency = secret, "inr"
    body = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {"amount": 4999, "currency": "INR", "notes": {"order_id": "7"}}}}}).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    with mock.patch.object(rz, "mark_paid") as mp:
        rz.handle_webhook(DB, body, {"x-razorpay-signature": sig})
        mp.assert_called_once_with(DB, 7, 4999)
        mp.reset_mock()
        try:
            rz.handle_webhook(DB, body, {"x-razorpay-signature": "0" * 64})
        except err.ApiError as e:
            assert e.status == 400 and e.code == "invalid_signature"
        else:
            raise AssertionError("bad signature accepted")
        wrong_cur = body.replace(b"INR", b"USD")
        rz.handle_webhook(DB, wrong_cur, {"x-razorpay-signature": hmac.new(secret.encode(), wrong_cur, hashlib.sha256).hexdigest()})
        assert not mp.called                                                              # other currency never marks paid
    rz.cfg.razorpay_webhook_secret = "your-webhook-secret"
    try:
        rz.handle_webhook(DB, body, {})
    except err.ApiError as e:
        assert e.status == 503


def test_paypal_webhook_capture_rules():
    m, files = _gen("flask", "paypal")
    pp, err = _load(files, ["app.payments_core", "app.errors"])
    pp.cfg.paypal_client_id = pp.cfg.paypal_client_secret = "id"
    pp.cfg.paypal_webhook_id, pp.cfg.paypal_currency = "WH", "usd"
    hdr = {"paypal-transmission-id": "1", "paypal-transmission-sig": "s", "paypal-cert-url": "https://x", "paypal-auth-algo": "a", "paypal-transmission-time": "t"}
    approved = lambda amt, cur="USD": json.dumps({"event_type": "CHECKOUT.ORDER.APPROVED", "resource": {"id": "PP1", "purchase_units": [{"custom_id": "5", "amount": {"currency_code": cur, "value": amt}}]}}).encode()
    order = types.SimpleNamespace(status="pending", total=12.5)
    calls = []
    with mock.patch.object(pp, "_verified", return_value=True), mock.patch.object(pp, "get_order", return_value=order), mock.patch.object(pp, "_api", side_effect=lambda *a, **k: calls.append(a) or (True, {})):
        pp.handle_webhook(DB, approved("12.50"), hdr)
        assert len(calls) == 1 and calls[0][0] == "/v2/checkout/orders/PP1/capture" and calls[0][2] == "capture-PP1"
        pp.handle_webhook(DB, approved("1.00"), hdr)                  # amount differs from the stored order
        pp.handle_webhook(DB, approved("12.50", "EUR"), hdr)          # other currency
        order.status = "paid"
        pp.handle_webhook(DB, approved("12.50"), hdr)                 # not pending any more
        assert len(calls) == 1
    with mock.patch.object(pp, "_verified", return_value=False):
        try:
            pp.handle_webhook(DB, approved("12.50"), hdr)
        except err.ApiError as e:
            assert e.status == 400 and e.code == "invalid_signature"
        else:
            raise AssertionError("unverified event accepted")
    done = json.dumps({"event_type": "PAYMENT.CAPTURE.COMPLETED", "resource": {"status": "COMPLETED", "custom_id": "5", "amount": {"currency_code": "USD", "value": "12.50"}}}).encode()
    with mock.patch.object(pp, "_verified", return_value=True), mock.patch.object(pp, "mark_paid") as mp:
        pp.handle_webhook(DB, done, hdr)
        mp.assert_called_once_with(DB, 5, 1250)
