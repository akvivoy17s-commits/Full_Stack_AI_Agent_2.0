const jwt = require('jsonwebtoken');
const cfg = require('../config');
const schema = require('../schema');
const { HttpError } = require('../lib/http');

const isAdmin = (u) => !!u && u.role === schema.adminRole;

// Verifies the bearer token (HS256 only) and sets req.user = { id, role }.
function authenticate(req, res, next) {
  const m = /^Bearer (.+)$/i.exec(req.headers.authorization || '');
  if (!m) return next(new HttpError(401, 'unauthorized', 'Authentication required'));
  try {
    const p = jwt.verify(m[1], cfg.jwt.secret, { algorithms: ['HS256'] });
    req.user = { id: String(p.sub), role: p.role };
    return next();
  } catch (e) {
    return next(new HttpError(401, 'invalid_token', 'Invalid or expired token'));
  }
}

// Access levels come from the app spec: public | user | owner | admin. 'owner' is finished per record in the route.
const requireAdmin = (req, res, next) =>
  isAdmin(req.user) ? next() : next(new HttpError(403, 'forbidden', 'You do not have access to this resource'));

const verifyToken = (token) => {
  try { const p = jwt.verify(String(token), cfg.jwt.secret, { algorithms: ['HS256'] }); return { id: String(p.sub), role: p.role }; } catch (e) { return null; }
};

const guard = (level) => (level === 'public' ? [] : level === 'admin' ? [authenticate, requireAdmin] : [authenticate]);

const signAccess = (user) =>
  jwt.sign({ role: user.role }, cfg.jwt.secret, { algorithm: 'HS256', subject: String(user.id), expiresIn: Math.round(cfg.jwt.accessTtlMin * 60) });

module.exports = { verifyToken, authenticate, requireAdmin, guard, isAdmin, signAccess };
