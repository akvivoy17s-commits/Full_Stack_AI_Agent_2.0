const { HttpError } = require('../lib/http');

// Translate driver errors (SQLite, PostgreSQL, MySQL, SQL Server, MongoDB) into client errors. Returns null for anything else.
function mapDbError(err) {
  if (!err) return null;
  const code = String(err.code || '');
  const msg = String(err.message || '');
  const num = Number(err.number || (err.originalError && err.originalError.number) || 0);   // SQL Server (tedious)
  if (['23505', 'ER_DUP_ENTRY', 'SQLITE_CONSTRAINT_UNIQUE', 'SQLITE_CONSTRAINT_PRIMARYKEY', '11000'].includes(code) || num === 2627 || num === 2601 || /UNIQUE constraint failed/.test(msg)) {
    return new HttpError(409, 'conflict', 'A record with the same unique value already exists');
  }
  if (['23503', 'ER_ROW_IS_REFERENCED_2', 'ER_NO_REFERENCED_ROW_2', 'SQLITE_CONSTRAINT_FOREIGNKEY'].includes(code) || num === 547 || /FOREIGN KEY constraint failed/.test(msg)) {
    return new HttpError(409, 'conflict', 'The record is referenced by, or references, another record');
  }
  return null;
}
module.exports = { mapDbError };
