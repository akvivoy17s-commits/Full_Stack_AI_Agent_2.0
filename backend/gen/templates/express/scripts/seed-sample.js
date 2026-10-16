// Optional sample data for development: npm run seed:sample
// Inserts a few obviously-fake rows per entity (from src/schema.js). Safe to run twice: an entity that already has rows is left alone.
// Records that point at User are linked to the admin created by `npm run seed:admin`; run that first if the app has sign-in.
const cfg = require('../src/config');
const schema = require('../src/schema');

(async () => {
  cfg.validate();
  if (process.env.APP_ENV === 'production' && process.env.ALLOW_SAMPLE_DATA !== 'true') {
    throw new Error('Refusing to add sample data in production (set ALLOW_SAMPLE_DATA=true to override)');
  }
  cfg.autoMigrate = true;
  const db = await require('../src/db').connect();
  const ids = {};
  const admin = schema.auth ? await db.findOne('User', { email: (process.env.ADMIN_EMAIL || '').trim().toLowerCase() }) : null;
  if (admin) ids.User = [admin.id];
  let done = 0;
  for (const plan of schema.seed) {
    const page = await db.list(plan.entity, { page: 1, limit: 100 });
    if (page.total) {                       // keep what is there and let later entities point at it
      ids[plan.entity] = page.rows.map((r) => r.id).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0)).slice(0, 3);
      console.log(`Skipped ${plan.entity}: it already has data.`);
      continue;
    }
    const refs = [...new Set(plan.rows.flatMap((r) => Object.values(r)).filter((v) => v && typeof v === 'object').map((v) => v.$ref[0]))];
    if (refs.includes('User') && !admin) { console.log(`Skipped ${plan.entity}: it points at a user; run \`npm run seed:admin\` first.`); continue; }
    const absent = refs.filter((p) => !ids[p]);
    if (absent.length) { console.log(`Skipped ${plan.entity}: it needs ${absent.join(', ')} records first.`); continue; }
    ids[plan.entity] = [];
    for (const row of plan.rows) {
      const data = Object.fromEntries(Object.entries(row).map(([k, v]) => [k, v && typeof v === 'object' ? ids[v.$ref[0]][v.$ref[1]] : v]));
      ids[plan.entity].push((await db.create(plan.entity, data)).id);
    }
    done += 1;
    console.log(`Added ${plan.rows.length} ${plan.entity} record(s).`);
  }
  await db.close();
  console.log(done ? 'Sample data is ready.' : 'Nothing to add.');
})().catch((e) => {
  console.error('Seed failed:', e.message);
  process.exit(1);
});
