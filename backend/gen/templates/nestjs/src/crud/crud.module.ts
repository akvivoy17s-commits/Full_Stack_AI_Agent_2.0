import { Module } from '@nestjs/common';
import { SCHEMA } from '../schema';
import { makeCrudController } from './crud.controller';
import { CrudService } from './crud.service';

@Module({
  controllers: Object.values(SCHEMA.entities).filter((e) => !e.internal && e.ops.length).map(makeCrudController),
  providers: [CrudService],
})
export class CrudModule {}
