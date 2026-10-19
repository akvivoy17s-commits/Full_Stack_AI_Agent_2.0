# Complete Angular + TypeScript Guide for Full-Stack Development

**A practical reference for Angular templates, TypeScript, components, functions, signals, services, routing, forms, HTTP, testing, security, and production applications.**

> **About “100%”:** Angular, TypeScript, browser APIs, and the surrounding ecosystem continue to evolve. There is no finite, official list of every possible syntax form and API. This guide is designed as a broad, practical reference to the core language and the major Angular APIs used in real-world applications. Check the official references linked throughout this file for APIs introduced after your installed version.
>
> **Modern baseline:** Examples favor standalone components, typed TypeScript, signals, the built-in template control flow (`@if`, `@for`, `@switch`), functional route guards/interceptors, and current Angular CLI conventions. Some projects use other valid APIs or older NgModule-based architecture; those are covered where important.

---

## Table of Contents

1. What Angular Is
2. Prerequisites: TypeScript Essentials
3. Installing Tools and Creating a Project
4. Angular CLI Commands
5. Angular Project Structure
6. The Standalone Application Bootstrap
7. Components and Component Metadata
8. Templates and Template Syntax
9. Interpolation and Data Binding
10. Built-in Template Control Flow
11. Template Variables and Expression Rules
12. Component Inputs and Outputs
13. Component Lifecycle
14. Signals: `signal`, `computed`, `effect`, `linkedSignal`
15. Directives: Attribute, Structural, and Custom
16. Pipes and Custom Pipes
17. Dependency Injection and Providers
18. Services and Application Architecture
19. RxJS: Observables and Operators
20. Signals and RxJS Interoperability
21. Routing and Navigation
22. Route Parameters, Guards, Resolvers, Lazy Loading
23. Forms: Template-Driven and Reactive
24. Signal Forms (Version-Dependent)
25. Validation and Typed Forms
26. HTTP Client and REST APIs
27. Interceptors, Error Handling, and Retries
28. State Management Patterns
29. Content Projection, Queries, and Dynamic Components
30. Animations, Styling, and Accessibility
31. File Uploads and Browser APIs
32. Authentication and Authorization Patterns
33. Security Best Practices
34. Server-Side Rendering, Hydration, and Prerendering
35. Testing with Angular's Current Tooling
36. Debugging and Performance
37. Build, Environment Configuration, and Deployment
38. Common Errors and Solutions
39. Mini Full-Stack CRUD Example
40. TypeScript Syntax Reference
41. Angular API and Syntax Reference
42. Recommended Learning Path and Projects
43. Official Documentation

---

# 1. What Angular Is

Angular is a TypeScript-based web application framework. It provides components, templates, dependency injection, routing, forms, HTTP tools, testing integration, and rendering options.

Core building blocks:

- **Component:** TypeScript class + template + styles, responsible for a UI section.
- **Template:** HTML enhanced with interpolation, bindings, control flow, and pipes.
- **Directive:** Adds behavior or changes how an element is displayed.
- **Pipe:** Formats a value for display.
- **Service:** Holds reusable logic, API access, or shared state.
- **Dependency injection (DI):** Provides services and values to classes/functions.
- **Router:** Maps URLs to views and navigation behavior.
- **Signals and RxJS:** Tools for reactive state and asynchronous streams.
- **Angular CLI:** Generates, serves, tests, and builds projects.

Angular runs in the browser, but Angular applications can also use server-side rendering (SSR) or prerendering (SSG). The framework is not itself a database or backend server; full-stack applications normally call a backend API.

# 2. Prerequisites: TypeScript Essentials

Angular code is commonly written in TypeScript. Learn JavaScript fundamentals first, then TypeScript's type system.

## 2.1 Variables and primitive types

```ts
let count: number = 1;
const username: string = 'Ajmal';
const isReady: boolean = true;
let maybeName: string | undefined;
let nothing: null = null;
const big: bigint = 123n;
```

Use `const` by default. Use `let` when a binding must be reassigned. Avoid `var` in modern TypeScript.

## 2.2 Arrays and tuples

```ts
const scores: number[] = [10, 20, 30];
const names: Array<string> = ['Asha', 'Maya'];
const pair: [string, number] = ['age', 25];
```

## 2.3 Objects, type aliases, and interfaces

```ts
interface User {
  id: number;
  name: string;
  email?: string;       // optional property
  readonly createdAt: Date;
}

type UserStatus = 'active' | 'disabled' | 'pending';
type ApiResult<T> = { data: T; error?: never } | { data?: never; error: string };

const user: User = { id: 1, name: 'Asha', createdAt: new Date() };
```

Use interfaces to describe object contracts, and type aliases for unions, intersections, mapped types, and other type expressions. Either can describe many object shapes.

## 2.4 Union, intersection, and literal types

```ts
type ID = string | number;
type WithTimestamp = { createdAt: Date };
type Admin = User & { permissions: string[] };
type Theme = 'light' | 'dark' | 'system';
```

## 2.5 Functions and return types

```ts
function add(a: number, b: number): number {
  return a + b;
}

const multiply = (a: number, b: number): number => a * b;

function logMessage(message: string): void {
  console.log(message);
}

function findUser(id: number): User | undefined {
  return id === user.id ? user : undefined;
}
```

Other function concepts include optional parameters (`value?: string`), default parameters (`limit = 10`), rest parameters (`...items: string[]`), overload signatures, callback types, generics, and `async` functions returning `Promise<T>`.

## 2.6 Narrowing and type guards

```ts
function printValue(value: string | number): string {
  if (typeof value === 'number') return value.toFixed(2);
  return value.toUpperCase();
}

function isUser(value: unknown): value is User {
  return typeof value === 'object' && value !== null && 'id' in value && 'name' in value;
}
```

Prefer `unknown` over `any` for values whose type is not yet known. Validate data at runtime; TypeScript types do not validate incoming network responses.

## 2.7 Generics

```ts
function first<T>(items: readonly T[]): T | undefined {
  return items[0];
}

interface Repository<T, ID> {
  getById(id: ID): Promise<T | undefined>;
  list(): Promise<T[]>;
}
```

Useful utilities: `Partial<T>`, `Required<T>`, `Readonly<T>`, `Pick<T, K>`, `Omit<T, K>`, `Record<K, V>`, `Exclude<T, U>`, `Extract<T, U>`, `NonNullable<T>`, `Parameters<F>`, `ReturnType<F>`, `Awaited<T>`, and `satisfies` for validating a value's shape without throwing away its more specific inferred type.

## 2.8 Classes, access modifiers, and enums

