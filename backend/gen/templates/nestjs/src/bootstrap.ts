import { NestFactory } from '@nestjs/core';
import { NestExpressApplication } from '@nestjs/platform-express';
import { json } from 'express';
import { readFileSync } from 'fs';
import { join } from 'path';
import helmet from 'helmet';
import { AppModule } from './app.module';
import { mountIntent, mountWebhook } from './integrations/pay-mount';
import { cfg } from './config';
import { SCHEMA } from './schema';

// Integration files exist only when the app uses them, so they are loaded by name (a literal path would fail to compile when the file is absent).
const load = (name: string) => import(`./integrations/${name}`);

// Shared by main.ts and the tests so both run the same security setup.
export async function createApp(): Promise<NestExpressApplication> {
  cfg.validate();
  const app = await NestFactory.create<NestExpressApplication>(AppModule, {
    bodyParser: false,
    logger: cfg.env === 'test' ? false : ['log', 'warn', 'error'],
  });
  app.disable('x-powered-by');
  if (cfg.trustProxy !== '0') app.set('trust proxy', /^\d+$/.test(cfg.trustProxy) ? Number(cfg.trustProxy) : cfg.trustProxy);
  app.use(helmet());
  app.enableCors({ origin: cfg.corsOrigins, methods: ['GET', 'POST', 'PUT', 'DELETE'], allowedHeaders: ['Content-Type', 'Authorization'] });
  if (SCHEMA.integrations.uploads) {
    const { uploads, uploadErrors } = await load('uploads');   // before the JSON parser: the raw file is the body
    app.use('/api/uploads', uploads(), uploadErrors);
  }
  mountWebhook(app);                                  // payments: before the JSON parser, the signature covers the raw bytes
  app.use(json({ limit: '100kb' }));
  mountIntent(app);
  if (SCHEMA.integrations.cache || SCHEMA.integrations.ws) {
    const { live } = await load('live');
    app.use('/api', live());
  }
  app.setGlobalPrefix('api');
  const apiDoc = JSON.parse(readFileSync(join(__dirname, '..', 'openapi.json'), 'utf8')); // same document in every generated backend
  const esc = (s: unknown) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c] as string));
  app.get('/api/openapi.json', (_req, res) => res.json(apiDoc));
  app.get('/api/docs', (_req, res) => {
    const rows = Object.entries<Record<string, { summary?: string }>>(apiDoc.paths).flatMap(([p, ops]) => Object.entries(ops).map(([m, o]) => `<tr><td><b>${m.toUpperCase()}</b></td><td><code>${esc(p)}</code></td><td>${esc(o.summary || '')}</td></tr>`)).join('');
    res.type('html').send(`<!doctype html><meta charset=utf-8><title>${esc(apiDoc.info.title)}</title><style>body{font:15px system-ui;margin:2rem auto;max-width:60rem;padding:0 1rem}td{padding:.35rem .6rem;border-bottom:1px solid #ddd;vertical-align:top}</style><h1>${esc(apiDoc.info.title)}</h1><p>Machine readable: <a href=/api/openapi.json>/api/openapi.json</a></p><table>${rows}</table>`);
  });
  app.enableShutdownHooks();
  return app;
}
