const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const cfg = require('./config');
const schema = require('./schema');
const { notFound, errorHandler } = require('./middleware/error');
const { apiLimiter } = require('./middleware/rateLimit');

function createApp(db) {
  cfg.validate();
  const app = express();
  app.disable('x-powered-by');
  if (cfg.trustProxy !== '0') app.set('trust proxy', /^\d+$/.test(cfg.trustProxy) ? Number(cfg.trustProxy) : cfg.trustProxy);
  app.use(helmet());
  app.use(cors({ origin: cfg.corsOrigins, methods: ['GET', 'POST', 'PUT', 'DELETE'], allowedHeaders: ['Content-Type', 'Authorization'] }));
  if (db && schema.integrations.payments) app.post('/api/payments/webhook', ...require('./routes/payments').webhook(db)); // raw body, before express.json
  app.use(express.json({ limit: '100kb' }));
  app.use('/api', apiLimiter);
  if (db && (schema.integrations.cache || schema.integrations.ws)) app.use('/api', require('./middleware/live')());

  app.get('/api/health', async (req, res) => {
    try {
      if (db) await db.ping();
      res.json({ status: 'ok', ...(db && { db: 'up' }), ...(schema.integrations.cache && { cache: cfg.redisUrl ? 'redis' : 'memory' }) });
    } catch (e) {
      res.status(503).json({ status: 'degraded', db: 'down' });
    }
  });
  const fs = require('fs');
  const path = require('path');
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const apiDoc = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'openapi.json'), 'utf8')); // same document in every generated backend
  app.get('/api/openapi.json', (req, res) => res.json(apiDoc));
  app.get('/api/docs', (req, res) => {
    const rows = Object.entries(apiDoc.paths).flatMap(([p, ops]) => Object.entries(ops).map(([m, o]) => `<tr><td><b>${m.toUpperCase()}</b></td><td><code>${esc(p)}</code></td><td>${esc(o.summary || '')}</td></tr>`)).join('');
    res.type('html').send(`<!doctype html><meta charset=utf-8><title>${esc(apiDoc.info.title)}</title><style>body{font:15px system-ui;margin:2rem auto;max-width:60rem;padding:0 1rem}td{padding:.35rem .6rem;border-bottom:1px solid #ddd;vertical-align:top}</style><h1>${esc(apiDoc.info.title)}</h1><p>Machine readable: <a href=/api/openapi.json>/api/openapi.json</a></p><table>${rows}</table>`);
  });
  if (schema.auth) app.use('/api/auth', require('./routes/auth')(db));
  if (db && schema.integrations.payments) app.use('/api/payments', require('./routes/payments').intent(db));
  if (db) app.use('/api', require('./routes/crud')(db));
  if (db && schema.checkout) app.use('/api/checkout', require('./routes/checkout')(db));
  if (schema.integrations.uploads) app.use('/api/uploads', require('./routes/uploads')());

  app.use(notFound);
  app.use(errorHandler);
  return app;
}

module.exports = { createApp };