```ts
class ApiError extends Error {
  constructor(message: string, public readonly statusCode: number) {
    super(message);
    this.name = 'ApiError';
  }
}

class Counter {
  #value = 0; // JavaScript private field
  increment(): number { return ++this.#value; }
}

enum LegacyStatus { Pending, Complete }
```

Angular services/components are classes. TypeScript also supports `public`, `protected`, `private`, `readonly`, `abstract`, accessors, static members, and parameter properties. Use string unions for many application states when a runtime enum is unnecessary.

## 2.9 Imports and exports

```ts
export interface Product { id: number; name: string; }
export function formatPrice(value: number): string { return `$${value.toFixed(2)}`; }
import { formatPrice, type Product } from './product';
```

## 2.10 Async TypeScript

```ts
async function loadUser(id: number): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<User>;
}
```

In production, validate external data rather than blindly asserting `as Promise<User>`.

# 3. Installing Tools and Creating a Project

Install a currently supported Node.js LTS release, then use the Angular CLI.

```bash
npm install -g @angular/cli
ng version
ng new task-manager --routing --style=scss
cd task-manager
ng serve --open
```

CLI prompts and generated filenames can change by Angular version. Modern projects commonly use standalone components. The `--routing` flag configures routing, and `--style=scss` selects SCSS; choose CSS if preferred.

Create an application with SSR enabled when needed:

```bash
ng new content-site --routing --style=scss --ssr
```

Do not install a random version copied from an old tutorial. Use the official compatibility table and CLI documentation for your installed Angular/Node.js/TypeScript combination.

# 4. Angular CLI Commands

```bash
ng new my-app                       # Create a project
ng serve                            # Development server
ng build                            # Production build
ng test                             # Run unit tests (test runner depends on setup/version)
ng generate component features/home # Generate a component
ng g c features/home                # Short form
ng g service core/api               # Generate a service
ng g directive shared/highlight     # Generate a directive
ng g pipe shared/truncate           # Generate a pipe
ng g guard core/auth                # Generate a guard
ng g interceptor core/auth          # Generate an interceptor
ng g interface models/user          # Generate an interface
ng g enum models/status              # Generate an enum
ng add @angular/ssr                  # Add server rendering to an existing app
ng update                           # Inspect/update dependencies
```

Check each command's options with `ng generate --help` or `ng help`. A generator's output and filenames may vary by style guide and CLI version.

# 5. Angular Project Structure

A typical standalone app resembles:

```text
src/
  app/
    app.component.ts
    app.component.html
    app.component.scss
    app.config.ts
    app.routes.ts
    core/
      auth.service.ts
      api.service.ts
    features/
      products/
        product-list.component.ts
        product-detail.component.ts
    shared/
      loading-spinner.component.ts
  environments/
  index.html
  main.ts
angular.json
package.json
tsconfig.json
```

Recommended boundaries:

- `core/`: application-wide infrastructure (auth/session, interceptors, app-wide services).
- `features/`: feature-specific screens and domain logic.
- `shared/`: reusable UI components, directives, pipes.
- `models/` or feature-local types: TypeScript interfaces/types.
- Keep components focused on view logic; move reusable business logic and I/O to services.

# 6. The Standalone Application Bootstrap

`src/main.ts`:

```ts
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';

bootstrapApplication(AppComponent, appConfig)
  .catch((error: unknown) => console.error(error));
```

`src/app/app.config.ts`:

```ts
import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
  ],
};
```

`AppComponent`:

```ts
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet />',
})
export class AppComponent {}
```

In modern Angular, standalone is the recommended default and may be implicit. Explicit imports make dependencies easy to inspect. Older apps may use `NgModule` and `bootstrapModule`; both styles exist.

# 7. Components and Component Metadata

A component is a class decorated with `@Component`.

```ts
import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-counter',
  standalone: true,
  template: `
    <h2>Count: {{ count() }}</h2>
    <button type="button" (click)="increment()">Add</button>
  `,
  styles: [`button { cursor: pointer; }`],
})
export class CounterComponent {
  readonly count = signal(0);
  increment(): void { this.count.update(value => value + 1); }
}
```

Common component metadata:

- `selector`: custom HTML selector.
- `template` / `templateUrl`: inline or external template.
- `styles` / `styleUrl` / `styleUrls`: component styles; available metadata options depend on version.
- `imports`: standalone component dependencies (components, directives, pipes, or NgModules).
- `providers`: providers scoped to this component subtree.
- `changeDetection`: change detection strategy when appropriate.
- `encapsulation`: CSS encapsulation strategy.
- `host`: host-element bindings/listeners.

Generate a component:

```bash
ng generate component products/product-card
```

## 7.1 Component class members

```ts
export class ProfileComponent {
  title = 'Profile';
  readonly version = 1;
  private selectedId: number | null = null;

  get hasSelection(): boolean {
    return this.selectedId !== null;
  }

  select(id: number): void {
    this.selectedId = id;
  }
}
```

Class members can include fields, methods, accessors (`get`/`set`), constructors, static members, and private fields. Avoid business logic in constructors; inject dependencies and initialize simple state there, then use lifecycle hooks or reactive patterns when the task requires it.

# 8. Templates and Template Syntax

Angular templates are HTML with Angular expression and binding syntax. A template can be inline or an external `.html` file.

```html
<h1>{{ pageTitle }}</h1>
<img [src]="avatarUrl" [alt]="displayName">
<button type="button" (click)="save()">Save</button>
```

Templates are not general TypeScript files. Keep them declarative: complex transformations, network requests, and side effects belong in TypeScript/services, not in template expressions.

# 9. Interpolation and Data Binding

## 9.1 Interpolation

```html
<p>{{ name }}</p>
<p>{{ 2 + 3 }}</p>
<p>{{ user().name }}</p>
```

Interpolation converts an expression into text. If a member is a signal, read it by calling it: `count()`.

## 9.2 Property binding

```html
<button [disabled]="isSaving">Save</button>
<img [src]="imageUrl" [alt]="imageDescription">
<div [class.active]="isActive"></div>
<div [style.width.px]="width"></div>
```

## 9.3 Event binding

```html
<button (click)="save()">Save</button>
<input (input)="onInput($event)">
<form (ngSubmit)="submit()">...</form>
```

```ts
onInput(event: Event): void {
  const input = event.target as HTMLInputElement;
  console.log(input.value);
}
```

## 9.4 Two-way binding

`[(ngModel)]` requires `FormsModule` in the component's imports:

```ts
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-name-editor',
  standalone: true,
  imports: [FormsModule],
  template: `<input [(ngModel)]="name"><p>{{ name }}</p>`,
})
export class NameEditorComponent { name = 'Asha'; }
```

