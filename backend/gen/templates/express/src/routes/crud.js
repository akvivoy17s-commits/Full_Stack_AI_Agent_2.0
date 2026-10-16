const express = require('express');
const schema = require('../schema');
const { HttpError, wrap } = require('../lib/http');
const { guard, isAdmin } = require('../middleware/auth');
const { publicLimiter } = require('../middleware/rateLimit');
const { validateBody, parseList } = require('../lib/validate');

const E = schema.entities;
const has = (e, n) => e.fields.some((f) => f.name === n);
const notFound = () => new HttpError(404, 'not_found', 'Record not found');

// Generic, spec-driven CRUD. Access is enforced here on the server: public | user | owner | admin.
module.exports = function crud(db) {
  const router = express.Router();

  // Owner-scoped entities only expose the caller's own records to non-admins.
  const scope = (e, req) => (e.read === 'owner' && e.ownerField && !isAdmin(req.user) ? { [e.ownerField]: db.parseId(req.user.id) } : {});
  const mine = (e, rec, req, level) => level !== 'owner' || !e.ownerField || isAdmin(req.user) || String(rec[e.ownerField]) === String(req.user.id);

  async function checkRefs(e, data) {
    const errors = {};
    for (const f of e.fields) {
      if (f.type === 'ref' && data[f.name] != null && !(await db.get(f.ref, data[f.name]))) errors[f.name] = 'refers to a record that does not exist';
    }
    if (Object.keys(errors).length) throw new HttpError(400, 'validation_failed', 'Invalid input', errors);
  }

  async function load(e, req, level) {
    const id = db.parseId(req.params.id);
    const rec = id == null ? null : await db.get(e.name, id);
    if (!rec || !mine(e, rec, req, level)) throw notFound(); // 404, not 403: do not reveal other users' records
    return rec;
  }

  for (const e of Object.values(E)) {
    if (e.internal || !e.ops.length) continue;
    const base = '/' + e.path;
    const wr = [...(e.write === 'public' ? [publicLimiter] : []), ...guard(e.write)];

    if (e.ops.includes('list')) {
      router.get(base, ...guard(e.read), wrap(async (req, res) => {
        const o = parseList(e, req.query);
        const r = await db.list(e.name, { ...o, where: scope(e, req) });
        res.json({ data: r.rows, page: o.page, limit: o.limit, total: r.total });
      }));
    }
    if (e.ops.includes('get')) {
      router.get(base + '/:id', ...guard(e.read), wrap(async (req, res) => res.json(await load(e, req, e.read))));
    }
    if (e.ops.includes('create')) {
      router.post(base, ...wr, wrap(async (req, res) => {
        const data = validateBody(e, req.body, false);
        await checkRefs(e, data);
        if (e.ownerField && req.user) data[e.ownerField] = db.parseId(req.user.id);
        if (has(e, 'created_at')) data.created_at = new Date().toISOString();
        res.status(201).json(await db.create(e.name, data));
      }));
    }
    if (e.ops.includes('update')) {
      router.put(base + '/:id', ...wr, wrap(async (req, res) => {
        await load(e, req, e.write);
        const data = validateBody(e, req.body, true);
        await checkRefs(e, data);
        if (has(e, 'updated_at')) data.updated_at = new Date().toISOString();
        res.json(await db.update(e.name, db.parseId(req.params.id), data));
      }));
    }
    if (e.ops.includes('delete')) {
      router.delete(base + '/:id', ...wr, wrap(async (req, res) => {
        await load(e, req, e.write);
        await db.remove(e.name, db.parseId(req.params.id));
        res.status(204).end();
      }));
    }
  }
  return router;
};
