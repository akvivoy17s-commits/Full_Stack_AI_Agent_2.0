import { SCHEMA } from '../schema';
import { Field } from '../common/types';

// One place decides the column type per database; the entity definitions and the migration both use it.
const TYPES = {
  sqlite: { int: 'integer', float: 'real', bool: 'boolean', datetime: 'datetime', text: 'text' },
  postgresql: { int: 'integer', float: 'double precision', bool: 'boolean', datetime: 'timestamptz', text: 'text' },
  mysql: { int: 'int', float: 'double', bool: 'boolean', datetime: 'datetime', text: 'mediumtext' },
  mssql: { int: 'int', float: 'float', bool: 'bit', datetime: 'datetime2', text: 'nvarchar' },
} as const;

export function sqlType(f: Pick<Field, 'type'>): { type: string; length?: string } {
  const t = TYPES[(SCHEMA.db as keyof typeof TYPES) ?? 'sqlite'];
  switch (f.type) {
    case 'string':
    case 'email':
      return { type: 'varchar', length: '255' };
    case 'enum':
      return { type: 'varchar', length: '64' };
    case 'url':
      return { type: 'varchar', length: '2048' };
    case 'text':
      return t.text === 'nvarchar' ? { type: 'nvarchar', length: 'MAX' } : { type: t.text };   // SQL Server: nvarchar(max)
    case 'int':
    case 'ref':
      return { type: t.int };
    case 'float':
      return { type: t.float };
    case 'bool':
      return { type: t.bool };
    default:
      return { type: t.datetime };
  }
}