Angular convention calls `[(...)]` “banana-in-a-box” syntax. For custom component two-way binding, use the supported model/input-output conventions for your Angular version.

## 9.5 Class and style bindings

```html
<div [class.error]="hasError" [class.selected]="selected"></div>
<div [ngClass]="{ active: isActive, disabled: isDisabled }"></div>
<div [style.color]="textColor" [style.width.px]="width"></div>
<div [ngStyle]="{ color: textColor, fontSize: fontSize }"></div>
```

`NgClass` and `NgStyle` must be imported when used. Direct class/style bindings cover many common cases without them.

# 10. Built-in Template Control Flow

Modern Angular offers built-in `@if`, `@for`, `@switch`, and `@defer` blocks.

## 10.1 `@if` / `@else`

```html
@if (user(); as currentUser) {
  <h2>Welcome, {{ currentUser.name }}</h2>
} @else {
  <p>Please sign in.</p>
}
```

## 10.2 `@for` / `@empty`

```html
@for (product of products(); track product.id; let i = $index) {
  <article>
    <span>{{ i + 1 }}</span>
    <h3>{{ product.name }}</h3>
  </article>
} @empty {
  <p>No products available.</p>
}
```

The `track` expression helps Angular keep DOM elements aligned with list items. Prefer a stable unique key such as `product.id`.

Available contextual variables include `$index`, `$count`, `$first`, `$last`, `$even`, and `$odd`. You can alias them with `let`.

## 10.3 `@switch`

```html
@switch (status()) {
  @case ('loading') { <p>Loading…</p> }
  @case ('success') { <p>Done.</p> }
  @case ('error') { <p>Something went wrong.</p> }
  @default { <p>Ready.</p> }
}
```

## 10.4 `@defer`

```html
@defer (on viewport) {
  <app-analytics-chart />
} @placeholder {
  <p>Chart will load when visible.</p>
} @loading (minimum 200ms) {
  <app-spinner />
} @error {
  <p>Could not load chart.</p>
}
```

Other triggers include interaction, hover, idle, timer, and conditions, with details depending on Angular version. Use defer blocks to split eligible dependencies from the initial bundle; confirm loading and placeholder behavior in your build.

# 11. Template Variables and Expression Rules

```html
<input #searchBox>
<button (click)="search(searchBox.value)">Search</button>

@let total = price() * quantity();
<p>Total: {{ total }}</p>
```

A template reference variable (`#name`) identifies an element, directive, or component instance depending on where it is declared. Template `@let` variables store an expression result in the template scope.

Angular template expressions support property access, method calls, arithmetic/logical operators, nullish coalescing, optional chaining (with Angular template-expression semantics), and other restricted syntax. They are not unrestricted JavaScript: avoid `new`, assignment expressions, arrow functions, and arbitrary statement blocks directly in interpolation. Move nontrivial logic to TypeScript.

# 12. Component Inputs and Outputs

Modern signal-based inputs/outputs are available in contemporary Angular releases; classic `@Input()` / `@Output()` APIs remain widely used.

## 12.1 Signal inputs

```ts
import { Component, input, computed } from '@angular/core';

@Component({
  selector: 'app-user-card',
  standalone: true,
  template: `<h3>{{ name() }}</h3><p>{{ label() }}</p>`,
})
export class UserCardComponent {
  name = input.required<string>();
  role = input<'admin' | 'member'>('member');
  label = computed(() => `${this.name()} — ${this.role()}`);
}
```

Parent template:

```html
<app-user-card [name]="currentUser().name" [role]="'admin'" />
```

Input transforms can normalize values. Check the current API documentation for exact overloads and options available in your installed Angular version.

## 12.2 Output events

```ts
import { Component, output } from '@angular/core';

@Component({ selector: 'app-save-button', template: `<button (click)="saved.emit(true)">Save</button>` })
export class SaveButtonComponent {
  saved = output<boolean>();
}
```

Parent:

```html
<app-save-button (saved)="onSaved($event)" />
```

```ts
onSaved(success: boolean): void {
  console.log('Saved:', success);
}
```

The classic alternative uses `@Input()` and `@Output()`, often with `EventEmitter<T>`. Use signal inputs/outputs or decorators consistently within a codebase and follow current Angular guidance.

## 12.3 Model inputs and two-way component binding

Where supported by the Angular version, `model()` can expose a writable model signal for component two-way binding:

```ts
import { Component, model } from '@angular/core';
@Component({ selector: 'app-rating', template: `<button (click)="rating.update(v => Math.min(5, v + 1))">Rate: {{ rating() }}</button>` })
export class RatingComponent { rating = model(0); }
```

Parent usage: `<app-rating [(rating)]="ratingValue" />`. Verify exact model API support in your version.

# 13. Component Lifecycle

Lifecycle hooks are class methods that Angular calls at defined points in a component/directive's lifetime.

Common hooks:

- `ngOnChanges(changes: SimpleChanges)` — input changes; runs before `ngOnInit` on initial inputs.
- `ngOnInit()` — component initialization after initial input values are set.
- `ngDoCheck()` — custom change checking; use rarely because it can run frequently.
- `ngAfterContentInit()` — projected content initialized.
- `ngAfterContentChecked()` — projected content checked.
- `ngAfterViewInit()` — component view and child views initialized.
- `ngAfterViewChecked()` — view checked.
- `ngOnDestroy()` — cleanup before destruction.

Example:

```ts
import { Component, OnInit, OnDestroy } from '@angular/core';

@Component({ selector: 'app-example', template: `<p>Ready</p>` })
export class ExampleComponent implements OnInit, OnDestroy {
  ngOnInit(): void { console.log('Initialized'); }
  ngOnDestroy(): void { console.log('Destroyed'); }
}
```

Modern Angular also provides render callbacks such as `afterNextRender` and `afterEveryRender` for appropriate DOM-related tasks. Browser-only DOM work must be handled carefully in SSR environments. Avoid changing template state in the middle of a change-detection traversal; use the lifecycle guidance for your version.

# 14. Signals: `signal`, `computed`, `effect`, `linkedSignal`

Signals represent reactive state. Reading a signal calls it as a function.

```ts
import { Component, signal, computed, effect } from '@angular/core';

@Component({ selector: 'app-cart', template: `
  <button (click)="increase()">Add item</button>
  <p>Count: {{ count() }}</p>
  <p>Total: {{ total() }}</p>
` })
export class CartComponent {
  readonly count = signal(0);
  readonly unitPrice = signal(12);
  readonly total = computed(() => this.count() * this.unitPrice());

  constructor() {
    effect(() => console.debug('Cart count changed:', this.count()));
  }

  increase(): void { this.count.update(n => n + 1); }
}
```

