const { HttpError } = require('../lib/http');
const { mapDbError } = require('../db/errors');

function notFound(req, res, next) {
  next(new HttpError(404, 'not_found', 'Route not found'));
}

// One place decides what the client sees. Internal details are logged, never returned.
// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
  if (res.headersSent) return next(err);
  let e = err;
  if (err && err.type === 'entity.parse.failed') e = new HttpError(400, 'invalid_json', 'Request body is not valid JSON');
  else if (err && err.type === 'entity.too.large') e = new HttpError(413, 'payload_too_large', 'Request body is too large');
  else if (!(err instanceof HttpError)) e = mapDbError(err) || err;
  if (e instanceof HttpError) {
    return res.status(e.status).json({ error: { code: e.code, message: e.message, ...(e.details && { details: e.details }) } });
  }
  console.error(`${req.method} ${req.path} failed: ${err && err.message}`);
  return res.status(500).json({ error: { code: 'internal_error', message: 'Something went wrong' } });
}

module.exports = { notFound, errorHandler };
