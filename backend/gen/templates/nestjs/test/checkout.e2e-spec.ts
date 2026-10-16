// Generated checkout + payments tests (only shipped when the app has checkout).
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-require-imports */
import { INestApplication } from '@nestjs/common';
import { createHmac } from 'crypto';
import request from 'supertest';
import { createApp } from '../src/bootstrap';
import { DB, Db } from '../src/db/db';
import { SCHEMA } from '../src/schema';

const skip = !!SCHEMA.db && SCHEMA.db !== 'sqlite' && !process.env.TEST_DATABASE_URL;
const PW = 'Passw0rd!long';
let seq = 0;
const rnd = (): string => `${++seq}${Math.floor(Math.random() * 1e9)}`;

(skip ? describe.skip : describe)('checkout', () => {
  let app: INestApplication;
  let db: Db;

  beforeAll(async () => {
    app = await createApp();
    await app.init();
    db = app.get<Db>(DB);
  });
  afterAll(async () => {
    await app?.close();
  });

  const call = async (method: 'get' | 'post', path: string, body?: unknown, token?: string) => {
    let r = request(app.getHttpServer())[method](path);
    if (token) r = r.set('Authorization', `Bearer ${token}`);
    if (body !== undefined) r = r.send(body as object);
    const res = await r;
    return { status: res.status, body: res.body } as { status: number; body: any };
  };
  const has = (e: string, f: string) => SCHEMA.entities[e].fields.some((x) => x.name === f);

  async function signUp() {
    const email = `c${rnd()}@example.com`;
    expect((await call('post', '/api/auth/register', { email, name: 'Buyer', password: PW })).status).toBe(201);
    const r = await call('post', '/api/auth/login', { email, password: PW });
    return { token: r.body.accessToken as string, id: r.body.user.id as number };
  }
  async function product(price: number, stock: number) {
    const o: Record<string, unknown> = {};
    for (const f of SCHEMA.entities.Product.fields) {
      if (!f.required) continue;
      if (f.name === 'price') o.price = price;
      else if (f.name === 'stock') o.stock = stock;
      else if (f.type === 'enum') o[f.name] = (f.values as string[])[0];
      else if (f.type === 'bool') o[f.name] = true;
      else if (f.type === 'int' || f.type === 'float') o[f.name] = 1;
      else if (f.type === 'datetime') o[f.name] = new Date().toISOString();
      else o[f.name] = `p${rnd()}`;
    }
    if (has('Product', 'active')) o.active = true;
    return db.create('Product', o);
  }

  it('needs a signed-in user and a valid body', async () => {
    expect((await call('post', '/api/checkout', { items: [{ productId: 1, quantity: 1 }] })).status).toBe(401);
    const u = await signUp();
    for (const bad of [{}, { items: [] }, { items: 'x' }, { items: [{ productId: 1, quantity: 0 }] }, { items: [{ productId: 1, quantity: 1.5 }] },
      { items: [{ productId: 1, quantity: '2' }] }, { items: [{ productId: 1, quantity: 99 }, { productId: 1, quantity: 1 }] }, { items: [null] }]) {
      const r = await call('post', '/api/checkout', bad, u.token);
      expect([400]).toContain(r.status);
      expect(r.body.error.code).toBe('validation_failed');
    }
    expect((await call('post', '/api/checkout', { items: [{ productId: 987654, quantity: 1 }] }, u.token)).body.error.code).toBe('invalid_product');
  });

  it('prices and stock come from the database, not the client', async () => {
    const u = await signUp();
    const p = await product(19.99, 5);
    const r = await call('post', '/api/checkout', { items: [{ productId: p.id, quantity: 2 }], total: 0.01, price: 0.01 }, u.token);
    expect(r.status).toBe(201);
    expect(r.body.order.total).toBe(39.98);
    expect(r.body.order.status).toBe('pending');
    expect(Number((await db.get('Product', p.id))?.stock)).toBe(3);
    const stored = await db.get('Order', r.body.order.orderId);
    expect(Number(stored?.total)).toBe(39.98);
    expect(String(stored?.user_id)).toBe(String(u.id));
  });

  it('never oversells and rolls back completely', async () => {
    const u = await signUp();
    const a = await product(10, 1);
    const b = await product(5, 10);
    const r = await call('post', '/api/checkout', { items: [{ productId: b.id, quantity: 3 }, { productId: a.id, quantity: 2 }] }, u.token);
    expect(r.status).toBe(409);
    expect(r.body.error.code).toBe('insufficient_stock');
    expect(Number((await db.get('Product', b.id))?.stock)).toBe(10);     // nothing was taken
    expect(Number((await db.get('Product', a.id))?.stock)).toBe(1);
    const ok = await Promise.all([1, 2, 3].map(() => call('post', '/api/checkout', { items: [{ productId: a.id, quantity: 1 }] }, u.token)));
    expect(ok.filter((x) => x.status === 201).length).toBe(1);          // one unit, one winner
    expect(Number((await db.get('Product', a.id))?.stock)).toBe(0);
  });

  if (SCHEMA.integrations.payments) {
    it('payment intent: sign-in required, own order only, no client amount', async () => {
      expect((await call('post', '/api/payments/intent', { orderId: 1 })).status).toBe(401);
      const u = await signUp();
      const other = await signUp();
      const p = await product(12.5, 3);
      const o = await call('post', '/api/checkout', { items: [{ productId: p.id, quantity: 1 }] }, u.token);
      const id = o.body.order.orderId;
      expect([404, 503]).toContain((await call('post', '/api/payments/intent', { orderId: id }, other.token)).status);   // someone else's order is never charged
      const mine = await call('post', '/api/payments/intent', { orderId: id, amount: 1 }, u.token);
      expect(mine.status).toBe(503);                                  // test environment has placeholder provider credentials: no request is made
      expect(mine.body.error.code).toBe('payments_unavailable');
      expect((await call('post', '/api/payments/intent', {}, u.token)).status).toBe(503);
    });

    it('webhook rejects unsigned and wrongly signed requests', async () => {
      const body = JSON.stringify({ type: 'payment_intent.succeeded', data: { object: { metadata: { order_id: '1' }, amount_received: 100 } } });
      const bad = await request(app.getHttpServer()).post('/api/payments/webhook').set('Content-Type', 'application/json')
        .set('stripe-signature', `t=${Math.floor(Date.now() / 1000)},v1=${'0'.repeat(64)}`).set('x-razorpay-signature', '0'.repeat(64)).send(body);
      expect([400, 503]).toContain(bad.status);
      expect(['invalid_signature', 'payments_unavailable']).toContain(bad.body.error.code);
      expect((await request(app.getHttpServer()).post('/api/payments/webhook').set('Content-Type', 'application/json').send(body)).status).not.toBe(200);
    });

    it('a correctly signed webhook marks only a matching pending order paid (replay is harmless)', async () => {
      const u = await signUp();
      const p = await product(7.25, 4);
      const id = (await call('post', '/api/checkout', { items: [{ productId: p.id, quantity: 2 }] }, u.token)).body.order.orderId;
      const secretS = process.env.STRIPE_WEBHOOK_SECRET || '';
      const secretR = process.env.RAZORPAY_WEBHOOK_SECRET || '';
      const send = async (amount: number) => {
        const ts = Math.floor(Date.now() / 1000);
        const stripe = JSON.stringify({ type: 'payment_intent.succeeded', data: { object: { metadata: { order_id: String(id) }, amount_received: amount } } });
        const rzp = JSON.stringify({ event: 'payment.captured', payload: { payment: { entity: { amount, currency: 'inr', notes: { order_id: String(id) } } } } });
        return request(app.getHttpServer()).post('/api/payments/webhook').set('Content-Type', 'application/json')
          .set('stripe-signature', `t=${ts},v1=${createHmac('sha256', secretS).update(`${ts}.${stripe}`).digest('hex')}`).send(stripe)
          .then(async (r) => (r.status === 200 || !secretR ? r : request(app.getHttpServer()).post('/api/payments/webhook').set('Content-Type', 'application/json')
            .set('x-razorpay-signature', createHmac('sha256', secretR).update(rzp).digest('hex')).send(rzp)));
      };
      const wrong = await send(1);
      if (wrong.status === 503) return;                                // PayPal apps verify through PayPal's API (needs the network): nothing to run here
      expect(String((await db.get('Order', id))?.status)).toBe('pending');   // amount mismatch ignored
      expect((await send(1450)).status).toBe(200);
      expect(String((await db.get('Order', id))?.status)).toBe('paid');
      expect((await send(1450)).status).toBe(200);                      // replay
      expect(String((await db.get('Order', id))?.status)).toBe('paid');
    });
  }
});
