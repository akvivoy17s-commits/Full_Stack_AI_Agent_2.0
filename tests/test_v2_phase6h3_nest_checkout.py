"""Phase 6H.3: checkout + Stripe/Razorpay/PayPal payments for NestJS (SQL databases).
Static checks always run; the TypeScript is transpiled and the real checkout/payment logic is executed in node (stubbed Nest/express/db) when node + typescript exist."""
import hashlib
import hmac
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from backend.gen import model, nest
from backend.spec import compose
from gen_helpers import stack_for

STORE = "online store with products cart and orders, stripe payments, image uploads, live updates, redis cache"


def _find_ts():
    """Path of a globally installed `typescript` package (used only to transpile and run the generated code), else None."""
    if not shutil.which("node") or not shutil.which("npm"):
        return None
    root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    p = Path(root) / "typescript"
    return p if root and p.exists() else None


TSC = _find_ts()


def _gen(brief=STORE, db="sqlite", **extra):
    st = stack_for(db, brief, backend="nestjs", **extra)
    spec = compose.build(brief, st)
    m = model.build(spec, st)
    return m, nest.generate(spec, st, m)


def test_nest_gets_checkout_and_stripe():
    m, files = _gen()
    assert m["checkout"] and m["integrations"]["payments"] and m["paymentProvider"] == "stripe"
    assert {"POST /api/checkout", "POST /api/payments/intent", "POST /api/payments/webhook"} <= set(m["manifest"])
    assert not {"checkout", "payments"} & set(m["not_generated"]), m["not_generated"]
    for f in ("checkout/checkout.controller.ts", "checkout/checkout.service.ts", "checkout/checkout.module.ts", "integrations/pay.ts", "integrations/payments.ts",
              "integrations/pay-mount.ts", "integrations/notify.ts", "../test/checkout.e2e-spec.ts"):
        assert f"backend/src/{f}".replace("src/../", "") in files, f
    assert "payments_razorpay.ts" not in "".join(files) and "payments_paypal.ts" not in "".join(files)
    assert '"checkout": true' in files["backend/src/schema.ts"]
    assert "CheckoutModule" in files["backend/src/app.module.ts"]
    assert '"jsonwebtoken"' in files["backend/package.json"]
    assert "STRIPE_CURRENCY=" in files["backend/.env.example"] and "STRIPE_SECRET_KEY=" in files["backend/.env.example"]
    paths = json.loads(files["backend/openapi.json"])["paths"]
    assert "/api/checkout" in paths and "/api/payments/intent" in paths
    assert "Checkout:" in files["backend/README.md"] and "Payments (Stripe)" in files["backend/README.md"]
    assert "cache.invalidate()" in files["backend/src/integrations/notify.ts"] and "events.emit" in files["backend/src/integrations/notify.ts"]
    assert "mountWebhook(app)" in files["backend/src/bootstrap.ts"] and files["backend/src/bootstrap.ts"].index("mountWebhook(app)") < files["backend/src/bootstrap.ts"].index("json({")


@pytest.mark.parametrize("prov", ["razorpay", "paypal"])
def test_other_providers(prov):
    m, files = _gen(STORE.replace("stripe", prov))
    assert m["checkout"] and m["integrations"]["payments"] and m["paymentProvider"] == prov
    assert prov in files["backend/src/integrations/payments.ts"].lower()
    assert f"{prov.upper()}_CURRENCY=" in files["backend/.env.example"]
    assert not any(k.endswith(("payments_razorpay.ts", "payments_paypal.ts")) for k in files)


def test_plain_and_unsupported_apps_unchanged():
    m, files = _gen("college management system with student login and courses")
    assert not m["checkout"]
    assert not any("checkout" in k or k.endswith(("pay.ts", "payments.ts", "notify.ts")) for k in files)
    assert "no payments" in files["backend/src/integrations/pay-mount.ts"]
    m, files = _gen(STORE, db="mongodb")
    assert not m["checkout"] and "checkout" in m["not_generated"] and not any("checkout" in k for k in files)
    st = stack_for("sqlite", STORE, backend="nestjs")
    spec = compose.build(STORE, st)
    spec["env"] = [v for v in spec["env"] if "STRIPE" not in v["name"]]                  # no payment provider in the spec: checkout only
    m = model.build(spec, st)
    files = nest.generate(spec, st, m)
    assert m["checkout"] and not m["integrations"]["payments"] and "backend/src/integrations/payments.ts" not in files
    assert "cache.invalidate()" in files["backend/src/integrations/notify.ts"]


