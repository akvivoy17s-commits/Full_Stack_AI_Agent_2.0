import { Body, Controller, HttpCode, Inject, Post, Req, UseGuards } from '@nestjs/common';
import { AuthGuard } from '../auth/access';
import { AuthedRequest } from '../common/types';
import { CheckoutService } from './checkout.service';

@Controller('checkout')
export class CheckoutController {
  constructor(@Inject(CheckoutService) private readonly checkout: CheckoutService) {}

  @Post()
  @HttpCode(201)
  @UseGuards(AuthGuard)
  create(@Body() body: unknown, @Req() req: AuthedRequest) {
    return this.checkout.create(req.user, body);
  }
}
