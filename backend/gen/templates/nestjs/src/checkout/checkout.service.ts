import { Inject, Injectable } from '@nestjs/common';
import { HttpError } from '../common/http-error';
import { AuthUser } from '../common/types';
import { DB, Db, Row } from '../db/db';
import { changed } from '../integrations/notify';
import { SCHEMA } from '../schema';

const has = (entity: string, field: string): boolean => SCHEMA.entities[entity].fields.some((f) => f.name === field);
const fail = (status: number, code: string, message: string, details?: Record<string, string>): HttpError => new HttpError(status, code, message, details);

// Transactional checkout. The server reads prices and stock; client-provided totals are never trusted.
@Injectable()
export class CheckoutService {
  constructor(@Inject(DB) private readonly db: Db) {}

  private items(input: unknown): Map<number, number> {
    if (!Array.isArray(input) || input.length < 1 || input.length > 50) throw fail(400, 'validation_failed', 'items must be an array containing 1 to 50 items', { items: 'invalid_item_count' });
    const qty = new Map<number, number>();
    for (const line of input) {
      if (!line || typeof line !== 'object' || Array.isArray(line)) throw fail(400, 'validation_failed', 'Each item must contain productId and quantity');
      const l = line as Record<string, unknown>;
      const id = this.db.parseId(l.productId ?? l.product_id);
      const n = l.quantity;
      if (id == null || typeof id !== 'number' || typeof n !== 'number' || !Number.isInteger(n) || n < 1 || n > 99) throw fail(400, 'validation_failed', 'Invalid productId or quantity', { item: 'invalid_product_or_quantity' });
      const sum = (qty.get(id) || 0) + n;
      if (sum > 99) throw fail(400, 'validation_failed', 'A product quantity cannot exceed 99');
      qty.set(id, sum);
    }
    return qty;
  }

  async create(user: AuthUser | undefined, body: unknown): Promise<{ order: Row }> {
    const db = this.db;
    if (!db.tx) throw fail(503, 'checkout_unavailable', 'Transactional checkout is not configured for this database');
    const userId = db.parseId(user?.id);
    if (userId == null) throw fail(401, 'unauthorized', 'A valid signed-in user is required');
    const qty = this.items((body as { items?: unknown } | null)?.items);
    const now = new Date();

    const order = await db.tx(async (t) => {
      const rows = new Map((await t.lock('Product', [...qty.keys()])).map((p) => [Number(p.id), p]));
      if (rows.size !== qty.size) throw fail(400, 'invalid_product', 'One or more products do not exist');
      const lines: { id: number; n: number; cents: number }[] = [];
      let total = 0;
      for (const [id, n] of qty) {
        const p = rows.get(id) as Row;
        if (has('Product', 'active') && !(p.active === true || p.active === 1 || p.active === '1')) throw fail(409, 'product_unavailable', 'One or more products are no longer available');
        const stock = Number(p.stock);
        const price = Number(p.price);
        if (!Number.isInteger(stock) || stock < n) throw fail(409, 'insufficient_stock', 'There is not enough stock for one or more products');
        if (p.price == null || !Number.isFinite(price) || price < 0) throw fail(409, 'invalid_price', 'A product has an invalid server-side price');
        const cents = Math.round(price * 100);
        total += cents * n;
        if (!Number.isSafeInteger(total)) throw fail(400, 'total_too_large', 'Order total is too large');
        lines.push({ id, n, cents });
      }
      const od: Row = {};
      if (has('Order', 'user_id')) od.user_id = userId;
      if (has('Order', 'status')) od.status = 'pending';
      if (has('Order', 'total')) od.total = total / 100;
      if (has('Order', 'created_at')) od.created_at = now.toISOString();
      const orderId = await t.insert('Order', od);
      if (!Number.isSafeInteger(orderId) || orderId < 1) throw fail(500, 'checkout_failed', 'Could not create the order');
      // Conditional stock updates: no overselling even when requests race.
      for (const l of lines) if (!(await t.take('Product', l.id, 'stock', l.n))) throw fail(409, 'insufficient_stock', 'Stock changed during checkout; please retry');
      for (const l of lines) {
        const r: Row = {};
        if (has('OrderItem', 'order_id')) r.order_id = orderId;
        if (has('OrderItem', 'product_id')) r.product_id = l.id;
        if (has('OrderItem', 'user_id')) r.user_id = userId;
        if (has('OrderItem', 'quantity')) r.quantity = l.n;
        if (has('OrderItem', 'unit_price')) r.unit_price = l.cents / 100;
        await t.insert('OrderItem', r);
      }
      return { orderId, total: total / 100, items: lines.length, status: 'pending', created_at: now.toISOString() };
    });
    await changed(['Order', 'Product', 'OrderItem']);
    return { order };
  }
}
