"""Phase 6A: Express integrations (Redis/in-memory cache, uploads, Stripe payments, WebSocket). Pure Python; node --check runs when node is installed."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from backend.gen import express, model
from backend.spec import compose
from gen_helpers import stack_for

STORE = "online store with products cart and orders, stripe payments, image uploads, live updates, redis cache"
PLAIN = "college management system with student login and courses"


def _gen(brief, backend="express", db="sqlite", **extra):
    st = stack_for(db, brief, backend=backend, **extra)
    spec = compose.build(brief, st)
    m = model.build(spec, st)
    return spec, st, m


def test_express_store_generates_every_integration():
    spec, st, m = _gen(STORE, cache="redis", storage="local")
    assert m["integrations"] == {"cache": True, "uploads": True, "payments": True, "ws": True}
    assert not {"payments", "file uploads", "WebSocket live updates"} & set(m["not_generated"])
    files = express.generate(spec, st, m)
    for f in ("lib/cache.js", "lib/events.js", "middleware/live.js", "routes/uploads.js", "routes/payments.js", "ws.js"):
        assert f"backend/src/{f}" in files
    deps = json.loads(files["backend/package.json"])["dependencies"]
    assert "redis" in deps and "ws" in deps
    assert {"POST /api/uploads", "POST /api/payments/intent", "POST /api/payments/webhook"} <= set(m["manifest"])
    paths = json.loads(files["backend/openapi.json"])["paths"]
    assert "/api/uploads" in paths and "/api/payments/intent" in paths
    env = files["backend/.env.example"]
    assert "UPLOAD_MAX_BYTES=" in env and "WS_MAX_CLIENTS=" in env and "CACHE_TTL_SECONDS=" in env
    assert "## Integrations" in files["backend/README.md"]


def test_plain_app_gets_no_integration_files():
    spec, st, m = _gen(PLAIN)
    assert not any(m["integrations"].values())
    files = express.generate(spec, st, m)
    assert not any(k.endswith(("cache.js", "ws.js", "uploads.js", "payments.js", "live.js")) for k in files)
    deps = json.loads(files["backend/package.json"])["dependencies"]
    assert "redis" not in deps and "ws" not in deps


def test_other_backends_still_report_these_as_not_generated():
    _, _, m = _gen(STORE, backend="spring", cache="redis", storage="local")      # since 6D Spring has cache, uploads and WebSocket; payments need Express
    assert m["integrations"] == {"cache": True, "uploads": True, "payments": True, "ws": True}      # payments: 6H.5
    assert "payments" not in m["not_generated"]


def test_stripe_webhook_checks_raw_body_signature_and_amount():
    t = (express.TPL / "src" / "routes" / "payments.js").read_text()
    assert "timingSafeEqual" in t and "express.raw" in t and "amount_received" in t
    assert "req.body.amount" not in t and "req.body.total" not in t      # amount only from the stored order
    app = (express.TPL / "src" / "app.js").read_text()
    assert app.index("payments').webhook") < app.index("express.json(")     # raw body must come first


def test_uploads_detect_type_from_bytes_and_randomise_names():
    t = (express.TPL / "src" / "routes" / "uploads.js").read_text()
    assert "randomBytes" in t and "nosniff" in t and "sandbox" in t and "originalname" not in t and "req.headers['content-type']" not in t


def test_ws_checks_origin_and_requires_auth_message():
    t = (express.TPL / "src" / "ws.js").read_text()
    assert "verifyClient" in t and "corsOrigins" in t and "4401" in t and "token" not in t.split("verifyClient")[1].split("onChange")[0].replace("origin", "")


def test_generated_js_parses():
    node = shutil.which("node")
    if not node:
        return
    spec, st, m = _gen(STORE, cache="redis", storage="local")
    with tempfile.TemporaryDirectory() as d:
        for k, v in express.generate(spec, st, m).items():
            if k.endswith(".js"):
                p = Path(d) / k
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(v, encoding="utf-8")
                r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True)
                assert r.returncode == 0, (k, r.stderr)


# ------------------------------------------------------------------ Phase 6B: Python web layers
STORE_PY = STORE


def test_python_backends_flags_and_files():
    for be, ws in (("fastapi", True), ("flask", False)):
        spec, st, m = _gen(STORE_PY, backend=be, cache="redis", storage="local")
        assert m["integrations"] == {"cache": True, "uploads": True, "payments": True, "ws": ws}, be       # 6H.1: Stripe checkout for FastAPI/Flask
        assert "payments" not in m["not_generated"] and ("WebSocket live updates" in m["not_generated"]) == (not ws)
        from backend.gen import fastapi_gen, flask_gen
        files = (fastapi_gen if be == "fastapi" else flask_gen).generate(spec, st, m)
        for f in ("cache.py", "live_core.py", "uploads_core.py", "live.py", "routes/uploads.py"):
            assert f"backend/app/{f}" in files, (be, f)
        assert "redis>=5,<6" in files["backend/requirements.txt"] and "## Integrations" in files["backend/README.md"]
        assert "/api/uploads" in json.loads(files["backend/openapi.json"])["paths"]
        spec, st, m = _gen(PLAIN, backend=be)
        files = (fastapi_gen if be == "fastapi" else flask_gen).generate(spec, st, m)
        assert not any(k.endswith(("app/cache.py", "app/live.py", "app/uploads_core.py")) for k in files)


def test_django_and_nest_get_cache_and_uploads_nest_also_ws():
    from backend.gen import django_gen, nest
    for be, gen, ws in (("django", django_gen, False), ("nestjs", nest, True)):
        spec, st, m = _gen(STORE_PY, backend=be, cache="redis", storage="local")
        assert m["integrations"] == {"cache": True, "uploads": True, "payments": be in ("nestjs", "django"), "ws": ws}, be      # 6H.3 Nest, 6H.4 Django: payments
        files = gen.generate(spec, st, m)
        assert "## Integrations" in files["backend/README.md"] and "UPLOAD_MAX_BYTES=" in files["backend/.env.example"]
        if be == "django":
            for f in ("cache.py", "live.py", "live_core.py", "uploads_core.py", "uploads_views.py"):
                assert f"backend/app/{f}" in files, f
            assert "redis>=5,<6" in files["backend/requirements.txt"]
        else:
            for f in ("cache", "events", "live", "uploads", "ws"):
                assert f"backend/src/integrations/{f}.ts" in files, f
            deps = json.loads(files["backend/package.json"])["dependencies"]
            assert {"redis", "ws", "jsonwebtoken"} <= set(deps)
        spec, st, m = _gen(PLAIN, backend=be)
        files = gen.generate(spec, st, m)
        assert not any(("integrations/" in k and not k.endswith("pay-mount.ts")) or k.endswith(("app/cache.py", "app/live.py", "app/uploads_core.py")) for k in files)


def test_websocket_without_cache_still_ships_the_cache_module_it_imports():
    B = "online store with products cart and orders, live updates"
    for be, gen_name, path in (("express", "express", "backend/src/lib/cache.js"), ("fastapi", "fastapi_gen", "backend/app/cache.py"), ("nestjs", "nest", "backend/src/integrations/cache.ts")):
        import importlib
        gen = importlib.import_module("backend.gen." + gen_name)
        spec, st, m = _gen(B, backend=be)
        if not m["integrations"]["ws"]:
            continue
        assert not m["integrations"]["cache"] and path in gen.generate(spec, st, m), be


def test_flask_cache_and_uploads_over_http():
    import pytest
    pytest.importorskip("flask")
    from gen_helpers import FakeDb, load_project, unload
    path, S = load_project(brief=STORE_PY, backend="flask", cache="redis", storage="local")
    try:
        import os
        os.environ["UPLOAD_DIR"] = str(path / "up")
        from app.main import create_app
        from app.security import hash_password
        db = FakeDb(S)
        c = create_app(db).test_client()
        db.create("User", {"email": "a@example.com", "name": "A", "password_hash": hash_password("Passw0rd!long"), "role": "admin"})
        tok = c.post("/api/auth/login", json={"email": "a@example.com", "password": "Passw0rd!long"}).get_json()["accessToken"]
        H = {"Authorization": f"Bearer {tok}"}
        assert c.get("/api/health").get_json()["cache"] == "memory"
        r1, r2 = c.get("/api/products", headers=H), c.get("/api/products", headers=H)
        assert (r1.headers["X-Cache"], r2.headers["X-Cache"]) == ("MISS", "HIT") and r1.get_json() == r2.get_json()
        assert c.get("/api/products", headers={"Authorization": "Bearer other"}).headers["X-Cache"] == "MISS"   # entries are per caller (Authorization header)
        P = {f["name"]: {"string": "x", "text": "x", "int": 5, "float": 9.5, "bool": True, "url": "https://example.com/a", "email": "e@example.com"}.get(f["type"], "x")
             for f in S["entities"]["Product"]["fields"] if f["required"] and f["type"] != "ref"}
        assert c.post("/api/products", json=P, headers=H).status_code == 201
        assert c.get("/api/products", headers=H).headers["X-Cache"] == "MISS"          # the write invalidated every cached read
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
        r = c.post("/api/uploads", data=png, headers={**H, "Content-Type": "text/html"})
        assert r.status_code == 201 and r.get_json()["type"] == "image/png" and r.get_json()["name"].endswith(".png")
        g = c.get(r.get_json()["url"], headers=H)
        assert g.status_code == 200 and g.data == png and g.headers["X-Content-Type-Options"] == "nosniff"
        assert c.post("/api/uploads", data=b"<script>alert(1)</script>" * 3, headers=H).status_code == 415
        assert c.post("/api/uploads", data=b"", headers=H).status_code == 400
        assert c.get("/api/uploads/../../etc/passwd", headers=H).status_code == 404
        assert c.get("/api/uploads/" + "a" * 32 + ".png", headers=H).status_code == 404
        assert c.post("/api/uploads", data=png).status_code == 401
        assert c.post("/api/products", data=b"x" * 200000, headers={**H, "Content-Type": "application/json"}).status_code == 413   # normal routes keep the 100 kB cap
    finally:
        unload(path)


# ---- Phase 6D: Spring Boot ------------------------------------------------------------------------------------------------------------

def _spring(brief, db="sqlite", **extra):
    from backend.gen import spring_gen
    spec, st, m = _gen(brief, backend="spring", db=db, **extra)
    return m, spring_gen.generate(spec, st, m)


def test_spring_store_generates_cache_uploads_and_websocket():
    for db in ("sqlite", "postgresql", "mongodb"):
        m, files = _spring(STORE, db, cache="redis", storage="local")
        assert m["integrations"] == {"cache": True, "uploads": True, "payments": db != "mongodb", "ws": True}
        base = "backend/src/main/java/app/integrations/"
        for f in ("Cache", "Events", "LiveFilter", "UploadController", "UploadKinds", "WsConfig", "WsHandler", "WsTokens"):
            assert f"{base}{f}.java" in files, f
        assert "backend/src/test/java/app/CacheTest.java" in files and "backend/src/test/java/app/UploadKindsTest.java" in files
        pom = files["backend/pom.xml"]
        assert "<artifactId>jedis</artifactId>" in pom and "spring-boot-starter-websocket" in pom
        assert "app.cache=true" in files["backend/src/main/resources/application.properties"]
        assert "UPLOAD_EXEMPT" not in files["backend/src/main/java/app/web/ApiFilters.java"]      # /api/uploads has its own size cap
        assert '"/api/uploads".equals(req.getRequestURI())' in files["backend/src/main/java/app/web/ApiFilters.java"]
        assert "UPLOAD_MAX_BYTES=" in files["backend/.env.example"] and "## Integrations" in files["backend/README.md"]
        assert "/api/uploads" in files["backend/src/main/resources/openapi.json"]
        assert ("payments" in m["not_generated"]) == (db == "mongodb")                              # 6H.5: SQL databases get payments; MongoDB has no checkout


def test_spring_plain_app_gets_no_integration_files():
    m, files = _spring(PLAIN)
    assert not any("/integrations/" in k or k.endswith(("CacheTest.java", "UploadKindsTest.java")) for k in files)
    pom = files["backend/pom.xml"]
    assert "jedis" not in pom and "websocket" not in pom
    assert "app.cache=false" in files["backend/src/main/resources/application.properties"]
    assert "UPLOAD_EXEMPT" in files["backend/src/main/java/app/web/ApiFilters.java"] or "/*UPLOAD_EXEMPT*/" in files["backend/src/main/java/app/web/ApiFilters.java"]


def test_spring_websocket_only_ships_cache_it_uses_and_no_auth_stub():
    m, files = _spring("blog with live updates", "sqlite")
    I = m["integrations"]
    if I["ws"]:
        assert "backend/src/main/java/app/integrations/Cache.java" in files and "jedis" in files["backend/pom.xml"]
        if not m["auth"]:
            assert "app.core.Jwt" not in files["backend/src/main/java/app/integrations/WsTokens.java"]


# ---- Phase 6E: Razorpay + PayPal on Express ------------------------------------------------------------------------------------------

NAME = {"stripe": "Stripe", "razorpay": "Razorpay", "paypal": "PayPal"}


def _pay_gen(prov, backend="express", db="sqlite"):
    B = f"online store with products cart and orders, {prov} payments, image uploads, live updates, redis cache"
    return _gen(B, backend=backend, db=db, cache="redis", storage="local")


def test_express_payments_follow_the_spec_provider():
    for prov, host, other in (("stripe", "api.stripe.com", "razorpay"), ("razorpay", "api.razorpay.com", "paypal"), ("paypal", "api-m", "razorpay")):
        spec, st, m = _pay_gen(prov)
        assert m["paymentProvider"] == prov and m["integrations"]["payments"]
        files = express.generate(spec, st, m)
        pj = files["backend/src/routes/payments.js"]
        assert host in pj and other not in pj.lower().replace("paypal-request-id", "")
        assert ("backend/src/lib/pay.js" in files) == (prov != "stripe")
        assert not any(k.endswith(("payments_razorpay.js", "payments_paypal.js")) for k in files)
        assert model.PAY_CUR[prov][0] in files["backend/.env.example"] and NAME[prov] in files["backend/README.md"]
        assert NAME[prov] in files["backend/openapi.json"]
    assert "PAYPAL_WEBHOOK_ID=" in express.generate(*_pay_gen("paypal"))["backend/.env.example"]


def test_payments_for_spring_since_6h5():      # 6H.1/6H.2 FastAPI + Flask, 6H.3 NestJS, 6H.4 Django, 6H.5 Spring
    _, _, m = _pay_gen("razorpay", backend="spring")
    assert m["integrations"]["payments"] and m["paymentProvider"] == "razorpay" and "payments" not in m["not_generated"]


_NODE_HARNESS = r"""
const crypto = require('crypto'); const assert = require('assert');
process.env.RAZORPAY_KEY_ID = 'rzp_test_1'; process.env.RAZORPAY_KEY_SECRET = 'sec'; process.env.RAZORPAY_WEBHOOK_SECRET = 'whsec';
process.env.PAYPAL_CLIENT_ID = 'cid'; process.env.PAYPAL_CLIENT_SECRET = 'csec'; process.env.PAYPAL_WEBHOOK_ID = 'WH-1';
const schema = require('./src/schema');
const orders = [{ id: 1, user_id: 7, status: 'pending', total: 12.5 }, { id: 2, user_id: 7, status: 'pending', total: 20 }];
const db = { parseId: (v) => { const n = Number(v); return Number.isInteger(n) && n > 0 ? n : null; },
  knex: () => { let c = {}; const m = (r) => Object.keys(c).every((k) => r[k] === c[k]); const q = { where: (w) => { c = w; return q; }, first: async () => orders.find(m), update: async (p) => { orders.filter(m).forEach((r) => Object.assign(r, p)); } }; return q; } };
