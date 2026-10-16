// Read cache: Redis when REDIS_URL is set and reachable, otherwise a small in-memory TTL map. A cache failure never fails a request.
const cfg = require('../config');
const mem = new Map();
let memVer = 1;
let redis = null;
let ready = null;

async function client() {
  if (!cfg.redisUrl) return null;
  if (!ready) {
    ready = (async () => {
      try {
        const c = require('redis').createClient({ url: cfg.redisUrl, socket: { reconnectStrategy: false } });
        c.on('error', () => {});
        await c.connect();
        redis = c;
      } catch (e) {
        redis = null;
        console.warn('Redis unavailable, using the in-memory cache');
      }
    })();
  }
  await ready;
  return redis;
}

async function version() {
  try { const r = await client(); if (r) return (await r.get('cache:ver')) || '0'; } catch (e) { /* fall through */ }
  return String(memVer);
}

async function get(key) {
  try {
    const r = await client();
    if (r) { const v = await r.get(key); return v ? JSON.parse(v) : null; }
  } catch (e) { return null; }
  const hit = mem.get(key);
  if (!hit || hit.exp < Date.now()) { mem.delete(key); return null; }
  return hit.value;
}

async function set(key, value, ttlSec) {
  try {
    const r = await client();
    if (r) { await r.set(key, JSON.stringify(value), { EX: ttlSec }); return; }
  } catch (e) { return; }
  if (mem.size >= 500) mem.delete(mem.keys().next().value);
  mem.set(key, { value, exp: Date.now() + ttlSec * 1000 });
}

// Any successful write bumps the version, so every cached read becomes unreachable at once (entries then expire by TTL).
async function invalidate() {
  memVer += 1;
  try { const r = await client(); if (r) await r.incr('cache:ver'); } catch (e) { /* ignore */ }
}

async function close() { if (redis) { try { await redis.quit(); } catch (e) { /* ignore */ } } }

module.exports = { get, set, version, invalidate, close, client };
