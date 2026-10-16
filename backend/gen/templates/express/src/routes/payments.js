const express = require('express');
const crypto = require('crypto');
const cfg = require('../config');
const schema = require('../schema');
const { HttpError, wrap } = require('../lib/http');
const { guard } = require('../middleware/auth');

// Stripe, called with fetch (no SDK). The amount always comes from the stored order, never from the client.
const TOLERANCE_SEC = 300;

function verifySignature(raw, header, secret) {
  const parts = Object.fromEntries(String(header || '').split(',').map((p) => p.trim().split('=')).filter((p) => p.length === 2));
  const ts = Number(parts.t);
  if (!Number.isInteger(ts) || Math.abs(Date.now() / 1000 - ts) > TOLERANCE_SEC || !parts.v1) return false;
  const want = crypto.createHmac('sha256', secret).update(`${ts}.`).update(raw).digest();
  const got = Buffer.from(parts.v1, 'hex');
  return got.length === want.length && crypto.timingSafeEqual(got, want);
}

// Mounted BEFORE express.json(): the signature is computed over the exact raw bytes.
function webhook(db) {
  return [express.raw({ type: 'application/json', limit: '256kb' }), wrap(async (req, res) => {
    if (!cfg.stripe.webhookSecret) throw new HttpError(503, 'payments_unavailable', 'Payments are not configured');
    if (!Buffer.isBuffer(req.body) || !verifySignature(req.body, req.headers['stripe-signature'], cfg.stripe.webhookSecret)) {
      throw new HttpError(400, 'invalid_signature', 'Invalid webhook signature');
    }
    let event;
    try { event = JSON.parse(req.body.toString('utf8')); } catch (e) { throw new HttpError(400, 'invalid_json', 'Request body is not valid JSON'); }
    const obj = event && event.data && event.data.object;
    const orderId = obj && obj.metadata && db.parseId(obj.metadata.order_id);
    if (event.type === 'payment_intent.succeeded' && orderId != null) {
      // Idempotent: only a pending order whose total matches the amount paid is marked paid.
      const Order = schema.entities.Order;
      const order = await db.knex(Order.table).where({ id: orderId }).first();
      if (order && order.status === 'pending' && Math.round(Number(order.total) * 100) === obj.amount_received) {
        await db.knex(Order.table).where({ id: orderId, status: 'pending' }).update({ status: 'paid' });
        require('../lib/events').emit('change', { entity: 'Order', op: 'update' });
        if (schema.integrations.cache) require('../lib/cache').invalidate();
      }
    }
    res.json({ received: true });
  })];
}

function intent(db) {
  const router = express.Router();
  router.post('/intent', ...guard('user'), wrap(async (req, res) => {
    if (!cfg.stripe.secretKey || cfg.stripe.secretKey.startsWith('your-')) throw new HttpError(503, 'payments_unavailable', 'Payments are not configured');
    const userId = db.parseId(req.user && req.user.id);
    const orderId = db.parseId(req.body && req.body.orderId);
    if (userId == null || orderId == null) throw new HttpError(400, 'validation_failed', 'orderId is required', { orderId: 'required' });
    const Order = schema.entities.Order;
    const order = await db.knex(Order.table).where({ id: orderId, user_id: userId }).first();
    if (!order) throw new HttpError(404, 'not_found', 'Order not found');
    if (order.status !== 'pending') throw new HttpError(409, 'order_not_payable', 'This order is not awaiting payment');
    const cents = Math.round(Number(order.total) * 100);
    if (!Number.isSafeInteger(cents) || cents < 50) throw new HttpError(409, 'invalid_amount', 'This order total cannot be charged');
    const form = new URLSearchParams({ amount: String(cents), currency: cfg.stripe.currency, 'metadata[order_id]': String(orderId), 'automatic_payment_methods[enabled]': 'true' });
    let r;
    try {
      r = await fetch('https://api.stripe.com/v1/payment_intents', {
        method: 'POST', body: form, signal: AbortSignal.timeout(10000),
        headers: { Authorization: `Bearer ${cfg.stripe.secretKey}`, 'Content-Type': 'application/x-www-form-urlencoded', 'Idempotency-Key': `order-${orderId}-${cents}` },
      });
    } catch (e) { throw new HttpError(502, 'payment_provider_unreachable', 'The payment provider could not be reached'); }
    const data = await r.json().catch(() => ({}));
    if (!r.ok || !data.client_secret) throw new HttpError(502, 'payment_provider_error', 'The payment provider rejected the request');
    res.status(201).json({ clientSecret: data.client_secret, orderId, amount: cents / 100, currency: cfg.stripe.currency });
  }));
  return router;
}

module.exports = { intent, webhook, verifySignature };
