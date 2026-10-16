import { Body, Controller, Delete, Get, HttpCode, Inject, Param, Post, Put, Query, Req, Type, UseGuards } from '@nestjs/common';
import { enabled, guardsFor } from '../auth/access';
import { PublicLimit } from '../common/rate-limit';
import { AuthedRequest, Entity, Op } from '../common/types';
import { CrudService } from './crud.service';

// One controller class per entity, built from the app spec. Operations the spec does not define answer 404 like any unknown route.
export function makeCrudController(e: Entity): Type<unknown> {
  const on = (op: Op) => enabled(e.ops.includes(op));
  const writeGuards = (op: Op) => [on(op), ...(e.write === 'public' ? [PublicLimit] : []), ...guardsFor(e.write)];

  @Controller(e.path)
  class EntityController {
    constructor(@Inject(CrudService) private readonly crud: CrudService) {}

    @Get()
    @UseGuards(on('list'), ...guardsFor(e.read))
    list(@Query() q: Record<string, unknown>, @Req() req: AuthedRequest) {
      return this.crud.list(e, q, req.user);
    }

    @Get(':id')
    @UseGuards(on('get'), ...guardsFor(e.read))
    get(@Param('id') id: string, @Req() req: AuthedRequest) {
      return this.crud.get(e, id, req.user);
    }

    @Post()
    @HttpCode(201)
    @UseGuards(...writeGuards('create'))
    create(@Body() b: unknown, @Req() req: AuthedRequest) {
      return this.crud.create(e, b, req.user);
    }

    @Put(':id')
    @UseGuards(...writeGuards('update'))
    update(@Param('id') id: string, @Body() b: unknown, @Req() req: AuthedRequest) {
      return this.crud.update(e, id, b, req.user);
    }

    @Delete(':id')
    @HttpCode(204)
    @UseGuards(...writeGuards('delete'))
    async remove(@Param('id') id: string, @Req() req: AuthedRequest): Promise<void> {
      await this.crud.remove(e, id, req.user);
    }
  }

  Object.defineProperty(EntityController, 'name', { value: `${e.name}Controller` });
  return EntityController;
}
