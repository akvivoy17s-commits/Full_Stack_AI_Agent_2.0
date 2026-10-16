// Express-level middleware on /api: caches GET reads of CRUD resources per caller; after every successful write it invalidates
// the cache and announces { entity, op } to WebSocket clients (metadata only, never record data).
import { createHash } from 'crypto';
import type { NextFunction, Request, Response } from 'express';
import { SCHEMA } from '../schema';
import * as cache from './cache';
import { events } from './events';

const byPath = new Map(Object.values(SCHEMA.entities).filter((e) => !e.internal).map((e) => [e.path, e.name]));
const OPS: Record<string, string> = { POST: 'create', PUT: 'update', DELETE: 'delete' };

export function live() {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    const entity = byPath.get(req.path.split('/')[1]);
    if (!entity) return next();
    if (req.method === 'GET' && SCHEMA.integrations.cache) {
      const who = createHash('sha256').update(req.headers.authorization || '').digest('hex').slice(0, 16);
      const key = `r:${await cache.version()}:${who}:${req.originalUrl}`;
      const hit = await cache.get(key);
      if (hit) { res.set('X-Cache', 'HIT'); res.status(200).json(hit); return; }
      res.set('X-Cache', 'MISS');
      const send = res.json.bind(res);
      res.json = (body: unknown) => { if (res.statusCode === 200) void cache.set(key, body); return send(body); };
    } else if (OPS[req.method]) {
      res.on('finish', () => {
        if (res.statusCode >= 400) return;
        if (SCHEMA.integrations.cache) void cache.invalidate();
        events.emit('change', { entity, op: OPS[req.method] });
      });
    }
    return next();
  };
}
