// Shared by the Stripe, Razorpay and PayPal routers. The amount always comes from the caller's own stored order, never from the client.
import type { NextFunction, Request, RequestHandler, Response } from 'express';
import * as jwt from 'jsonwebtoken';
import { HttpError } from '../common/http-error';
import { cfg } from '../config';
import { Db } from '../db/db';
import { changed } from './notify';

export const wrap = (fn: (req: Request, res: Response) => Promise<void>): RequestHandler => (req: Request, res: Response, next: NextFunction) => {
  fn(req, res).catch(next);       // errors reach Nest's global exception filter: same { error } envelope as the rest of the API
};

// Same rule as the guard on the other routes: a valid HS256 access token; sets req.user.
export function signedIn(req: Request, _res: Response, next: NextFunction): void {
  const m = /^Bearer (.+)$/i.exec(req.headers.authorization || '');
  if (!m) return next(new HttpError(401, 'unauthorized', 'Authentication required'));
  try {
    const p = jwt.verify(m[1], cfg.jwt.key, { algorithms: ['HS256'] }) as { sub: string; role: string };
    (req as Request & { user?: { id: string; role: string } }).user = { id: String(p.sub), role: p.role };
    next();
  } catch {
    next(new HttpError(401, 'invalid_token', 'Invalid or expired token'));
  }
}

export async function payableOrder(db: Db, req: Request): Promise<{ orderId: number; minor: number; total: number }> {
  const user = (req as Request & { user?: { id: string } }).user;
  const userId = db.parseId(user?.id);
  const orderId = db.parseId((req.body as { orderId?: unknown } | undefined)?.orderId);
  if (userId == null || typeof orderId !== 'number') throw new HttpError(400, 'validation_failed', 'orderId is required', { orderId: 'required' });
  const order = await db.findOne('Order', { id: orderId, user_id: userId }, { raw: true });
  if (!order) throw new HttpError(404, 'not_found', 'Order not found');
  if (order.status !== 'pending') throw new HttpError(409, 'order_not_payable', 'This order is not awaiting payment');
  const minor = Math.round(Number(order.total) * 100);
  if (!Number.isSafeInteger(minor) || minor < 50) throw new HttpError(409, 'invalid_amount', 'This order total cannot be charged');
  return { orderId, minor, total: minor / 100 };
}

// Idempotent: only a pending order whose total (in minor units) equals the amount actually paid is marked paid.
export async function markPaid(db: Db, orderId: number | string | null, paidMinor: unknown): Promise<boolean> {
  if (typeof orderId !== 'number' || typeof paidMinor !== 'number' || !Number.isSafeInteger(paidMinor) || !db.updateWhere) return false;
  const order = await db.findOne('Order', { id: orderId }, { raw: true });
  if (!order || order.status !== 'pending' || Math.round(Number(order.total) * 100) !== paidMinor) return false;
  const n = await db.updateWhere('Order', { id: orderId, status: 'pending' }, { status: 'paid' });   // conditional: a replay or a race changes nothing
  if (n > 0) await changed(['Order']);
  return n > 0;
}

export function parseJson(raw: Buffer): Record<string, any> {   // eslint-disable-line @typescript-eslint/no-explicit-any
  try {
    const v = JSON.parse(raw.toString('utf8'));
    if (v && typeof v === 'object' && !Array.isArray(v)) return v;
  } catch { /* fall through */ }
  throw new HttpError(400, 'invalid_json', 'Request body is not valid JSON');
}

export const unreachable = (): HttpError => new HttpError(502, 'payment_provider_unreachable', 'The payment provider could not be reached');
export const rejected = (): HttpError => new HttpError(502, 'payment_provider_error', 'The payment provider rejected the request');
export const unavailable = (): HttpError => new HttpError(503, 'payments_unavailable', 'Payments are not configured');
export const placeholder = (v?: string): boolean => !v || String(v).startsWith('your-');
