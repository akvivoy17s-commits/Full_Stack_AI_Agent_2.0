const cfg = require('./config');
const schema = require('./schema');
const { createApp } = require('./app');

async function main() {
  cfg.validate();
  const db = schema.db ? await require('./db').connect() : null;
  const server = createApp(db).listen(cfg.port, () => console.log(`API listening on http://localhost:${cfg.port}/api/health`));
  if (schema.integrations.ws) require('./ws').attach(server);
  server.requestTimeout = 30000;
  server.headersTimeout = 20000;
  const stop = async () => {
    server.close();
    if (schema.integrations.cache) await require('./lib/cache').close();
    if (db) await db.close();
    process.exit(0);
  };
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
}

main().catch((e) => {
  console.error('Startup failed:', e.message);
  process.exit(1);
});