Core signal APIs:

```ts
const value = signal(0);           // writable signal
value();                            // read
value.set(10);                      // replace value
value.update(n => n + 1);           // update from current value
const doubled = computed(() => value() * 2); // derived, read-only signal
effect(() => console.log(value())); // side effect reacting to reads
```

Rules and advice:

- Keep derived state in `computed`, not in duplicated writable fields.
- Keep effects for side effects (logging, integrations, persistence) rather than copying one signal to another.
- Objects/arrays still need immutable updates when that is your chosen state pattern.
- Do not mutate a signal's object without updating the signal if consumers must be notified.
- `linkedSignal` and resource-style APIs have version-specific capabilities; consult the docs before relying on newer APIs.

# 15. Directives: Attribute, Structural, and Custom

Directives add behavior to elements. Components are directives with templates.

## 15.1 Built-in directives

Classic structural directives include `*ngIf`, `*ngFor`, and `ngSwitch`; built-in `@if`, `@for`, and `@switch` are the modern template control flow. Common attribute directives include `ngClass`, `ngStyle`, and `ngModel`.

Standalone component imports are explicit:

```ts
import { Component } from '@angular/core';
import { NgClass, NgStyle } from '@angular/common';

@Component({
  selector: 'app-status', standalone: true,
  imports: [NgClass, NgStyle],
  template: `<p [ngClass]="{ online: online }" [ngStyle]="{ opacity: online ? 1 : 0.5 }">Status</p>`,
})
export class StatusComponent { online = true; }
```

## 15.2 Custom attribute directive

```ts
import { Directive, ElementRef, Renderer2, inject, input, effect } from '@angular/core';

@Directive({ selector: '[appHighlight]', standalone: true })
export class HighlightDirective {
  private readonly el = inject(ElementRef<HTMLElement>);
  private readonly renderer = inject(Renderer2);
  readonly appHighlight = input('yellow');

  constructor() {
    effect(() => {
      this.renderer.setStyle(this.el.nativeElement, 'backgroundColor', this.appHighlight());
    });
  }
}
```

Usage: `<p [appHighlight]="'lightblue'">Highlighted text</p>`.

Prefer `Renderer2`/supported host bindings for DOM behavior where appropriate. Avoid direct unsafe DOM manipulation, and consider SSR compatibility. Another common approach is `host: { '(mouseenter)': '...' }` in directive/component metadata or host listeners supported by the API.

# 16. Pipes and Custom Pipes

Pipes transform values for display. Built-in examples include `date`, `currency`, `decimal`, `percent`, `uppercase`, `lowercase`, `titlecase`, `json`, `slice`, and `async`.

```html
<p>{{ today | date:'mediumDate' }}</p>
<p>{{ price | currency:'INR':'symbol':'1.2-2' }}</p>
<p>{{ username | uppercase }}</p>
```

Import built-in pipes or `CommonModule` if required in the standalone component.

Custom pipe:

```ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'truncate', standalone: true })
export class TruncatePipe implements PipeTransform {
  transform(value: string | null | undefined, limit = 30): string {
    if (!value) return '';
    return value.length <= limit ? value : `${value.slice(0, limit)}…`;
  }
}
```

Template: `{{ description | truncate:50 }}`. Pipes should usually be pure and free of side effects; use a service for I/O.

# 17. Dependency Injection and Providers

Dependency injection (DI) lets a class/function receive services and values instead of constructing them internally.

## 17.1 Injectable service

```ts
import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class LoggerService {
  log(message: string): void { console.log(message); }
}
```

Use it in a component:

```ts
import { Component, inject } from '@angular/core';
import { LoggerService } from './logger.service';

@Component({ selector: 'app-home', template: `<p>Home</p>` })
export class HomeComponent {
  private readonly logger = inject(LoggerService);
  constructor() { this.logger.log('Home loaded'); }
}
```

Constructor injection also works:

```ts
constructor(private readonly logger: LoggerService) {}
```

Do not use `inject()` arbitrarily anywhere. It must be used in an Angular injection context (such as field initialization or a supported provider/factory context).

## 17.2 Provider scopes

- `providedIn: 'root'`: application-wide singleton in common cases.
- Component `providers`: instance scoped to that component's injector/subtree.
- Route providers: values/services scoped to a route subtree.
- `ApplicationConfig.providers`: application-level providers.

## 17.3 Injection tokens

```ts
import { InjectionToken, inject } from '@angular/core';

export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL');

// In application config:
// { provide: API_BASE_URL, useValue: 'https://api.example.com' }

export function apiUrl(path: string): string {
  return `${inject(API_BASE_URL)}${path}`;
}
```

Common provider strategies include `useValue`, `useClass`, `useExisting`, and `useFactory`. Multi providers can supply multiple values for a token when the API supports them.

# 18. Services and Application Architecture

Put reusable logic and external I/O in services. Keep components focused on presenting state and responding to UI actions.

```ts
export interface Task {
  id: number;
  title: string;
  completed: boolean;
}

import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class TaskService {
  private readonly http = inject(HttpClient);

  list(): Observable<Task[]> {
    return this.http.get<Task[]>('/api/tasks');
  }

  create(input: Pick<Task, 'title'>): Observable<Task> {
    return this.http.post<Task>('/api/tasks', input);
  }
}
```

`HttpClient` generic types inform TypeScript; they do not validate server JSON at runtime. Validate untrusted responses when needed.

Recommended boundaries:

- Components: view state and user actions.
- Services: business operations, shared state, APIs.
- Types: domain contracts and DTOs.
- Interceptors: cross-cutting HTTP concerns.
- Guards/resolvers: route access and pre-navigation data requirements.

# 19. RxJS: Observables and Operators

Angular uses RxJS extensively for asynchronous streams and HTTP results.

```ts
import { Observable, of, map, filter, catchError, throwError } from 'rxjs';

const numbers$: Observable<number> = of(1, 2, 3);
const doubled$ = numbers$.pipe(map(n => n * 2));
```

Key concepts:

- `Observable<T>`: a stream which can emit values over time.
- `subscribe()`: starts/subscribes to a stream in typical cold-observable cases.
- `pipe()`: composes operators.
- `map`, `filter`, `tap`, `switchMap`, `concatMap`, `mergeMap`, `exhaustMap`.
- `debounceTime`, `distinctUntilChanged`, `take`, `takeUntil`, `catchError`, `finalize`, `retry`.
- `combineLatest`, `forkJoin`, `merge`, `concat`, `of`, `from`, `defer`, `timer`, `interval`.

Example search stream:

