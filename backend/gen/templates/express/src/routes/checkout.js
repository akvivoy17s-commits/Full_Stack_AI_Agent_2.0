const express = require('express');
const schema = require('../schema');
const { HttpError, wrap } = require('../lib/http');
const { guard } = require('../middleware/auth');

// Transactional checkout. The server fetches prices/stock; client-provided totals are never trusted.
module.exports = function checkout(db) {
  const router = express.Router();
  const Product = schema.entities.Product;
  const Order = schema.entities.Order;
  const OrderItem = schema.entities.OrderItem;
  const has = (e, field) => e.fields.some((f) => f.name === field);

  router.post('/', ...guard('user'), wrap(async (req, res) => {
    if (!db || !db.knex || !schema.checkout) {
      throw new HttpError(503, 'checkout_unavailable', 'Transactional checkout is not configured for this database');
    }
    const userId = db.parseId(req.user && req.user.id);
    if (userId == null) throw new HttpError(401, 'unauthorized', 'A valid signed-in user is required');

    const input = req.body && req.body.items;
    if (!Array.isArray(input) || input.length < 1 || input.length > 50) {
      throw new HttpError(400, 'validation_failed', 'items must be an array containing 1 to 50 items', { items: 'invalid_item_count' });
    }

    const quantities = new Map();
    for (const line of input) {
      if (!line || typeof line !== 'object' || Array.isArray(line)) {
        throw new HttpError(400, 'validation_failed', 'Each item must contain productId and quantity');
      }
      const rawId = line.productId ?? line.product_id;
      const productId = db.parseId(rawId);
      const quantity = line.quantity;
      if (productId == null || !Number.isInteger(quantity) || quantity < 1 || quantity > 99) {
        throw new HttpError(400, 'validation_failed', 'Invalid productId or quantity', { item: 'invalid_product_or_quantity' });
      }
      quantities.set(productId, (quantities.get(productId) || 0) + quantity);
      if (quantities.get(productId) > 99) {
        throw new HttpError(400, 'validation_failed', 'A product quantity cannot exceed 99');
      }
    }

    const result = await db.knex.transaction(async (trx) => {
      let q = trx(Product.table).select('*').whereIn('id', [...quantities.keys()]);
      if (db.kind !== 'sqlite') q = q.forUpdate();
      const rows = await q;
      const byId = new Map(rows.map((p) => [Number(p.id), p]));
      if (byId.size !== quantities.size) throw new HttpError(400, 'invalid_product', 'One or more products do not exist');

      const lines = [];
      let totalCents = 0;
      for (const [productId, quantity] of quantities) {
        const product = byId.get(Number(productId));
        if (has(Product, 'active') && !(product.active === true || product.active === 1 || product.active === '1')) {
          throw new HttpError(409, 'product_unavailable', 'One or more products are no longer available');
        }
        const stock = Number(product.stock);
        const price = Number(product.price);
        if (!Number.isInteger(stock) || stock < quantity) {
          throw new HttpError(409, 'insufficient_stock', 'There is not enough stock for one or more products');
        }
        if (!Number.isFinite(price) || price < 0) {
          throw new HttpError(409, 'invalid_price', 'A product has an invalid server-side price');
        }
        const cents = Math.round(price * 100);
        if (!Number.isSafeInteger(cents * quantity) || totalCents + cents * quantity > Number.MAX_SAFE_INTEGER) {
          throw new HttpError(400, 'total_too_large', 'Order total is too large');
        }
        totalCents += cents * quantity;
        lines.push({ product, productId, quantity, cents });
      }

      const now = new Date().toISOString();
      const orderData = {};
      if (has(Order, 'user_id')) orderData.user_id = userId;
      if (has(Order, 'status')) orderData.status = 'pending';
      if (has(Order, 'total')) orderData.total = totalCents / 100;
      if (has(Order, 'created_at')) orderData.created_at = now;
      let ins = trx(Order.table).insert(orderData);
      if (db.kind === 'postgresql') ins = ins.returning('id');
      const inserted = await ins;
      const orderId = Number(typeof inserted[0] === 'object' ? inserted[0].id : inserted[0]);
      if (!Number.isSafeInteger(orderId) || orderId < 1) throw new HttpError(500, 'checkout_failed', 'Could not create the order');

      const itemRows = lines.map(({ productId, quantity, cents }) => {
        const row = {};
        if (has(OrderItem, 'order_id')) row.order_id = orderId;
        if (has(OrderItem, 'product_id')) row.product_id = productId;
        if (has(OrderItem, 'user_id')) row.user_id = userId;
        if (has(OrderItem, 'quantity')) row.quantity = quantity;
        if (has(OrderItem, 'unit_price')) row.unit_price = cents / 100;
        return row;
      });

      // Conditional stock updates protect against overselling even when requests race.
      for (const { productId, quantity } of lines) {
        const changed = await trx(Product.table).where({ id: productId }).where('stock', '>=', quantity).decrement('stock', quantity);
        if (Number(changed) !== 1) throw new HttpError(409, 'insufficient_stock', 'Stock changed during checkout; please retry');
      }
      await trx(OrderItem.table).insert(itemRows);
      return { orderId, total: totalCents / 100, items: itemRows.length, status: 'pending', created_at: now };
    });

    res.status(201).json({ order: result });
  }));

  return router;
};
