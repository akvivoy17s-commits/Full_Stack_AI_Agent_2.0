// Mounted on /api when cache or WebSocket is enabled: caches GET reads of CRUD resources per caller, and on every
// successful write invalidates the cache and announces { entity, op } to WebSocket clients (metadata only, never record data).
const crypto = require('crypto');
const cfg = require('../config');
const schema = require('../schema');
const cache = require('../lib/cache');
const events = require('../lib/events');

const byPath = new Map(Object.values(schema.entities).filter((e) => !e.internal).map((e) => [e.path, e.name]));
const OPS = { POST: 'create', PUT: 'update', DELETE: 'delete' };

module.exports = function live() {
  return async (req, res, next) => {
    const entity = byPath.get(req.path.split('/')[1]);
    if (!entity) return next();
    if (req.method === 'GET' && schema.integrations.cache) {
      const who = crypto.createHash('sha256').update(req.headers.authorization || '').digest('hex').slice(0, 16);
      const key = `r:${await cache.version()}:${who}:${req.originalUrl}`;
      const hit = await cache.get(key);
      if (hit) { res.set('X-Cache', 'HIT'); return res.status(200).json(hit); }
      res.set('X-Cache', 'MISS');
      const json = res.json.bind(res);
      res.json = (body) => { if (res.statusCode === 200) cache.set(key, body, cfg.cacheTtlSec); return json(body); };
    } else if (OPS[req.method]) {
      res.on('finish', () => {
        if (res.statusCode >= 400) return;
        if (schema.integrations.cache) cache.invalidate();
        events.emit('change', { entity, op: OPS[req.method] });
      });
    }
    return next();
  };
};
