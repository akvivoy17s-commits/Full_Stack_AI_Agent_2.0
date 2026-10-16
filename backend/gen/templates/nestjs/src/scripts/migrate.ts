import { SCHEMA } from '../schema';
import { cfg } from '../config';
import { connect } from '../db/connect';

(async () => {
  cfg.validate();
  cfg.autoMigrate = true;
  const db = await connect();
  console.log(SCHEMA.db === 'mongodb' ? 'Indexes are in place (MongoDB has no migrations).' : 'Migrations are up to date.');
  await db?.close();
})().catch((e: Error) => {
  console.error('Migration failed:', e.message);
  process.exit(1);
});
