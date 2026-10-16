import { createApp } from './bootstrap';
import { cfg } from './config';
import { SCHEMA } from './schema';

async function main(): Promise<void> {
  const app = await createApp();
  const server = await app.listen(cfg.port);
  if (SCHEMA.integrations.ws) (await import(`./integrations/${'ws'}`)).attachWs(server);
  server.requestTimeout = 30000;
  server.headersTimeout = 20000;
  console.log(`API listening on http://localhost:${cfg.port}/api/health`);
}

main().catch((e: Error) => {
  console.error('Startup failed:', e.message);
  process.exit(1);
});
