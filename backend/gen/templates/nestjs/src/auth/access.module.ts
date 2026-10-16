import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { cfg } from '../config';
import { AdminGuard, AuthGuard } from './access';

@Module({
  imports: [JwtModule.register({ global: true, secret: cfg.jwt.key, signOptions: { algorithm: 'HS256' } })],
  providers: [AuthGuard, AdminGuard],
  exports: [AuthGuard, AdminGuard],
})
export class AccessModule {}
