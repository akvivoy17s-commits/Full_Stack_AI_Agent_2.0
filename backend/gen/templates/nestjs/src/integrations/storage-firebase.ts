// Firebase Storage through the Admin SDK: a PRIVATE bucket, files are only served through the API.
// The service-account key comes from a file path in the environment and is never logged, returned or committed.
import { readFileSync } from 'fs';
import { cfg } from '../config';

export class StorageError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let admin: any = null;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function sdk(): any {
  if (admin) return admin;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let a: any;
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    a = require('firebase-admin');
  } catch {
    throw new StorageError(503, 'firebase_unavailable', 'Firebase is not available on this server');
  }
  const f = cfg.firebase;
  try {
    const opts: Record<string, unknown> = { credential: f.serviceAccountPath ? a.credential.cert(JSON.parse(readFileSync(f.serviceAccountPath, 'utf8'))) : a.credential.applicationDefault() };
    if (f.projectId) opts.projectId = f.projectId;
    if (f.storageBucket) opts.storageBucket = f.storageBucket;
    if (!a.apps.length) a.initializeApp(opts);
  } catch {
    throw new StorageError(503, 'storage_unavailable', 'File storage is not configured');
  }
  admin = a;
  return admin;
}

export const store = {
  async put(key: string, body: Buffer, contentType: string): Promise<void> {
    try {
      await sdk().storage().bucket().file(key).save(body, { contentType, resumable: false });
    } catch (e) {
      if (e instanceof StorageError) throw e;
      throw new StorageError(502, 'storage_error', 'The file storage rejected the request');
    }
  },
  async get(key: string): Promise<Buffer | null> {
    try {
      const [buf] = await sdk().storage().bucket().file(key).download();
      return buf as Buffer;
    } catch (e) {
      if (e instanceof StorageError) throw e;
      const c = (e as { code?: number | string }).code;
      if (c === 404 || c === 'ENOENT') return null;
      throw new StorageError(502, 'storage_error', 'The file storage rejected the request');
    }
  },
};
