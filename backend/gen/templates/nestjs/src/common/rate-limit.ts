import { CanActivate, ExecutionContext, Injectable, Type } from '@nestjs/common';
import { cfg } from '../config';
import { HttpError } from './http-error';

// Fixed-window limiter, in memory and per process. Behind several instances use a shared store (see README).
const WINDOW_MS = 15 * 60 * 1000;
const buckets = new Map<string, { n: number; reset: number }>();

export function allow(key: string, limit: number, now = Date.now()): boolean {
  if (buckets.size > 5000) for (const [k, b] of buckets) if (b.reset <= now) buckets.delete(k);
  const b = buckets.get(key);
  if (!b || b.reset <= now) {
    buckets.set(key, { n: 1, reset: now + WINDOW_MS });
    return true;
  }
  b.n += 1;
  return b.n <= limit;
}

export function rateLimitGuard(name: string, limit: number): Type<CanActivate> {
  @Injectable()
  class RateLimitGuard implements CanActivate {
    canActivate(ctx: ExecutionContext): boolean {
      const req = ctx.switchToHttp().getRequest();
      if (!allow(`${name}:${req.ip}`, cfg.env === 'test' ? 100000 : limit)) {
        throw new HttpError(429, 'rate_limited', 'Too many requests, try again later');
      }
      return true;
    }
  }
  return RateLimitGuard;
}

export const AuthLimit = rateLimitGuard('auth', 20);
export const PublicLimit = rateLimitGuard('public', 30);
export const ApiLimit = rateLimitGuard('api', 600);
