// SQL adapter (SQLite, PostgreSQL, MySQL, SQL Server) on TypeORM. Table and column names come from src/schema.ts only; every value is a bound parameter.
import { Brackets, DataSource, DataSourceOptions, EntitySchema, EntitySchemaColumnOptions, Repository } from 'typeorm';
import { Entity, Field } from '../common/types';
import { cfg } from '../config';
import { InitMigration1700000000000 } from '../migrations/001-init';
import { SCHEMA } from '../schema';
import { sqlType } from './column-types';
import { Db, ListOpts, Row, Tx } from './db';

const kind = SCHEMA.db as 'sqlite' | 'postgresql' | 'mysql' | 'mssql';
const E = SCHEMA.entities;
const entity = (n: string): Entity => {
  if (!E[n]) throw new Error(`unknown entity ${n}`);
  return E[n];
};
const esc = (s: string): string => s.replace(/[!%_]/g, '!$&');

function schemaOf(e: Entity): EntitySchema {
  const columns: Record<string, EntitySchemaColumnOptions> = {
    id: { ...sqlType({ type: 'int' }), primary: true, generated: 'increment' } as EntitySchemaColumnOptions,
  };
  for (const f of e.fields) columns[f.name] = { ...sqlType(f), nullable: !f.required } as EntitySchemaColumnOptions;
  return new EntitySchema({ name: e.name, tableName: e.table, columns });
}

