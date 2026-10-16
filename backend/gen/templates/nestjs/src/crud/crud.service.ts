import { Inject, Injectable } from '@nestjs/common';
import { isAdmin } from '../auth/access';
import { HttpError } from '../common/http-error';
import { Access, AuthUser, Entity } from '../common/types';
import { parseList, validateBody } from '../common/validate';
import { DB, Db, Row } from '../db/db';

const has = (e: Entity, n: string): boolean => e.fields.some((f) => f.name === n);
const notFound = () => new HttpError(404, 'not_found', 'Record not found');

// Generic, spec-driven CRUD. Access is enforced here on the server: public | user | owner | admin.
@Injectable()
export class CrudService {
  constructor(@Inject(DB) private readonly db: Db) {}

  // Owner-scoped entities only expose the caller's own records to non-admins.
  private scope(e: Entity, user?: AuthUser): Row {
    return e.read === 'owner' && e.ownerField && user && !isAdmin(user) ? { [e.ownerField]: this.db.parseId(user.id) } : {};
  }

  private mine(e: Entity, rec: Row, user: AuthUser | undefined, level: Access): boolean {
    return level !== 'owner' || !e.ownerField || isAdmin(user) || (!!user && String(rec[e.ownerField]) === String(user.id));
  }

  private async checkRefs(e: Entity, data: Row): Promise<void> {
    const errors: Record<string, string> = {};
    for (const f of e.fields) {
      if (f.type === 'ref' && data[f.name] != null && f.ref && !(await this.db.get(f.ref, data[f.name]))) errors[f.name] = 'refers to a record that does not exist';
    }
    if (Object.keys(errors).length) throw new HttpError(400, 'validation_failed', 'Invalid input', errors);
  }

  private async load(e: Entity, rawId: string, user: AuthUser | undefined, level: Access): Promise<Row> {
    const id = this.db.parseId(rawId);
    const rec = id == null ? null : await this.db.get(e.name, id);
    if (!rec || !this.mine(e, rec, user, level)) throw notFound(); // 404, not 403: do not reveal other users' records
    return rec;
  }

  async list(e: Entity, query: Record<string, unknown>, user?: AuthUser) {
    const o = parseList(e, query);
    const r = await this.db.list(e.name, { ...o, where: this.scope(e, user) });
    return { data: r.rows, page: o.page, limit: o.limit, total: r.total };
  }

  get(e: Entity, id: string, user?: AuthUser): Promise<Row> {
    return this.load(e, id, user, e.read);
  }

  async create(e: Entity, body: unknown, user?: AuthUser): Promise<Row> {
    const data = validateBody(e, body, false);
    await this.checkRefs(e, data);
    if (e.ownerField && user) data[e.ownerField] = this.db.parseId(user.id);
    if (has(e, 'created_at')) data.created_at = new Date().toISOString();
    return this.db.create(e.name, data);
  }

  async update(e: Entity, id: string, body: unknown, user?: AuthUser): Promise<Row | null> {
    await this.load(e, id, user, e.write);
    const data = validateBody(e, body, true);
    await this.checkRefs(e, data);
    if (has(e, 'updated_at')) data.updated_at = new Date().toISOString();
    return this.db.update(e.name, this.db.parseId(id) as number | string, data);
  }

  async remove(e: Entity, id: string, user?: AuthUser): Promise<void> {
    await this.load(e, id, user, e.write);
    await this.db.remove(e.name, this.db.parseId(id) as number | string);
  }
}
