// Stripe, called with fetch (no SDK). The amount always comes from the stored order, never from the client.
import { Router, raw } from 'express';
import type { Request, RequestHandler } from 'express';
import { createHmac, timingSafeEqual } from 'crypto';
import { HttpError } from '../common/http-error';
import { cfg } from '../config';
import { Db } from '../db/db';
import * as pay from './pay';

const TOLERANCE_SEC = 300;

export function verifySignature(body: Buffer, header: unknown, secret: string, now = Date.now() / 1000): boolean {
  const parts = Object.fromEntries(String(header || '').split(',').map((p) => p.trim().split('=')).filter((p) => p.length === 2));
  const ts = Number(parts.t);
  if (!Number.isInteger(ts) || Math.abs(now - ts) > TOLERANCE_SEC || !/^[0-9a-f]{64}$/i.test(parts.v1 || '')) return false;
  const want = createHmac('sha256', secret).update(`${ts}.`).update(body).digest();
  return timingSafeEqual(Buffer.from(parts.v1, 'hex'), want);
}

// Mounted BEFORE the JSON parser: the signature is computed over the exact raw bytes.
export function webhook(db: Db): RequestHandler[] {
  return [raw({ type: 'application/json', limit: '256kb' }), pay.wrap(async (req: Request, res) => {
    if (pay.placeholder(cfg.stripe.webhookSecret)) throw pay.unavailable();
    if (!Buffer.isBuffer(req.body) || !verifySignature(req.body, req.headers['stripe-signature'], cfg.stripe.webhookSecret)) {
      throw new HttpError(400, 'invalid_signature', 'Invalid webhook signature');
    }
    const event = pay.parseJson(req.body);
    const obj = event.data?.object;
    if (event.type === 'payment_intent.succeeded' && obj?.metadata) await pay.markPaid(db, db.parseId(obj.metadata.order_id), obj.amount_received);
    res.json({ received: true });
  })];
}

export function intent(db: Db): Router {
  const router = Router();
  router.post('/intent', pay.signedIn, pay.wrap(async (req, res) => {
    if (pay.placeholder(cfg.stripe.secretKey)) throw pay.unavailable();
    const { orderId, minor, total } = await pay.payableOrder(db, req);
    const form = new URLSearchParams({ amount: String(minor), currency: cfg.stripe.currency, 'metadata[order_id]': String(orderId), 'automatic_payment_methods[enabled]': 'true' });
    let r: Response;
    try {
      r = await fetch('https://api.stripe.com/v1/payment_intents', {
        method: 'POST', body: form, signal: AbortSignal.timeout(10000),
        headers: { Authorization: `Bearer ${cfg.stripe.secretKey}`, 'Content-Type': 'application/x-www-form-urlencoded', 'Idempotency-Key': `order-${orderId}-${minor}` },
      });
    } catch { throw pay.unreachable(); }
    const data = (await r.json().catch(() => ({}))) as { client_secret?: string };
    if (!r.ok || !data.client_secret) throw pay.rejected();
    res.status(201).json({ clientSecret: data.client_secret, orderId, amount: total, currency: cfg.stripe.currency });
  }));
  return router;
}
