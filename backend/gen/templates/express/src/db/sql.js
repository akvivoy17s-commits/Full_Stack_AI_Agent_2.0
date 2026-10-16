// SQL adapter (SQLite, PostgreSQL, MySQL, SQL Server) on Knex. Every query is parameterised; table and column names come from src/schema.js only.
const path = require('path');
const knexLib = require('knex');
const schema = require('../schema');
const cfg = require('../config');

const kind = schema.db;
const E = schema.entities;
const CLIENT = { sqlite: 'better-sqlite3', postgresql: 'pg', mysql: 'mysql2', mssql: 'mssql' }[kind];

function connection() {
  const u = cfg.databaseUrl;
  if (kind === 'sqlite') return { filename: u.replace(/^sqlite:\/\/\//, '').replace(/^sqlite:\/\//, '') || ':memory:' };
  const x = new URL(u);
  if (kind === 'mssql') {      // mssql://user:pass@host:1433/db  (tedious driver; local servers use self-signed certificates)
    const ssl = process.env.DATABASE_SSL === 'true';
    return { server: x.hostname, port: x.port ? Number(x.port) : 1433, user: decodeURIComponent(x.username), password: decodeURIComponent(x.password),
      database: x.pathname.replace(/^\//, ''), options: { encrypt: ssl || x.searchParams.get('encrypt') === 'true', trustServerCertificate: !ssl } };
  }
  const c = { host: x.hostname, user: decodeURIComponent(x.username), password: decodeURIComponent(x.password), database: x.pathname.replace(/^\//, '') };
  if (x.port) c.port = Number(x.port);
  if (kind === 'postgresql' && process.env.DATABASE_SSL === 'true') c.ssl = true;
  if (kind === 'mysql') Object.assign(c, { timezone: 'Z', charset: 'utf8mb4' });
  return c;
}

const stamp = (d) => (kind === 'mssql' ? d : kind === 'mysql' ? d.toISOString().slice(0, 19).replace('T', ' ') : d.toISOString());
function toDb(f, v) {
  if (v === null || v === undefined) return null;
  if (f.type === 'datetime') return stamp(new Date(v));
  if (f.type === 'bool') return kind === 'postgresql' ? !!v : v ? 1 : 0;
  return v;
}

function fromRow(e, row, raw) {
  if (!row) return null;
  const o = { id: row.id };
  for (const f of e.fields) {
    if (!raw && e.sensitive.includes(f.name)) continue;
    let v = row[f.name];
    if (v === undefined) continue;
    if (v !== null) {
      if (f.type === 'bool') v = !!v;
      else if (f.type === 'datetime') v = new Date(v).toISOString();
    }
    o[f.name] = v;
  }
  return o;
}

const entity = (n) => {
  if (!E[n]) throw new Error(`unknown entity ${n}`);
  return E[n];
};
const esc = (s) => s.replace(/[!%_]/g, '!$&');

async function migrate(db) {
  await db.migrate.latest({ directory: path.join(__dirname, '..', '..', 'migrations') });
}

async function connect() {
  const db = knexLib({
    client: CLIENT,
    connection: connection(),
    useNullAsDefault: true,
    pool: kind === 'sqlite'
      ? { min: 1, max: 1, afterCreate: (conn, done) => { conn.pragma('foreign_keys = ON'); done(null, conn); } }
      : { min: 0, max: 10 },
  });
  await db.raw('select 1');
  if (cfg.autoMigrate) await migrate(db);

  const row = (e, data) => Object.fromEntries(e.fields.filter((f) => f.name in data).map((f) => [f.name, toDb(f, data[f.name])]));
  const cond = (e, where) => Object.fromEntries(Object.entries(where).map(([k, v]) => {
    const f = e.fields.find((x) => x.name === k);
    return [k, f ? toDb(f, v) : v];
  }));

  const api = {
    kind,
    knex: db,
    parseId(v) {
      const n = Number(v);
      return typeof v !== 'object' && Number.isInteger(n) && n > 0 && n <= 2147483647 ? n : null;
    },
    clean: (name, r) => fromRow(entity(name), r, false),
    async get(name, id, opt = {}) {
      return fromRow(entity(name), await db(entity(name).table).where({ id }).first(), opt.raw);
    },
    async findOne(name, where, opt = {}) {
      const e = entity(name);
      return fromRow(e, await db(e.table).where(cond(e, where)).first(), opt.raw);
    },
    async list(name, { where = {}, filters = {}, q, page = 1, limit = 20, sort = { field: 'id', dir: 'desc' } } = {}) {
      const e = entity(name);
      const qb = db(e.table).where(cond(e, { ...where, ...filters }));
      if (q && e.searchable.length) {
        const pat = `%${esc(q.toLowerCase())}%`;
        qb.where((b) => e.searchable.forEach((f, i) => b[i ? 'orWhereRaw' : 'whereRaw']("LOWER(??) LIKE ? ESCAPE '!'", [f, pat])));
      }
      const total = Number((await qb.clone().count({ c: '*' }).first()).c);
      qb.orderBy(sort.field, sort.dir);
      if (sort.field !== 'id') qb.orderBy('id', 'desc'); // stable pages
      const rows = await qb.limit(limit).offset((page - 1) * limit);
      return { rows: rows.map((r) => fromRow(e, r)), total };
    },
    async create(name, data) {
      const e = entity(name);
      const ins = db(e.table).insert(row(e, data));
      const r = kind === 'postgresql' || kind === 'mssql' ? await ins.returning('id') : await ins;
      const id = typeof r[0] === 'object' ? r[0].id : r[0];
      return api.get(name, id);
    },
    async update(name, id, data) {
      const e = entity(name);
      const d = row(e, data);
      if (Object.keys(d).length) await db(e.table).where({ id }).update(d);
      return api.get(name, id);
    },
    async remove(name, id) {
      return (await db(entity(name).table).where({ id }).del()) > 0;
    },
    async removeWhere(name, where) {
      const e = entity(name);
      return db(e.table).where(cond(e, where)).del();
    },
    migrate: () => migrate(db),
    ping: () => db.raw('select 1'),
    close: () => db.destroy(),
  };
  return api;
}

module.exports = { connect };