const call = async (handlers, req) => { const h = handlers[handlers.length - 1]; let err = null, out = null; await h(req, { json: (b) => { out = b; }, status() { return this; } }, (e) => { err = e; }); return { err, out }; };
(async () => {
  // ---- Razorpay
  const rz = require('./src/routes/payments');
  const sign = (b, s = 'whsec') => crypto.createHmac('sha256', s).update(b).digest('hex');
  const ev = (id, amount, cur = 'INR') => Buffer.from(JSON.stringify({ event: 'payment.captured', payload: { payment: { entity: { amount, currency: cur, notes: { order_id: String(id) } } } } }));
  let b = ev(1, 1250);
  assert(rz.verifySignature(b, sign(b), 'whsec') && !rz.verifySignature(b, sign(b, 'x'), 'whsec') && !rz.verifySignature(b, 'zz', 'whsec'));
  let r = await call(rz.webhook(db), { body: b, headers: { 'x-razorpay-signature': 'a'.repeat(64) } });
  assert(r.err && r.err.status === 400 && orders[0].status === 'pending');
  b = ev(2, 1999); r = await call(rz.webhook(db), { body: b, headers: { 'x-razorpay-signature': sign(b) } });
  assert(!r.err && orders[1].status === 'pending');                                   // wrong amount ignored
  b = ev(1, 1250, 'USD'); r = await call(rz.webhook(db), { body: b, headers: { 'x-razorpay-signature': sign(b) } });
  assert(orders[0].status === 'pending');                                             // wrong currency ignored
  b = ev(1, 1250); r = await call(rz.webhook(db), { body: b, headers: { 'x-razorpay-signature': sign(b) } });
  assert(!r.err && orders[0].status === 'paid');
  orders[0].status = 'cancelled'; r = await call(rz.webhook(db), { body: b, headers: { 'x-razorpay-signature': sign(b) } });
  assert(orders[0].status === 'cancelled');                                           // replay never resurrects an order
  orders[0].status = 'pending';
  let sent = null; global.fetch = async (u, o) => { sent = { u, o }; return { ok: true, json: async () => ({ id: 'order_X' }) }; };
  r = await call(rz.intent(db).stack.map((l) => l.handle), { user: { id: 7 }, body: { orderId: 1, amount: 1 } });
  assert(r.out && r.out.razorpayOrderId === 'order_X' && JSON.parse(sent.o.body).amount === 1250 && !('keySecret' in r.out));
  console.log('razorpay ok');
})().catch((e) => { console.error(e); process.exit(1); });
"""


def _run_node(prov, script, storage="local"):
    node = shutil.which("node")
    if not node:
        return
    spec, st, m = _gen(f"online store with products cart and orders, {prov} payments, image uploads, live updates, redis cache", cache="redis", storage=storage)
    with tempfile.TemporaryDirectory() as d:
        for k, v in express.generate(spec, st, m).items():
            if k.startswith("backend/src/") and k.endswith(".js"):
                p = Path(d) / k[len("backend/"):]
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(v, encoding="utf-8")
        nm = Path(d) / "node_modules"
        for name, body in (("dotenv", "exports.config=()=>{};"), ("jsonwebtoken", "exports.verify=()=>({sub:'7',role:'user'});exports.sign=()=>'t';"),
                           ("express", "const f=()=>{};f.raw=()=>(q,s,n)=>n&&n();f.json=f.raw;f.Router=()=>{const s=[];const r={stack:s,routes:{}};['post','get'].forEach(m=>{r[m]=(p,...h)=>{r.routes[m+' '+p]=h;h.forEach(x=>s.push({handle:x}));return r;};});return r;};module.exports=f;")):
            (nm / name).mkdir(parents=True, exist_ok=True)
            (nm / name / "index.js").write_text(body)
        (Path(d) / "t.js").write_text(script)
        r = subprocess.run([node, "t.js"], cwd=d, capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stderr + r.stdout


def test_razorpay_webhook_and_intent_behaviour_in_node():
    _run_node("razorpay", _NODE_HARNESS)


_PAYPAL_HARNESS = r"""
const assert = require('assert');
process.env.PAYPAL_CLIENT_ID = 'cid'; process.env.PAYPAL_CLIENT_SECRET = 'csec'; process.env.PAYPAL_WEBHOOK_ID = 'WH-1';
const orders = [{ id: 1, user_id: 7, status: 'pending', total: 12.5 }, { id: 2, user_id: 7, status: 'pending', total: 20 }];
const db = { parseId: (v) => { const n = Number(v); return Number.isInteger(n) && n > 0 ? n : null; },
  knex: () => { let c = {}; const m = (r) => Object.keys(c).every((k) => r[k] === c[k]); const q = { where: (w) => { c = w; return q; }, first: async () => orders.find(m), update: async (p) => { orders.filter(m).forEach((r) => Object.assign(r, p)); } }; return q; } };
