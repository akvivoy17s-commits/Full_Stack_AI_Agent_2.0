// Razorpay, called with fetch (no SDK). The amount comes from the stored order, in paise.
import { Router, raw } from 'express';
import type { Request, RequestHandler } from 'express';
import { createHmac, timingSafeEqual } from 'crypto';
import { HttpError } from '../common/http-error';
import { cfg } from '../config';
import { Db } from '../db/db';
import * as pay from './pay';

export function verifySignature(body: Buffer, header: unknown, secret: string): boolean {
  if (!secret || typeof header !== 'string' || !/^[0-9a-f]{64}$/i.test(header)) return false;
  return timingSafeEqual(Buffer.from(header, 'hex'), createHmac('sha256', secret).update(body).digest());
}

// Mounted BEFORE the JSON parser: the signature is computed over the exact raw bytes.
export function webhook(db: Db): RequestHandler[] {
  return [raw({ type: 'application/json', limit: '256kb' }), pay.wrap(async (req: Request, res) => {
    if (pay.placeholder(cfg.razorpay.webhookSecret)) throw pay.unavailable();
    if (!Buffer.isBuffer(req.body) || !verifySignature(req.body, req.headers['x-razorpay-signature'], cfg.razorpay.webhookSecret)) {
      throw new HttpError(400, 'invalid_signature', 'Invalid webhook signature');
    }
    const event = pay.parseJson(req.body);
    const p = event.payload?.payment?.entity;
    if (event.event === 'payment.captured' && p?.notes && String(p.currency).toLowerCase() === cfg.razorpay.currency) {
      await pay.markPaid(db, db.parseId(p.notes.order_id), p.amount);
    }
    res.json({ received: true });
  })];
}

export function intent(db: Db): Router {
  const router = Router();
  router.post('/intent', pay.signedIn, pay.wrap(async (req, res) => {
    if (pay.placeholder(cfg.razorpay.keyId) || pay.placeholder(cfg.razorpay.keySecret)) throw pay.unavailable();
    const { orderId, minor, total } = await pay.payableOrder(db, req);
    let r: Response;
    try {
      r = await fetch('https://api.razorpay.com/v1/orders', {
        method: 'POST', signal: AbortSignal.timeout(10000),
        headers: { Authorization: 'Basic ' + Buffer.from(`${cfg.razorpay.keyId}:${cfg.razorpay.keySecret}`).toString('base64'), 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: minor, currency: cfg.razorpay.currency.toUpperCase(), receipt: `order-${orderId}`, notes: { order_id: String(orderId) } }),
      });
    } catch { throw pay.unreachable(); }
    const data = (await r.json().catch(() => ({}))) as { id?: string };
    if (!r.ok || !data.id) throw pay.rejected();
    // keyId is public by design (the checkout widget needs it); the secret never leaves the server.
    res.status(201).json({ razorpayOrderId: data.id, keyId: cfg.razorpay.keyId, orderId, amount: total, currency: cfg.razorpay.currency });
  }));
  return router;
}
