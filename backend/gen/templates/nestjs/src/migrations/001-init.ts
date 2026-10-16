import { MigrationInterface, QueryRunner, Table, TableColumnOptions, TableIndexOptions } from 'typeorm';
import { sqlType } from '../db/column-types';
import { SCHEMA } from '../schema';

// Built from src/schema.ts (parents first, so foreign keys always point at an existing table).
const entities = Object.values(SCHEMA.entities);
const tableOf = (name: string): string => SCHEMA.entities[name].table;

export class InitMigration1700000000000 implements MigrationInterface {
  name = 'InitMigration1700000000000';

  async up(q: QueryRunner): Promise<void> {
    for (const e of entities) {
      const columns: TableColumnOptions[] = [{ name: 'id', ...sqlType({ type: 'int' }), isPrimary: true, isGenerated: true, generationStrategy: 'increment' }];
      const foreignKeys = [];
      const indices: TableIndexOptions[] = [];
      for (const f of e.fields) {
        // SQL Server allows one NULL per unique index, so an optional unique column gets a filtered index (several NULLs allowed, like the other databases).
        const filtered = SCHEMA.db === 'mssql' && f.unique && !f.required;
        columns.push({ name: f.name, ...sqlType(f), isNullable: !f.required, isUnique: f.unique && !filtered } as TableColumnOptions);
        if (filtered) indices.push({ name: `uq_${e.table}_${f.name}`, columnNames: [f.name], isUnique: true, where: `[${f.name}] IS NOT NULL` });
        else if (f.index) indices.push({ name: `idx_${e.table}_${f.name}`, columnNames: [f.name] });
        if (f.type === 'ref' && f.fk && f.ref) {
          foreignKeys.push({ columnNames: [f.name], referencedTableName: tableOf(f.ref), referencedColumnNames: ['id'], onDelete: f.onDelete ?? 'RESTRICT' });
        }
      }
      await q.createTable(new Table({ name: e.table, columns, foreignKeys, indices }), true);
    }
  }

  async down(q: QueryRunner): Promise<void> {
    for (const e of [...entities].reverse()) await q.dropTable(e.table, true, true, true);
  }
}