function options(): DataSourceOptions {
  const common = { entities: Object.values(E).map(schemaOf), migrations: [InitMigration1700000000000], synchronize: false, logging: false };
  const url = cfg.databaseUrl;
  if (kind === 'sqlite') {
    const database = url.replace(/^sqlite:\/\/\//, '').replace(/^sqlite:\/\//, '') || ':memory:';
    return { type: 'better-sqlite3', database, ...common };
  }
  if (kind === 'postgresql') return { type: 'postgres', url, ssl: process.env.DATABASE_SSL === 'true', ...common } as DataSourceOptions;
  if (kind === 'mssql') {      // mssql://user:pass@host:1433/db (local servers use self-signed certificates)
    const x = new URL(url);
    const ssl = process.env.DATABASE_SSL === 'true';
    return { type: 'mssql', host: x.hostname, port: x.port ? Number(x.port) : 1433, username: decodeURIComponent(x.username), password: decodeURIComponent(x.password),
      database: x.pathname.replace(/^\//, ''), options: { encrypt: ssl || x.searchParams.get('encrypt') === 'true', trustServerCertificate: !ssl }, ...common } as DataSourceOptions;
  }
  return { type: 'mysql', url, timezone: 'Z', charset: 'utf8mb4', ...common } as DataSourceOptions;
}

// SQLite and MySQL store booleans as 0/1; bound WHERE parameters are not converted by TypeORM, so do it here.
const whereValue = (f: Field | undefined, v: unknown): unknown => (f?.type === 'bool' && kind !== 'postgresql' ? (v ? 1 : 0) : v);

function fromRow(e: Entity, row: Row | null | undefined, raw?: boolean): Row | null {
  if (!row) return null;
  const o: Row = { id: row.id };
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

export async function connect(): Promise<Db> {
  const ds = new DataSource(options());
  await ds.initialize();
  if (cfg.autoMigrate) await ds.runMigrations();
  const repo = (n: string): Repository<Row> => ds.getRepository<Row>(entity(n).name);

  // Values as stored: datetimes become Date objects (TypeORM writes them in the right format for each driver).
  const row = (e: Entity, data: Row): Row =>
    Object.fromEntries(e.fields.filter((f) => f.name in data).map((f) => [f.name, f.type === 'datetime' && data[f.name] != null ? new Date(data[f.name]) : data[f.name]]));
  const cond = (e: Entity, where: Row): Row =>
    Object.fromEntries(Object.entries(where).map(([k, v]) => [k, whereValue(e.fields.find((x) => x.name === k), v)]));
  const apply = (e: Entity, qb: ReturnType<Repository<Row>['createQueryBuilder']>, where: Row): void => {
    Object.entries(cond(e, where)).forEach(([k, v], i) => {
      if (!e.fields.some((f) => f.name === k) && k !== 'id') throw new Error(`unknown column ${k}`);
      if (v === null) qb.andWhere(`t.${k} IS NULL`);
      else qb.andWhere(`t.${k} = :w${i}`, { [`w${i}`]: v });
    });
  };

  const api: Db = {
    kind,
    parseId(v) {
      const n = Number(v);
      return typeof v !== 'object' && Number.isInteger(n) && n > 0 && n <= 2147483647 ? n : null;
    },
    clean: (name, r) => fromRow(entity(name), r, false) as Row,
    async get(name, id, opt = {}) {
      return fromRow(entity(name), await repo(name).findOneBy({ id } as never), opt.raw);
    },
    async findOne(name, where, opt = {}) {
      const e = entity(name);
      const qb = repo(name).createQueryBuilder('t');
      apply(e, qb, where);
      return fromRow(e, await qb.getOne(), opt.raw);
    },
    async list(name, { where = {}, filters = {}, q, page = 1, limit = 20, sort = { field: 'id', dir: 'desc' } }: ListOpts = {}) {
      const e = entity(name);
      const qb = repo(name).createQueryBuilder('t');
      apply(e, qb, { ...where, ...filters });
      if (q && e.searchable.length) {
        const pat = `%${esc(q.toLowerCase())}%`;
        qb.andWhere(new Brackets((b) => e.searchable.forEach((f) => b.orWhere(`LOWER(t.${f}) LIKE :q ESCAPE '!'`, { q: pat }))));
      }
      const total = await qb.getCount();
      qb.orderBy(`t.${sort.field}`, sort.dir === 'asc' ? 'ASC' : 'DESC');
      if (sort.field !== 'id') qb.addOrderBy('t.id', 'DESC');
      const rows = await qb.skip((page - 1) * limit).take(limit).getMany();
      return { rows: rows.map((r) => fromRow(e, r) as Row), total };
    },
    async create(name, data) {
      const r = await repo(name).insert(row(entity(name), data) as never);
      return (await api.get(name, r.identifiers[0].id)) as Row;
    },
    async update(name, id, data) {
      const d = row(entity(name), data);
      if (Object.keys(d).length) await repo(name).update({ id } as never, d as never);
      return api.get(name, id);
    },
    async remove(name, id) {
      const r = await repo(name).delete(id);
      return typeof r.affected === 'number' ? r.affected > 0 : true;
    },
    async removeWhere(name, where) {
      const e = entity(name);
      const before = await repo(name).countBy(cond(e, where) as never);
      const r = await repo(name).delete(cond(e, where) as never);
      return typeof r.affected === 'number' ? r.affected : before;
    },
    async updateWhere(name, where, data) {
      const e = entity(name);
      const d = row(e, data);
      if (!Object.keys(d).length) return 0;
      const r = await repo(name).update(cond(e, where) as never, d as never);
      return typeof r.affected === 'number' ? r.affected : 0;
    },
    // Everything inside fn commits together or not at all (any throw rolls back).
    tx: (fn) =>
      ds.transaction((em) => {
        const r = (n: string): Repository<Row> => em.getRepository<Row>(entity(n).name);
        const t: Tx = {
          async lock(name, ids) {
            const qb = r(name).createQueryBuilder('t').where('t.id IN (:...ids)', { ids });
            if (kind !== 'sqlite') qb.setLock('pessimistic_write');   // SQLite serialises writers itself
            return qb.getMany();
          },
          async insert(name, data) {
            const x = await r(name).insert(row(entity(name), data) as never);
            return Number(x.identifiers[0].id);
          },
          async take(name, id, field, qty) {
            if (!entity(name).fields.some((f) => f.name === field) || !Number.isInteger(qty) || qty < 1) throw new Error('invalid stock update');
            const x = await r(name).createQueryBuilder().update().set({ [field]: () => `${field} - ${qty}` } as never).where(`id = :id AND ${field} >= :qty`, { id, qty }).execute();
            return Number(x.affected) === 1;
          },
        };
        return fn(t);
      }),
    migrate: async () => {
      await ds.runMigrations();
    },
    ping: () => ds.query('select 1'),
    close: async () => {
      if (ds.isInitialized) await ds.destroy();
    },
  };
  return api;
}
