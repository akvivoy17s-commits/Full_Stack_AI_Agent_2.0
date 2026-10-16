const express = require('express');
const crypto = require('crypto');
const cfg = require('../config');
const { HttpError, wrap } = require('../lib/http');
const { guard } = require('../middleware/auth');
const pay = require('../lib/pay');

// Razorpay, called with fetch (no SDK). The amount comes from the stored order, in paise.
function verifySignature(raw, header, secret) {
  if (!secret || typeof header !== 'string' || !/^[0-9a-f]{64}$/i.test(header)) return false;
  const want = crypto.createHmac('sha256', secret).update(raw).digest();
  const got = Buffer.from(header, 'hex');
  return got.length === want.length && crypto.timingSafeEqual(got, want);
}

// Mounted BEFORE express.json(): the signature is computed over the exact raw bytes.
function webhook(db) {
  return [express.raw({ type: 'application/json', limit: '256kb' }), wrap(async (req, res) => {
    if (pay.placeholder(cfg.razorpay.webhookSecret)) throw pay.unavailable();
    if (!Buffer.isBuffer(req.body) || !verifySignature(req.body, req.headers['x-razorpay-signature'], cfg.razorpay.webhookSecret)) {
      throw new HttpError(400, 'invalid_signature', 'Invalid webhook signature');
    }
    const event = pay.parseJson(req.body);
    const p = event && event.payload && event.payload.payment && event.payload.payment.entity;
    if (event.event === 'payment.captured' && p && p.notes && String(p.currency).toLowerCase() === cfg.razorpay.currency) {
      await pay.markPaid(db, db.parseId(p.notes.order_id), p.amount);
    }
    res.json({ received: true });
  })];
}

function intent(db) {
  const router = express.Router();
  router.post('/intent', ...guard('user'), wrap(async (req, res) => {
    if (pay.placeholder(cfg.razorpay.keyId) || pay.placeholder(cfg.razorpay.keySecret)) throw pay.unavailable();
    const { orderId, minor, total } = await pay.payableOrder(db, req);
    let r;
    try {
      r = await fetch('https://api.razorpay.com/v1/orders', {
        method: 'POST', signal: AbortSignal.timeout(10000),
        headers: { Authorization: 'Basic ' + Buffer.from(`${cfg.razorpay.keyId}:${cfg.razorpay.keySecret}`).toString('base64'), 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: minor, currency: cfg.razorpay.currency.toUpperCase(), receipt: `order-${orderId}`, notes: { order_id: String(orderId) } }),
      });
    } catch (e) { throw pay.unreachable(); }
    const data = await r.json().catch(() => ({}));
    if (!r.ok || !data.id) throw pay.rejected();
    // keyId is public by design (the checkout widget needs it); the secret never leaves the server.
    res.status(201).json({ razorpayOrderId: data.id, keyId: cfg.razorpay.keyId, orderId, amount: total, currency: cfg.razorpay.currency });
  }));
  return router;
}

module.exports = { intent, webhook, verifySignature };
