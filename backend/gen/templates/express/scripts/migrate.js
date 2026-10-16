const cfg = require('../src/config');
const schema = require('../src/schema');

(async () => {
  cfg.validate();
  cfg.autoMigrate = true;
  const db = await require('../src/db').connect();
  console.log(schema.db === 'mongodb' ? 'Indexes are in place (MongoDB has no migrations).' : 'Migrations are up to date.');
  await db.close();
})().catch((e) => {
  console.error('Migration failed:', e.message);
  process.exit(1);
});
