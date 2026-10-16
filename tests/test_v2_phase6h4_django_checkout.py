"""Phase 6H.4: checkout + Stripe/Razorpay/PayPal payments for Django (SQL databases).
Django is not installed here, so the generated logic runs against a small in-memory fake of the Django ORM; every file is compiled."""
import json
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

from backend.gen import django_gen, model
from backend.spec import compose
from gen_helpers import stack_for

STORE = "online store with products cart and orders, stripe payments, image uploads, live updates, redis cache"


def _gen(brief=STORE, db="sqlite"):
    st = stack_for(db, brief, backend="django")
    spec = compose.build(brief, st)
    m = model.build(spec, st)
    return m, django_gen.generate(spec, st, m)


def test_django_gets_checkout_and_every_provider():
    for prov in ("stripe", "razorpay", "paypal"):
        for db in ("sqlite", "postgresql", "mysql", "mssql"):
            m, files = _gen(STORE.replace("stripe", prov), db)
            assert m["checkout"] and m["integrations"]["payments"] and m["paymentProvider"] == prov, (prov, db)
            assert {"POST /api/checkout", "POST /api/payments/intent", "POST /api/payments/webhook"} <= set(m["manifest"])
            assert not {"checkout", "payments"} & set(m["not_generated"])
            for f in ("checkout_core.py", "pay_shared.py", "payments_core.py", "checkout_views.py", "payments_views.py"):
                assert f"backend/app/{f}" in files, (prov, f)
            assert "sqlalchemy" not in files["backend/app/checkout_core.py"] + files["backend/app/pay_shared.py"]
            assert not {"backend/app/payments_razorpay.py", "backend/app/payments_paypal.py"} & set(files)
            assert prov in files["backend/app/payments_core.py"].lower()
            assert "checkout_views" in files["backend/app/urls.py"] and "/api/checkout" in json.loads(files["backend/openapi.json"])["paths"]
            for rel, txt in files.items():
                if rel.endswith(".py"):
                    compile(txt, rel, "exec")


def test_plain_django_apps_ship_no_checkout_or_sqlalchemy_files():
    pay = {f"backend/app/{x}" for x in ("payments_core.py", "pay_shared.py", "payments_razorpay.py", "payments_paypal.py", "payments_views.py")}
    m, files = _gen("college management system with student login and courses")
    assert not m["checkout"] and not (pay | {"backend/app/checkout_core.py", "backend/app/checkout_views.py"}) & set(files)
    m, files = _gen(STORE.replace("stripe payments, ", ""))             # checkout without a payment provider
    assert m["checkout"] and "backend/app/checkout_core.py" in files and not pay & set(files)


class QS:
    def __init__(self, t, rows):
        self.t, self.rows = t, rows

    def select_for_update(self):
        return self

    def filter(self, **kw):
        def ok(r):
            for k, v in kw.items():
                f, _, op = k.partition("__")
                a = r["id"] if f == "pk" else r[f]
                if (op == "in" and a not in v) or (op == "gte" and not a >= v) or (not op and a != v):
                    return False
            return True
        return QS(self.t, [r for r in self.rows if ok(r)])

    def values(self):
        return QS(self.t, [dict(r) for r in self.rows])

    def first(self):
        return self.rows[0] if self.rows else None

    def __iter__(self):
        return iter(self.rows)

    def update(self, **kw):
        for r in self.rows:
            for k, v in kw.items():
                r[k] = v(r) if callable(v) else v
        return len(self.rows)


class Model:
    def __init__(self, t, store, name):
        self.objects, self.t, self.store = self, t, store

    def select_for_update(self): return QS(self.t, self.store[self.t])
    def filter(self, **kw): return QS(self.t, self.store[self.t]).filter(**kw)

    def create(self, **kw):
        rows = self.store[self.t]
        row = {"id": len(rows) + 1, **kw}
        rows.append(row)
        return types.SimpleNamespace(pk=row["id"])


class Expr:
    def __init__(self, f): self.f = f
    def __sub__(self, n): return lambda r: r[self.f] - n


def _load(files):
    d = tempfile.mkdtemp()
    for rel, txt in files.items():
        if rel.startswith("backend/app/") and "/migrations" not in rel:
            p = Path(d) / rel.removeprefix("backend/")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt, encoding="utf-8")
    ns = {}
    exec("KEYS = " + files["backend/app/models.py"].split("KEYS = ", 1)[1], ns)
    return d, ns["KEYS"]


