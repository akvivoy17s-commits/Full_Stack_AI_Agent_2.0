const rateLimit = require('express-rate-limit');
const cfg = require('../config');

const make = (limit) =>
  rateLimit({
    windowMs: 15 * 60 * 1000,
    limit: cfg.env === 'test' ? 100000 : limit,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: { code: 'rate_limited', message: 'Too many requests, try again later' } },
  });

module.exports = { authLimiter: make(20), publicLimiter: make(30), apiLimiter: make(600) };
