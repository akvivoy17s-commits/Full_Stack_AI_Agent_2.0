// Uploads: the type comes from the file's magic bytes, never from the client's Content-Type or file name. Stored under a random name.
// Mounted before the JSON parser: the raw file is the request body.
import { Router, raw } from 'express';
import type { NextFunction, Request, Response } from 'express';
import { randomBytes } from 'crypto';
import { promises as fs } from 'fs';
import * as jwt from 'jsonwebtoken';
import { resolve } from 'path';
import { cfg } from '../config';
import { SCHEMA } from '../schema';

const KINDS: { ext: string; mime: string; test: (b: Buffer) => boolean }[] = [
  { ext: 'png', mime: 'image/png', test: (b) => b.length > 8 && b.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) },
  { ext: 'jpg', mime: 'image/jpeg', test: (b) => b.length > 3 && b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff },
  { ext: 'gif', mime: 'image/gif', test: (b) => b.length > 6 && /^GIF8[79]a$/.test(b.subarray(0, 6).toString('latin1')) },
  { ext: 'webp', mime: 'image/webp', test: (b) => b.length > 12 && b.subarray(0, 4).toString('latin1') === 'RIFF' && b.subarray(8, 12).toString('latin1') === 'WEBP' },
  { ext: 'pdf', mime: 'application/pdf', test: (b) => b.length > 5 && b.subarray(0, 5).toString('latin1') === '%PDF-' },
];
const NAME = /^[0-9a-f]{32}\.(png|jpg|gif|webp|pdf)$/;
const fail = (res: Response, status: number, code: string, message: string) => res.status(status).json({ error: { code, message } });

function who(req: Request, res: Response, next: NextFunction): void {
  if (!SCHEMA.auth) return next();
  const m = /^Bearer (.+)$/i.exec(req.headers.authorization || '');
  try {
    if (!m) throw new Error('missing');
    jwt.verify(m[1], cfg.jwt.key, { algorithms: ['HS256'] });
    return next();
  } catch {
    fail(res, 401, m ? 'invalid_token' : 'unauthorized', m ? 'Invalid or expired token' : 'Authentication required');
  }
}

export function uploads(): Router {
  const router = Router();
  const dir = resolve(cfg.upload.dir);

  router.post('/', who, raw({ type: () => true, limit: cfg.upload.maxBytes }), async (req, res, next) => {
    try {
      const body: Buffer = Buffer.isBuffer(req.body) ? req.body : Buffer.alloc(0);
      if (!body.length) return void fail(res, 400, 'validation_failed', 'Send the file as the request body');
      const kind = KINDS.find((k) => k.test(body));
      if (!kind) return void fail(res, 415, 'unsupported_type', 'Only PNG, JPEG, GIF, WebP and PDF files are accepted');
      const name = `${randomBytes(16).toString('hex')}.${kind.ext}`;
      await fs.mkdir(dir, { recursive: true });
      await fs.writeFile(`${dir}/${name}`, body, { flag: 'wx', mode: 0o640 });
      res.status(201).json({ name, url: `/api/uploads/${name}`, size: body.length, type: kind.mime });
    } catch (e) { next(e); }
  });

  router.get('/:name', who, (req, res) => {
    const name = String(req.params.name);
    const kind = NAME.test(name) ? KINDS.find((k) => name.endsWith('.' + k.ext)) : undefined;
    if (!kind) return void fail(res, 404, 'not_found', 'File not found');
    res.set({ 'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "default-src 'none'; sandbox", 'Cache-Control': 'private, max-age=3600' });
    res.type(kind.mime);
    res.sendFile(name, { root: dir, dotfiles: 'deny' }, (err) => { if (err && !res.headersSent) fail(res, 404, 'not_found', 'File not found'); });
  });
  return router;
}

// Payload-too-large from raw(): same envelope as the rest of the API.
export function uploadErrors(err: { type?: string }, _req: Request, res: Response, next: NextFunction): void {
  if (err && err.type === 'entity.too.large') return void fail(res, 413, 'payload_too_large', 'The file is too large');
  next(err);
}