def _ts():
    return TSC and Path(TSC).exists() and shutil.which("node")


@pytest.mark.skipif(not _ts(), reason="node + typescript not installed")
@pytest.mark.parametrize("brief,db", [(STORE, "sqlite"), (STORE, "postgresql"), (STORE.replace("stripe", "razorpay"), "mysql"), (STORE.replace("stripe", "paypal"), "sqlite"),
                                      ("online store with products cart and orders, checkout", "sqlite"), ("college management system with student login and courses", "sqlite")])
def test_generated_typescript_parses(brief, db):
    m, files = _gen(brief, db)
    d = Path(tempfile.mkdtemp())
    for rel, txt in files.items():
        if rel.endswith(".ts"):
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(txt, encoding="utf-8")
    script = ("const ts=require(process.argv[1]);const fs=require('fs');const path=require('path');let bad=0;"
              "const walk=(x)=>fs.readdirSync(x,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(x,e.name)):[path.join(x,e.name)]);"
              "for(const f of walk(process.argv[2]).filter(f=>f.endsWith('.ts'))){const r=ts.transpileModule(fs.readFileSync(f,'utf8'),{reportDiagnostics:true,compilerOptions:{module:1,target:9}});"
              "if(r.diagnostics.length){bad++;console.log(f,r.diagnostics.map(x=>x.messageText));}}process.exit(bad?1:0)")
    r = subprocess.run(["node", "-e", script, str(TSC), str(d / "backend")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


HARNESS = r"""
const ts=require(process.argv[1]), fs=require('fs'), path=require('path'), Module=require('module'), crypto=require('crypto'), assert=require('assert');
const root=process.argv[2]+'/backend/src', out=fs.mkdtempSync('/tmp/nestco-');
const files=fs.readdirSync(root,{recursive:true}).filter(f=>f.endsWith('.ts'));
for(const f of files){const o=path.join(out,f.replace(/\.ts$/,'.js'));fs.mkdirSync(path.dirname(o),{recursive:true});
  fs.writeFileSync(o,ts.transpileModule(fs.readFileSync(path.join(root,f),'utf8'),{compilerOptions:{module:1,target:9,experimentalDecorators:true}}).outputText);}
const SCHEMA={db:'sqlite',integrations:{cache:false,ws:false,uploads:false,payments:true},entities:{
  Product:{fields:[{name:'price'},{name:'stock'},{name:'active'}]},Order:{fields:[{name:'user_id'},{name:'status'},{name:'total'},{name:'created_at'}]},
  OrderItem:{fields:[{name:'order_id'},{name:'product_id'},{name:'user_id'},{name:'quantity'},{name:'unit_price'}]}}};
class HttpError extends Error{constructor(status,code,message,details){super(message);this.status=status;this.code=code;this.details=details;}}
const stubs={'@nestjs/common':{Inject:()=>()=>{},Injectable:()=>()=>{}},'express':{Router:()=>({post(){}}),raw:()=>()=>{}},'jsonwebtoken':{verify:()=>({})}};
const orig=Module._load;
Module._load=function(req,parent,...r){
  if(stubs[req])return stubs[req];
  if(/schema$/.test(req))return{SCHEMA};
  if(/http-error$/.test(req))return{HttpError};
  if(/config$/.test(req))return{cfg:{jwt:{key:'k'},stripe:{secretKey:'',webhookSecret:'whsec',currency:'usd'},razorpay:{webhookSecret:'rz',currency:'inr',keyId:'',keySecret:''},paypal:{currency:'usd',env:'sandbox'}}};
  if(/db\/db$/.test(req))return{DB:Symbol('DB')};
  if(/notify$/.test(req))return{changed:async(e)=>{global.CHANGED.push(...e);}};
  return orig.call(this,req,parent,...r);};
global.CHANGED=[];
const load=(p)=>require(path.join(out,p));
(async()=>{
  // ---- fake SQL db with transactional semantics (copy on begin, commit on success)
  const mk=()=>({Product:[{id:1,price:19.99,stock:5,active:true},{id:2,price:5,stock:1,active:true},{id:3,price:3,stock:9,active:false}],Order:[],OrderItem:[]});
  let data=mk();
  const db={parseId:(v)=>{const n=Number(v);return typeof v!=='object'&&Number.isInteger(n)&&n>0?n:null},
    async findOne(n,w){return data[n].find(r=>Object.entries(w).every(([k,v])=>r[k]==v))||null},
    async updateWhere(n,w,d){let c=0;for(const r of data[n])if(Object.entries(w).every(([k,v])=>r[k]==v)){Object.assign(r,d);c++}return c},
    async tx(fn){const snap=JSON.parse(JSON.stringify(data));try{return await fn({
      async lock(n,ids){return data[n].filter(r=>ids.includes(r.id))},
      async insert(n,row){const id=data[n].length+1;data[n].push({id,...row});return id},
      async take(n,id,f,q){const r=data[n].find(x=>x.id===id);if(r[f]<q)return false;r[f]-=q;return true}})}catch(e){data=snap;throw e}}};
  const {CheckoutService}=load('checkout/checkout.service.js');
  const svc=new CheckoutService(db);
  const fail=async(p,code,status)=>{try{await p}catch(e){assert.strictEqual(e.code,code);if(status)assert.strictEqual(e.status,status);return}throw new Error('accepted, wanted '+code)};
  const U={id:'7',role:'user'};
  const r=await svc.create(U,{items:[{productId:1,quantity:2},{product_id:1,quantity:1}],total:0.01});
  assert.strictEqual(r.order.total,59.97);assert.strictEqual(data.Product[0].stock,2);assert.strictEqual(data.OrderItem.length,1);assert.strictEqual(data.OrderItem[0].quantity,3);
  assert.strictEqual(data.Order[0].status,'pending');assert.strictEqual(data.Order[0].user_id,7);
  // rollback: second product lacks stock -> first product's stock must be untouched, no order row left
  data=mk();
  await fail(svc.create(U,{items:[{productId:1,quantity:2},{productId:2,quantity:2}]}),'insufficient_stock',409);
  assert.strictEqual(data.Product[0].stock,5);assert.strictEqual(data.Order.length,0);
  await fail(svc.create(U,{items:[{productId:3,quantity:1}]}),'product_unavailable',409);
  await fail(svc.create(U,{items:[{productId:99,quantity:1}]}),'invalid_product',400);
  await fail(svc.create(undefined,{items:[{productId:1,quantity:1}]}),'unauthorized',401);
  for(const bad of [null,{},{items:[]},{items:'x'},{items:[null]},{items:[1]},{items:[{productId:1,quantity:0}]},{items:[{productId:1,quantity:1.5}]},{items:[{productId:1,quantity:'2'}]},{items:[{productId:1,quantity:true}]},
    {items:[{productId:1,quantity:99},{productId:1,quantity:1}]},{items:[{productId:0,quantity:1}]},{items:[{productId:{},quantity:1}]},{items:Array(51).fill({productId:1,quantity:1})}])
    await fail(svc.create(U,bad),'validation_failed',400);
  // ---- Stripe signature
  const stripe=load('integrations/payments.js');
  const raw=Buffer.from('{"a":1}'),now=1700000000,sig=(ts,b=raw,s='whsec')=>`t=${ts},v1=`+crypto.createHmac('sha256',s).update(`${ts}.`).update(b).digest('hex');
  assert(stripe.verifySignature(raw,sig(now),'whsec',now));
  assert(!stripe.verifySignature(raw,sig(now),'whsec',now+301));
  assert(!stripe.verifySignature(Buffer.from('{"a":2}'),sig(now),'whsec',now));
  assert(!stripe.verifySignature(raw,sig(now,raw,'x'),'whsec',now));
  for(const h of ['',undefined,'t=x,v1=00',`t=${now}`,`t=${now},v1=zz`,`t=${now},v1=${'0'.repeat(64)}`])assert(!stripe.verifySignature(raw,h,'whsec',now));
  // ---- markPaid: exact minor-unit match, pending only, replay harmless, order never resurrected
  const pay=load('integrations/pay.js');
  data=mk();const o=await svc.create(U,{items:[{productId:1,quantity:1}]});const id=o.order.orderId;global.CHANGED.length=0;
  assert.strictEqual(await pay.markPaid(db,id,1998),false);assert.strictEqual(data.Order[0].status,'pending');
  assert.strictEqual(await pay.markPaid(db,null,1999),false);assert.strictEqual(await pay.markPaid(db,id,'1999'),false);assert.strictEqual(await pay.markPaid(db,id,19.99),false);
  assert.strictEqual(await pay.markPaid(db,id,1999),true);assert.strictEqual(data.Order[0].status,'paid');assert(global.CHANGED.includes('Order'));
  assert.strictEqual(await pay.markPaid(db,id,1999),false);
  data.Order[0].status='cancelled';assert.strictEqual(await pay.markPaid(db,id,1999),false);assert.strictEqual(data.Order[0].status,'cancelled');
  // ---- payableOrder: own pending order only, amount from storage
  data=mk();const o2=await svc.create(U,{items:[{productId:2,quantity:1}]});
  const req=(uid,body)=>({user:{id:uid},body});
  const p=await pay.payableOrder(db,req('7',{orderId:o2.order.orderId,amount:1}));assert.deepStrictEqual(p,{orderId:1,minor:500,total:5});
  await fail(pay.payableOrder(db,req('8',{orderId:1})),'not_found',404);
  await fail(pay.payableOrder(db,req('7',{})),'validation_failed',400);
  data.Order[0].status='paid';await fail(pay.payableOrder(db,req('7',{orderId:1})),'order_not_payable',409);
  console.log('HARNESS OK');
})().catch(e=>{console.error(e);process.exit(1)});
"""


@pytest.mark.skipif(not _ts(), reason="node + typescript not installed")
def test_checkout_and_payment_logic_runs():
    m, files = _gen()
    d = Path(tempfile.mkdtemp())
    for rel, txt in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
    r = subprocess.run(["node", "-e", HARNESS, str(TSC), str(d)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and "HARNESS OK" in r.stdout, r.stdout + r.stderr


@pytest.mark.skipif(not _ts(), reason="node + typescript not installed")
def test_razorpay_signature_logic():
    m, files = _gen(STORE.replace("stripe", "razorpay"))
    d = Path(tempfile.mkdtemp())
    for rel, txt in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
    script = ("const ts=require(process.argv[1]),fs=require('fs'),Module=require('module'),crypto=require('crypto'),assert=require('assert');"
              "const src=fs.readFileSync(process.argv[2]+'/backend/src/integrations/payments.ts','utf8');"
              "const js=ts.transpileModule(src,{compilerOptions:{module:1,target:9}}).outputText;const o=Module._load;"
              "Module._load=function(r,...a){if(/express$/.test(r))return{Router:()=>({}),raw:()=>0};if(/http-error|config|db\\/db|\\.\\/pay$/.test(r))return{};return o.call(this,r,...a)};"
              "const m={exports:{}};new Function('exports','require','module',js)(m.exports,require,m);const raw=Buffer.from('{\"x\":1}');"
              "const good=crypto.createHmac('sha256','s3cret').update(raw).digest('hex');"
              "assert(m.exports.verifySignature(raw,good,'s3cret'));assert(!m.exports.verifySignature(raw,good,'other'));assert(!m.exports.verifySignature(Buffer.from('{}'),good,'s3cret'));"
              "for(const h of [undefined,'','zz',good.slice(1),good.toUpperCase()+'0'])assert(!m.exports.verifySignature(raw,h,'s3cret'));assert(!m.exports.verifySignature(raw,good,''));console.log('OK')")
    r = subprocess.run(["node", "-e", script, str(TSC), str(d)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and "OK" in r.stdout, r.stdout + r.stderr