const call = async (handlers, req) => { const h = handlers[handlers.length - 1]; let err = null, out = null; await h(req, { json: (b) => { out = b; }, status() { return this; } }, (e) => { err = e; }); return { err, out }; };
let verdict = 'SUCCESS'; const calls = [];
global.fetch = async (u, o) => {
  calls.push({ u, o });
  const json = (b) => ({ ok: true, json: async () => b });
  if (u.endsWith('/v1/oauth2/token')) return json({ access_token: 'T', expires_in: 3000 });
  if (u.endsWith('/verify-webhook-signature')) return json({ verification_status: verdict });
  if (u.endsWith('/v2/checkout/orders')) return json({ id: 'PP1', links: [{ rel: 'payer-action', href: 'https://paypal.test/approve' }] });
  return json({ status: 'COMPLETED' });
};
const H = { 'paypal-transmission-id': 'a', 'paypal-transmission-sig': 'b', 'paypal-cert-url': 'https://api.paypal.com/c', 'paypal-auth-algo': 'SHA256withRSA', 'paypal-transmission-time': 't' };
const body = (o) => Buffer.from(JSON.stringify(o));
const completed = (id, value, cur = 'USD') => body({ event_type: 'PAYMENT.CAPTURE.COMPLETED', resource: { status: 'COMPLETED', custom_id: String(id), amount: { value, currency_code: cur } } });
const approved = (id, value) => body({ event_type: 'CHECKOUT.ORDER.APPROVED', resource: { id: 'PP' + id, purchase_units: [{ custom_id: String(id), amount: { value, currency_code: 'USD' } }] } });
(async () => {
  const pp = require('./src/routes/payments');
  verdict = 'FAILURE';
  let r = await call(pp.webhook(db), { body: completed(1, '12.50'), headers: H });
  assert(r.err && r.err.status === 400 && orders[0].status === 'pending');          // PayPal says the signature is bad
  verdict = 'SUCCESS';
  r = await call(pp.webhook(db), { body: completed(1, '12.50'), headers: {} });
  assert(r.err && r.err.status === 400);                                              // no signature headers at all
  r = await call(pp.webhook(db), { body: completed(2, '19.99'), headers: H });
  assert(!r.err && orders[1].status === 'pending');                                   // wrong amount
  r = await call(pp.webhook(db), { body: completed(1, '12.50', 'EUR'), headers: H });
  assert(orders[0].status === 'pending');                                             // wrong currency
  calls.length = 0; r = await call(pp.webhook(db), { body: approved(2, '1.00'), headers: H });
  assert(!calls.some((c) => c.u.endsWith('/capture')));                               // approved for a different amount: no capture
  calls.length = 0; r = await call(pp.webhook(db), { body: approved(1, '12.50'), headers: H });
  const cap = calls.find((c) => c.u.endsWith('/v2/checkout/orders/PP1/capture'));
  assert(cap && cap.o.headers['PayPal-Request-Id'] === 'capture-PP1');                // idempotent server-side capture
  r = await call(pp.webhook(db), { body: completed(1, '12.50'), headers: H });
  assert(!r.err && orders[0].status === 'paid');
  r = await call(pp.webhook(db), { body: completed(1, '12.50'), headers: H });
  assert(!r.err && orders[0].status === 'paid');                                      // replay is harmless
  calls.length = 0; r = await call(pp.intent(db).stack.map((l) => l.handle), { user: { id: 7 }, body: { orderId: 2, amount: 1 } });
  const create = calls.find((c) => c.u.endsWith('/v2/checkout/orders'));
  assert(r.out && r.out.approveUrl === 'https://paypal.test/approve' && JSON.parse(create.o.body).purchase_units[0].amount.value === '20.00');
  console.log('paypal ok');
})().catch((e) => { console.error(e); process.exit(1); });
"""


def test_paypal_webhook_and_intent_behaviour_in_node():
    _run_node("paypal", _PAYPAL_HARNESS)


# ---- Phase 6F: S3 storage for Express ------------------------------------------------------------------------------------------------

def _s3_gen(backend="express", storage="s3", brief=STORE):
    return _gen(brief, backend=backend, cache="redis", storage=storage)


def test_express_s3_storage_replaces_local_disk_uploads():
    spec, st, m = _s3_gen()
    assert m["integrations"]["uploads"] and m["storage"] == "s3"
    files = express.generate(spec, st, m)
    up = files["backend/src/routes/uploads.js"]
    assert "s3.put" in up and "writeFile" not in up and "sendFile" not in up and "originalname" not in up
    assert "backend/src/lib/s3.js" in files and not any(k.endswith("uploads_s3.js") for k in files)
    env = files["backend/.env.example"]
    assert all(k in env for k in ("S3_BUCKET=", "S3_ENDPOINT=", "S3_ACCESS_KEY_ID=", "S3_SECRET_ACCESS_KEY=", "UPLOAD_MAX_BYTES=")) and "UPLOAD_DIR" not in env
    assert "PRIVATE S3" in files["backend/README.md"]
    spec, st, m = _s3_gen(storage="local")
    files = express.generate(spec, st, m)
    assert "writeFile" in files["backend/src/routes/uploads.js"] and "backend/src/lib/s3.js" not in files


def test_s3_is_generated_for_every_backend_since_6h6():      # see tests/test_v2_phase6h6_storage.py for the per-backend checks
    for be in ("fastapi", "flask", "nestjs", "spring", "django"):
        _, _, m = _s3_gen(backend=be)
        assert m["integrations"]["uploads"] and m["storage"] == "s3", be


_S3_HARNESS = r"""
const assert = require('assert');
process.env.S3_ENDPOINT = 'https://minio.test:9000'; process.env.S3_BUCKET = 'bk'; process.env.S3_REGION = 'us-east-1';
process.env.S3_ACCESS_KEY_ID = 'AK'; process.env.S3_SECRET_ACCESS_KEY = 'SK';
const s3 = require('./src/lib/s3'); const cfg = require('./src/config');
// AWS documentation vector (GET Object with a Range header): the signature must match byte for byte.
const a = s3.authorization({ method: 'GET', host: 'examplebucket.s3.amazonaws.com', path: '/test.txt', headers: { Range: 'bytes=0-9' },
  payloadHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', amzDate: '20130524T000000Z', region: 'us-east-1',
  accessKeyId: 'AKIAIOSFODNN7EXAMPLE', secretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' });
assert(a.header.endsWith('Signature=f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41'), a.header);
assert.deepStrictEqual(s3.target('k.png'), { url: 'https://minio.test:9000/bk/k.png', host: 'minio.test:9000', path: '/bk/k.png' });   // path style
cfg.s3.endpoint = 'https://s3.eu-west-1.amazonaws.com';
assert.strictEqual(s3.target('k.png').url, 'https://bk.s3.eu-west-1.amazonaws.com/k.png');                                          // virtual-hosted style
cfg.s3.endpoint = 'https://minio.test:9000';
const store = new Map(); const calls = [];
global.fetch = async (u, o) => { calls.push({ u, o });
  if (o.method === 'PUT') { store.set(u, Buffer.from(o.body)); return { ok: true, status: 200 }; }
  const b = store.get(u); return b ? { ok: true, status: 200, arrayBuffer: async () => b } : { ok: false, status: 404 }; };
const png = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.alloc(40)]);
const handler = (router, m) => router.routes[m + ' /'] ? router.routes[m + ' /'].slice(-1)[0] : router.routes[m + ' /:name'].slice(-1)[0];
const run = async (h, req) => { let err = null, out = null, code = 200, hdr = {}, sent = null;
  await h(req, { status(c) { code = c; return this; }, json: (b) => { out = b; }, set: (o) => Object.assign(hdr, o), type: (t) => { hdr.type = t; }, send: (b) => { sent = b; } }, (e) => { err = e; });
  return { err, out, code, hdr, sent }; };
