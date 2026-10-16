// Generated tests: they read src/schema.js, so they cover every entity and access rule of THIS app.
// SQLite runs in memory. For PostgreSQL / MySQL / MongoDB set TEST_DATABASE_URL to a disposable database.
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret-' + 'x'.repeat(40);
process.env.CORS_ORIGINS = 'http://localhost:5173';
process.env.AUTO_MIGRATE = 'true';

const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const schema = require('../src/schema');

const skip = schema.db && schema.db !== 'sqlite' && !process.env.TEST_DATABASE_URL ? 'set TEST_DATABASE_URL to run the database tests' : false;
if (schema.db === 'sqlite') process.env.DATABASE_URL = 'sqlite:///:memory:';
else if (process.env.TEST_DATABASE_URL) process.env.DATABASE_URL = process.env.TEST_DATABASE_URL;

if (skip) {
  test('database tests', { skip }, () => {});
} else {
  const bcrypt = schema.auth ? require('bcryptjs') : null;
  let db;
  let server;
  let base;
  let seq = 0;
  const PW = 'Passw0rd!long';
  const rnd = () => `${++seq}${Math.floor(Math.random() * 1e9)}`;

  before(async () => {
    db = schema.db ? await require('../src/db').connect() : null;
    const app = require('../src/app').createApp(db);
    server = await new Promise((resolve) => { const s = app.listen(0, '127.0.0.1', () => resolve(s)); });
    base = `http://127.0.0.1:${server.address().port}`;
  });
  after(async () => {
    if (server) await new Promise((resolve) => server.close(resolve));
    if (db) await db.close();
  });

  const call = async (method, path, body, token) => {
    const res = await fetch(base + path, {
      method,
      headers: { 'content-type': 'application/json', ...(token && { authorization: `Bearer ${token}` }) },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    let json = null;
    try { json = await res.json(); } catch (e) { /* 204 */ }
    return { status: res.status, body: json };
  };

  const sample = (f) => ({
    string: `s${rnd()}`, text: `text ${rnd()}`, email: `e${rnd()}@example.com`, url: `https://example.com/${rnd()}`,
    int: Number(rnd().slice(0, 9)), float: 1.5, bool: true, datetime: new Date().toISOString(),
  }[f.type]);

  // Required values for an entity. api=true leaves out what the server sets itself.
  async function values(e, api) {
    const o = {};
    for (const f of e.fields) {
      if (!f.required) continue;
      if (api && (f.name === e.ownerField || e.sensitive.includes(f.name) || f.name === 'created_at')) continue;
      if (f.type === 'ref') o[f.name] = (await fixture(schema.entities[f.ref])).id;
      else if (f.type === 'enum') o[f.name] = f.values[0];
      else if (f.name === 'password_hash') o[f.name] = await bcrypt.hash(PW, 4);
      else if (f.name === 'created_at') o[f.name] = new Date().toISOString();
      else o[f.name] = sample(f);
    }
    return o;
  }
  const fixture = async (e) => db.create(e.name, await values(e, false));

  async function makeUser(role) {
    const email = `u${rnd()}@example.com`;
    if (role) {
      await db.create('User', { email, name: 'Seeded', password_hash: await bcrypt.hash(PW, 4), role, created_at: new Date().toISOString() });
    } else {
      assert.equal((await call('POST', '/api/auth/register', { email, name: 'Test User', password: PW })).status, 201);
    }
    const r = await call('POST', '/api/auth/login', { email, password: PW });
    assert.equal(r.status, 200);
    return { token: r.body.accessToken, id: r.body.user.id, email };
  }

  test('health check', async () => {
    const r = await call('GET', '/api/health');
    assert.equal(r.status, 200);
    assert.equal(r.body.status, 'ok');
  });
  test('unknown route returns a JSON 404', async () => {
    const r = await call('GET', '/api/does-not-exist');
    assert.equal(r.status, 404);
    assert.equal(r.body.error.code, 'not_found');
  });

  if (schema.auth) {
    test('register, login, me, refresh rotation, logout', async () => {
      const email = `a${rnd()}@example.com`;
      let r = await call('POST', '/api/auth/register', { email, name: 'Test', password: PW });
      assert.equal(r.status, 201);
      assert.equal(r.body.user.role, schema.defaultRole);
      assert.notEqual(schema.defaultRole, schema.adminRole); // sign-up never creates an administrator
      assert.ok(!('password_hash' in r.body.user));
      assert.equal((await call('POST', '/api/auth/register', { email, name: 'Test', password: PW })).status, 409);
      assert.equal((await call('POST', '/api/auth/register', { email: 'bad', name: '', password: 'x' })).status, 400);
      assert.equal((await call('POST', '/api/auth/register', { email: `b${rnd()}@example.com`, name: 'X', password: PW, role: schema.adminRole })).status, 400);
      assert.equal((await call('POST', '/api/auth/login', { email, password: 'wrong-password' })).status, 401);
      r = await call('POST', '/api/auth/login', { email, password: PW });
      assert.equal(r.status, 200);
      const { accessToken, refreshToken } = r.body;
      assert.equal((await call('GET', '/api/auth/me')).status, 401);
      assert.equal((await call('GET', '/api/auth/me', undefined, 'not-a-token')).status, 401);
      assert.equal((await call('GET', '/api/auth/me', undefined, accessToken)).body.user.email, email);
      if (schema.refresh) {
        r = await call('POST', '/api/auth/refresh', { refreshToken });
        assert.equal(r.status, 200);
        assert.notEqual(r.body.refreshToken, refreshToken);
        assert.equal((await call('POST', '/api/auth/refresh', { refreshToken })).status, 401); // single use
      }
      assert.equal((await call('POST', '/api/auth/logout', {}, accessToken)).status, 204);
    });
    if (schema.entities.User.ops.includes('list')) {
      test('user list is admin only and never exposes password hashes', async () => {
        const admin = await makeUser(schema.adminRole);
        const user = await makeUser();
        assert.equal((await call('GET', '/api/users')).status, 401);
        assert.equal((await call('GET', '/api/users', undefined, user.token)).status, 403);
        const r = await call('GET', '/api/users', undefined, admin.token);
        assert.equal(r.status, 200);
        assert.ok(r.body.data.length >= 2 && r.body.data.every((u) => !('password_hash' in u)));
      });
    }
    test('login rejects non-string credentials (operator injection)', async () => {
      const r = await call('POST', '/api/auth/login', { email: { $ne: 'x' }, password: { $ne: 'x' } });
      assert.equal(r.status, 400);
    });
  }

  if (schema.checkout) {
    test('checkout uses server prices, ownership and a stock-safe transaction', async () => {
      const user = await makeUser();
      const product = await db.create('Product', {
        name: `Checkout ${rnd()}`, description: 'test product', price: 12.5, stock: 3, active: true,
      });
      assert.equal((await call('POST', '/api/checkout', { items: [{ productId: product.id, quantity: 2 }] })).status, 401);
      const r = await call('POST', '/api/checkout', {
        total: 0.01, items: [{ productId: product.id, quantity: 2, price: 0.01 }],
      }, user.token);
      assert.equal(r.status, 201, JSON.stringify(r.body));
      assert.equal(r.body.order.total, 25);
      assert.equal(r.body.order.status, 'pending');
      const stored = await db.get('Product', product.id);
      assert.equal(Number(stored.stock), 1);
      const items = await db.list('OrderItem', { where: { order_id: r.body.order.orderId }, page: 1, limit: 10 });
      assert.equal(items.total, 1);
      assert.equal(String(items.rows[0].user_id), String(user.id));
      assert.equal(Number(items.rows[0].unit_price), 12.5);
      const rejected = await call('POST', '/api/checkout', { items: [{ productId: product.id, quantity: 2 }] }, user.token);
      assert.equal(rejected.status, 409);
      assert.equal(Number((await db.get('Product', product.id)).stock), 1); // rollback leaves stock unchanged
    });
  }

  for (const e of Object.values(schema.entities).filter((x) => !x.internal && !x.isUser && x.ops.length)) {
    test(`${e.name}: access rules and CRUD`, async () => {
      const p = `/api/${e.path}`;
      const admin = schema.auth ? await makeUser(schema.adminRole) : { token: undefined };
      const user = schema.auth ? await makeUser() : { token: undefined };
      const fresh = () => values(e, true); // every request gets its own values (unique fields)
      const body = await fresh();
      const has = (op) => e.ops.includes(op);

      if (has('list')) {
        const anon = await call('GET', p);
        assert.equal(anon.status, e.read === 'public' ? 200 : 401);
        if (e.read === 'admin') assert.equal((await call('GET', p, undefined, user.token)).status, 403);
      }
      if (has('create')) {
        assert.equal((await call('POST', p, await fresh())).status, e.write === 'public' ? 201 : 401);
        if (e.write === 'admin') assert.equal((await call('POST', p, await fresh(), user.token)).status, 403);
        assert.equal((await call('POST', p, { ...(await fresh()), bogus: 1 }, admin.token)).status, 400); // unknown fields are rejected
        if (Object.keys(body).length) assert.equal((await call('POST', p, {}, admin.token)).status, 400); // required fields
      }
      if (!has('create')) return;
      const made = await call('POST', p, await fresh(), admin.token);
      assert.equal(made.status, 201);
      const id = made.body.id;
      assert.ok(id !== undefined);
      if (e.ownerField && schema.auth) assert.equal(String(made.body[e.ownerField]), String(admin.id));
      for (const s of e.sensitive) assert.ok(!(s in made.body));

      if (has('get')) {
        assert.equal((await call('GET', `${p}/${id}`, undefined, admin.token)).status, 200);
        assert.equal((await call('GET', `${p}/${schema.db === 'mongodb' ? '0'.repeat(24) : 999999999}`, undefined, admin.token)).status, 404);
        assert.equal((await call('GET', `${p}/abc`, undefined, admin.token)).status, 404);
      }
      if (has('list')) {
        const l = await call('GET', `${p}?limit=5`, undefined, admin.token);
        assert.equal(l.status, 200);
        assert.ok(Array.isArray(l.body.data) && l.body.total >= 1 && l.body.page === 1 && l.body.limit === 5);
        assert.equal((await call('GET', `${p}?limit=0`, undefined, admin.token)).status, 400);
      }
      if (has('update') && Object.keys(body).length) {
        assert.equal((await call('PUT', `${p}/${id}`, await fresh(), admin.token)).status, 200);
        if (schema.auth) assert.equal((await call('PUT', `${p}/${id}`, await fresh())).status, e.write === 'public' ? 200 : 401);
      }
      if (has('get') && e.ownerField && e.write === 'owner' && schema.auth) {
        const mine = await call('POST', p, await fresh(), user.token);
        assert.equal(mine.status, 201);
        const other = await makeUser();
        assert.equal((await call('GET', `${p}/${mine.body.id}`, undefined, user.token)).status, 200);
        assert.equal((await call('GET', `${p}/${mine.body.id}`, undefined, other.token)).status, 404); // other users cannot see it
        assert.equal((await call('GET', `${p}/${mine.body.id}`, undefined, admin.token)).status, 200);
      }
      if (has('delete')) {
        assert.equal((await call('DELETE', `${p}/${id}`, undefined, admin.token)).status, 204);
        if (has('get')) assert.equal((await call('GET', `${p}/${id}`, undefined, admin.token)).status, 404);
      }
    });
  }
}
