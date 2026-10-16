// Generated tests: they read src/schema.ts, so they cover every entity and access rule of THIS app.
/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-require-imports */
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { createApp } from '../src/bootstrap';
import { Entity, Field } from '../src/common/types';
import { DB, Db } from '../src/db/db';
import { SCHEMA } from '../src/schema';

const skip = !!SCHEMA.db && SCHEMA.db !== 'sqlite' && !process.env.TEST_DATABASE_URL;
const bcrypt: any = SCHEMA.auth ? require('bcryptjs') : null;
const PW = 'Passw0rd!long';
let seq = 0;
const rnd = (): string => `${++seq}${Math.floor(Math.random() * 1e9)}`;

(skip ? describe.skip : describe)(skip ? 'api (set TEST_DATABASE_URL to run the database tests)' : 'api', () => {
  let app: INestApplication;
  let db: Db | null = null;

  beforeAll(async () => {
    app = await createApp();
    await app.init();
    db = SCHEMA.db ? app.get<Db>(DB) : null;
  });
  afterAll(async () => {
    await app?.close();
  });

  const call = async (method: 'get' | 'post' | 'put' | 'delete', path: string, body?: unknown, token?: string) => {
    let r = request(app.getHttpServer())[method](path);
    if (token) r = r.set('Authorization', `Bearer ${token}`);
    if (body !== undefined) r = r.send(body as object);
    const res = await r;
    return { status: res.status, body: res.body && Object.keys(res.body).length ? res.body : null } as { status: number; body: any };
  };

  const sample = (f: Field): unknown =>
    ({
      string: `s${rnd()}`, text: `text ${rnd()}`, email: `e${rnd()}@example.com`, url: `https://example.com/${rnd()}`,
      int: Number(rnd().slice(0, 9)), float: 1.5, bool: true, datetime: new Date().toISOString(),
    } as Record<string, unknown>)[f.type];

  // Required values for an entity. api=true leaves out what the server sets itself.
  async function values(e: Entity, api: boolean): Promise<Record<string, unknown>> {
    const o: Record<string, unknown> = {};
    for (const f of e.fields) {
      if (!f.required) continue;
      if (api && (f.name === e.ownerField || e.sensitive.includes(f.name) || f.name === 'created_at')) continue;
      if (f.type === 'ref') o[f.name] = (await fixture(SCHEMA.entities[f.ref as string])).id;
      else if (f.type === 'enum') o[f.name] = (f.values as string[])[0];
      else if (f.name === 'password_hash') o[f.name] = await bcrypt.hash(PW, 4);
      else if (f.name === 'created_at') o[f.name] = new Date().toISOString();
      else o[f.name] = sample(f);
    }
    return o;
  }
  const fixture = async (e: Entity) => (db as Db).create(e.name, await values(e, false));

  async function makeUser(role?: string) {
    const email = `u${rnd()}@example.com`;
    if (role) {
      await (db as Db).create('User', { email, name: 'Seeded', password_hash: await bcrypt.hash(PW, 4), role, created_at: new Date().toISOString() });
    } else {
      expect((await call('post', '/api/auth/register', { email, name: 'Test User', password: PW })).status).toBe(201);
    }
    const r = await call('post', '/api/auth/login', { email, password: PW });
    expect(r.status).toBe(200);
    return { token: r.body.accessToken as string, id: r.body.user.id as string | number, email };
  }

  it('health check', async () => {
    const r = await call('get', '/api/health');
    expect(r.status).toBe(200);
    expect(r.body.status).toBe('ok');
  });

  it('unknown route returns a JSON 404', async () => {
    const r = await call('get', '/api/does-not-exist');
    expect(r.status).toBe(404);
    expect(r.body.error.code).toBe('not_found');
  });

  if (SCHEMA.db) {
    it('malformed JSON returns a JSON 400', async () => {
      const res = await request(app.getHttpServer()).post('/api/auth/login').set('Content-Type', 'application/json').send('{"bad"');
      expect(res.status).toBe(400);
      expect(res.body.error.code).toBe('invalid_json');
    });
  }

  if (SCHEMA.auth) {
    it('register, login, me, refresh rotation, logout', async () => {
      const email = `a${rnd()}@example.com`;
      let r = await call('post', '/api/auth/register', { email, name: 'Test', password: PW });
      expect(r.status).toBe(201);
      expect(r.body.user.role).toBe(SCHEMA.defaultRole);
      expect(SCHEMA.defaultRole).not.toBe(SCHEMA.adminRole); // sign-up never creates an administrator
      expect('password_hash' in r.body.user).toBe(false);
      expect((await call('post', '/api/auth/register', { email, name: 'Test', password: PW })).status).toBe(409);
      expect((await call('post', '/api/auth/register', { email: 'bad', name: '', password: 'x' })).status).toBe(400);
      expect((await call('post', '/api/auth/register', { email: `b${rnd()}@example.com`, name: 'X', password: PW, role: SCHEMA.adminRole })).status).toBe(400);
      expect((await call('post', '/api/auth/login', { email, password: 'wrong-password' })).status).toBe(401);
      r = await call('post', '/api/auth/login', { email, password: PW });
      expect(r.status).toBe(200);
      const { accessToken, refreshToken } = r.body;
      expect((await call('get', '/api/auth/me')).status).toBe(401);
      expect((await call('get', '/api/auth/me', undefined, 'not-a-token')).status).toBe(401);
      expect((await call('get', '/api/auth/me', undefined, accessToken)).body.user.email).toBe(email);
      if (SCHEMA.refresh) {
        r = await call('post', '/api/auth/refresh', { refreshToken });
        expect(r.status).toBe(200);
        expect(r.body.refreshToken).not.toBe(refreshToken);
        expect((await call('post', '/api/auth/refresh', { refreshToken })).status).toBe(401); // single use
      }
      expect((await call('post', '/api/auth/logout', {}, accessToken)).status).toBe(204);
    });

    if (SCHEMA.entities.User.ops.includes('list')) {
      it('user list is admin only and never exposes password hashes', async () => {
        const admin = await makeUser(SCHEMA.adminRole);
        const user = await makeUser();
        expect((await call('get', '/api/users')).status).toBe(401);
        expect((await call('get', '/api/users', undefined, user.token)).status).toBe(403);
        const r = await call('get', '/api/users', undefined, admin.token);
        expect(r.status).toBe(200);
        expect(r.body.data.length).toBeGreaterThanOrEqual(2);
        expect(r.body.data.every((u: any) => !('password_hash' in u))).toBe(true);
      });
    }

    it('login rejects non-string credentials (operator injection)', async () => {
      expect((await call('post', '/api/auth/login', { email: { $ne: 'x' }, password: { $ne: 'x' } })).status).toBe(400);
    });
  }

  for (const e of Object.values(SCHEMA.entities).filter((x) => !x.internal && !x.isUser && x.ops.length)) {
    it(`${e.name}: access rules and CRUD`, async () => {
      const p = `/api/${e.path}`;
      const admin: any = SCHEMA.auth ? await makeUser(SCHEMA.adminRole) : { token: undefined };
      const user: any = SCHEMA.auth ? await makeUser() : { token: undefined };
      const fresh = () => values(e, true); // every request gets its own values (unique fields)
      const body = await fresh();
      const has = (op: string) => (e.ops as string[]).includes(op);

      if (has('list')) {
        expect((await call('get', p)).status).toBe(e.read === 'public' ? 200 : 401);
        if (e.read === 'admin') expect((await call('get', p, undefined, user.token)).status).toBe(403);
      }
      if (has('create')) {
        expect((await call('post', p, await fresh())).status).toBe(e.write === 'public' ? 201 : 401);
        if (e.write === 'admin') expect((await call('post', p, await fresh(), user.token)).status).toBe(403);
        expect((await call('post', p, { ...(await fresh()), bogus: 1 }, admin.token)).status).toBe(400); // unknown fields are rejected
        if (Object.keys(body).length) expect((await call('post', p, {}, admin.token)).status).toBe(400); // required fields
      }
      if (!has('create')) return;
      const made = await call('post', p, await fresh(), admin.token);
      expect(made.status).toBe(201);
      const id = made.body.id;
      expect(id).toBeDefined();
      if (e.ownerField && SCHEMA.auth) expect(String(made.body[e.ownerField])).toBe(String(admin.id));
      for (const s of e.sensitive) expect(s in made.body).toBe(false);

      if (has('get')) {
        expect((await call('get', `${p}/${id}`, undefined, admin.token)).status).toBe(200);
        expect((await call('get', `${p}/${SCHEMA.db === 'mongodb' ? '0'.repeat(24) : 999999999}`, undefined, admin.token)).status).toBe(404);
        expect((await call('get', `${p}/abc`, undefined, admin.token)).status).toBe(404);
      }
      if (has('list')) {
        const l = await call('get', `${p}?limit=5`, undefined, admin.token);
        expect(l.status).toBe(200);
        expect(Array.isArray(l.body.data) && l.body.total >= 1 && l.body.page === 1 && l.body.limit === 5).toBe(true);
        expect((await call('get', `${p}?limit=0`, undefined, admin.token)).status).toBe(400);
      }
      if (has('update') && Object.keys(body).length) {
        expect((await call('put', `${p}/${id}`, await fresh(), admin.token)).status).toBe(200);
        if (SCHEMA.auth) expect((await call('put', `${p}/${id}`, await fresh())).status).toBe(e.write === 'public' ? 200 : 401);
      }
      if (has('get') && e.ownerField && e.write === 'owner' && SCHEMA.auth) {
        const mine = await call('post', p, await fresh(), user.token);
        expect(mine.status).toBe(201);
        const other = await makeUser();
        expect((await call('get', `${p}/${mine.body.id}`, undefined, user.token)).status).toBe(200);
        expect((await call('get', `${p}/${mine.body.id}`, undefined, other.token)).status).toBe(404); // other users cannot see it
        expect((await call('get', `${p}/${mine.body.id}`, undefined, admin.token)).status).toBe(200);
      }
      if (has('delete')) {
        expect((await call('delete', `${p}/${id}`, undefined, admin.token)).status).toBe(204);
        if (has('get')) expect((await call('get', `${p}/${id}`, undefined, admin.token)).status).toBe(404);
      }
    });
  }
});
