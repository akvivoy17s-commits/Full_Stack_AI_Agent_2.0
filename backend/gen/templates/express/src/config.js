require('dotenv').config();
const env = process.env;
const list = (v) => (v || '').split(',').map((s) => s.trim()).filter(Boolean);
const schema = require('./schema');

const cfg = {
  env: env.NODE_ENV || 'development',
  port: Number(env.PORT || 8000),
  corsOrigins: list(env.CORS_ORIGINS),
  trustProxy: env.TRUST_PROXY || '0',
  databaseUrl: env.DATABASE_URL || env.MONGODB_URI || '',
  autoMigrate: env.AUTO_MIGRATE === 'true',
  jwt: {
    secret: env.JWT_SECRET || '',
    accessTtlMin: Number(env.JWT_ACCESS_TTL_MIN || 15),
    refreshTtlDays: Number(env.JWT_REFRESH_TTL_DAYS || 7),
  },
  redisUrl: env.REDIS_URL || '',
  cacheTtlSec: Number(env.CACHE_TTL_SECONDS || 30),
  upload: { dir: env.UPLOAD_DIR || './uploads', maxBytes: Number(env.UPLOAD_MAX_BYTES || 5 * 1024 * 1024) },
  stripe: { secretKey: env.STRIPE_SECRET_KEY || '', webhookSecret: env.STRIPE_WEBHOOK_SECRET || '', currency: (env.STRIPE_CURRENCY || 'usd').toLowerCase() },
  s3: { endpoint: env.S3_ENDPOINT || '', bucket: env.S3_BUCKET || '', region: env.S3_REGION || 'us-east-1', accessKeyId: env.S3_ACCESS_KEY_ID || '', secretAccessKey: env.S3_SECRET_ACCESS_KEY || '' },
  razorpay: { keyId: env.RAZORPAY_KEY_ID || '', keySecret: env.RAZORPAY_KEY_SECRET || '', webhookSecret: env.RAZORPAY_WEBHOOK_SECRET || '', currency: (env.RAZORPAY_CURRENCY || 'inr').toLowerCase() },
  paypal: { clientId: env.PAYPAL_CLIENT_ID || '', clientSecret: env.PAYPAL_CLIENT_SECRET || '', webhookId: env.PAYPAL_WEBHOOK_ID || '', env: env.PAYPAL_ENV === 'live' ? 'live' : 'sandbox', currency: (env.PAYPAL_CURRENCY || 'usd').toLowerCase() },
  firebase: { projectId: env.FIREBASE_PROJECT_ID || '', serviceAccountPath: env.FIREBASE_SERVICE_ACCOUNT_PATH || '', storageBucket: env.FIREBASE_STORAGE_BUCKET || '' },
  wsMaxClients: Number(env.WS_MAX_CLIENTS || 500),
  bcryptRounds: env.NODE_ENV === 'test' ? 4 : 12,
};

// Fail fast with a readable message instead of failing later with a confusing one.
cfg.validate = function validate() {
  const errs = [];
  if (!Number.isInteger(cfg.port) || cfg.port < 1 || cfg.port > 65535) errs.push('PORT must be a valid port number');
  if (!cfg.corsOrigins.length) errs.push('CORS_ORIGINS must list the allowed browser origins (comma separated)');
  if (schema.db && !cfg.databaseUrl) errs.push('DATABASE_URL is required');
  if (schema.auth) {
    if (cfg.jwt.secret.length < 32 || cfg.jwt.secret.startsWith('<')) errs.push('JWT_SECRET must be a random string of at least 32 characters');
    if (!(cfg.jwt.accessTtlMin > 0) || !(cfg.jwt.refreshTtlDays > 0)) errs.push('JWT_ACCESS_TTL_MIN and JWT_REFRESH_TTL_DAYS must be positive numbers');
  }
  if (schema.firebaseAuth && !cfg.firebase.projectId) errs.push('FIREBASE_PROJECT_ID is required for Firebase sign-in');
  if (schema.storage === 'firebase-storage' && !cfg.firebase.storageBucket) errs.push('FIREBASE_STORAGE_BUCKET is required for Firebase Storage uploads');
  if (errs.length) throw new Error('Invalid configuration: ' + errs.join('; '));
};

module.exports = cfg;