(async () => {
  const router = require('./src/routes/uploads')();
  let r = await run(handler(router, 'post'), { body: png, headers: {} });
  const name = r.out && r.out.name;
  assert(r.code === 201 && r.out.type === 'image/png' && /^[0-9a-f]{32}\.png$/.test(r.out.name), JSON.stringify(r));
  const put = calls.find((c) => c.o.method === 'PUT');
  assert(put.u === `https://minio.test:9000/bk/${r.out.name}` && put.o.headers['Content-Type'] === 'image/png' && /^AWS4-HMAC-SHA256 Credential=AK\//.test(put.o.headers.Authorization));
  assert(!JSON.stringify(put.o.headers).includes('SK'));                                            // the secret never goes on the wire
  const n = calls.length;
  r = await run(handler(router, 'post'), { body: Buffer.from('<script>alert(1)</script>'.repeat(3)), headers: {} });
  assert(r.err && r.err.status === 415 && calls.length === n);                                       // rejected before touching the bucket
  r = await run(handler(router, 'get'), { params: { name }, headers: {} });
  assert(!r.err && Buffer.compare(r.sent, png) === 0 && r.hdr['X-Content-Type-Options'] === 'nosniff' && r.hdr.type === 'image/png');
  r = await run(handler(router, 'get'), { params: { name: 'a'.repeat(32) + '.png' }, headers: {} });
  assert(r.err && r.err.status === 404);                                                              // valid name, no such object
  const m = calls.length;
  for (const bad of ['../../etc/passwd', 'a.png', 'x'.repeat(32) + '.exe', name + '/..']) {
    r = await run(handler(router, 'get'), { params: { name: bad }, headers: {} });
    assert(r.err && r.err.status === 404);
  }
  assert(calls.length === m);                                                                         // bad names never reach the bucket
  cfg.s3.secretAccessKey = 'your-secret-access-key';
  r = await run(handler(router, 'post'), { body: png, headers: {} });
  assert(r.err && r.err.status === 503);                                                              // placeholder credentials: clear error, no request
  console.log('s3 ok');
})().catch((e) => { console.error(e); process.exit(1); });
"""


def test_s3_storage_signing_and_routes_in_node():
    _run_node("razorpay", _S3_HARNESS, storage="s3")
