import { ArgumentsHost, Catch, ExceptionFilter } from '@nestjs/common';
import { mapDbError } from './db-errors';
import { HttpError } from './http-error';

// Decides what the client sees. Framework errors (unknown route, bad JSON, body too large) are mapped to the same envelope;
// anything unexpected is logged and answered with a generic 500: internal details are never returned.
export function toHttpError(err: unknown): HttpError | null {
  if (err instanceof HttpError) return err;
  const e = err as { getStatus?: () => number; type?: string } | null;
  const status = e && typeof e.getStatus === 'function' ? e.getStatus() : 0;
  if (e?.type === 'entity.parse.failed' || status === 400) return new HttpError(400, 'invalid_json', 'Request body is not valid JSON');
  if (e?.type === 'entity.too.large' || status === 413) return new HttpError(413, 'payload_too_large', 'Request body is too large');
  if (status === 404) return new HttpError(404, 'not_found', 'Route not found');
  if (status >= 400 && status < 500) return new HttpError(status, 'request_failed', 'The request could not be processed');
  return mapDbError(err);
}

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(err: unknown, host: ArgumentsHost): void {
    const http = host.switchToHttp();
    const res = http.getResponse();
    const e = toHttpError(err);
    if (e) {
      res.status(e.status).json({ error: { code: e.code, message: e.message, ...(e.details && { details: e.details }) } });
      return;
    }
    const req = http.getRequest();
    console.error(`${req.method} ${req.path} failed: ${(err as Error)?.message}`);
    res.status(500).json({ error: { code: 'internal_error', message: 'Something went wrong' } });
  }
}
