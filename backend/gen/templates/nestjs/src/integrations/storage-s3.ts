// S3-compatible object storage (AWS S3, MinIO, Cloudflare R2, DigitalOcean Spaces) with Signature V4, called with fetch (no SDK).
// The bucket stays PRIVATE: files are only served through the API, which applies the same sign-in rule as local uploads.
import { createHash, createHmac } from 'crypto';
import { cfg } from '../config';

export class StorageError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

const hmac = (k: Buffer | string, d: string): Buffer => createHmac('sha256', k).update(d).digest();
const sha = (d: Buffer | string): string => createHash('sha256').update(d).digest('hex');
const enc = (s: string): string => encodeURIComponent(s).replace(/[!'()*]/g, (c) => '%' + c.charCodeAt(0).toString(16).toUpperCase());

export function authorization(o: { method: string; host: string; path: string; payloadHash: string; amzDate: string; region: string; accessKeyId: string; secretAccessKey: string }) {
  const lower: Record<string, string> = { host: o.host, 'x-amz-content-sha256': o.payloadHash, 'x-amz-date': o.amzDate };
  const names = Object.keys(lower).sort();
  const signed = names.join(';');
  const canonical = [o.method, o.path.split('/').map(enc).join('/'), '', names.map((n) => `${n}:${lower[n]}`).join('\n') + '\n', signed, o.payloadHash].join('\n');
  const day = o.amzDate.slice(0, 8);
  const scope = `${day}/${o.region}/s3/aws4_request`;
  const toSign = ['AWS4-HMAC-SHA256', o.amzDate, scope, sha(canonical)].join('\n');
  const key = hmac(hmac(hmac(hmac('AWS4' + o.secretAccessKey, day), o.region), 's3'), 'aws4_request');
  const signature = createHmac('sha256', key).update(toSign).digest('hex');
  return { header: `AWS4-HMAC-SHA256 Credential=${o.accessKeyId}/${scope}, SignedHeaders=${signed}, Signature=${signature}`, headers: lower };
}

// AWS endpoints use the virtual-hosted style (bucket.host); every other S3-compatible service uses path style (host/bucket).
export function target(key: string): { url: string; host: string; path: string } {
  const u = new URL(cfg.s3.endpoint);
  return /(^|\.)amazonaws\.com$/.test(u.hostname)
    ? { url: `${u.protocol}//${cfg.s3.bucket}.${u.host}/${key}`, host: `${cfg.s3.bucket}.${u.host}`, path: `/${key}` }
    : { url: `${u.protocol}//${u.host}/${cfg.s3.bucket}/${key}`, host: u.host, path: `/${cfg.s3.bucket}/${key}` };
}

const configured = (): boolean => [cfg.s3.endpoint, cfg.s3.bucket, cfg.s3.accessKeyId, cfg.s3.secretAccessKey].every((v) => v && !v.startsWith('your-'));

async function send(method: string, key: string, body?: Buffer, contentType?: string): Promise<Response> {
  if (!configured()) throw new StorageError(503, 'storage_unavailable', 'File storage is not configured');
  const t = target(key);
  const payload = body || Buffer.alloc(0);
  const amzDate = new Date().toISOString().replace(/[:-]|\.\d{3}/g, '');
  const a = authorization({ method, host: t.host, path: t.path, payloadHash: sha(payload), amzDate, region: cfg.s3.region, accessKeyId: cfg.s3.accessKeyId, secretAccessKey: cfg.s3.secretAccessKey });
  try {
    return await fetch(t.url, { method, body: body ? new Uint8Array(body) : undefined, signal: AbortSignal.timeout(15000), headers: { ...a.headers, ...(contentType ? { 'Content-Type': contentType } : {}), Authorization: a.header } });
  } catch {
    throw new StorageError(502, 'storage_unreachable', 'The file storage could not be reached');
  }
}

export const store = {
  async put(key: string, body: Buffer, contentType: string): Promise<void> {
    const r = await send('PUT', key, body, contentType);
    if (!r.ok) throw new StorageError(502, 'storage_error', 'The file storage rejected the request');
  },
  async get(key: string): Promise<Buffer | null> {
    const r = await send('GET', key);
    if (r.status === 404) return null;
    if (!r.ok) throw new StorageError(502, 'storage_error', 'The file storage rejected the request');
    return Buffer.from(await r.arrayBuffer());
  },
};
