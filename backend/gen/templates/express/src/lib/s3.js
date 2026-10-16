const crypto = require('crypto');
const cfg = require('../config');
const { HttpError } = require('./http');

// S3-compatible object storage (AWS S3, MinIO, Cloudflare R2, DigitalOcean Spaces) with Signature V4, called with fetch (no SDK).
// The bucket stays PRIVATE: files are only served through the API, which applies the same sign-in rule as local uploads.
const hmac = (k, d) => crypto.createHmac('sha256', k).update(d).digest();
const sha = (d) => crypto.createHash('sha256').update(d).digest('hex');
const enc = (s) => encodeURIComponent(s).replace(/[!'()*]/g, (c) => '%' + c.charCodeAt(0).toString(16).toUpperCase());

function authorization({ method, host, path, headers = {}, payloadHash, amzDate, region, accessKeyId, secretAccessKey }) {
  const all = { ...headers, host, 'x-amz-content-sha256': payloadHash, 'x-amz-date': amzDate };
  const lower = Object.fromEntries(Object.entries(all).map(([k, v]) => [k.toLowerCase(), String(v).trim()]));
  const names = Object.keys(lower).sort();
  const signed = names.join(';');
  const canonical = [method, path.split('/').map(enc).join('/'), '', names.map((n) => `${n}:${lower[n]}`).join('\n') + '\n', signed, payloadHash].join('\n');
  const day = amzDate.slice(0, 8);
  const scope = `${day}/${region}/s3/aws4_request`;
  const toSign = ['AWS4-HMAC-SHA256', amzDate, scope, sha(canonical)].join('\n');
  const key = hmac(hmac(hmac(hmac('AWS4' + secretAccessKey, day), region), 's3'), 'aws4_request');
  const signature = crypto.createHmac('sha256', key).update(toSign).digest('hex');
  return { header: `AWS4-HMAC-SHA256 Credential=${accessKeyId}/${scope}, SignedHeaders=${signed}, Signature=${signature}`, headers: lower };
}

// AWS endpoints use the virtual-hosted style (bucket.host); every other S3-compatible service uses path style (host/bucket).
function target(key) {
  const u = new URL(cfg.s3.endpoint);
  return /(^|\.)amazonaws\.com$/.test(u.hostname)
    ? { url: `${u.protocol}//${cfg.s3.bucket}.${u.host}/${key}`, host: `${cfg.s3.bucket}.${u.host}`, path: `/${key}` }
    : { url: `${u.protocol}//${u.host}/${cfg.s3.bucket}/${key}`, host: u.host, path: `/${cfg.s3.bucket}/${key}` };
}

const configured = () => ['endpoint', 'bucket', 'accessKeyId', 'secretAccessKey'].every((k) => cfg.s3[k] && !String(cfg.s3[k]).startsWith('your-'));

async function send(method, key, body, contentType) {
  if (!configured()) throw new HttpError(503, 'storage_unavailable', 'File storage is not configured');
  const t = target(key);
  const payload = body || Buffer.alloc(0);
  const amzDate = new Date().toISOString().replace(/[:-]|\.\d{3}/g, '');
  const a = authorization({ method, host: t.host, path: t.path, payloadHash: sha(payload), amzDate, region: cfg.s3.region, accessKeyId: cfg.s3.accessKeyId, secretAccessKey: cfg.s3.secretAccessKey });
  try {
    return await fetch(t.url, { method, body: body || undefined, signal: AbortSignal.timeout(15000), headers: { ...a.headers, ...(contentType ? { 'Content-Type': contentType } : {}), Authorization: a.header } });
  } catch (e) { throw new HttpError(502, 'storage_unreachable', 'The file storage could not be reached'); }
}

async function put(key, body, contentType) {
  const r = await send('PUT', key, body, contentType);
  if (!r.ok) throw new HttpError(502, 'storage_error', 'The file storage rejected the request');
}

async function get(key) {
  const r = await send('GET', key);
  if (r.status === 404) return null;
  if (!r.ok) throw new HttpError(502, 'storage_error', 'The file storage rejected the request');
  return Buffer.from(await r.arrayBuffer());
}

module.exports = { put, get, authorization, target };
