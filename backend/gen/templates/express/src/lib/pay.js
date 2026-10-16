const schema = require('../schema');
const { HttpError } = require('./http');

// Shared by the Razorpay and PayPal routes. The amount always comes from the caller's own stored order, never from the client.
async function payableOrder(db, req) {
  const userId = db.parseId(req.user && req.user.id);
  const orderId = db.parseId(req.body && req.body.orderId);
  if (userId == null || orderId == null) throw new HttpError(400, 'validation_failed', 'orderId is required', { orderId: 'required' });
  const Order = schema.entities.Order;
  const order = await db.knex(Order.table).where({ id: orderId, user_id: userId }).first();
  if (!order) throw new HttpError(404, 'not_found', 'Order not found');
  if (order.status !== 'pending') throw new HttpError(409, 'order_not_payable', 'This order is not awaiting payment');
  const minor = Math.round(Number(order.total) * 100);
  if (!Number.isSafeInteger(minor) || minor < 50) throw new HttpError(409, 'invalid_amount', 'This order total cannot be charged');
  return { orderId, minor, total: minor / 100 };
}

// Idempotent: only a pending order whose total (in minor units) equals the amount actually paid is marked paid.
async function markPaid(db, orderId, paidMinor) {
  if (orderId == null || !Number.isSafeInteger(paidMinor)) return false;
  const Order = schema.entities.Order;
  const order = await db.knex(Order.table).where({ id: orderId }).first();
  if (!order || order.status !== 'pending' || Math.round(Number(order.total) * 100) !== paidMinor) return false;
  await db.knex(Order.table).where({ id: orderId, status: 'pending' }).update({ status: 'paid' });
  require('./events').emit('change', { entity: 'Order', op: 'update' });
  if (schema.integrations.cache) require('./cache').invalidate();
  return true;
}

function parseJson(raw) {
  try { return JSON.parse(raw.toString('utf8')); } catch (e) { throw new HttpError(400, 'invalid_json', 'Request body is not valid JSON'); }
}

const unreachable = () => new HttpError(502, 'payment_provider_unreachable', 'The payment provider could not be reached');
const rejected = () => new HttpError(502, 'payment_provider_error', 'The payment provider rejected the request');
const unavailable = () => new HttpError(503, 'payments_unavailable', 'Payments are not configured');
const placeholder = (v) => !v || String(v).startsWith('your-');

module.exports = { payableOrder, markPaid, parseJson, unreachable, rejected, unavailable, placeholder };
