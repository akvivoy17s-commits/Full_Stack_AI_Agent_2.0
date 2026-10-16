export type FieldType = 'string' | 'text' | 'email' | 'url' | 'int' | 'float' | 'bool' | 'datetime' | 'enum' | 'ref';
export type Access = 'public' | 'user' | 'owner' | 'admin';
export type Op = 'list' | 'get' | 'create' | 'update' | 'delete';

export interface Field {
  name: string;
  type: FieldType;
  required: boolean;
  unique: boolean;
  values?: string[];
  ref?: string;
  fk?: boolean;
  index?: boolean;
  onDelete?: 'CASCADE' | 'RESTRICT' | 'SET NULL' | 'NO ACTION';
}

export interface Entity {
  name: string;
  table: string;
  path: string;
  fields: Field[];
  read: Access;
  write: Access;
  searchable: string[];
  sensitive: string[];
  ownerField: string | null;
  isUser: boolean;
  internal: boolean;
  ops: Op[];
}

export interface Schema {
  db: 'sqlite' | 'postgresql' | 'mysql' | 'mssql' | 'mongodb' | null;
  auth: boolean;
  refresh: boolean;
  roles: string[];
  adminRole: string;
  defaultRole: string;
  entities: Record<string, Entity>;
  integrations: { cache: boolean; uploads: boolean; payments: boolean; ws: boolean };
  checkout: boolean;
  seed: { entity: string; rows: Record<string, unknown>[] }[];
}

export interface AuthUser {
  id: string;
  role: string;
}

// What controllers read from the request: the user set by AuthGuard (undefined on public routes).
export interface AuthedRequest {
  user?: AuthUser;
}