```ts
import { FormControl } from '@angular/forms';
import { debounceTime, distinctUntilChanged, switchMap, startWith } from 'rxjs';

readonly search = new FormControl('', { nonNullable: true });
readonly results$ = this.search.valueChanges.pipe(
  startWith(this.search.value),
  debounceTime(250),
  distinctUntilChanged(),
  switchMap(query => this.api.search(query)),
);
```

Choose flattening operators carefully:

- `switchMap`: cancel/unsubscribe from the previous inner stream when a new value arrives; useful for search.
- `concatMap`: queue inner work in order.
- `mergeMap`: allow concurrent inner work.
- `exhaustMap`: ignore new source values while an inner stream is active; useful for some submit actions.

Manage subscriptions. Prefer the `async` pipe, `takeUntilDestroyed()` or other lifecycle-safe patterns instead of leaking manual subscriptions.

# 20. Signals and RxJS Interoperability

Angular provides integration helpers in `@angular/core/rxjs-interop`.

```ts
import { toSignal, toObservable, takeUntilDestroyed } from '@angular/core/rxjs-interop';

// In an Angular injection context:
readonly tasks = toSignal(this.taskService.list(), { initialValue: [] as Task[] });

// A signal can be bridged to an observable:
readonly query$ = toObservable(this.querySignal);
```

`takeUntilDestroyed()` completes an observable subscription when the current Angular context is destroyed. Use interoperability functions when the boundary between signals and streams is useful; avoid duplicating state without a reason.

# 21. Routing and Navigation

`app.routes.ts`:

```ts
import { Routes } from '@angular/router';
import { HomeComponent } from './features/home/home.component';

export const routes: Routes = [
  { path: '', component: HomeComponent, title: 'Home' },
  { path: '**', redirectTo: '' },
];
```

Configure routing in `app.config.ts`:

```ts
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

export const appConfig = {
  providers: [provideRouter(routes)],
};
```

The root template needs `<router-outlet />`, and navigation usually uses:

```html
<a routerLink="/products">Products</a>
<a [routerLink]="['/products', product.id]">Details</a>
```

Import `RouterLink` and `RouterOutlet` in standalone components that use them.

Programmatic navigation:

```ts
import { Router } from '@angular/router';
import { inject } from '@angular/core';

private readonly router = inject(Router);
openProduct(id: number): void {
  void this.router.navigate(['/products', id], { queryParams: { tab: 'details' } });
}
```

# 22. Route Parameters, Guards, Resolvers, Lazy Loading

## 22.1 Parameters

```ts
{ path: 'products/:id', loadComponent: () => import('./product-detail.component').then(m => m.ProductDetailComponent) }
```

Read a parameter with `ActivatedRoute`:

```ts
import { ActivatedRoute } from '@angular/router';
import { inject } from '@angular/core';

private readonly route = inject(ActivatedRoute);
readonly id$ = this.route.paramMap.pipe(map(params => params.get('id')));
```

## 22.2 Lazy-loaded routes

```ts
export const routes: Routes = [
  {
    path: 'admin',
    loadChildren: () => import('./admin/admin.routes').then(m => m.ADMIN_ROUTES),
  },
];
```

## 22.3 Functional route guard

```ts
import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.isAuthenticated() ? true : router.createUrlTree(['/login']);
};
```

A route guard is a client-side UX/navigation mechanism, not a security boundary. The backend must independently authorize every protected request.

## 22.4 Resolver

```ts
import { ResolveFn } from '@angular/router';
import { inject } from '@angular/core';

export const productResolver: ResolveFn<Product> = route =>
  inject(ProductService).getById(Number(route.paramMap.get('id')));
```

A resolver can load required data before activating the route. Handle missing parameters and errors intentionally.

# 23. Forms: Template-Driven and Reactive

Angular supports template-driven forms and reactive forms. Reactive forms are often preferred for complex forms because their model and validation are explicit in TypeScript.

## 23.1 Template-driven forms

```ts
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({ selector: 'app-login', standalone: true, imports: [FormsModule], template: `
  <form #form="ngForm" (ngSubmit)="submit(form.value)">
    <input name="email" [(ngModel)]="email" required email>
    <button [disabled]="form.invalid">Sign in</button>
  </form>
` })
export class LoginComponent {
  email = '';
  submit(value: unknown): void { console.log(value); }
}
```

## 23.2 Reactive forms

```ts
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({ selector: 'app-register', standalone: true, imports: [ReactiveFormsModule], template: `
  <form [formGroup]="form" (ngSubmit)="submit()">
    <label>Email <input formControlName="email"></label>
    @if (form.controls.email.touched && form.controls.email.invalid) {
      <p role="alert">Enter a valid email.</p>
    }
    <button type="submit" [disabled]="form.invalid">Register</button>
  </form>
` })
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    console.log(this.form.getRawValue());
  }
}
```

Common reactive-form APIs: `FormControl`, `FormGroup`, `FormArray`, `FormBuilder`, `Validators`, `setValue`, `patchValue`, `reset`, `getRawValue`, `markAsTouched`, `markAllAsTouched`, `enable`, `disable`, `valueChanges`, `statusChanges`, `addControl`, `removeControl`, and `setValidators`.

## 23.3 Custom validator

```ts
import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function noWhitespace(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null =>
    String(control.value ?? '').trim().length > 0 ? null : { whitespace: true };
}
```

## 23.4 Async validator

An async validator returns `Promise<ValidationErrors | null>` or `Observable<ValidationErrors | null>`. For example, call a service to see whether a username already exists. Debounce and handle API failures appropriately.

## 23.5 Signal Forms

Recent Angular documentation also describes Signal Forms APIs, including `form()` and `FormField`. Availability and maturity depend on the Angular version in use. Treat Signal Forms as version-dependent and check the current official guide before adopting them in a production app. Do not mix examples from different major versions without checking API compatibility.

# 24. Validation and Typed Forms

- Add required, email, min/max length, min/max numeric value, and pattern validators when relevant.
- Show errors in a readable, accessible way, and connect errors to fields using `aria-describedby`.
- Validate on both client and server. Client-side validation improves UX but can be bypassed.
- Typed reactive forms help prevent incorrect form value access at compile time.
- Use `nonNullable` controls when `null` is not a valid value.
- For cross-field validation, apply a validator to the containing `FormGroup`.

# 25. HTTP Client and REST APIs

Set up `HttpClient` using a provider in the application config:

```ts
import { provideHttpClient } from '@angular/common/http';
// Add provideHttpClient() to ApplicationConfig.providers.
```

Service:

