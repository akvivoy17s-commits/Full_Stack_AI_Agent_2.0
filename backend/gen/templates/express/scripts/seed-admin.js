// Creates the first admin from ADMIN_EMAIL / ADMIN_PASSWORD. Public sign-up can never create an admin.
const bcrypt = require('bcryptjs');
const cfg = require('../src/config');
const schema = require('../src/schema');
const { EMAIL } = require('../src/lib/validate');

(async () => {
  cfg.validate();
  const email = (process.env.ADMIN_EMAIL || '').trim().toLowerCase();
  const pw = process.env.ADMIN_PASSWORD || '';
  if (!EMAIL.test(email) || pw.length < 8 || Buffer.byteLength(pw) > 72 || pw.startsWith('<')) {
    throw new Error('Set ADMIN_EMAIL and ADMIN_PASSWORD (8-72 characters) in .env first');
  }
  cfg.autoMigrate = true;
  const db = await require('../src/db').connect();
  if (await db.findOne('User', { email })) {
    console.log('That account already exists; nothing changed.');
  } else {
    const data = { email, name: 'Administrator', password_hash: await bcrypt.hash(pw, cfg.bcryptRounds), role: schema.adminRole };
    if (schema.entities.User.fields.some((f) => f.name === 'created_at')) data.created_at = new Date().toISOString();
    await db.create('User', data);
    console.log(`Admin created: ${email}`);
  }
  await db.close();
})().catch((e) => {
  console.error('Seed failed:', e.message);
  process.exit(1);
});