def _mapped_for(store):
    from contextlib import contextmanager

    @contextmanager
    def mapped():                                    # transaction.atomic stand-in: roll back on any error
        snap = {t: [dict(r) for r in rows] for t, rows in store.items()}
        try:
            yield
        except BaseException:
            for t in store:
                store[t][:] = snap[t]
            raise
    return mapped


def test_checkout_and_payment_logic_on_fake_orm():
    m, files = _gen()
    d, keys = _load(files)
    sys.path.insert(0, d)
    for k in [k for k in sys.modules if k == "app" or k.startswith("app.")]:
        del sys.modules[k]
    store = {n: [] for n in keys}
    mapped = _mapped_for(store)
    models = types.ModuleType("app.models")
    models.KEYS = keys
    for n in keys:
        setattr(models, n, Model(n, store, n))
    dj = mock.MagicMock()
    dj.db.models.F = Expr
    stubs = {"django": dj, "django.db": dj.db, "django.db.models": dj.db.models, "django.views.decorators.csrf": dj, "dotenv": types.SimpleNamespace(load_dotenv=lambda *a, **k: None)}
    with mock.patch.dict(sys.modules, stubs):
        import importlib
        pkg = importlib.import_module("app")
        sys.modules["app.models"] = models
        schema = importlib.import_module("app.schema")
        orm = types.ModuleType("app.db.django_orm")
        orm.E, orm._mapped = schema.SCHEMA["entities"], mapped
        orm._model = lambda n: getattr(models, n)
        orm._in = lambda e, data: {keys[e["name"]].get(k, k): v for k, v in data.items()}
        dbpkg = types.ModuleType("app.db")
        dbpkg.__path__ = []
        sys.modules["app.db"], sys.modules["app.db.django_orm"] = dbpkg, orm
        co = importlib.import_module("app.checkout_core")
        ps = importlib.import_module("app.pay_shared")
        err = importlib.import_module("app.errors")
        kp, ko = keys["Product"], keys["Order"]
        store["Product"] += [{"id": 1, kp["name"]: "a", kp["price"]: 19.99, kp["stock"]: 5, **({kp["active"]: True} if "active" in kp else {})},
                             {"id": 2, kp["name"]: "b", kp["price"]: 5.0, kp["stock"]: 1, **({kp["active"]: True} if "active" in kp else {})}]
        db = types.SimpleNamespace(parse_id=lambda v: v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None)

        def code(fn, *a):
            try:
                fn(*a)
            except err.ApiError as e:
                return e.status, e.code
            raise AssertionError("expected ApiError")

        o = co.create_order(db, 7, [{"productId": 1, "quantity": 2}, {"productId": 2, "quantity": 1}])
        assert o["total"] == 44.98 and o["status"] == "pending" and store["Product"][0][kp["stock"]] == 3 and store["Product"][1][kp["stock"]] == 0
        assert len(store["Order"]) == 1 and len(store["OrderItem"]) == 2
        # failures leave stock/orders untouched
        assert code(co.create_order, db, 7, [{"productId": 2, "quantity": 1}]) == (409, "insufficient_stock")
        assert code(co.create_order, db, 7, [{"productId": 1, "quantity": 1}, {"productId": 99, "quantity": 1}]) == (400, "invalid_product")
        assert code(co.create_order, db, 7, [{"productId": 1, "quantity": 0}]) == (400, "validation_failed")
        assert code(co.create_order, db, None, [{"productId": 1, "quantity": 1}]) == (401, "unauthorized")
        assert store["Product"][0][kp["stock"]] == 3 and len(store["Order"]) == 1 and len(store["OrderItem"]) == 2
        # payments: own pending order only, exact minor-unit amount, idempotent
        assert ps.payable_order(db, 7, 1) == (1, 4498, 44.98)
        assert code(ps.payable_order, db, 8, 1) == (404, "not_found")
        assert ps.mark_paid(db, 1, 4497) is False and store["Order"][0][ko["status"]] == "pending"
        assert ps.mark_paid(db, 1, 4498) is True and store["Order"][0][ko["status"]] == "paid"
        assert ps.mark_paid(db, 1, 4498) is False
        assert code(ps.payable_order, db, 7, 1) == (409, "order_not_payable")
        assert ps.get_order(db, 1).status == "paid" and ps.get_order(db, 5) is None
