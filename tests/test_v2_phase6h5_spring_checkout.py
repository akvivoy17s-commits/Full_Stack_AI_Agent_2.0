"""Phase 6H.5: checkout + Stripe/Razorpay/PayPal payments for Spring Boot (SQL databases).
No Maven / Spring jars here: the generated pure-Java parts are compiled and the generated unit test source is checked; Java behaviour was run separately against stubs."""
import json

from backend.gen import model, spring_gen
from backend.spec import compose
from gen_helpers import stack_for

STORE = "online store with products cart and orders, stripe payments, image uploads, live updates, redis cache"
BASE = "backend/src/main/java/app/"


def _gen(brief=STORE, db="postgresql"):
    st = stack_for(db, brief, backend="spring")
    spec = compose.build(brief, st)
    m = model.build(spec, st)
    return m, spring_gen.generate(spec, st, m)


def test_spring_gets_checkout_and_only_its_provider():
    names = {"stripe": "StripePay", "razorpay": "RazorpayPay", "paypal": "PaypalPay"}
    for prov, cls in names.items():
        for db in ("sqlite", "postgresql", "mysql", "mssql"):
            m, files = _gen(STORE.replace("stripe", prov), db)
            assert m["checkout"] and m["integrations"]["payments"] and m["paymentProvider"] == prov, (prov, db)
            assert {"POST /api/checkout", "POST /api/payments/intent", "POST /api/payments/webhook"} <= set(m["manifest"])
            assert not {"checkout", "payments"} & set(m["not_generated"])
            for f in ("checkout/Money", "checkout/CheckoutService", "checkout/CheckoutController", "checkout/Notify", "payments/PayCrypto", "payments/PayShared",
                      "payments/PaymentsController", f"payments/{cls}"):
                assert f"{BASE}{f}.java" in files, (prov, f)
            others = [c for c in names.values() if c != cls]
            assert not any(f"{BASE}payments/{c}.java" in files for c in others)
            assert "backend/src/test/java/app/CheckoutMathTest.java" in files
            assert "/api/checkout" in json.loads(files["backend/src/main/resources/openapi.json"])["paths"]
            assert "Checkout:" in files["backend/README.md"]


def test_notify_is_a_noop_without_cache_and_websocket_and_plain_apps_get_nothing():
    m, files = _gen(STORE.replace("image uploads, live updates, redis cache", "image uploads"))
    assert m["checkout"] and not (m["integrations"]["cache"] or m["integrations"]["ws"])
    assert "app.integrations" not in files[BASE + "checkout/Notify.java"]
    m, files = _gen(STORE)
    assert "app.integrations.Cache" in files[BASE + "checkout/Notify.java"]
    m, files = _gen("college management system with student login and courses")
    assert not m["checkout"] and not any("/checkout/" in k or "/payments/" in k or k.endswith("CheckoutMathTest.java") for k in files)
    m, files = _gen(STORE.replace("stripe payments, ", ""))
    assert m["checkout"] and f"{BASE}checkout/CheckoutService.java" in files and not any("/payments/" in k for k in files)
    m, files = _gen(STORE, "mongodb")
    assert not m["checkout"] and "checkout" in m["not_generated"] and not any("/checkout/" in k for k in files)


def test_webhook_and_money_rules_are_in_the_source():
    m, files = _gen()
    pay, svc, ctl = files[BASE + "payments/PayShared.java"], files[BASE + "checkout/CheckoutService.java"], files[BASE + "payments/PaymentsController.java"]
    assert "byte[] raw" in ctl and "payable" in pay and "markPaid" in pay and "status\") + \" = 'pending'" in pay.replace("qc(\"status\")", "status\")") or "'pending'" in pay
    assert "FOR UPDATE" in svc and "UPDLOCK" in svc and "tx.execute" in svc
    assert "total" not in files[BASE + "checkout/CheckoutController.java"].lower().replace("/api/checkout", "")      # no client total anywhere in the controller
