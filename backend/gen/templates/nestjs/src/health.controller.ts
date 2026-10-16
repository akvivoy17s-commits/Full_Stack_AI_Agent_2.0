import { Controller, Get, Inject, Optional, Res } from '@nestjs/common';
import type { Response } from 'express';
import { DB, Db } from './db/db';
import { SCHEMA } from './schema';

@Controller('health')
export class HealthController {
  constructor(@Optional() @Inject(DB) private readonly db?: Db | null) {}

  @Get()
  async check(@Res({ passthrough: true }) res: Response) {
    try {
      if (this.db) await this.db.ping();
      const cache = SCHEMA.integrations.cache ? { cache: await (await import(`./integrations/${'cache'}`)).backend() } : {};
      return { status: 'ok', ...(this.db && { db: 'up' }), ...cache };
    } catch {
      res.status(503);
      return { status: 'degraded', db: 'down' };
    }
  }
}
