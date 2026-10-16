import { HttpError } from './http-error';

// Translate driver errors (SQLite, PostgreSQL, MySQL, SQL Server, MongoDB) into client errors. Returns null for anything else.
export function mapDbError(err: unknown): HttpError | null {
  const e = err as { code?: unknown; message?: unknown; driverError?: { code?: unknown; number?: unknown } } | null;
  if (!e) return null;
  const code = String(e.code ?? e.driverError?.code ?? '');
  const msg = String(e.message ?? '');
  const num = Number(e.driverError?.number ?? 0); // SQL Server (mssql driver)
  if (['23505', 'ER_DUP_ENTRY', 'SQLITE_CONSTRAINT_UNIQUE', 'SQLITE_CONSTRAINT_PRIMARYKEY', '11000'].includes(code) || num === 2627 || num === 2601 || /UNIQUE constraint failed/.test(msg)) {
    return new HttpError(409, 'conflict', 'A record with the same unique value already exists');
  }
  if (['23503', 'ER_ROW_IS_REFERENCED_2', 'ER_NO_REFERENCED_ROW_2', 'SQLITE_CONSTRAINT_FOREIGNKEY'].includes(code) || num === 547 || /FOREIGN KEY constraint failed/.test(msg)) {
    return new HttpError(409, 'conflict', 'The record is referenced by, or references, another record');
  }
  return null;
}
