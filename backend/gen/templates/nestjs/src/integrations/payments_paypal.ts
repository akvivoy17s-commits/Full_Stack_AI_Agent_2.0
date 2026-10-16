// PayPal Orders v2, called with fetch (no SDK). The amount comes from the stored order. After the buyer approves, the verified
// CHECKOUT.ORDER.APPROVED webhook captures the payment on the server, and PAYMENT.CAPTURE.COMPLETED marks the order paid.
import { Router, raw } from 'express';
import type { Request, RequestHandler } from 'express';
import { HttpError } from '../common/http-error';
import { cfg } from '../config';
import { Db } from '../db/db';
import * as pay from './pay';

type Json = Record<string, any>;   // eslint-disable-line @typescript-eslint/no-explicit-any
const base = (): string => (cfg.paypal.env === 'live' ? 'https://api-m.paypal.com' : 'https://api-m.sandbox.paypal.com');
const configured = (): boolean => !pay.placeholder(cfg.paypal.clientId) && !pay.placeholder(cfg.paypal.clientSecret);
let token = { value: '', exp: 0 };

async function accessToken(): Promise<string> {
  if (token.value && token.exp > Date.now() + 30000) return token.value;
  let r: Response;
  try {
    r = await fetch(`${base()}/v1/oauth2/token`, {
      method: 'POST', body: 'grant_type=client_credentials', signal: AbortSignal.timeout(10000),
      headers: { Authorization: 'Basic ' + Buffer.from(`${cfg.paypal.clientId}:${cfg.paypal.clientSecret}`).toString('base64'), 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  } catch { throw pay.unreachable(); }
  const data = (await r.json().catch(() => ({}))) as Json;
  if (!r.ok || !data.access_token) throw pay.rejected();
  token = { value: data.access_token, exp: Date.now() + Number(data.expires_in || 300) * 1000 };
  return token.value;
}

async function api(path: string, body: Json, requestId?: string): Promise<{ ok: boolean; data: Json }> {
  const t = await accessToken();
  let r: Response;
  try {
    r = await fetch(base() + path, {
      method: 'POST', signal: AbortSignal.timeout(10000), body: JSON.stringify(body),
      headers: { Authorization: `Bearer ${t}`, 'Content-Type': 'application/json', ...(requestId ? { 'PayPal-Request-Id': requestId } : {}) },
    });
  } catch { throw pay.unreachable(); }
  return { ok: r.ok, data: (await r.json().catch(() => ({}))) as Json };
}

// PayPal verifies its own signature (and the certificate URL) for us; we only forward the headers and the parsed event.
async function verified(headers: Request['headers'], event: Json): Promise<boolean> {
  const h = (k: string): string | undefined => (typeof headers[k] === 'string' ? (headers[k] as string) : undefined);
  if (!h('paypal-transmission-id') || !h('paypal-transmission-sig') || !h('paypal-cert-url')) return false;
  const { ok, data } = await api('/v1/notifications/verify-webhook-signature', {
    auth_algo: h('paypal-auth-algo'), cert_url: h('paypal-cert-url'), transmission_id: h('paypal-transmission-id'),
    transmission_sig: h('paypal-transmission-sig'), transmission_time: h('paypal-transmission-time'), webhook_id: cfg.paypal.webhookId, webhook_event: event,
  });
  return ok && data.verification_status === 'SUCCESS';
}

const minorOf = (v: unknown): number => Math.round(Number(v) * 100);

// Mounted BEFORE the JSON parser: the raw body is parsed here.
export function webhook(db: Db): RequestHandler[] {
  return [raw({ type: 'application/json', limit: '256kb' }), pay.wrap(async (req: Request, res) => {
    if (!configured() || pay.placeholder(cfg.paypal.webhookId)) throw pay.unavailable();
    if (!Buffer.isBuffer(req.body)) throw new HttpError(400, 'invalid_signature', 'Invalid webhook signature');
    const event = pay.parseJson(req.body);
    if (!(await verified(req.headers, event))) throw new HttpError(400, 'invalid_signature', 'Invalid webhook signature');
    const r: Json = event.resource || {};
    const cur = cfg.paypal.currency.toUpperCase();
    if (event.event_type === 'PAYMENT.CAPTURE.COMPLETED' && r.amount?.currency_code === cur && r.status === 'COMPLETED') {
      await pay.markPaid(db, db.parseId(r.custom_id), minorOf(r.amount.value));
    } else if (event.event_type === 'CHECKOUT.ORDER.APPROVED' && r.id) {
      // Capture only an order we created: same stored order, same amount, still pending. PayPal-Request-Id makes the capture idempotent.
      const unit: Json = (r.purchase_units || [])[0] || {};
      const orderId = db.parseId(unit.custom_id);
      const order = orderId == null ? null : await db.findOne('Order', { id: orderId }, { raw: true });
      if (order && order.status === 'pending' && unit.amount?.currency_code === cur && minorOf(unit.amount.value) === minorOf(order.total)) {
        await api(`/v2/checkout/orders/${encodeURIComponent(r.id)}/capture`, {}, `capture-${r.id}`);
      }
    }
    res.json({ received: true });
  })];
}

export function intent(db: Db): Router {
  const router = Router();
  router.post('/intent', pay.signedIn, pay.wrap(async (req, res) => {
    if (!configured()) throw pay.unavailable();
    const { orderId, minor, total } = await pay.payableOrder(db, req);
    const { ok, data } = await api('/v2/checkout/orders', {
      intent: 'CAPTURE',
      purchase_units: [{ custom_id: String(orderId), amount: { currency_code: cfg.paypal.currency.toUpperCase(), value: (minor / 100).toFixed(2) } }],
    }, `order-${orderId}-${minor}`);
    if (!ok || !data.id) throw pay.rejected();
    const link = ((data.links || []) as Json[]).find((l) => l.rel === 'payer-action' || l.rel === 'approve');
    res.status(201).json({ paypalOrderId: data.id, approveUrl: link ? link.href : null, orderId, amount: total, currency: cfg.paypal.currency });
  }));
  return router;
}
