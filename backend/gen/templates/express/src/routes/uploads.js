const express = require('express');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const cfg = require('../config');
const schema = require('../schema');
const { HttpError, wrap } = require('../lib/http');
const { guard } = require('../middleware/auth');

// Type comes from the file's magic bytes, never from the client's Content-Type or file name. Stored under a random name.
const KINDS = [
  { ext: 'png', mime: 'image/png', test: (b) => b.length > 8 && b.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])) },
  { ext: 'jpg', mime: 'image/jpeg', test: (b) => b.length > 3 && b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff },
  { ext: 'gif', mime: 'image/gif', test: (b) => b.length > 6 && /^GIF8[79]a$/.test(b.subarray(0, 6).toString('latin1')) },
  { ext: 'webp', mime: 'image/webp', test: (b) => b.length > 12 && b.subarray(0, 4).toString('latin1') === 'RIFF' && b.subarray(8, 12).toString('latin1') === 'WEBP' },
  { ext: 'pdf', mime: 'application/pdf', test: (b) => b.length > 5 && b.subarray(0, 5).toString('latin1') === '%PDF-' },
];
const NAME = /^[0-9a-f]{32}\.(png|jpg|gif|webp|pdf)$/;

module.exports = function uploads() {
  const router = express.Router();
  const dir = path.resolve(cfg.upload.dir);
  const level = schema.auth ? 'user' : 'public';

  // Send the raw file as the request body (Content-Type is ignored): curl --data-binary @photo.png -H "Authorization: Bearer ..." /api/uploads
  router.post('/', ...guard(level), express.raw({ type: () => true, limit: cfg.upload.maxBytes }), wrap(async (req, res) => {
    const body = Buffer.isBuffer(req.body) ? req.body : Buffer.alloc(0);
    if (!body.length) throw new HttpError(400, 'validation_failed', 'Send the file as the request body');
    const kind = KINDS.find((k) => k.test(body));
    if (!kind) throw new HttpError(415, 'unsupported_type', 'Only PNG, JPEG, GIF, WebP and PDF files are accepted');
    const name = `${crypto.randomBytes(16).toString('hex')}.${kind.ext}`;
    await fs.promises.mkdir(dir, { recursive: true });
    await fs.promises.writeFile(path.join(dir, name), body, { flag: 'wx', mode: 0o640 });
    res.status(201).json({ name, url: `/api/uploads/${name}`, size: body.length, type: kind.mime });
  }));

  router.get('/:name', ...guard(level), wrap(async (req, res) => {
    if (!NAME.test(req.params.name)) throw new HttpError(404, 'not_found', 'File not found');
    const mime = KINDS.find((k) => req.params.name.endsWith('.' + k.ext)).mime;
    res.set({ 'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "default-src 'none'; sandbox", 'Cache-Control': 'private, max-age=3600' });
    res.type(mime);
    res.sendFile(req.params.name, { root: dir, dotfiles: 'deny' }, (err) => {
      if (err && !res.headersSent) res.status(404).json({ error: { code: 'not_found', message: 'File not found' } });
    });
  }));
  return router;
};
