import { CanActivate, ExecutionContext, Injectable, Type } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { HttpError } from '../common/http-error';
import { Access, AuthUser } from '../common/types';
import { SCHEMA } from '../schema';

export const isAdmin = (u?: AuthUser | null): boolean => !!u && u.role === SCHEMA.adminRole;

// Verifies the bearer token (HS256 only) and sets req.user = { id, role }.
@Injectable()
export class AuthGuard implements CanActivate {
  constructor(private readonly jwt: JwtService) {}

  async canActivate(ctx: ExecutionContext): Promise<boolean> {
    const req = ctx.switchToHttp().getRequest();
    const m = /^Bearer (.+)$/i.exec(req.headers.authorization || '');
    if (!m) throw new HttpError(401, 'unauthorized', 'Authentication required');
    try {
      const p = await this.jwt.verifyAsync<{ sub: string; role: string }>(m[1], { algorithms: ['HS256'] });
      req.user = { id: String(p.sub), role: p.role } as AuthUser;
      return true;
    } catch {
      throw new HttpError(401, 'invalid_token', 'Invalid or expired token');
    }
  }
}

@Injectable()
export class AdminGuard implements CanActivate {
  canActivate(ctx: ExecutionContext): boolean {
    if (!isAdmin(ctx.switchToHttp().getRequest().user)) throw new HttpError(403, 'forbidden', 'You do not have access to this resource');
    return true;
  }
}

// Access levels come from the app spec: public | user | owner | admin. 'owner' is finished per record in CrudService.
export const guardsFor = (level: Access): Type<CanActivate>[] => (level === 'public' ? [] : level === 'admin' ? [AuthGuard, AdminGuard] : [AuthGuard]);

// A route that exists in the controller class but not in this app answers with the same 404 as any unknown route.
export function enabled(on: boolean): Type<CanActivate> {
  @Injectable()
  class Enabled implements CanActivate {
    canActivate(): boolean {
      if (!on) throw new HttpError(404, 'not_found', 'Route not found');
      return true;
    }
  }
  return Enabled;
}
