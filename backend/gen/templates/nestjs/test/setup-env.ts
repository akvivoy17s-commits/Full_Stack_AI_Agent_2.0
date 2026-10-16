// Runs before every test file (jest `setupFiles`): the config module reads these at import time.
// SQLite runs in memory. For PostgreSQL / MySQL / MongoDB set TEST_DATABASE_URL to a disposable database.
import { SCHEMA } from '../src/schema';

process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret-' + 'x'.repeat(40);
process.env.CORS_ORIGINS = 'http://localhost:5173';
process.env.AUTO_MIGRATE = 'true';
delete process.env.MONGODB_URI;
if (SCHEMA.db === 'sqlite') process.env.DATABASE_URL = 'sqlite:///:memory:';
else if (process.env.TEST_DATABASE_URL) process.env.DATABASE_URL = process.env.TEST_DATABASE_URL;
else delete process.env.DATABASE_URL;
process.env.STRIPE_WEBHOOK_SECRET = 'whsec_test_' + 'y'.repeat(30);       // payment tests sign webhooks with these; API keys stay placeholders so no provider is ever called
process.env.RAZORPAY_WEBHOOK_SECRET = 'rzp_test_' + 'z'.repeat(30);
delete process.env.STRIPE_SECRET_KEY;
delete process.env.RAZORPAY_KEY_ID;
delete process.env.RAZORPAY_KEY_SECRET;
delete process.env.PAYPAL_CLIENT_ID;
delete process.env.PAYPAL_CLIENT_SECRET;
delete process.env.PAYPAL_WEBHOOK_ID;
