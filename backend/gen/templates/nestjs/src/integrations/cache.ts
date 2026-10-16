// Read cache: Redis when REDIS_URL is set and reachable, otherwise a small in-memory TTL map. A cache failure never fails a request.
import { cfg } from '../config';

/* eslint-disable @typescript-eslint/no-explicit-any */
const mem = new Map<string, { value: unknown; exp: number }>();
let memVer = 1;
let redis: any = null;
let ready: Promise<void> | null = null;

async function client(): Promise<any> {
  if (!cfg.redisUrl) return null;
  if (!ready) {
    ready = (async () => {
      try {
        const c = require('redis').createClient({ url: cfg.redisUrl, socket: { reconnectStrategy: false } });
        c.on('error', () => undefined);
        await c.connect();
        redis = c;
      } catch {
        redis = null;
        console.warn('Redis unavailable, using the in-memory cache');
      }
    })();
  }
  await ready;
  return redis;
}

export const backend = async (): Promise<string> => ((await client()) ? 'redis' : 'memory');

export async function version(): Promise<string> {
  try { const r = await client(); if (r) return (await r.get('cache:ver')) || '0'; } catch { /* use memory */ }
  return String(memVer);
}

export async function get(key: string): Promise<unknown> {
  try {
    const r = await client();
    if (r) { const v = await r.get(key); return v ? JSON.parse(v) : null; }
  } catch { return null; }
  const hit = mem.get(key);
  if (!hit || hit.exp < Date.now()) { mem.delete(key); return null; }
  return hit.value;
}

export async function set(key: string, value: unknown): Promise<void> {
  try {
    const r = await client();
    if (r) { await r.set(key, JSON.stringify(value), { EX: cfg.cacheTtlSec }); return; }
  } catch { return; }
  if (mem.size >= 500) mem.delete(mem.keys().next().value as string);
  mem.set(key, { value, exp: Date.now() + cfg.cacheTtlSec * 1000 });
}

// Any successful write bumps the version, so every cached read becomes unreachable at once (entries then expire by TTL).
export async function invalidate(): Promise<void> {
  memVer += 1;
  try { const r = await client(); if (r) await r.incr('cache:ver'); } catch { /* ignore */ }
}

export async function close(): Promise<void> {
  if (redis) { try { await redis.quit(); } catch { /* ignore */ } }
}
