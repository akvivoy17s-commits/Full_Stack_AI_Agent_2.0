import { Inject, Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcryptjs';
import { createHash, randomBytes } from 'crypto';
import { HttpError } from '../common/http-error';
import { AuthUser } from '../common/types';
import { EMAIL } from '../common/validate';
import { cfg } from '../config';
import { DB, Db, Row } from '../db/db';
import { SCHEMA } from '../schema';

const USER = 'User';
const sha = (t: string): string => createHash('sha256').update(t).digest('hex');
const str = (v: unknown, max: number): v is string => typeof v === 'string' && v.length <= max;
const invalid = () => new HttpError(401, 'invalid_credentials', 'Invalid email or password');
const body = (b: unknown): Record<string, unknown> => (b && typeof b === 'object' ? (b as Record<string, unknown>) : {});

// Sign-up, sign-in, token refresh (rotating, single use), sign-out, current user.
@Injectable()
export class AuthService {
  private readonly dummy = bcrypt.hashSync('not-a-real-password', cfg.bcryptRounds); // equalises timing for unknown emails

  constructor(
    @Inject(DB) private readonly db: Db,
    private readonly jwt: JwtService,
  ) {}

  private async issue(user: Row) {
    const out: Record<string, unknown> = {
      user,
      accessToken: await this.jwt.signAsync({ role: user.role }, { subject: String(user.id), expiresIn: Math.round(cfg.jwt.accessTtlMin * 60) }),
      tokenType: 'Bearer',
      expiresIn: Math.round(cfg.jwt.accessTtlMin * 60),
    };
    if (SCHEMA.refresh) {
      const raw = randomBytes(48).toString('base64url');
      await this.db.create('RefreshToken', { user_id: user.id, token_hash: sha(raw), expires_at: new Date(Date.now() + cfg.jwt.refreshTtlDays * 864e5).toISOString() });
      out.refreshToken = raw;
    }
    return out;
  }

  async register(input: unknown) {
    const b = body(input);
    const errors: Record<string, string> = {};
    if (!str(b.email, 255) || !EMAIL.test(b.email.trim())) errors.email = 'must be a valid email';
    if (!str(b.name, 255) || !b.name.trim()) errors.name = 'is required (max 255 characters)';
    if (!str(b.password, 200) || b.password.length < 8 || Buffer.byteLength(b.password) > 72) errors.password = 'must be 8-72 characters';
    for (const k of Object.keys(b)) if (!['email', 'name', 'password'].includes(k)) errors[k] = 'is not an accepted field';
    if (Object.keys(errors).length) throw new HttpError(400, 'validation_failed', 'Invalid input', errors);
    const data: Row = {
      email: (b.email as string).trim().toLowerCase(),
      name: (b.name as string).trim(),
      password_hash: await bcrypt.hash(b.password as string, cfg.bcryptRounds),
      role: SCHEMA.defaultRole, // never client-controlled; the first admin is created with `npm run seed:admin`
    };
    if (SCHEMA.entities[USER].fields.some((f) => f.name === 'created_at')) data.created_at = new Date().toISOString();
    return this.issue(await this.db.create(USER, data));
  }

  async login(input: unknown) {
    const b = body(input);
    if (!str(b.email, 255) || !str(b.password, 200)) throw new HttpError(400, 'validation_failed', 'email and password must be text');
    const u = await this.db.findOne(USER, { email: b.email.trim().toLowerCase() }, { raw: true });
    const ok = await bcrypt.compare(b.password, u ? u.password_hash : this.dummy);
    if (!u || !ok) throw invalid();
    return this.issue(this.db.clean(USER, u));
  }

  async refresh(input: unknown) {
    const t = body(input).refreshToken;
    const fail = () => new HttpError(401, 'invalid_token', 'Invalid refresh token');
    if (!str(t, 200)) throw fail();
    const row = await this.db.findOne('RefreshToken', { token_hash: sha(t) });
    // delete-then-check: a token can be used once, even under concurrent requests
    if (!row || (await this.db.removeWhere('RefreshToken', { token_hash: sha(t) })) !== 1 || new Date(row.expires_at) < new Date()) throw fail();
    const user = await this.db.get(USER, row.user_id);
    if (!user) throw fail();
    return this.issue(user);
  }

  async logout(user: AuthUser, input: unknown): Promise<void> {
    if (!SCHEMA.refresh) return;
    const t = body(input).refreshToken;
    const where: Row = { user_id: this.db.parseId(user.id) };
    if (str(t, 200)) where.token_hash = sha(t);
    await this.db.removeWhere('RefreshToken', where); // without a token: sign out everywhere
  }

  async me(user: AuthUser) {
    const u = await this.db.get(USER, this.db.parseId(user.id) as number | string);
    if (!u) throw new HttpError(401, 'invalid_token', 'Account no longer exists');
    return { user: u };
  }
}
