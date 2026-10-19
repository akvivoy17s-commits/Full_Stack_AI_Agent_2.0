# NestJS Backend — Complete Syntax, Functions & Full-Stack Guide

> Practical reference for NestJS + TypeScript: setup, core APIs, HTTP, validation, database integrations, auth, security, testing, and deployment.
>
> **Checked:** 18 October 2026. The NestJS release page lists **v12.1.3** as the latest release at the time of checking. Confirm compatibility with your Node.js version and dependencies before starting a new project.
>
> **Scope note:** A literal inventory of every framework/third-party API, overload, option, and future function cannot fit in one document and changes with versions. This guide covers the major NestJS syntax, commonly used functions, patterns, and integrations; official links at the end are the authority for exact version-specific details.

## Contents
1. [What NestJS is](#1-what-nestjs-is)
2. [Architecture and request flow](#2-architecture-and-request-flow)
3. [Setup and CLI](#3-setup-and-cli)
4. [Project structure](#4-project-structure)
5. [TypeScript essentials](#5-typescript-essentials)
6. [Bootstrap and configuration](#6-bootstrap-and-configuration)
7. [Controllers and routes](#7-controllers-and-routes)
8. [Providers and dependency injection](#8-providers-and-dependency-injection)
9. [Modules](#9-modules)
10. [DTOs and validation](#10-dtos-and-validation)
11. [Pipes](#11-pipes)
12. [Exceptions and filters](#12-exceptions-and-filters)
13. [Middleware](#13-middleware)
14. [Guards and authorization](#14-guards-and-authorization)
15. [Interceptors](#15-interceptors)
16. [Custom decorators](#16-custom-decorators)
17. [Environment configuration](#17-environment-configuration)
18. [Database integrations](#18-database-integrations)
19. [TypeORM](#19-typeorm)
20. [Prisma](#20-prisma)
21. [MongoDB/Mongoose](#21-mongodbmongoose)
22. [Transactions and pagination](#22-transactions-and-pagination)
23. [Authentication](#23-authentication)
24. [Security checklist](#24-security-checklist)
25. [Caching and HTTP clients](#25-caching-and-http-clients)
26. [Events, schedules, and queues](#26-events-schedules-and-queues)
27. [Files and static assets](#27-files-and-static-assets)
28. [WebSockets, GraphQL, and microservices](#28-websockets-graphql-and-microservices)
29. [Swagger / OpenAPI](#29-swagger--openapi)
30. [Testing](#30-testing)
31. [Logging and health checks](#31-logging-and-health-checks)
32. [Versioning, CORS, cookies](#32-versioning-cors-cookies)
33. [Deployment and Docker](#33-deployment-and-docker)
34. [Architecture patterns](#34-architecture-patterns)
35. [Cheat sheet](#35-cheat-sheet)
36. [Common issues](#36-common-issues)
37. [Learning roadmap](#37-learning-roadmap)
38. [Official documentation](#38-official-documentation)

## 1. What NestJS is

NestJS is a Node.js framework for building maintainable server applications. It uses TypeScript by default and organizes apps around **modules**, **controllers**, **providers**, decorators, and dependency injection. Under the hood, it can use Express or Fastify.

Common uses: REST APIs, auth services, e-commerce backends, SaaS products, GraphQL, WebSockets, scheduled jobs, queue workers, and microservices.

| Express alone | NestJS |
|---|---|
| Flexible but architecture is up to you | Modules/controllers/services provide conventions |
| DI must be added or designed separately | Built-in dependency injection |
| Validation is assembled manually | Pipes integrate with runtime DTO validation |
| Test design depends heavily on project structure | Testing utilities and provider overrides are built in |

NestJS doesn't require a particular database. Common choices include PostgreSQL/MySQL with Prisma, TypeORM, or Drizzle, and MongoDB with Mongoose.

## 2. Architecture and request flow

### Main concepts
- **Module:** groups feature components and declares dependencies.
- **Controller:** maps HTTP requests to methods.
- **Provider/service:** business logic or reusable injectable functionality.
- **DTO/schema:** validates data at the API boundary.
- **Pipe:** validates/transforms values.
- **Guard:** decides whether a request may proceed.
- **Interceptor:** wraps handler execution for timing, mapping, caching, etc.
- **Filter:** turns exceptions into HTTP responses.
- **Middleware:** runs early in the HTTP pipeline.
- **Decorator:** attaches metadata or extracts values.

### Typical HTTP lifecycle

```text
request -> middleware -> guards -> interceptors(before)
        -> pipes/validation -> controller -> service/repository
        -> interceptors(after) -> response
exception -> applicable exception filter -> error response
```

Exact order and behavior can differ for HTTP, GraphQL, WebSockets, and microservices. Keep controllers thin: route/input/output; services: business rules; repositories/ORM: persistence; guards/policies: access control.

## 3. Setup and CLI

Install Node.js in a version supported by your Nest release. The current deployment docs specify Node.js 20.19+ or 22.12+ on the Node 22 line; verify the official prerequisites for the chosen major.

```bash
node --version
npm --version
npm install --global @nestjs/cli
nest --version
nest new my-api
cd my-api
npm run start:dev
```

Without a global install:

```bash
npx @nestjs/cli new my-api
```

### Common CLI commands

```bash
nest --help
nest new api
nest g module users
nest g controller users
nest g service users
nest g resource products
nest g guard auth
nest g interceptor logging
nest g pipe parse-id
nest g filter api-errors
nest g middleware request-logger
nest g decorator current-user
nest build
nest start
nest start --watch
nest start --debug --watch
```

Use `nest <command> --help` for flags supported by your installed CLI. `nest g resource` can scaffold CRUD endpoints and ask which API style to use.

### Package scripts
Common scripts are `build`, `start`, `start:dev`, `start:debug`, `start:prod`, `lint`, `test`, and `test:e2e`. Generated projects vary by version/template; inspect your actual `package.json`. Some templates use Vitest, others Jest.

## 4. Project structure

```text
src/
  main.ts
  app.module.ts
  common/
    decorators/
    filters/
    guards/
    interceptors/
    pipes/
  config/
  database/
  auth/
    auth.module.ts
    auth.controller.ts
    auth.service.ts
    dto/
  users/
    users.module.ts
    users.controller.ts
    users.service.ts
    dto/
    entities/
test/
.env.example
package.json
tsconfig.json
nest-cli.json
```

Prefer feature-first organization. Keep `common/` limited to truly shared concerns; domain-specific code belongs to its feature module.

## 5. TypeScript essentials

```ts
const serviceName: string = 'catalog-api';
let total: number = 0;
const active: boolean = true;
const ids: number[] = [1, 2, 3];

type Role = 'user' | 'admin';

interface UserSummary {
  id: string;
  email: string;
  role: Role;
  displayName?: string;
}

async function loadUser(id: string): Promise<UserSummary | null> {
  return id ? { id, email: 'demo@example.com', role: 'user' } : null;
}

class ExampleService {
  constructor(private readonly prefix: string) {}
  format(value: string): string { return `${this.prefix}${value}`; }
}

function first<T>(items: T[]): T | undefined { return items[0]; }
```

Access modifiers: `public`, `private`, `protected`; `readonly` prevents reassignment; `static` belongs to the class. Useful syntax includes `?.` optional chaining, `??` nullish fallback, `...spread`, union types, type guards, and generics.

```ts
const display = user?.profile?.name ?? 'Guest';

type Result =
  | { ok: true; value: string }
  | { ok: false; message: string };

function message(result: Result): string {
  return result.ok ? result.value : result.message;
}
```

TypeScript interfaces/types disappear at runtime; they do not validate request JSON. Use DTO classes with decorators or a runtime schema such as Zod.

## 6. Bootstrap and configuration

### `src/main.ts`

```ts
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.setGlobalPrefix('api');
  app.enableCors({
    origin: ['http://localhost:5173'],
    credentials: true,
  });
  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
  }));

  await app.listen(process.env.PORT ?? 3000);
}
void bootstrap();
```

`whitelist` removes undecorated properties, `forbidNonWhitelisted` rejects them, and `transform` enables supported transformations. CORS origins should be explicit; don't blindly allow all origins when credentials are enabled.

DI-managed global providers can be registered using `APP_GUARD`, `APP_FILTER`, and `APP_INTERCEPTOR` in module providers. This is often better than `new SomeGuard()` in `main.ts` when the component has dependencies.

## 7. Controllers and routes

```ts
import {
  Body, Controller, Delete, Get, HttpCode, HttpStatus,
  Param, Patch, Post, Query,
} from '@nestjs/common';

@Controller('products')
export class ProductsController {
  @Get()
  findAll(@Query('search') search?: string) {
    return { search: search ?? '', items: [] };
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return { id };
  }

  @Post()
  create(@Body() dto: CreateProductDto) {
    return this.productsService.create(dto);
  }

  @Patch(':id')
  update(@Param('id') id: string, @Body() dto: UpdateProductDto) {
    return this.productsService.update(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  remove(@Param('id') id: string) {
    return this.productsService.remove(id);
  }

  constructor(private readonly productsService: ProductsService) {}
}
```

The DTOs and service above must exist and be registered in the module. Typical route decorators: `@Get`, `@Post`, `@Put`, `@Patch`, `@Delete`, `@Options`, `@Head`, and `@All`.

### Parameter decorators

```ts
@Param() params
@Param('id') id
@Query() query
@Query('page') page
@Body() body
@Body('name') name
@Headers() headers
@Headers('authorization') authorization
@Req() request
@Res() response
@Ip() ip
@Session() session
@HostParam('tenant') tenant
```

Use `@Req()` and especially `@Res()` only when you need direct adapter behavior; manual response mode changes how Nest handles the route response. Query/path values normally arrive as strings. Use parse pipes or validated DTO transformation to convert them.

### Status and headers

```ts
@Post()
@HttpCode(HttpStatus.CREATED)
create() { return { created: true }; }

@Header('Cache-Control', 'no-store')
@Get('private')
getPrivate() { return { data: 'private' }; }
```

Common codes: `OK`, `CREATED`, `ACCEPTED`, `NO_CONTENT`, `BAD_REQUEST`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `UNPROCESSABLE_ENTITY`, `TOO_MANY_REQUESTS`, and `INTERNAL_SERVER_ERROR`.

## 8. Providers and dependency injection

Services are usually providers.

```ts
import { Injectable, NotFoundException } from '@nestjs/common';

@Injectable()
export class ProductsService {
  private readonly items = new Map<string, { id: string; name: string }>();

  findAll() { return [...this.items.values()]; }

  findOne(id: string) {
    const item = this.items.get(id);
    if (!item) throw new NotFoundException('Product not found');
    return item;
  }

  create(name: string) {
    const id = crypto.randomUUID();
    const item = { id, name };
    this.items.set(id, item);
    return item;
  }
}
```

This in-memory map is only a teaching sample; it loses data on restart. A real app uses a database or other durable storage.

### Constructor injection

```ts
@Injectable()
export class BillingService {
  constructor(
    private readonly payments: PaymentsService,
    private readonly audit: AuditService,
  ) {}
}
```

### Custom provider patterns

```ts
const providers = [
  { provide: 'APP_NAME', useValue: 'catalog-api' },
  { provide: 'PAYMENT_GATEWAY', useClass: StripePaymentGateway },
  {
    provide: 'OPTIONS',
    useFactory: (config: ConfigService) => ({
      retries: config.get<number>('RETRIES', 3),
    }),
    inject: [ConfigService],
  },
  { provide: 'ALIAS', useExisting: PaymentsService },
];
```

Inject string/symbol tokens with `@Inject('PAYMENT_GATEWAY')`. In larger apps prefer exported `Symbol` constants to avoid typos. `@Optional()` marks an optional dependency.

### Provider scopes and lifecycle

Default scope is singleton. `Scope.REQUEST` creates request-associated scope; transient scope creates a new instance for each consumer. Request/transient scopes have costs and should be deliberate.

Useful lifecycle hooks include `onModuleInit`, `onApplicationBootstrap`, `onModuleDestroy`, `beforeApplicationShutdown`, and `onApplicationShutdown`. Enable shutdown hooks using `app.enableShutdownHooks()` when your lifecycle requires them.

`forwardRef()` can resolve some unavoidable circular dependencies, but refactor into a shared provider/module when possible rather than building an architecture around cycles.

## 9. Modules

```ts
@Module({
  imports: [],
  controllers: [ProductsController],
  providers: [ProductsService],
  exports: [ProductsService],
})
export class ProductsModule {}
```

- `imports`: modules whose exported providers are needed.
- `controllers`: controllers owned by this module.
- `providers`: DI-managed classes/values.
- `exports`: providers other modules are allowed to inject.

Import a feature module from another module to use its exported service. Use `@Global()` sparingly: explicit imports make dependencies easier to inspect.

### Dynamic module concept

```ts
@Module({})
export class StorageModule {
  static register(options: StorageOptions): DynamicModule {
    return {
      module: StorageModule,
      providers: [
        { provide: 'STORAGE_OPTIONS', useValue: options },
        StorageService,
      ],
      exports: [StorageService],
    };
  }
}
```

Import `DynamicModule` and the relevant types from `@nestjs/common`. Advanced tools include `ModuleRef`, lazy-loaded modules, and async/dynamic module configuration; see official docs for full signatures.

## 10. DTOs and validation

Install common class validation dependencies:

```bash
npm install class-validator class-transformer
```

```ts
import {
  IsEmail, IsEnum, IsInt, IsOptional, IsString,
  Max, MaxLength, Min, MinLength,
} from 'class-validator';
import { Type } from 'class-transformer';

enum Role { USER = 'user', ADMIN = 'admin' }

export class CreateUserDto {
  @IsEmail()
  email!: string;

  @IsString()
  @MinLength(8)
  @MaxLength(128)
  password!: string;

  @IsOptional()
  @IsString()
  @MaxLength(80)
  displayName?: string;

  @IsOptional()
  @IsEnum(Role)
  role?: Role;
}

export class PaginationDto {
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page = 1;

  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit = 20;
}
```

Common `class-validator` decorators:
- Text: `@IsString`, `@IsNotEmpty`, `@Length`, `@MinLength`, `@MaxLength`, `@Matches`.
- Numbers: `@IsInt`, `@IsNumber`, `@Min`, `@Max`, `@IsPositive`.
- Boolean/email/URL: `@IsBoolean`, `@IsEmail`, `@IsUrl`.
- Arrays: `@IsArray`, `@ArrayMinSize`, `@ArrayMaxSize`, `@ArrayUnique`.
- Enum/optional: `@IsEnum`, `@IsOptional`.
- Nested: `@ValidateNested`, commonly with `@Type(() => ChildDto)`.
- Other: `@IsUUID`, `@IsDate`, `@IsObject`, `@IsDefined`, `@ValidateIf`, `@IsIn`, `@IsNotIn`.

### DTO reuse / updates

```ts
import { PartialType, PickType, OmitType, IntersectionType } from '@nestjs/mapped-types';

export class UpdateUserDto extends PartialType(CreateUserDto) {}
```

`PartialType` makes inherited DTO properties optional; `PickType`, `OmitType`, and `IntersectionType` can derive other DTOs. Use the correct mapped-types package for the chosen API style (REST/GraphQL).

TypeScript interfaces are not runtime validators. DTO validation only works when the pipe is configured and you pass the DTO class as the runtime type.

## 11. Pipes

Pipes validate or transform handler parameters.

Common built-ins: `ValidationPipe`, `ParseIntPipe`, `ParseFloatPipe`, `ParseBoolPipe`, `ParseArrayPipe`, `ParseUUIDPipe`, `ParseEnumPipe`, `DefaultValuePipe`, and `ParseFilePipe`.

```ts
@Get(':id')
findOne(@Param('id', ParseIntPipe) id: number) {
  return this.service.findOne(id);
}

@Get()
list(@Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number) {
  return { page };
}
```

Custom pipe:

```ts
import {
  ArgumentMetadata, BadRequestException, Injectable, PipeTransform,
} from '@nestjs/common';

@Injectable()
export class TrimPipe implements PipeTransform {
  transform(value: unknown, _metadata: ArgumentMetadata) {
    if (typeof value !== 'string') return value;
    const output = value.trim();
    if (!output) throw new BadRequestException('Value cannot be blank');
    return output;
  }
}
```

Pipes are for boundary validation/transformation. Keep substantial business workflows in services.

## 12. Exceptions and filters

Common exceptions include `BadRequestException`, `UnauthorizedException`, `ForbiddenException`, `NotFoundException`, `ConflictException`, `UnprocessableEntityException`, `TooManyRequestsException`, `ServiceUnavailableException`, and `InternalServerErrorException`.

```ts
if (!product) throw new NotFoundException('Product not found');
```

### Exception filter example

```ts
@Catch()
export class ApiExceptionFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();
    const status = exception instanceof HttpException
      ? exception.getStatus()
      : HttpStatus.INTERNAL_SERVER_ERROR;

    response.status(status).json({
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      message: status === 500 ? 'Internal server error' : 'Request failed',
    });
  }
}
```

The example needs imports from `@nestjs/common` and Express types if using Express. It intentionally hides unknown internal errors from the client. Log diagnostic details securely on the server. Filters can be route-, controller-, or globally scoped; use `APP_FILTER` for a DI-managed global filter.

## 13. Middleware

Middleware handles early request processing, such as request IDs and basic request logging. Authentication/authorization usually belongs in guards.

```ts
@Injectable()
export class RequestLogMiddleware implements NestMiddleware {
  use(req: Request, _res: Response, next: NextFunction) {
    console.log(req.method, req.originalUrl);
    next();
  }
}
```

Register it:

```ts
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer.apply(RequestLogMiddleware)
      .exclude({ path: 'health', method: RequestMethod.GET })
      .forRoutes('*');
  }
}
```

Import types/classes from `@nestjs/common` and adapter-specific request/response types. For production, use structured logs; never log tokens, passwords, or sensitive request bodies. Fastify middleware differs from Express middleware.

## 14. Guards and authorization

### API key guard shape

```ts
@Injectable()
export class ApiKeyGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const key = request.headers['x-api-key'];
    return typeof key === 'string' && key === process.env.API_KEY;
  }
}
```

Import `CanActivate`, `ExecutionContext`, and `Injectable`. This is a minimal example, not a complete identity system; protect/rotate secrets and use a proper auth strategy for real users.

### Roles metadata and guard

```ts
export const ROLES_KEY = 'roles';
export const Roles = (...roles: string[]) => SetMetadata(ROLES_KEY, roles);

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private readonly reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const required = this.reflector.getAllAndOverride<string[]>(ROLES_KEY, [
      context.getHandler(), context.getClass(),
    ]);
    if (!required?.length) return true;

    const user = context.switchToHttp().getRequest().user as
      { roles?: string[] } | undefined;

    return !!user?.roles && required.some(role => user.roles!.includes(role));
  }
}
```

Use after an authentication guard populates `request.user`:

```ts
@UseGuards(AccessTokenGuard, RolesGuard)
@Roles('admin')
@Delete(':id')
remove(@Param('id') id: string) {
  return this.service.remove(id);
}
```

Authorization must enforce record ownership and tenant boundaries on the server; hiding buttons in the frontend is not a security control. `APP_GUARD` registers a DI-managed global guard.

## 15. Interceptors

Interceptors run before/after handler execution. They are useful for request timing, response shaping, or observability.

```ts
@Injectable()
export class TimingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<unknown> {
    const started = Date.now();
    return next.handle().pipe(
      tap({
        next: () => console.log(`completed in ${Date.now() - started}ms`),
        error: () => console.log(`failed after ${Date.now() - started}ms`),
      }),
    );
  }
}
```

Example response mapping:

```ts
return next.handle().pipe(map(data => ({ success: true, data })));
```

Imports commonly include `CallHandler`, `ExecutionContext`, `Injectable`, `NestInterceptor`, RxJS `Observable`, `tap`, and `map`. Be careful not to wrap file downloads, streams, or endpoints with special response formats unintentionally.

## 16. Custom decorators

```ts
export const CurrentUser = createParamDecorator(
  (_data: unknown, context: ExecutionContext) =>
    context.switchToHttp().getRequest().user,
);
```

Use it after the authentication guard:

```ts
@UseGuards(AccessTokenGuard)
@Get('me')
getProfile(@CurrentUser() user: AuthenticatedUser) {
  return user;
}
```

`applyDecorators()` can combine repeated decorators into one reusable decorator. Use custom decorators for common metadata and parameter extraction, but keep auth policy understandable.

## 17. Environment configuration

Install:

```bash
npm install @nestjs/config
```

Configure:

```ts
@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env.local', '.env'],
    }),
  ],
})
export class AppModule {}
```

Read config:

```ts
@Injectable()
export class ExampleService {
  constructor(private readonly config: ConfigService) {}
  getPort(): number {
    return this.config.get<number>('PORT', 3000);
  }
}
```

Example `.env.example`:

```dotenv
NODE_ENV=development
PORT=3000
DATABASE_URL=postgresql://user:password@localhost:5432/app_db
JWT_SECRET=replace-with-long-random-secret
FRONTEND_ORIGIN=http://localhost:5173
```

A generic like `get<number>()` does not validate/convert the real environment string. Validate required values at startup. Commit `.env.example`, not real `.env` secrets. Use a secret manager or protected runtime environment for production, and never log all configuration values.

## 18. Database integrations

Nest is database-agnostic. Common documented options include:
- **TypeORM:** entities/repositories, `@nestjs/typeorm`.
- **Prisma:** generated type-safe client.
- **Drizzle:** TypeScript-first schema/query builder.
- **Mongoose:** MongoDB schemas/models, `@nestjs/mongoose`.
- **MikroORM** and **Sequelize** for other SQL/data-mapping approaches.

Pick one integration initially. Use migrations and database constraints in production; don't rely on automatic schema synchronization against important data.

## 19. TypeORM

For PostgreSQL, a typical install is:

```bash
npm install @nestjs/typeorm typeorm pg
```

Connection configuration:

```ts
TypeOrmModule.forRoot({
  type: 'postgres',
  host: process.env.DB_HOST,
  port: Number(process.env.DB_PORT ?? 5432),
  username: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  autoLoadEntities: true,
  synchronize: false,
});
```

Use `ConfigService`/async configuration and validate the values in a real app. `synchronize: true` is not a safe production migration strategy.

### Entity

```ts
@Entity('products')
export class Product {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ length: 160 })
  name!: string;

  @Column({ type: 'text', nullable: true })
  description!: string | null;

  @Column({ type: 'numeric', precision: 12, scale: 2 })
  price!: string;

  @Column({ default: true })
  active!: boolean;

  @CreateDateColumn()
  createdAt!: Date;

  @UpdateDateColumn()
  updatedAt!: Date;
}
```

Import decorators from `typeorm`. Numeric columns can be returned as strings by drivers; handle monetary precision deliberately.

### Repository CRUD shape

Register with `TypeOrmModule.forFeature([Product])` and inject:

```ts
constructor(
  @InjectRepository(Product)
  private readonly repo: Repository<Product>,
) {}

findAll() {
  return this.repo.find({ order: { createdAt: 'DESC' } });
}

async findOne(id: string) {
  const item = await this.repo.findOne({ where: { id } });
  if (!item) throw new NotFoundException('Product not found');
  return item;
}

create(dto: CreateProductDto) {
  return this.repo.save(this.repo.create(dto));
}

async update(id: string, dto: UpdateProductDto) {
  const item = await this.findOne(id);
  this.repo.merge(item, dto);
  return this.repo.save(item);
}

async remove(id: string) {
  await this.repo.delete(id);
}
```

Common repository APIs include `find`, `findOne`, `findBy`, `findOneBy`, `findAndCount`, `count`, `create`, `save`, `insert`, `update`, `upsert`, `delete`, `remove`, `softDelete`, `restore`, `createQueryBuilder`, and `manager`. Exact signatures differ by TypeORM version.

### Query builder

```ts
const items = await repo.createQueryBuilder('product')
  .where('product.active = :active', { active: true })
  .andWhere('product.price >= :min', { min: 100 })
  .orderBy('product.createdAt', 'DESC')
  .take(20)
  .getMany();
```

Parameterize user input; never concatenate user-controlled text into raw SQL.

Migrations are commonly generated/run using TypeORM CLI and a configured data source. CLI file paths/options vary by TypeORM version/build. Keep migration files in version control; review and test them before deployment. In transactions, ensure all related queries use the transaction manager.

## 20. Prisma

Typical starting commands:

```bash
npm install @prisma/client
npm install --save-dev prisma
npx prisma init
npx prisma format
npx prisma validate
npx prisma generate
npx prisma migrate dev --name init
```

Prisma's current major may require configuration/driver adapters that differ from older tutorials; follow the docs for the installed major. Use the production migration command documented by your version, commonly `prisma migrate deploy`, rather than development migration commands in deployment.

### Schema example

```prisma
model Product {
  id          String   @id @default(cuid())
  name        String
  description String?
  priceCents  Int
  active      Boolean  @default(true)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  @@index([active, createdAt])
}
```

### Injectable client service pattern

```ts
@Injectable()
export class PrismaService extends PrismaClient
  implements OnModuleInit, OnModuleDestroy {
  async onModuleInit() { await this.$connect(); }
  async onModuleDestroy() { await this.$disconnect(); }
}
```

This is a common older client pattern; adapt initialization to the Prisma major and database adapter in your application.

### CRUD operations

```ts
return this.prisma.product.findMany({
  where: { active: true },
  orderBy: { createdAt: 'desc' },
  take: 20,
});

return this.prisma.product.findUnique({ where: { id } });
return this.prisma.product.create({ data });
return this.prisma.product.update({ where: { id }, data });
return this.prisma.product.delete({ where: { id } });
```

Common APIs: `findMany`, `findUnique`, `findUniqueOrThrow`, `findFirst`, `count`, `aggregate`, `groupBy`, `create`, `createMany`, `update`, `updateMany`, `upsert`, `delete`, `deleteMany`, `$transaction`, `$connect`, `$disconnect`, `$queryRaw`, and `$executeRaw`. Raw query APIs need correct parameterization. Validate input; do not return private columns indiscriminately.

## 21. MongoDB/Mongoose

Install:

```bash
npm install @nestjs/mongoose mongoose
```

Connection:

```ts
MongooseModule.forRoot(process.env.MONGODB_URI!);
```

For real deployments, validate the URI and usually configure through `ConfigService`.

### Schema

```ts
@Schema({ timestamps: true })
export class Product {
  @Prop({ required: true, trim: true, maxlength: 160 })
  name!: string;

  @Prop({ required: true, min: 0 })
  price!: number;

  @Prop({ default: true })
  active!: boolean;
}
export const ProductSchema = SchemaFactory.createForClass(Product);
```

Register with `MongooseModule.forFeature([{ name: Product.name, schema: ProductSchema }])`, then inject:

```ts
constructor(
  @InjectModel(Product.name)
  private readonly products: Model<ProductDocument>,
) {}

findAll() {
  return this.products.find({ active: true }).lean().exec();
}

create(dto: CreateProductDto) {
  return this.products.create(dto);
}

update(id: string, dto: UpdateProductDto) {
  return this.products.findByIdAndUpdate(
    id, { $set: dto }, { new: true, runValidators: true },
  ).exec();
}

remove(id: string) {
  return this.products.findByIdAndDelete(id).exec();
}
```

Common operations: `find`, `findOne`, `findById`, `create`, `insertMany`, `updateOne`, `updateMany`, `findOneAndUpdate`, `findByIdAndUpdate`, `deleteOne`, `deleteMany`, `findByIdAndDelete`, `aggregate`, `countDocuments`, `exists`, and `populate`. Do not accept arbitrary client-supplied Mongo filters; build queries from validated allow-listed fields.

## 22. Transactions and pagination

### Offset pagination

```ts
const page = Math.max(1, requestedPage);
const limit = Math.min(100, Math.max(1, requestedLimit));
const skip = (page - 1) * limit;

const [items, total] = await repo.findAndCount({
  skip, take: limit, order: { createdAt: 'DESC' },
});

return {
  items, page, limit, total,
  totalPages: Math.ceil(total / limit),
};
```

Cap limits. Cursor pagination can work better for very large datasets; use a stable, indexed cursor key such as `(createdAt, id)`.

### Transactions

```ts
await prisma.$transaction(async tx => {
  // All queries for this atomic operation must use tx.
});
```

TypeORM uses the transaction callback's manager. Mongo transaction behavior depends on deployment configuration and driver support. Use transactions when multiple writes must succeed or fail together, and enforce critical invariants with database constraints too.

Database best practices:
- Add indexes for measured query/filter/order needs.
- Use unique constraints for unique business rules under concurrency.
- Avoid N+1 queries.
- Return only required fields.
- Review query plans and slow-query logs.
- Back up data and test restores.
- Avoid running unbounded concurrent database calls.

## 23. Authentication

Authentication identifies the caller; authorization decides what they may do. Common methods are sessions, access/refresh tokens, OAuth/OIDC with an identity provider, and scoped API keys for server-to-server use.

### Passport/JWT integration pattern

```bash
npm install @nestjs/passport passport passport-jwt @nestjs/jwt
npm install --save-dev @types/passport-jwt
```

A complete flow typically:
1. Validates credentials against a password hash.
2. Issues a short-lived access token or server session.
3. Verifies credentials on protected routes.
4. Loads identity and permissions.
5. Enforces authorization/ownership per operation.
6. Defines logout, refresh rotation/revocation, and account recovery.

Protected route shape:

```ts
@UseGuards(AuthGuard('jwt'))
@Get('profile')
getProfile(@Request() req: { user: AuthenticatedUser }) {
  return req.user;
}
```

This assumes the Passport strategy and its module are implemented. The exact auth APIs available may change across Nest major versions; consult the official current authentication page.

### Password/security rules

Never store plaintext passwords; use a well-maintained password hashing implementation such as Argon2id or scrypt with suitable parameters. Plain SHA-256 is not a password storage scheme.

Don't hard-code token secrets. Validate token signature, allowed algorithm, expiration, issuer and audience as your system requires. JWTs are signed, not necessarily encrypted; do not put secrets in claims.

For cookies, use HTTPS, `HttpOnly`, deliberate `Secure` and `SameSite` settings, correct expiration/domain/path, CSRF protections where required, and shared storage if sessions must span multiple app instances. Never put tokens into logs.

## 24. Security checklist

- Validate all body, path, query, upload, and external API data.
- Enforce auth and record ownership on the backend.
- Rate-limit login, password reset, OTP, and expensive endpoints.
- Configure exact CORS origins.
- Use TLS and appropriate security headers.
- Store secrets outside git; rotate leaked credentials.
- Use parameterized queries and allow-listed database filters.
- Set request/upload size limits.
- Validate actual file content, not only user-provided MIME type.
- Add CSRF protection when cookie auth architecture requires it.
- Use least-privilege database credentials.
- Keep dependencies patched and audit them.
- Hide internal stack traces from clients.
- Log security events without passwords, tokens, cookies, or sensitive payloads.
- Add timeouts and controlled retries to external calls.
- Test authorization and tenant boundaries explicitly.

`@nestjs/throttler` is a common rate-limiting integration. Follow its current docs; in-memory counters do not automatically become a shared distributed rate limit.

## 25. Caching and HTTP clients

### Cache
Nest has a cache-manager integration; configuration and store APIs are version-dependent. Conceptual operations:

```ts
await cache.set('product:123', product, 30_000);
const value = await cache.get('product:123');
await cache.del('product:123');
```

Cache keys must include tenant/user context whenever access policy affects results. Define invalidation or expiry rules. Never put private data under a shared public cache key.

### External HTTP API

Install the Nest HTTP module:

```bash
npm install @nestjs/axios axios
```

```ts
@Injectable()
export class CatalogClient {
  constructor(private readonly http: HttpService) {}

  async getItems() {
    const response = await firstValueFrom(
      this.http.get('https://api.example.com/items', { timeout: 5000 }),
    );
    return response.data;
  }
}
```

Use `ConfigService` for base URL/tokens, validate upstream payloads, handle timeout and HTTP failures, and retry only when safe. Never disable TLS verification to work around a certificate problem. `HttpModule.register()`/`registerAsync()` can configure Axios defaults.

## 26. Events, schedules, and queues

### In-process events

Install `@nestjs/event-emitter` and import `EventEmitterModule.forRoot()`.

```ts
this.events.emit('orders.created', { orderId });

@OnEvent('orders.created')
async onOrderCreated(event: { orderId: string }) {
  // Send notification or trigger a local handler.
}
```

Imports omitted from the short syntax example. In-process events are not durable; a process crash can lose work.

### Scheduling

Install `@nestjs/schedule` and import `ScheduleModule.forRoot()`.

```ts
@Cron('0 0 * * *')
runDaily() {}

@Interval(60_000)
runEveryMinute() {}

@Timeout(5_000)
runOnceAfterStartup() {}
```

A multi-instance application may run each schedule on every instance. Add coordination/locking or a designated scheduler if duplicate runs are unsafe.

### Queue workers

BullMQ is common:

```bash
npm install @nestjs/bullmq bullmq
```

```ts
await this.queue.add('send-email', { userId }, {
  attempts: 5,
  backoff: { type: 'exponential', delay: 1000 },
  removeOnComplete: true,
});
```

Queues require configuration, usually Redis, and a worker/processor. Make jobs idempotent, handle retries/failure retention, and monitor job lag. Don't put secrets or unnecessary personal data in job payloads.

## 27. Files and static assets

Express-based uploads commonly use `FileInterceptor` and `@UploadedFile()`:

```ts
@Post('avatar')
@UseInterceptors(FileInterceptor('file'))
upload(@UploadedFile() file: Express.Multer.File) {
  return { name: file.originalname, size: file.size, type: file.mimetype };
}
```

The example shows route shape, not production safety. Set strict file sizes/types/counts, validate actual content, create server-side filenames, store private files outside public directories, authorize downloads, and consider malware scanning. For large assets use object storage rather than ephemeral app storage. Nest also supports multiple file/field interceptors and `StreamableFile` for streaming; exact APIs depend on the adapter.

## 28. WebSockets, GraphQL, and microservices

### WebSockets
Common decorators: `@WebSocketGateway`, `@WebSocketServer`, `@SubscribeMessage`, `@MessageBody`, `@ConnectedSocket`; lifecycle interfaces include gateway init/connect/disconnect. Nest can use Socket.IO or `ws`.

```ts
@WebSocketGateway({ cors: { origin: 'http://localhost:5173' } })
export class ChatGateway {
  @WebSocketServer() server!: Server;

  @SubscribeMessage('chat:send')
  handle(@MessageBody() body: { roomId: string; text: string }) {
    // Validate input and verify room membership server-side.
    this.server.to(body.roomId).emit('chat:new', { text: body.text });
  }
}
```

Imports/types depend on adapter. Never trust a client-supplied room/tenant ID; authenticate clients, validate payloads, limit message sizes, rate-limit, and plan scaling/pub-sub.

### GraphQL
Common decorators: `@Resolver`, `@Query`, `@Mutation`, `@Args`, `@Parent`, `@ResolveField`, `@ObjectType`, `@InputType`, `@Field`, and `@ArgsType`. Nest supports code-first/schema-first. Configure the GraphQL module using the official quick start.

GraphQL still needs auth, field/record authorization, pagination, batching/DataLoader where suitable, and query complexity/depth limits.

### Microservices
Documented transport patterns include Redis, MQTT, NATS, RabbitMQ, Kafka, gRPC and custom transports. Common handler decorators are `@MessagePattern` and `@EventPattern`; producers use client proxies. Plan retries, idempotency, timeouts, schema evolution, poison-message handling, and observability. Start with a modular monolith unless independent deployment/scaling needs justify microservices.

## 29. Swagger / OpenAPI

Install:

```bash
npm install @nestjs/swagger
```

Bootstrap:

```ts
const config = new DocumentBuilder()
  .setTitle('Catalog API')
  .setDescription('Catalog service')
  .setVersion('1.0')
  .addBearerAuth()
  .build();

const document = SwaggerModule.createDocument(app, config);
SwaggerModule.setup('api-docs', app, document);
```

Common decorators: `@ApiTags`, `@ApiOperation`, `@ApiResponse`, `@ApiParam`, `@ApiQuery`, `@ApiBody`, `@ApiBearerAuth`, `@ApiProperty`, and `@ApiPropertyOptional`. Use the docs for full schema and mapped-type support. Decide deliberately if docs should be public in production.

## 30. Testing

Nest provides `@nestjs/testing`. The current generated project may use Jest or Vitest.

```ts
const moduleRef = await Test.createTestingModule({
  providers: [ProductsService],
}).compile();

const service = moduleRef.get(ProductsService);
```

Mock dependencies using `useValue`/`useFactory` or the test module's provider override methods. For TypeORM, `getRepositoryToken(Entity)` is commonly used as the mock token. Match your installed test runner's mock functions and assertion APIs.

E2E tests boot the actual app and exercise HTTP paths, pipes, guards, filters, and serialization. Test:
- valid requests and response codes;
- invalid DTOs and unexpected fields;
- unauthenticated/unauthorized requests;
- ownership and tenant checks;
- missing/conflicting records;
- database constraints, transactions, migrations;
- external dependency timeouts/failures;
- pagination, limits, uploads and error shapes.

Don't test only that a method was called; test observable behavior and security boundaries.

## 31. Logging and health checks

### Built-in logger

```ts
private readonly logger = new Logger(ProductsService.name);

this.logger.log('Started');
this.logger.warn('Unexpected state');
this.logger.error('Operation failed');
this.logger.debug('Diagnostic details');
this.logger.verbose('Verbose diagnostic');
```

Use structured production logging with timestamp, severity, service/version, request/correlation ID, route template, status, latency and trace ID. Never log passwords, tokens, cookies or sensitive payloads. Current Nest observability docs describe instrumentation, tracing, error monitoring and dashboards.

Health checks should distinguish **liveness** (process can continue) and **readiness** (ready to accept traffic). Check required DB/broker/cache with timeouts. Avoid restart loops for temporary dependency failure.

Resilience: timeouts, bounded exponential backoff with jitter, retries only when safe, circuit breakers where appropriate, idempotency keys, graceful shutdown, queue monitoring, and backups/restoration drills.

## 32. Versioning, CORS, cookies

### URI versioning

```ts
app.enableVersioning({ type: VersioningType.URI });

@Controller({ path: 'products', version: '1' })
export class ProductsV1Controller {}
```

Routes may become `/v1/products` plus a global prefix. Nest also documents header/media-type/custom strategies. Define backward compatibility and deprecation rules.

### CORS

```ts
app.enableCors({
  origin: ['https://frontend.example.com'],
  methods: ['GET', 'POST', 'PATCH', 'DELETE'],
  credentials: true,
});
```

Frontend credentials settings must match. CORS is not authentication.

### Cookies/sessions
Use adapter-compatible cookie/session middleware. Configure `HttpOnly`, `Secure`, `SameSite`, expiry and domain/path intentionally. For server-side sessions across multiple instances, use a shared store. Protect cookie-authenticated unsafe operations against CSRF where required.

## 33. Deployment and Docker

### Build/run

```bash
npm run build
npm run start:prod
```

Confirm actual scripts and generated entry path. Nest outputs may differ by compiler/build configuration.

### Production checklist
- Supported runtime versions and compatible packages.
- Valid environment/config schema and protected secrets.
- Reviewed database migrations and backups.
- HTTPS, CORS and proxy settings.
- Rate limits, request/upload limits, security headers.
- Unit/integration/E2E tests in CI.
- Structured logs, metrics, tracing and alerts.
- Health/readiness endpoints and graceful shutdown.
- Rollback and incident response process.

### Multi-stage Dockerfile starting point

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=build /app/dist ./dist
USER node
EXPOSE 3000
CMD ["node", "dist/main"]
```

Adjust for your actual Node version, runtime dependencies, assets, native modules, and `dist` entry point.

`.dockerignore` example:

```gitignore
node_modules
dist
coverage
.git
.env
.env.*
!.env.example
npm-debug.log
```

Keep production secrets out of Dockerfiles and repository files. Inject them at runtime.

## 34. Architecture patterns

- **Modular monolith:** single deployment, clear feature modules; a strong default.
- **Repository:** abstracts persistence when it benefits testing/domain logic; don't add layers that merely duplicate ORM APIs.
- **CQRS:** separate commands/writes from queries/reads for complex domain needs; not required for simple CRUD.
- **Transactional outbox:** write business change and event record atomically, then publish.
- **Idempotency key:** make retrying an operation safe.
- **Distributed lock:** coordinate work across instances; requires expiry, ownership and failure semantics.
- **Saga/compensation:** coordinate multi-service operations without a single ACID transaction.

Nest supports CQRS and reliability-related patterns, but decorators alone do not make a system reliable. Use only patterns justified by concrete requirements.

## 35. Cheat sheet

### Core decorators

```ts
@Module({})
@Controller('items')
@Injectable()
@Get()
@Post()
@Put(':id')
@Patch(':id')
@Delete(':id')
@Body()
@Query()
@Param('id')
@Headers('x-request-id')
@UseGuards(AuthGuard)
@UsePipes(ValidationPipe)
@UseInterceptors(TimingInterceptor)
@UseFilters(ApiExceptionFilter)
@SetMetadata('roles', ['admin'])
```

### Package commands (install only what you need)

```bash
npm install @nestjs/config
npm install class-validator class-transformer
npm install @nestjs/swagger
npm install @nestjs/axios axios
npm install @nestjs/typeorm typeorm pg
npm install @nestjs/mongoose mongoose
npm install @nestjs/passport passport passport-jwt @nestjs/jwt
npm install @nestjs/throttler
npm install @nestjs/schedule
npm install @nestjs/event-emitter
npm install @nestjs/bullmq bullmq
npm install --save-dev @nestjs/testing
```

Check compatibility for the exact Nest major and package version. Don't install all packages into every app by default.

### HTTP status meaning

| Status | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 202 | Accepted for processing |
| 204 | Success with no response body |
| 400 | Invalid request |
| 401 | Missing/invalid authentication |
| 403 | Not authorized |
| 404 | Not found |
| 409 | Conflict |
| 422 | Semantically invalid input (API convention varies) |
| 429 | Rate limit |
| 500 | Unexpected server error |
| 503 | Temporarily unavailable |

## 36. Common issues

### “Nest can't resolve dependencies”
Check provider registration, module imports/exports, token spelling, factory `inject` list, and circular dependencies.

### 404 on an existing controller
Check controller/module registration, prefix, route versioning, actual HTTP method, static/dynamic route order, and running port.

### DTO validation not happening
Check global/route `ValidationPipe`, use a DTO class not a TypeScript interface, add validation decorators, and send the expected payload shape.

### Query parameter remains a string
Use `ParseIntPipe` or validated DTO transformation (`@Type(() => Number)` with `transform: true`) and enforce allowed ranges.

### Environment variable is undefined
Check `ConfigModule`, `.env` path and working directory, variable spelling, container/runtime environment, and startup validation.

### CORS error
Allow the exact origin/method/header combination; credentials require compatible explicit origins. CORS does not replace backend auth.

### Database connection fails
Check host/port from the process/container perspective, credentials, TLS, network rules, driver versions, server availability, and migrations. `localhost` inside a container is that container.

### Slow route
Measure latency, inspect query plans/indexes, find N+1 calls, limit response size, and set upstream timeouts before optimizing.

## 37. Learning roadmap

1. TypeScript, Node.js, promises, HTTP, JSON.
2. Nest modules/controllers/providers and DI.
3. DTOs, validation, pipes, exceptions, guards, interceptors.
4. REST conventions, environment config and Swagger.
5. Pick PostgreSQL + Prisma/TypeORM or MongoDB + Mongoose.
6. Migrations, indexes, transactions, pagination and ownership rules.
7. Authentication, authorization, rate limits, security.
8. Unit/e2e testing, logs, health checks and Docker.
9. Redis/queues/WebSockets/external APIs as needed.
10. GraphQL/microservices/CQRS when project demands them.

**Portfolio project:** Build a catalog/order API with user/admin roles, validated product CRUD, filtering/pagination, order ownership checks, transactional inventory updates, background notifications, unit/e2e tests, Swagger, Docker, migrations, and health checks.

## 38. Official documentation

### NestJS
- [Official documentation](https://docs.nestjs.com/)
- [First steps](https://docs.nestjs.com/first-steps)
- [Controllers](https://docs.nestjs.com/controllers)
- [Providers](https://docs.nestjs.com/providers)
- [Modules](https://docs.nestjs.com/modules)
- [Custom providers](https://docs.nestjs.com/fundamentals/custom-providers)
- [Pipes](https://docs.nestjs.com/pipes)
- [Validation](https://docs.nestjs.com/techniques/validation)
- [Exception filters](https://docs.nestjs.com/exception-filters)
- [Guards](https://docs.nestjs.com/guards)
- [Interceptors](https://docs.nestjs.com/interceptors)
- [Middleware](https://docs.nestjs.com/middleware)
- [Custom decorators](https://docs.nestjs.com/custom-decorators)
- [Configuration](https://docs.nestjs.com/techniques/configuration)
- [Database overview](https://docs.nestjs.com/techniques/database)
- [TypeORM](https://docs.nestjs.com/techniques/database#typeorm-integration)
- [Prisma recipe](https://docs.nestjs.com/recipes/prisma)
- [MongoDB](https://docs.nestjs.com/techniques/mongodb)
- [Authentication](https://docs.nestjs.com/security/authentication)
- [Authorization](https://docs.nestjs.com/security/authorization)
- [CORS](https://docs.nestjs.com/security/cors)
- [Rate limiting](https://docs.nestjs.com/security/rate-limiting)
- [Caching](https://docs.nestjs.com/techniques/caching)
- [HTTP module](https://docs.nestjs.com/techniques/http-module)
- [Scheduling](https://docs.nestjs.com/techniques/task-scheduling)
- [Queues](https://docs.nestjs.com/techniques/queues)
- [File uploads](https://docs.nestjs.com/techniques/file-upload)
- [WebSockets](https://docs.nestjs.com/websockets/gateways)
- [GraphQL](https://docs.nestjs.com/graphql/quick-start)
- [Microservices](https://docs.nestjs.com/microservices/basics)
- [OpenAPI / Swagger](https://docs.nestjs.com/openapi/introduction)
- [Testing](https://docs.nestjs.com/fundamentals/testing)
- [Deployment](https://docs.nestjs.com/deployment)
- [Release history](https://github.com/nestjs/nest/releases)

### Ecosystem
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [Node.js API docs](https://nodejs.org/docs/latest/api/)
- [Prisma](https://www.prisma.io/docs)
- [TypeORM](https://typeorm.io/)
- [Mongoose](https://mongoosejs.com/docs/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [MongoDB](https://www.mongodb.com/docs/)
- [RxJS](https://rxjs.dev/guide/overview)
- [Docker](https://docs.docker.com/)

---

## Final notes

1. Keep controllers thin and services focused on business logic.
2. Treat validation, authentication, authorization, and database constraints as different layers.
3. Start with one database integration and learn its migration/transaction model.
4. Test invalid inputs and denied access as carefully as successful paths.
5. Check official docs for exact package versions and signatures before copying examples into production.
6. Samples are templates: complete omitted imports/types/module setup and add application-specific DTOs, persistence, and tests.