```ts
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Product { id: number; name: string; price: number; }

@Injectable({ providedIn: 'root' })
export class ProductService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/products';

  list(search = ''): Observable<Product[]> {
    const params = new HttpParams().set('search', search);
    return this.http.get<Product[]>(this.baseUrl, { params });
  }
  getById(id: number): Observable<Product> {
    return this.http.get<Product>(`${this.baseUrl}/${id}`);
  }
  create(input: Omit<Product, 'id'>): Observable<Product> {
    return this.http.post<Product>(this.baseUrl, input);
  }
  update(id: number, input: Partial<Omit<Product, 'id'>>): Observable<Product> {
    return this.http.patch<Product>(`${this.baseUrl}/${id}`, input);
  }
  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}
```

HTTP verbs commonly used: `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`. `HttpClient` returns Observables; subscribe or bind them using an async/observable-to-signal pattern.

# 26. Interceptors, Error Handling, and Retries

Functional interceptor example:

```ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const token = auth.accessToken();
  const authenticatedRequest = token
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;
  return next(authenticatedRequest);
};
```

Register with `provideHttpClient(withInterceptors([authInterceptor]))`.

Error handling:

```ts
import { catchError, throwError, retry } from 'rxjs';

return this.http.get<Product[]>('/api/products').pipe(
  retry({ count: 2, delay: 300 }),
  catchError(error => {
    console.error('Product request failed', error);
    return throwError(() => error);
  }),
);
```

Retry only operations where retrying is safe. Do not blindly retry non-idempotent payments or create requests. Use centralized error handling where it improves consistency, but present meaningful UI errors to the user.

# 27. State Management Patterns

Choose the simplest state approach that fits the app:

1. Component-local state: fields or signals for a single component.
2. Shared service state: a service with signals for modest app-wide data.
3. RxJS streams: event streams, complex async composition, and cancellation.
4. A dedicated state library: use only when application complexity and team conventions justify it.

Shared signal service:

```ts
import { Injectable, computed, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class CartState {
  private readonly itemsState = signal<Array<{ id: number; price: number; qty: number }>>([]);
  readonly items = this.itemsState.asReadonly();
  readonly count = computed(() => this.itemsState().reduce((sum, item) => sum + item.qty, 0));
  readonly total = computed(() => this.itemsState().reduce((sum, item) => sum + item.price * item.qty, 0));

  add(item: { id: number; price: number }): void {
    this.itemsState.update(items => {
      const existing = items.find(x => x.id === item.id);
      return existing
        ? items.map(x => x.id === item.id ? { ...x, qty: x.qty + 1 } : x)
        : [...items, { ...item, qty: 1 }];
    });
  }
}
```

Avoid putting every value in global state. Keep related state close to where it is used, and never treat client state as authoritative for permissions, price, or account ownership.

# 28. Content Projection, Queries, and Dynamic Components

## 28.1 Content projection

Child component:

```ts
@Component({ selector: 'app-card', standalone: true, template: `
  <section class="card">
    <header><ng-content select="[card-title]"></ng-content></header>
    <div><ng-content></ng-content></div>
  </section>
` })
export class CardComponent {}
```

Usage:

```html
<app-card>
  <h2 card-title>Account</h2>
  <p>Projected body content.</p>
</app-card>
```

## 28.2 View/content queries

Modern query functions include `viewChild`, `viewChildren`, `contentChild`, and `contentChildren`; decorator-based `@ViewChild` / `@ContentChild` remain in existing code. Query results may be signal-based in modern Angular. Follow the documentation for timing and optionality.

## 28.3 Dynamic component rendering

Angular supports creating components dynamically through APIs such as `ViewContainerRef.createComponent` and, in appropriate contexts, programmatic rendering APIs. Use dynamic creation when the component type truly needs to be chosen at runtime, and clean up any separately managed resources.

# 29. Animations, Styling, and Accessibility

Angular supports CSS-based transitions and multiple animation approaches; API availability can vary across Angular versions. CSS transitions are often enough:

```css
.panel {
  opacity: 0;
  transform: translateY(8px);
  transition: opacity 180ms ease, transform 180ms ease;
}
.panel.open { opacity: 1; transform: translateY(0); }
@media (prefers-reduced-motion: reduce) {
  .panel { transition: none; }
}
```

Accessibility checklist:

- Use semantic HTML and real buttons/links.
- Give images meaningful `alt` text, or `alt=""` for decorative images.
- Associate labels with form inputs.
- Preserve visible keyboard focus and keyboard navigation.
- Announce form errors and important async status where appropriate.
- Do not use color alone to communicate status.
- Support reduced-motion preferences.
- Keep headings and landmarks in a logical order.

Angular CDK can help with accessible overlays, focus management, drag/drop, virtual scrolling, and other interaction primitives. Check the CDK docs before implementing complex interactions from scratch.

# 30. File Uploads and Browser APIs

File input example:

```html
<input type="file" accept="image/*" (change)="onFileSelected($event)">
```

```ts
onFileSelected(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.item(0);
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    console.warn('File exceeds 5 MB');
    return;
  }
  const body = new FormData();
  body.append('file', file);
  this.http.post('/api/uploads', body).subscribe();
}
```

The backend must enforce file type, size, authorization, and storage rules. Client-side checks are convenience only.

Other browser APIs commonly used in Angular include `localStorage`, `sessionStorage`, `navigator.clipboard`, `IntersectionObserver`, `ResizeObserver`, `AbortController`, Web Workers, and media APIs. Guard browser-only code for SSR, and do not store sensitive long-lived secrets in local storage by default.

# 31. Authentication and Authorization Patterns

A typical frontend authentication flow:

1. Submit credentials to a backend over HTTPS.
2. Backend verifies credentials and creates a session/token according to the chosen architecture.
3. Client stores only what is appropriate for that architecture.
4. Route guards help improve navigation UX.
5. HTTP interceptors attach suitable authorization information when required.
6. Backend authorizes each protected API request independently.

Security reminders:

- Never embed private API secrets in frontend environment files; frontend builds are public to users.
- Protect session cookies with suitable `HttpOnly`, `Secure`, and `SameSite` settings when cookie sessions are used.
- Understand CSRF protection for cookie-authenticated applications.
- Validate ownership and roles on the backend.
- Do not trust a hidden button or client-side route guard as authorization.
- Use established authentication libraries/providers rather than inventing cryptographic code.

# 32. Security Best Practices

Angular sanitizes many template-bound values to help prevent common XSS attacks. That does not make every kind of DOM access, HTML bypass, or application behavior safe.

- Avoid `innerHTML` and unsafe DOM construction where possible.
- Do not use `bypassSecurityTrust...` unless you understand and can justify the trusted value's source and sanitization requirements.
- Do not concatenate user input into SQL or shell commands on the backend.
- Protect API endpoints and validate all input server-side.
- Keep dependencies updated and review audit results.
- Avoid secrets in source control and client-side bundles.
- Enforce HTTPS and appropriate security headers.
- Implement CSRF, CORS, rate limiting, and authorization at the server/API layer as appropriate.

