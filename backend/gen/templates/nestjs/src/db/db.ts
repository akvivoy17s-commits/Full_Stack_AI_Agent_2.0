// The data-access contract. src/db/typeorm.db.ts (SQL) and src/db/mongoose.db.ts (MongoDB) implement it; services never see a driver.
export type Row = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

export interface ListOpts {
  where?: Row;
  filters?: Row;
  q?: string;
  page?: number;
  limit?: number;
  sort?: { field: string; dir: 'asc' | 'desc' };
}

// Minimal transaction surface for checkout (SQL only): row locks, inserts and a conditional decrement that cannot go below zero.
export interface Tx {
  lock(name: string, ids: number[]): Promise<Row[]>;
  insert(name: string, data: Row): Promise<number>;
  take(name: string, id: number, field: string, qty: number): Promise<boolean>;
}

export interface Db {
  kind: string;
  parseId(v: unknown): number | string | null;
  clean(name: string, row: Row): Row;
  get(name: string, id: number | string, opt?: { raw?: boolean }): Promise<Row | null>;
  findOne(name: string, where: Row, opt?: { raw?: boolean }): Promise<Row | null>;
  list(name: string, opts?: ListOpts): Promise<{ rows: Row[]; total: number }>;
  create(name: string, data: Row): Promise<Row>;
  update(name: string, id: number | string, data: Row): Promise<Row | null>;
  remove(name: string, id: number | string): Promise<boolean>;
  removeWhere(name: string, where: Row): Promise<number>;
  updateWhere?(name: string, where: Row, data: Row): Promise<number>;
  tx?<T>(fn: (t: Tx) => Promise<T>): Promise<T>;
  migrate(): Promise<void>;
  ping(): Promise<unknown>;
  close(): Promise<void>;
}

export const DB = Symbol('DB');
