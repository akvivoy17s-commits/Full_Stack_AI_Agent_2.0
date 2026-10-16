// Creates the first admin from ADMIN_EMAIL / ADMIN_PASSWORD. Public sign-up can never create an admin.
import * as bcrypt from 'bcryptjs';
import { EMAIL } from '../common/validate';
import { cfg } from '../config';
import { connect } from '../db/connect';
import { SCHEMA } from '../schema';

(async () => {
  cfg.validate();
  const email = (process.env.ADMIN_EMAIL || '').trim().toLowerCase();
  const pw = process.env.ADMIN_PASSWORD || '';
  if (!EMAIL.test(email) || pw.length < 8 || Buffer.byteLength(pw) > 72 || pw.startsWith('<')) {
    throw new Error('Set ADMIN_EMAIL and ADMIN_PASSWORD (8-72 characters) in .env first');
  }
  cfg.autoMigrate = true;
  const db = await connect();
  if (!db) throw new Error('This app has no database');
  if (await db.findOne('User', { email })) {
    console.log('That account already exists; nothing changed.');
  } else {
    const data: Record<string, unknown> = { email, name: 'Administrator', password_hash: await bcrypt.hash(pw, cfg.bcryptRounds), role: SCHEMA.adminRole };
    if (SCHEMA.entities.User.fields.some((f) => f.name === 'created_at')) data.created_at = new Date().toISOString();
    await db.create('User', data);
    console.log(`Admin created: ${email}`);
  }
  await db.close();
})().catch((e: Error) => {
  console.error('Seed failed:', e.message);
  process.exit(1);
});
