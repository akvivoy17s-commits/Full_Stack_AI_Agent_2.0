const fs = require('fs');
const cfg = require('../config');
const { HttpError } = require('./http');

// Firebase Admin SDK: verifies Firebase ID tokens (sign-in) and stores uploads in a PRIVATE Firebase Storage bucket.
// The service-account key comes from a file path in the environment and is never logged, returned or committed.
let admin = null;
function sdk() {
  if (admin) return admin;
  let a;
  try {
    a = require('firebase-admin');
  } catch {
    throw new HttpError(503, 'firebase_unavailable', 'Firebase is not available on this server');
  }
  const f = cfg.firebase;
  const opts = { credential: f.serviceAccountPath ? a.credential.cert(JSON.parse(fs.readFileSync(f.serviceAccountPath, 'utf8'))) : a.credential.applicationDefault() };
  if (f.projectId) opts.projectId = f.projectId;
  if (f.storageBucket) opts.storageBucket = f.storageBucket;
  if (!a.apps.length) a.initializeApp(opts);
  admin = a;
  return admin;
}

// Throws on a bad, expired or revoked token (the caller answers 401 without leaking the reason).
async function verifyIdToken(idToken) {
  return sdk().auth().verifyIdToken(idToken, true);
}

const bucket = () => sdk().storage().bucket();
const storage = {
  async put(key, body, contentType) {
    try {
      await bucket().file(key).save(body, { contentType, resumable: false });
    } catch (e) {
      if (e instanceof HttpError) throw e;
      throw new HttpError(502, 'storage_error', 'The file storage rejected the request');
    }
  },
  async get(key) {
    try {
      const [buf] = await bucket().file(key).download();
      return buf;
    } catch (e) {
      if (e instanceof HttpError) throw e;
      if (e && (e.code === 404 || e.code === 'ENOENT')) return null;
      throw new HttpError(502, 'storage_error', 'The file storage rejected the request');
    }
  },
};

module.exports = { verifyIdToken, storage };
