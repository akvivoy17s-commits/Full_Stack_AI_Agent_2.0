import { SCHEMA } from '../schema';
import { HttpError } from './http-error';
import { Entity, Field } from './types';

export const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const OBJECT_ID = /^[a-f0-9]{24}$/i;
const MONGO = SCHEMA.db === 'mongodb';
const INT32 = 2147483647; // ids and `int` fields are 32-bit columns in every SQL database we generate for
const isInt = (v: unknown): v is number => typeof v === 'number' && Number.isInteger(v) && Math.abs(v) <= INT32;

type Checked = { v: unknown } | { err: string };
const bad = (err: string): Checked => ({ err });

// Checks ONE value against its field definition. Returns { v } (normalised) or { err }.
export function one(f: Field, v: unknown): Checked {
  switch (f.type) {
    case 'string':
    case 'text': {
      if (typeof v !== 'string') return bad('must be text');
      const t = v.trim();
      const max = f.type === 'text' ? 20000 : 255;
      if (f.required && !t) return bad('is required');
      return t.length > max ? bad(`must be at most ${max} characters`) : { v: t };
    }
    case 'email':
      return typeof v === 'string' && v.length <= 255 && EMAIL.test(v.trim()) ? { v: v.trim().toLowerCase() } : bad('must be a valid email');
    case 'url':
      try {
        if (typeof v !== 'string' || v.length > 2048 || !/^https?:$/.test(new URL(v).protocol)) throw new Error('x');
        return { v: v.trim() };
      } catch {
        return bad('must be an http(s) URL');
      }
    case 'int':
      return isInt(v) ? { v } : bad('must be a whole number between -2147483647 and 2147483647');
    case 'float':
      return typeof v === 'number' && Number.isFinite(v) ? { v } : bad('must be a number');
    case 'bool':
      return typeof v === 'boolean' ? { v } : bad('must be true or false');
    case 'datetime':
      return typeof v === 'string' && !Number.isNaN(Date.parse(v)) ? { v: new Date(v).toISOString() } : bad('must be an ISO date-time');
    case 'enum':
      return typeof v === 'string' && (f.values ?? []).includes(v) ? { v } : bad(`must be one of: ${(f.values ?? []).join(', ')}`);
    case 'ref':
      return (MONGO ? typeof v === 'string' && OBJECT_ID.test(v) : isInt(v) && v > 0) ? { v } : bad('must be a valid id');
    default:
      return bad('has an unsupported type');
  }
}

// Fields a client may write. Sensitive columns, server-set timestamps and the owner link are never client-controlled.
const writable = (e: Entity, f: Field): boolean => !e.sensitive.includes(f.name) && f.name !== e.ownerField && !['id', 'created_at', 'updated_at'].includes(f.name);

export function validateBody(e: Entity, body: unknown, partial: boolean): Record<string, unknown> {
  if (!body || typeof body !== 'object' || Array.isArray(body)) throw new HttpError(400, 'validation_failed', 'Body must be a JSON object');
  const input = body as Record<string, unknown>;
  const fields = e.fields.filter((f) => writable(e, f));
  const names = new Set(fields.map((f) => f.name));
  const errors: Record<string, string> = {};
  const data: Record<string, unknown> = {};
  for (const k of Object.keys(input)) if (!names.has(k)) errors[k] = 'is not an accepted field';
  for (const f of fields) {
    if (!Object.prototype.hasOwnProperty.call(input, f.name)) {
      if (!partial && f.required) errors[f.name] = 'is required';
      continue;
    }
    const v = input[f.name];
    if (v === null) {
      if (f.required) errors[f.name] = 'is required';
      else data[f.name] = null;
      continue;
    }
    const r = one(f, v);
    if ('err' in r) errors[f.name] = r.err;
    else data[f.name] = r.v;
  }
  if (Object.keys(errors).length) throw new HttpError(400, 'validation_failed', 'Invalid input', errors);
  return data;
}

export interface ListQuery {
  page: number;
  limit: number;
  q?: string;
  filters: Record<string, unknown>;
  sort: { field: string; dir: 'asc' | 'desc' };
}

// ?page, ?limit (max 100), ?q (searches the searchable text fields) and exact filters on ref / enum / bool fields.
export function parseList(e: Entity, query: Record<string, unknown>): ListQuery {
  const num = (v: unknown, d: number, max: number): number => {
    if (v === undefined) return d;
    const n = Number(v);
    if (typeof v !== 'string' || !Number.isInteger(n) || n < 1) throw new HttpError(400, 'validation_failed', 'page and limit must be positive integers');
    return Math.min(n, max);
  };
  const page = num(query.page, 1, 1e6);
  const limit = num(query.limit, 20, 100);
  let q: string | undefined;
  if (query.q !== undefined) {
    if (typeof query.q !== 'string' || query.q.length > 100) throw new HttpError(400, 'validation_failed', 'q must be text up to 100 characters');
    q = query.q.trim() || undefined;
  }
  const filters: Record<string, unknown> = {};
  for (const f of e.fields.filter((x) => ['ref', 'enum', 'bool'].includes(x.type))) {
    const raw = query[f.name];
    if (raw === undefined) continue;
    if (typeof raw !== 'string') throw new HttpError(400, 'validation_failed', `${f.name} must be a single value`);
    let v: unknown = raw;
    if (f.type === 'bool') v = raw === 'true' ? true : raw === 'false' ? false : raw;
    else if (f.type === 'ref' && !MONGO) v = Number(raw);
    const r = one(f, v);
    if ('err' in r) throw new HttpError(400, 'validation_failed', `${f.name} ${r.err}`);
    filters[f.name] = r.v;
  }
  let sort = { field: 'id', dir: 'desc' as 'asc' | 'desc' };
  if (query.sort !== undefined) {
    if (typeof query.sort !== 'string') throw new HttpError(400, 'validation_failed', 'sort must be a single value');
    const desc = query.sort.startsWith('-');
    const name = desc ? query.sort.slice(1) : query.sort;
    const ok = name === 'id' || e.fields.some((f) => f.name === name && f.type !== 'text' && !(e.sensitive || []).includes(f.name));
    if (!ok) throw new HttpError(400, 'validation_failed', 'sort must be id or a non-text field name, optionally prefixed with - for descending');
    sort = { field: name, dir: desc ? 'desc' : 'asc' };
  }
  return { page, limit, q, filters, sort };
}
