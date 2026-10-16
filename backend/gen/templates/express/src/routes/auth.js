const crypto = require('crypto');
const express = require('express');
const bcrypt = require('bcryptjs');
const cfg = require('../config');
const schema = require('../schema');
const { HttpError, wrap } = require('../lib/http');
const { authenticate, signAccess } = require('../middleware/auth');
const { authLimiter } = require('../middleware/rateLimit');
const { EMAIL } = require('../lib/validate');

const USER = 'User';
const sha = (t) => crypto.createHash('sha256').update(t).digest('hex');
const invalid = new HttpError(401, 'invalid_credentials', 'Invalid email or password');
const str = (v, max) => typeof v === 'string' && v.length <= max;

// Sign-up, sign-in, token refresh (rotating, single use), sign-out, current user.
module.exports = function authRoutes(db) {
  const r = express.Router();
  const hasField = (n) => schema.entities[USER].fields.some((f) => f.name === n);
  const DUMMY = bcrypt.hashSync('not-a-real-password', cfg.bcryptRounds); // equalises timing for unknown emails

  async function issue(user) {
    const out = { user, accessToken: signAccess(user), tokenType: 'Bearer', expiresIn: Math.round(cfg.jwt.accessTtlMin * 60) };
    if (schema.refresh) {
      const raw = crypto.randomBytes(48).toString('base64url');
      await db.create('RefreshToken', { user_id: user.id, token_hash: sha(raw), expires_at: new Date(Date.now() + cfg.jwt.refreshTtlDays * 864e5).toISOString() });
      out.refreshToken = raw;
    }
    return out;
  }

  r.post('/register', authLimiter, wrap(async (req, res) => {
    const b = req.body || {};
    const errors = {};
    if (!str(b.email, 255) || !EMAIL.test(b.email.trim())) errors.email = 'must be a valid email';
    if (!str(b.name, 255) || !b.name.trim()) errors.name = 'is required (max 255 characters)';
    if (!str(b.password, 200) || b.password.length < 8 || Buffer.byteLength(b.password) > 72) errors.password = 'must be 8-72 characters';
    for (const k of Object.keys(b)) if (!['email', 'name', 'password'].includes(k)) errors[k] = 'is not an accepted field';
    if (Object.keys(errors).length) throw new HttpError(400, 'validation_failed', 'Invalid input', errors);
    const data = {
      email: b.email.trim().toLowerCase(),
      name: b.name.trim(),
      password_hash: await bcrypt.hash(b.password, cfg.bcryptRounds),
      role: schema.defaultRole, // never client-controlled; the first admin is created with `npm run seed:admin`
    };
    if (hasField('created_at')) data.created_at = new Date().toISOString();
    res.status(201).json(await issue(await db.create(USER, data)));
  }));

  if (schema.firebaseAuth) {
    // Exchange a Firebase ID token for this API's own token pair. Verified server side; the role is never read from the token.
    r.post('/firebase', authLimiter, wrap(async (req, res) => {
      const t = (req.body || {}).idToken;
      if (!str(t, 4096)) throw new HttpError(400, 'validation_failed', 'idToken must be text');
      let d;
      try {
        d = await require('../lib/firebase').verifyIdToken(t);
      } catch (e) {
        if (e instanceof HttpError) throw e;
        throw new HttpError(401, 'invalid_token', 'Invalid Firebase token');
      }
      if (typeof d.email !== 'string' || d.email_verified !== true || !EMAIL.test(d.email)) throw new HttpError(401, 'invalid_token', 'The Firebase account needs a verified email');
      const email = d.email.trim().toLowerCase();
      let u = await db.findOne(USER, { email }, { raw: true });
      if (u) return res.json(await issue(db.clean(USER, u)));
      const data = {
        email,
        name: String(d.name || email.split('@')[0]).slice(0, 255),
        password_hash: await bcrypt.hash(crypto.randomBytes(32).toString('base64url'), cfg.bcryptRounds), // unusable: this account signs in through Firebase
        role: schema.defaultRole,
      };
      if (hasField('created_at')) data.created_at = new Date().toISOString();
      res.json(await issue(await db.create(USER, data)));
    }));
  }

  r.post('/login', authLimiter, wrap(async (req, res) => {
    const b = req.body || {};
    if (!str(b.email, 255) || !str(b.password, 200)) throw new HttpError(400, 'validation_failed', 'email and password must be text');
    const u = await db.findOne(USER, { email: b.email.trim().toLowerCase() }, { raw: true });
    const ok = await bcrypt.compare(b.password, u ? u.password_hash : DUMMY);
    if (!u || !ok) throw invalid;
    res.json(await issue(db.clean(USER, u)));
  }));

  if (schema.refresh) {
    r.post('/refresh', authLimiter, wrap(async (req, res) => {
      const t = (req.body || {}).refreshToken;
      if (!str(t, 200)) throw new HttpError(401, 'invalid_token', 'Invalid refresh token');
      const row = await db.findOne('RefreshToken', { token_hash: sha(t) });
      // delete-then-check: a token can be used once, even under concurrent requests
      if (!row || (await db.removeWhere('RefreshToken', { token_hash: sha(t) })) !== 1 || new Date(row.expires_at) < new Date()) {
        throw new HttpError(401, 'invalid_token', 'Invalid refresh token');
      }
      const user = await db.get(USER, row.user_id);
      if (!user) throw new HttpError(401, 'invalid_token', 'Invalid refresh token');
      res.json(await issue(user));
    }));
  }

  r.post('/logout', authenticate, wrap(async (req, res) => {
    if (schema.refresh) {
      const t = (req.body || {}).refreshToken;
      const where = { user_id: db.parseId(req.user.id) };
      if (str(t, 200)) where.token_hash = sha(t);
      await db.removeWhere('RefreshToken', where); // without a token: sign out everywhere
    }
    res.status(204).end();
  }));

  r.get('/me', authenticate, wrap(async (req, res) => {
    const user = await db.get(USER, db.parseId(req.user.id));
    if (!user) throw new HttpError(401, 'invalid_token', 'Account no longer exists');
    res.json({ user });
  }));

  return r;
};
