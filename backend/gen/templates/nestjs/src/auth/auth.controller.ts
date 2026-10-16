import { Body, Controller, Get, HttpCode, Post, Req, UseGuards } from '@nestjs/common';
import { AuthLimit } from '../common/rate-limit';
import { AuthedRequest } from '../common/types';
import { SCHEMA } from '../schema';
import { AuthGuard, enabled } from './access';
import { AuthService } from './auth.service';

@Controller('auth')
export class AuthController {
  constructor(private readonly auth: AuthService) {}

  @Post('register')
  @UseGuards(AuthLimit)
  register(@Body() b: unknown) {
    return this.auth.register(b);
  }

  @Post('login')
  @HttpCode(200)
  @UseGuards(AuthLimit)
  login(@Body() b: unknown) {
    return this.auth.login(b);
  }

  @Post('refresh')
  @HttpCode(200)
  @UseGuards(enabled(SCHEMA.refresh), AuthLimit)
  refresh(@Body() b: unknown) {
    return this.auth.refresh(b);
  }

  @Post('logout')
  @HttpCode(204)
  @UseGuards(AuthGuard)
  async logout(@Req() req: AuthedRequest, @Body() b: unknown): Promise<void> {
    await this.auth.logout(req.user as NonNullable<AuthedRequest['user']>, b);
  }

  @Get('me')
  @UseGuards(AuthGuard)
  me(@Req() req: AuthedRequest) {
    return this.auth.me(req.user as NonNullable<AuthedRequest['user']>);
  }
}
