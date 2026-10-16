import { Global, Inject, Module, OnApplicationShutdown, Optional } from '@nestjs/common';
import { connect } from './connect';
import { DB, Db } from './db';

@Global()
@Module({ providers: [{ provide: DB, useFactory: () => connect() }], exports: [DB] })
export class DbModule implements OnApplicationShutdown {
  constructor(@Optional() @Inject(DB) private readonly db: Db | null) {}

  async onApplicationShutdown(): Promise<void> {
    await this.db?.close();
  }
}