# 33. Server-Side Rendering, Hydration, and Prerendering

Rendering strategies:

- **CSR:** Browser renders the app after downloading the JavaScript.
- **SSR:** Server generates HTML for a request, followed by client-side hydration.
- **SSG/prerendering:** HTML is generated during the build for routes known ahead of time.
- **Hybrid rendering:** Different routes can use different rendering modes.

Create a new app with SSR if appropriate:

```bash
ng new my-site --ssr
```

Or add SSR to an existing app using the CLI command documented for your Angular version. Modern Angular supports per-route rendering configurations through the SSR integration.

SSR cautions:

- `window`, `document`, `localStorage`, and other browser-only objects are not available in the same way on the server.
- Make rendering deterministic enough to avoid hydration mismatch.
- Avoid exposing user-specific/private data in cached prerendered HTML.
- Test routes in both server-rendered and browser contexts.

# 34. Testing with Angular's Current Tooling

Angular CLI testing defaults can vary by version and template; current setups may use Vitest, while older projects commonly use Karma/Jasmine. Follow your project's generated configuration.

A component test usually uses `TestBed` to configure the Angular testing environment:

```ts
import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach } from 'vitest';
import { CounterComponent } from './counter.component';

describe('CounterComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [CounterComponent] }).compileComponents();
  });

  it('creates the component', () => {
    const fixture = TestBed.createComponent(CounterComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
```

If the generated project uses a different runner, adapt the imports and assertion APIs accordingly. Testing concepts:

- Unit tests for functions and services.
- Component tests for templates and user interactions.
- HTTP tests using Angular's HTTP testing utilities.
- Router tests for navigation/guards.
- Integration and end-to-end tests for critical workflows.
- Mock external dependencies; do not rely on real production APIs in unit tests.

# 35. Debugging and Performance

Debugging tools:

- Browser developer tools: Console, Elements, Network, Performance, Application/Storage.
- Angular DevTools: component tree and supported profiling tools.
- TypeScript compiler and Angular template diagnostics.
- `ng build` to catch production compile issues.
- Unit tests and lint/type checks where configured.

Performance practices:

- Track lists using stable IDs.
- Use lazy routes and `@defer` for appropriate heavy UI.
- Prefer derived signals or well-designed streams instead of duplicate state.
- Avoid expensive method calls in templates when they run frequently.
- Use `OnPush` where appropriate and understand modern signal-driven change detection behavior.
- Use production builds and inspect bundle output.
- Use virtual scrolling for very large lists.
- Unsubscribe from long-lived streams or use lifecycle-safe helpers.
- Measure before optimizing.

# 36. Build, Environment Configuration, and Deployment

Common commands:

```bash
ng serve
ng test
ng build
```

Use the output path shown by the CLI/build configuration. Deploy the built frontend to a static host/CDN or serve it through a suitable web server. Configure SPA fallback routing as required by the host.

Environment configuration rules:

- Environment files in frontend apps are compiled into the client bundle; never place secrets there.
- Use deployment/runtime configuration for public URLs and non-secret flags.
- Configure API URLs for local, staging, and production environments.
- Keep server-side secrets exclusively in the backend's secret/configuration system.

# 37. Common Errors and Solutions

**Unknown element or directive**

- In a standalone component, import the component, directive, pipe, or Angular module used by the template.
- In an older NgModule app, declare/import items in the appropriate module.

**`NullInjectorError`**

- Ensure the dependency has a provider.
- Check whether it is provided at the intended scope.
- Verify required HTTP/router providers are configured.

**Template type-checking error**

- Correct the actual type mismatch rather than disabling type checks.
- Use explicit union/narrowing for nullable values.
- Check whether a signal needs `()` to read its value.

**HTTP CORS error**

- Configure CORS on the backend. Frontend code cannot bypass browser CORS enforcement.

**Routing returns a 404 after refresh**

- Configure the host to serve the SPA entry file for client-side routes, or use server routing as appropriate.

**Memory leak from subscription**

- Prefer `async`, `toSignal`, or `takeUntilDestroyed()` patterns where suitable.

**Signal not updating UI**

- Read the signal correctly and update with `.set()`/`.update()`.
- Avoid mutating a nested object without replacing/updating the tracked value.

**SSR crash because `window` is undefined**

- Keep browser-only API access in appropriate browser-only code paths and test SSR.

# 38. Mini Full-Stack CRUD Example

This is a frontend outline; `/api/tasks` must be implemented by a backend server.

## Model

```ts
export interface Task {
  id: number;
  title: string;
  completed: boolean;
}

export interface CreateTaskRequest {
  title: string;
}
```

## API service

```ts
@Injectable({ providedIn: 'root' })
export class TaskApiService {
  private readonly http = inject(HttpClient);
  readonly baseUrl = '/api/tasks';

  list(): Observable<Task[]> { return this.http.get<Task[]>(this.baseUrl); }
  create(input: CreateTaskRequest): Observable<Task> {
    return this.http.post<Task>(this.baseUrl, input);
  }
  update(id: number, patch: Partial<Pick<Task, 'title' | 'completed'>>): Observable<Task> {
    return this.http.patch<Task>(`${this.baseUrl}/${id}`, patch);
  }
  remove(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}
```

## Component state (illustrative)

```ts
@Component({
  selector: 'app-task-list',
  standalone: true,
  imports: [FormsModule],
  template: `
    <form (ngSubmit)="add()">
      <label>New task <input name="title" [(ngModel)]="newTitle" required></label>
      <button type="submit">Add</button>
    </form>

    @if (loading()) { <p>Loading…</p> }
    @if (error()) { <p role="alert">{{ error() }}</p> }
    @for (task of tasks(); track task.id) {
      <label>
        <input type="checkbox" [checked]="task.completed" (change)="toggle(task)">
        {{ task.title }}
        <button type="button" (click)="remove(task.id)">Delete</button>
      </label>
    } @empty {
      <p>No tasks yet.</p>
    }
  `,
})
export class TaskListComponent {
  private readonly api = inject(TaskApiService);
  readonly tasks = signal<Task[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  newTitle = '';

  ngOnInit(): void { this.refresh(); }

  refresh(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.list().pipe(finalize(() => this.loading.set(false))).subscribe({
      next: items => this.tasks.set(items),
      error: () => this.error.set('Could not load tasks.'),
    });
  }

  add(): void {
    const title = this.newTitle.trim();
    if (!title) return;
    this.api.create({ title }).subscribe({
      next: task => { this.tasks.update(items => [...items, task]); this.newTitle = ''; },
      error: () => this.error.set('Could not create task.'),
    });
  }

  toggle(task: Task): void {
    this.api.update(task.id, { completed: !task.completed }).subscribe({
      next: updated => this.tasks.update(items => items.map(item => item.id === updated.id ? updated : item)),
      error: () => this.error.set('Could not update task.'),
    });
  }

  remove(id: number): void {
    this.api.remove(id).subscribe({
      next: () => this.tasks.update(items => items.filter(task => task.id !== id)),
      error: () => this.error.set('Could not delete task.'),
    });
  }
}
```

This sample demonstrates component state, signals, template control flow, forms, dependency injection, HTTP services, and CRUD methods. In a larger production app, use lifecycle-safe async patterns, better error modeling, optimistic-update handling as appropriate, confirmation before destructive actions, and comprehensive tests. Add the required imports (`Component`, `OnInit`, `signal`, `inject`, `FormsModule`, `finalize`, `HttpClient`, `Observable`, etc.) from their respective packages. The API service/backend must be implemented separately.

# 39. TypeScript Syntax Reference

```ts
// Basic annotations
const name: string = 'Asha';
let count: number = 0;

// Union and literal types
type Role = 'admin' | 'editor' | 'viewer';
type Maybe<T> = T | null;

// Interfaces and optional/readonly properties
interface Entity { readonly id: number; title?: string; }

// Generics
function identity<T>(value: T): T { return value; }

// Function types
type Formatter = (value: number) => string;

// Async return type
async function getCount(): Promise<number> { return 1; }

// Type narrowing
function format(x: string | number): string {
  return typeof x === 'number' ? x.toFixed(2) : x.trim();
}

// Utility types
type UpdateEntity = Partial<Entity>;
type EntitySummary = Pick<Entity, 'id'>;
type EntityWithoutId = Omit<Entity, 'id'>;

// `keyof`, indexed access, `typeof`, and `satisfies`
const config = { retries: 3, mode: 'safe' } as const;
type Config = typeof config;
type ConfigKey = keyof Config;
const defaults = { retries: 3, mode: 'safe' } satisfies Record<string, string | number>;
```

Additional advanced TypeScript topics include conditional and mapped types, template literal types, discriminated unions, assertion functions, overloads, declaration merging, ambient types, module resolution, namespaces (mostly legacy/library contexts), decorators, variance/assignability, and compiler options. Learn them as your application requires; complex type-level programming is rarely the first priority for building an Angular app.

# 40. Angular API and Syntax Quick Reference

| Syntax / API | Purpose |
|---|---|
| `@Component({...})` | Declare a component |
| `@Directive({...})` | Declare a directive |
| `@Pipe({...})` | Declare a pipe |
| `@Injectable({...})` | Declare a service/provider class |
| `{{ value }}` | Interpolation |
| `[property]="expr"` | Property binding |
| `(event)="handler($event)"` | Event binding |
| `[(ngModel)]="value"` | Two-way binding for forms |
| `@if (...) { ... }` | Conditional rendering |
| `@for (item of items(); track item.id) { ... }` | List rendering |
| `@switch (value) { ... }` | Multi-branch rendering |
| `@defer { ... }` | Deferred loading block |
| `signal(initial)` | Writable reactive state |
| `computed(() => ...)` | Derived reactive value |
| `effect(() => ...)` | Reactive side effect |
| `input<T>()` | Signal-based component input |
| `output<T>()` | Component output event |
| `model<T>()` | Two-way model API where supported |
| `inject(Service)` | Resolve a dependency in an injection context |
| `provideRouter(routes)` | Configure Router |
| `provideHttpClient()` | Configure HttpClient |
| `FormControl` / `FormGroup` | Reactive forms |
| `Observable<T>` | RxJS asynchronous stream |
| `toSignal(observable)` | Bridge an observable to a signal |
| `toObservable(signal)` | Bridge a signal to an observable |
| `takeUntilDestroyed()` | Bind a stream subscription to lifecycle |
| `CanActivateFn` | Functional route guard type |
| `ResolveFn<T>` | Route resolver type |
| `HttpInterceptorFn` | Functional HTTP interceptor type |

# 41. Recommended Learning Path and Projects

Follow this order to avoid learning every advanced API before you can build anything:

1. TypeScript basics: types, functions, interfaces, unions, generics, imports.
2. Angular basics: components, templates, binding, built-in control flow, inputs/outputs.
3. Services and dependency injection.
4. Signals and basic RxJS concepts.
5. Routing, guards, resolvers, and lazy loading.
6. Reactive forms and validation.
7. HTTP APIs, error handling, and interceptors.
8. Testing, accessibility, security, and performance.
9. SSR/hydration if the use case benefits from it.
10. Build a complete app with a separately implemented API and database.

Practice project ideas:

- Beginner: counter, notes list, theme switcher, searchable table.
- Intermediate: form validation, API-driven product catalogue, pagination, filtering, sorting.
- Advanced: task manager with login, role-based UI, CRUD API, tests, error states, and deployment.
- Portfolio: dashboard with charts, settings, route-level lazy loading, accessible UI, and responsive layout.

For every project, verify that buttons and forms work, loading/error/empty states exist, API validation is handled, routes survive page refresh, and protected operations are authorized by the backend—not only by frontend code.

# 42. Official Documentation

Use the official documents as the source of truth for version-sensitive syntax and API details:

- Angular overview: https://angular.dev/overview
- Angular essentials: https://angular.dev/essentials
- Components: https://angular.dev/guide/components
- Templates: https://angular.dev/guide/templates
- Signals: https://angular.dev/guide/signals
- Dependency injection: https://angular.dev/guide/di
- Routing: https://angular.dev/guide/routing
- Forms: https://angular.dev/guide/forms
- HTTP client: https://angular.dev/guide/http
- Lifecycle: https://angular.dev/guide/components/lifecycle
- Testing: https://angular.dev/guide/testing
- SSR and prerendering: https://angular.dev/guide/ssr
- Angular CLI: https://angular.dev/tools/cli
- TypeScript Handbook: https://www.typescriptlang.org/docs/handbook/intro.html
- TypeScript generics: https://www.typescriptlang.org/docs/handbook/2/generics.html
- TypeScript utility types: https://www.typescriptlang.org/docs/handbook/utility-types.html

---

## Final note

This file is a broad study/reference guide, not a substitute for version-specific API documentation or hands-on practice. Angular's supported APIs and recommended patterns change across releases. Always run the app, type-check it, test important flows, and consult the official docs for the exact Angular version used by your project.
