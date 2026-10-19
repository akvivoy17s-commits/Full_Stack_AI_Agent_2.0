# Full-Stack Web Development — Frontend + Backend + Database Complete Concepts & Tools Guide

> A practical, end-to-end reference for learning how programming languages, frameworks, databases, developer tools, APIs, testing, security, and deployment work together to build a full-stack web application.

**Guide scope:** HTML, CSS, JavaScript, TypeScript, React, Tailwind CSS, backend architecture, Node.js/Express/NestJS, Python/FastAPI/Django, Java/Spring Boot, PHP/Laravel, Rust/Axum, SQL, PostgreSQL/MySQL, MongoDB, Redis, APIs, authentication, Git, Docker, testing, deployment and production practices.

**Important:** No single document can literally list every function, method, syntax form, configuration option, framework API, database command, third-party library, and future release across all these technologies. This guide teaches the major concepts, common syntax, practical patterns, and how to choose and combine tools. Use the official documentation linked at the end to verify exact APIs and version compatibility.

---

## Contents

1. [What Full-Stack Means](#1-what-full-stack-means)
2. [How a Web Application Works](#2-how-a-web-application-works)
3. [Choose a Stack Before Coding](#3-choose-a-stack-before-coding)
4. [Programming Languages and Their Roles](#4-programming-languages-and-their-roles)
5. [Developer Tools](#5-developer-tools)
6. [Plan a Web Application](#6-plan-a-web-application)
7. [Project Structure and Architecture](#7-project-structure-and-architecture)
8. [HTML Essentials](#8-html-essentials)
9. [CSS Essentials](#9-css-essentials)
10. [Tailwind CSS](#10-tailwind-css)
11. [JavaScript Fundamentals](#11-javascript-fundamentals)
12. [TypeScript Fundamentals](#12-typescript-fundamentals)
13. [Frontend Frameworks and React](#13-frontend-frameworks-and-react)
14. [Frontend State, Forms and Navigation](#14-frontend-state-forms-and-navigation)
15. [Frontend-to-Backend Communication](#15-frontend-to-backend-communication)
16. [HTTP, REST and API Design](#16-http-rest-and-api-design)
17. [Backend Fundamentals](#17-backend-fundamentals)
18. [Node.js + Express](#18-nodejs--express)
19. [NestJS](#19-nestjs)
20. [Python: FastAPI and Django](#20-python-fastapi-and-django)
21. [Java + Spring Boot](#21-java--spring-boot)
22. [PHP + Laravel and Rust + Axum](#22-php--laravel-and-rust--axum)
23. [Databases: Core Concepts](#23-databases-core-concepts)
24. [SQL Essentials](#24-sql-essentials)
25. [PostgreSQL and MySQL](#25-postgresql-and-mysql)
26. [MongoDB](#26-mongodb)
27. [Redis and Caching](#27-redis-and-caching)
28. [ORMs, Migrations and Data Access](#28-orms-migrations-and-data-access)
29. [Authentication and Authorization](#29-authentication-and-authorization)
30. [Security for the Whole Stack](#30-security-for-the-whole-stack)
31. [File Uploads and External APIs](#31-file-uploads-and-external-apis)
32. [Testing and Debugging](#32-testing-and-debugging)
33. [Git and GitHub Workflow](#33-git-and-github-workflow)
34. [Environment Variables and Secrets](#34-environment-variables-and-secrets)
35. [Docker and Local Development](#35-docker-and-local-development)
36. [Deployment and CI/CD](#36-deployment-and-cicd)
37. [Performance, SEO, Accessibility and UX](#37-performance-seo-accessibility-and-ux)
38. [A Working Mini Full-Stack CRUD Example](#38-a-working-mini-full-stack-crud-example)
39. [Project Completion Checklist](#39-project-completion-checklist)
40. [Learning Roadmap](#40-learning-roadmap)
41. [Syntax and Tool Cheat Sheet](#41-syntax-and-tool-cheat-sheet)
42. [Official Documentation](#42-official-documentation)

---

## 1. What Full-Stack Means

A full-stack web application includes the parts a user sees and the systems that make those parts work.

### Frontend
Runs mainly in the browser and is responsible for:
- Page structure and content.
- Layout, colors, typography, animations and responsiveness.
- Navigation, forms, buttons and interactive state.
- Calling backend APIs.
- Loading, success, empty and error states.
- Accessibility and a good user experience.

Common technologies: HTML, CSS, JavaScript, TypeScript, React, Angular, Vue, Svelte, Tailwind CSS, Bootstrap.

### Backend
Runs on a server and is responsible for:
- API routes and request handling.
- Business rules and workflows.
- Authentication and authorization.
- Input validation and safe data processing.
- Database access.
- Sending emails, processing uploads, talking to third-party APIs.
- Logging, rate limiting, background jobs and other server operations.

Common technologies: Node.js with Express/NestJS, Python with FastAPI/Django, Java with Spring Boot, PHP with Laravel, C# with ASP.NET Core, Go, Rust with Axum.

### Database and storage
Stores application information:
- Users and roles.
- Products, orders, posts, messages and settings.
- Relationships, audit records and business events.
- Search indexes, cached responses, uploaded files and generated content.

Common choices: PostgreSQL, MySQL, SQL Server, SQLite, MongoDB, Redis, object storage such as S3-compatible services.

### Infrastructure and developer workflow
Tools used to build, verify, release and operate the application:
- Git/GitHub, VS Code, terminal and browser developer tools.
- Package managers, test runners, linters and formatters.
- Docker and CI/CD.
- Hosting, monitoring, backups, secrets and alerts.

**Full-stack developer = builds and connects these layers**, rather than simply writing UI code.

---

## 2. How a Web Application Works

A typical request follows this flow:

```text
User
  |
  v
Browser UI (HTML + CSS + JS/TS + React)
  |
  | HTTPS request / JSON
  v
Backend API (Node/Nest, Python, Java, etc.)
  |
  | validation, authentication, business rules
  v
Data-access layer (ORM/query builder/driver)
  |
  v
Database (PostgreSQL/MySQL/MongoDB)
  |
  | results
  v
Backend returns HTTP status + JSON
  |
  v
Frontend updates the UI
```

Example: user submits a product form.

1. The frontend checks obvious field errors and submits a request.
2. The API validates the body again—never trust only frontend validation.
3. A guard/middleware/auth layer verifies identity where required.
4. The service checks business rules.
5. The data layer inserts a record using a parameterized query or ORM.
6. The backend returns `201 Created` with a safe response body.
7. The frontend displays the new product or a success message.

The server must treat every client request as untrusted, even if your own UI sends it.

### Browser vs server vs database

| Concern | Runs primarily in | Examples |
|---|---|---|
| Visual layout | Browser | CSS, Tailwind |
| UI state and interactions | Browser | React state/events |
| Secret API credentials | Server | Environment/secret store |
| Business rules | Server | Order eligibility |
| Persistent records | Database | Users, products |
| Shared short-lived values | Cache | Redis |
| Large uploaded media | Object storage | Images, videos |
| Version history | Git repository | Source code changes |

Never place a private database password, secret API key or privileged service token in browser code.

---

## 3. Choose a Stack Before Coding

Avoid mixing every language and framework into one application just because all are available. Pick one frontend, one backend, and one primary database first.

### Recommended starter combinations

| Goal | Frontend | Backend | Database |
|---|---|---|---|
| Modern JavaScript full stack | React + TypeScript + Tailwind | Node.js + Express | PostgreSQL |
| Structured TypeScript API | React/Next.js | NestJS | PostgreSQL + Prisma |
| Python API | React or Vue | FastAPI | PostgreSQL |
| Python all-in-one web app | Django templates or React | Django | PostgreSQL |
| Enterprise Java | React/Angular | Spring Boot | PostgreSQL/MySQL |
| PHP hosting ecosystem | Blade or React/Vue | Laravel | MySQL/PostgreSQL |
| Performance-oriented Rust API | React/Svelte | Axum | PostgreSQL |
| Small local app | HTML/CSS/JS | A lightweight server if needed | SQLite |
| Document-oriented product | React/Vue | Node/Python | MongoDB |
| Cache / background coordination | Any frontend | Any suitable backend | Redis alongside a primary DB |

### A sensible learning order

1. HTML + CSS + JavaScript.
2. TypeScript.
3. React and one styling approach (CSS or Tailwind).
4. HTTP, JSON, browser `fetch`.
5. One backend framework.
6. SQL + PostgreSQL or MySQL.
7. ORM and migrations.
8. Auth, security and tests.
9. Git, Docker and deployment.
10. Add caching, queues, WebSockets or microservices only when the project needs them.

### Choosing relational vs document databases

Use a relational database when your data has relationships, integrity rules, reports and multi-record transactions. Use a document database when the shape is document-oriented and its query/consistency model fits the application. Either type can serve many workloads; choose from real data/query requirements, not just trend.

---

## 4. Programming Languages and Their Roles

### HTML — structure

HTML describes semantic content and form controls. It is a markup language, not a general-purpose programming language.

```html
<main>
  <h1>Products</h1>
  <form>
    <label for="product-name">Name</label>
    <input id="product-name" name="name" required />
    <button type="submit">Create</button>
  </form>
</main>
```

### CSS — presentation

CSS controls layout, color, spacing, typography, animations and responsive styling.

```css
.product-card {
  display: grid;
  gap: 1rem;
  padding: 1.5rem;
  border-radius: 1rem;
}

@media (min-width: 48rem) {
  .product-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
```

### JavaScript — behavior

JavaScript handles interaction, validation, fetching data, transforming values and coordinating UI state.

```js
const response = await fetch('/api/products');
if (!response.ok) throw new Error('Request failed');
const products = await response.json();
```

### TypeScript — typed JavaScript

TypeScript adds static types and tooling support; it still compiles to JavaScript for ordinary browser/server execution.

```ts
type Product = {
  id: string;
  name: string;
  priceCents: number;
};

function formatPrice(product: Product): string {
  return (product.priceCents / 100).toFixed(2);
}
```

### Python
Common in APIs, data processing, automation and AI services. Frameworks include FastAPI and Django.

```py
def total(items: list[float]) -> float:
    return sum(items)
```

### Java
Common in structured enterprise services. Spring Boot provides dependency injection, HTTP APIs, configuration and data integration.

```java
public record ProductDto(String name, int priceCents) {}
```

### PHP
Widely used in server-rendered web applications and content management. Laravel supplies routing, validation, ORM, migrations, queues and other framework tools.

### Rust
Useful for services where memory safety and predictable performance matter. Web APIs commonly use frameworks such as Axum with Tokio and Serde.

### SQL
A language for defining and querying relational data.

```sql
SELECT id, name, price_cents
FROM products
WHERE active = TRUE
ORDER BY created_at DESC
LIMIT 20;
```

### JSON
A data-exchange format, not a programming language.

```json
{
  "id": "p_123",
  "name": "Keyboard",
  "priceCents": 4999
}
```

### Shell / terminal commands
PowerShell, Bash and shell scripts automate development and deployment tasks.

```bash
npm install
npm run dev
git status
```

**Important distinction:** languages, frameworks, databases and tools solve different problems. React is a UI library; TypeScript is a language; Node.js is a runtime; NestJS is a backend framework; PostgreSQL is a database; Docker packages applications.

---

## 5. Developer Tools

### Essential tools

- **VS Code or another IDE:** edit code, use debugging, terminal, extensions.
- **Browser DevTools:** inspect DOM/CSS, console errors, network requests, storage and performance.
- **Node.js + npm/pnpm/yarn:** run JavaScript tools and manage packages.
- **Python + venv/uv/pip:** run Python and isolate dependencies.
- **JDK + Maven/Gradle:** build Java projects.
- **Git + GitHub/GitLab:** version control and collaboration.
- **PostgreSQL/MySQL clients:** inspect schemas and run SQL.
- **API client:** test endpoints with requests, headers, JSON bodies and auth.
- **Docker Desktop/Engine:** run isolated development services.
- **Formatter/linter:** keep code readable and detect mistakes.
- **Test runner:** check behavior in repeatable ways.
- **CI/CD service:** run builds/tests and deploy through a controlled pipeline.

### Useful command-line checks

```bash
node --version
npm --version
git --version
docker --version
python --version
```

Only install a tool when your chosen stack needs it. Keep dependency versions documented and use the lockfile created by the package manager.

### Browser developer tools
Use:
- **Elements:** inspect HTML/CSS and computed layout.
- **Console:** check runtime errors and warnings.
- **Network:** inspect request URL, method, status, headers, payload and response.
- **Application/Storage:** inspect local/session storage and cookies.
- **Performance:** locate expensive tasks and slow rendering.
- **Accessibility checks:** verify semantics and keyboard behavior.

Do not share screenshots or logs that expose credentials, cookies, customer data or private URLs.

---

## 6. Plan a Web Application

Before creating files, write a compact specification.

### Define
1. **Goal:** What user problem does the website solve?
2. **Audience:** Who uses it, and what permissions do they have?
3. **Pages:** Home, login, dashboard, detail pages, profile, admin panel, etc.
4. **Entities:** User, Product, Order, Comment, Subscription, etc.
5. **Features:** CRUD, search, filter, pagination, uploads, payments, notifications.
6. **Interactions:** What does every visible button, form, menu, tab or filter do?
7. **Data model:** Fields, types, constraints and relationships.
8. **API contract:** Routes, input schemas, response schemas and error codes.
9. **Security:** authentication, permissions, ownership, rate limits, secrets.
10. **Acceptance criteria:** How will you prove that each feature works?

### Example: product inventory app

Entities:
- `User(id, email, password_hash, role, created_at)`
- `Product(id, name, description, price_cents, active, created_at, updated_at)`

Features:
- List products and search by name.
- Create/edit/archive products.
- Admin-only write operations.
- Pagination and validation.
- Error, empty and loading states.
- Unit and API tests.
- Deployment plus database backup plan.

Do not implement UI mock data and declare the feature complete if the user expects real database persistence.

---

## 7. Project Structure and Architecture

### Monorepo example

```text
fullstack-app/
├── apps/
│   ├── web/                  # React/Vite frontend
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── features/
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   ├── api/
│   │   │   ├── types/
│   │   │   └── main.tsx
│   │   └── package.json
│   └── api/                  # Backend app
│       ├── src/
│       │   ├── modules/
│       │   ├── routes/
│       │   ├── controllers/
│       │   ├── services/
│       │   ├── repositories/
│       │   ├── middleware/
│       │   ├── schemas/
│       │   └── main.ts
│       └── package.json
├── database/
│   ├── migrations/
│   └── seeds/
├── docs/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

This is an illustrative layout; NestJS, Django, Spring Boot and Laravel have their own conventional project structures.

### Typical request layers

```text
Route/controller
  -> input validation
  -> authentication/authorization
  -> service/use case (business logic)
  -> repository/ORM
  -> database
```

The exact execution order depends on the framework. Keep business logic out of UI components and avoid putting complex SQL, auth logic and business decisions in one giant controller function.

### Modular monolith vs microservices
Start with one deployable backend divided into feature modules for most small/medium projects. Microservices add network failures, deployment complexity, distributed tracing and consistency challenges. Split services when independent deployment, scaling, security boundaries or team ownership justify the cost.

---

## 8. HTML Essentials

### Document structure

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Product Dashboard</title>
    <meta name="description" content="Manage product inventory." />
  </head>
  <body>
    <header>
      <nav aria-label="Main navigation">
        <a href="/">Home</a>
      </nav>
    </header>
    <main>
      <h1>Products</h1>
      <section aria-labelledby="list-title">
        <h2 id="list-title">Product list</h2>
      </section>
    </main>
    <footer>Copyright information</footer>
  </body>
</html>
```

### Common semantic elements
- Structure: `header`, `nav`, `main`, `section`, `article`, `aside`, `footer`.
- Text: `h1`–`h6`, `p`, `strong`, `em`, `blockquote`, `code`.
- Lists: `ul`, `ol`, `li`, `dl`, `dt`, `dd`.
- Links/media: `a`, `img`, `picture`, `video`, `audio`, `figure`, `figcaption`.
- Forms: `form`, `label`, `input`, `textarea`, `select`, `option`, `button`, `fieldset`, `legend`.
- Tables: `table`, `caption`, `thead`, `tbody`, `tr`, `th`, `td`.
- Interactive/utility: `details`, `summary`, `dialog`, `template`.

### Forms

```html
<form id="product-form">
  <label for="name">Product name</label>
  <input id="name" name="name" required maxlength="120" />

  <label for="price">Price (cents)</label>
  <input id="price" name="priceCents" type="number" min="0" required />

  <button type="submit">Save product</button>
</form>
```

A label must be associated with its input. Native form attributes (`required`, `min`, `max`, `type`, `maxlength`) improve usability but do not replace backend validation.

### Accessibility/SEO basics
- Use a logical heading hierarchy.
- Add useful alternative text to meaningful images.
- Use `alt=""` for purely decorative images.
- Use descriptive link/button text.
- Define document title and useful description.
- Set page language.
- Avoid using a `<div>` for every element when a semantic element exists.

---

## 9. CSS Essentials

### CSS rule syntax

```css
.card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: white;
  box-shadow: 0 10px 30px rgb(15 23 42 / 8%);
}

.card h2 {
  margin: 0;
  font-size: 1.25rem;
}

.card:hover {
  transform: translateY(-2px);
}
```

### Selectors
- Element: `button`
- Class: `.card`
- ID: `#app`
- Descendant: `.card p`
- Direct child: `.card > p`
- Attribute: `input[required]`
- Pseudo-class: `:hover`, `:focus-visible`, `:checked`, `:disabled`
- Pseudo-element: `::before`, `::after`, `::placeholder`
- Selector list: `h1, h2, h3`

### Box model
Every CSS box involves content, padding, border and margin. `box-sizing: border-box` makes declared width include padding and border, which is often easier to reason about.

### Layout
- **Flexbox:** one-dimensional rows/columns and alignment.
- **Grid:** two-dimensional rows and columns.
- **Positioning:** static, relative, absolute, fixed, sticky.
- **Responsive rules:** `@media`.
- **Custom properties:** `--brand: #635bff;` used via `var(--brand)`.
- **Animation:** `@keyframes`, `animation`, `transition`, `transform`.

```css
:root {
  --brand: #4f46e5;
  --surface: #ffffff;
  --space: 1rem;
}

.layout {
  display: grid;
  grid-template-columns: 16rem minmax(0, 1fr);
  gap: var(--space);
}

@media (max-width: 48rem) {
  .layout {
    grid-template-columns: 1fr;
  }
}
```

### CSS functions
Common functions include `var()`, `calc()`, `min()`, `max()`, `clamp()`, `rgb()`, `hsl()`, `oklch()`, `linear-gradient()`, `radial-gradient()`, `minmax()`, `repeat()`, `fit-content()` and `url()`.

### Common pitfalls
- More selector specificity can override expected styles.
- Flex/grid children may need `min-width: 0` to prevent overflow.
- Avoid fixed widths that break small screens.
- Test keyboard focus and reduced motion.
- Prefer design tokens over random hard-coded colors.

---

## 10. Tailwind CSS

Tailwind is a utility-first styling framework. It is not a JavaScript component framework.

Example:

```html
<button class="rounded-lg bg-indigo-600 px-4 py-2 font-semibold text-white transition hover:bg-indigo-700 focus-visible:outline-2 disabled:opacity-50">
  Save
</button>
```

### Common class families
- Layout: `block`, `flex`, `grid`, `hidden`.
- Spacing: `p-*`, `m-*`, `gap-*`.
- Sizing: `w-*`, `h-*`, `min-w-*`, `max-w-*`, `size-*`.
- Typography: `text-*`, `font-*`, `leading-*`, `tracking-*`.
- Color: `text-*`, `bg-*`, `border-*`, `ring-*`.
- Borders: `border-*`, `rounded-*`.
- Effects: `shadow-*`, `opacity-*`, `blur-*`, `backdrop-blur-*`.
- Transform: `translate-*`, `rotate-*`, `scale-*`.
- Motion: `transition-*`, `duration-*`, `ease-*`, `animate-*`.
- Interaction: `cursor-*`, `select-*`, `pointer-events-*`.

### Variants

```html
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"></div>
<button class="hover:bg-indigo-700 focus-visible:ring-2 disabled:opacity-50"></button>
<div class="bg-white text-slate-900 dark:bg-slate-950 dark:text-white"></div>
```

Unprefixed styles apply by default; responsive prefixes apply at their configured breakpoint and above.

### Current v4 setup idea

For Vite, install `tailwindcss` and `@tailwindcss/vite`, add the plugin to Vite configuration, and put this in the CSS entry:

```css
@import "tailwindcss";
```

Tailwind v3 commonly used `@tailwind base;`, `@tailwind components;`, `@tailwind utilities;` plus a `tailwind.config.js` `content` array. Don't mix installation instructions without checking the version. See the official installation/upgrade guides.

### Dynamic classes
Don't construct strings like `` `bg-${color}-600` `` if the scanner cannot see complete class names. Instead, map allowed values to complete candidates:

```ts
const classes = {
  primary: 'bg-indigo-600 hover:bg-indigo-700',
  danger: 'bg-red-600 hover:bg-red-700',
};
```

Use Tailwind's theme customization and CSS variables for a consistent design system.

---

## 11. JavaScript Fundamentals

### Variables and values

```js
const appName = 'Store';
let count = 0;
const enabled = true;
const nothing = null;
let unknownValue; // undefined initially

const numbers = [2, 4, 6];
const user = { id: 'u1', email: 'demo@example.com' };
```

Prefer `const` by default and `let` for reassignment. Avoid `var` in new code unless maintaining legacy code.

### Types and operators
Primitive types include string, number, bigint, boolean, undefined, symbol and null. Objects include arrays, functions, dates and records.

```js
const total = 10 + 5;
const isValid = total >= 10 && enabled;
const label = user?.name ?? 'Guest';
```

Operators: arithmetic (`+ - * / % **`), comparison (`=== !== < > <= >=`), logical (`&& || !`), nullish coalescing (`??`), optional chaining (`?.`), assignment (`= += -=`), spread (`...`) and ternary (`condition ? a : b`).

Prefer `===` over coercive `==` in most application code.

### Conditions

```js
if (count > 10) {
  console.log('Large');
} else if (count > 0) {
  console.log('Positive');
} else {
  console.log('Zero or negative');
}

const statusLabel = enabled ? 'Enabled' : 'Disabled';

switch (statusLabel) {
  case 'Enabled':
    break;
  default:
    break;
}
```

### Loops

```js
for (let i = 0; i < numbers.length; i++) {}
for (const number of numbers) {}
while (count < 3) { count++; }
```

For arrays, common methods are `map`, `filter`, `find`, `findIndex`, `some`, `every`, `reduce`, `flatMap`, `includes`, `slice`, `sort`, `toSorted` (if runtime supports it), `forEach`, `push`, `pop`, `shift`, `unshift`, `splice`, and `join`.

```js
const doubled = numbers.map(n => n * 2);
const positives = numbers.filter(n => n > 0);
const found = numbers.find(n => n === 4);
const sum = numbers.reduce((total, n) => total + n, 0);
```

### Functions

```js
function add(a, b) {
  return a + b;
}

const multiply = (a, b) => a * b;

function greet(name = 'Guest') {
  return `Hello, ${name}`;
}
```

Understand parameters, arguments, return values, default parameters, rest parameters, closures and scope.

### Objects

```js
const product = { id: 'p1', name: 'Mouse', priceCents: 2499 };

const renamed = { ...product, name: 'Gaming Mouse' };
const { id, priceCents } = product;
```

Methods include `Object.keys`, `Object.values`, `Object.entries`, `Object.fromEntries`, `Object.assign`, `Object.hasOwn`, `Object.freeze`, `Object.is`, and `JSON.stringify`/`JSON.parse` for JSON serialization. JSON serialization has limits: functions, `undefined`, circular references, dates and special numeric values need care.

### Modules

```js
// math.js
export function add(a, b) { return a + b; }

// app.js
import { add } from './math.js';
```

### Promises and async/await

```js
async function loadProducts() {
  const response = await fetch('/api/products');
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return await response.json();
}

loadProducts()
  .then(products => console.log(products))
  .catch(error => console.error(error));
```

Use `try/catch/finally` for error handling and cleanup. `Promise.all()` runs independent promises concurrently and fails when one rejects; `Promise.allSettled()` reports every outcome.

### Browser APIs used in full-stack work
- `fetch()` for HTTP.
- `URL` / `URLSearchParams` for URLs and query parameters.
- `FormData` for forms/uploads.
- `localStorage` and `sessionStorage` for limited browser storage.
- `AbortController` to cancel requests.
- `setTimeout`, `setInterval`, `requestAnimationFrame`.
- DOM APIs: `querySelector`, `addEventListener`, `classList`, `createElement`, `append`, `remove`.

Storage in a browser is not a safe place for high-value secrets. Authentication storage choices require a threat-model decision; HttpOnly cookies can reduce token exposure to JavaScript but require suitable CSRF protections.

---

## 12. TypeScript Fundamentals

### Basic types

```ts
const title: string = 'Catalog';
const page: number = 1;
const active: boolean = true;
const ids: string[] = ['a', 'b'];
const prices: Array<number> = [10, 20];

type Role = 'customer' | 'admin';

interface User {
  id: string;
  email: string;
  role: Role;
  displayName?: string;
}
```

### Functions and generics

```ts
function byId<T extends { id: string }>(items: T[], id: string): T | undefined {
  return items.find(item => item.id === id);
}

type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; message: string; code?: string };
```

### Union and narrowing

```ts
function show(value: string | number) {
  if (typeof value === 'string') return value.toUpperCase();
  return value.toFixed(2);
}
```

### `unknown`, `any` and `never`
- `unknown`: value not yet checked; narrow before use.
- `any`: disables type checking; avoid spreading it through the app.
- `never`: values that cannot occur or functions that do not return normally.

### Interfaces, types, classes

```ts
interface Repository<T> {
  findById(id: string): Promise<T | null>;
  create(input: Omit<T, 'id'>): Promise<T>;
}

type UpdateProduct = Partial<Pick<Product, 'name' | 'priceCents'>>;
```

Common utility types: `Partial<T>`, `Required<T>`, `Readonly<T>`, `Pick<T, K>`, `Omit<T, K>`, `Record<K, T>`, `Exclude<T, U>`, `Extract<T, U>`, `NonNullable<T>`, `ReturnType<T>`, `Parameters<T>`, `Awaited<T>`.

Types are not runtime validation. Validate JSON received from an API using runtime schemas or DTO validation.

### TypeScript configuration concepts
- `strict`: enables strict type checking.
- `target`: JavaScript syntax target.
- `module`: module output/resolution model.
- `moduleResolution`: how imports resolve.
- `jsx`: JSX transformation mode.
- `noEmit`: type-check without generating JS.
- `outDir`: output directory.

Don't disable strict type checking just to hide problems in an existing codebase.

---

## 13. Frontend Frameworks and React

React is a library for building user interfaces from components. Other common options are Angular, Vue, Svelte and framework solutions such as Next.js or Nuxt. Learn the fundamentals of one before attempting all of them.

### Function component and props

```tsx
type ProductCardProps = {
  name: string;
  price: number;
};

function ProductCard({ name, price }: ProductCardProps) {
  return (
    <article className="rounded-xl border p-4">
      <h2 className="font-semibold">{name}</h2>
      <p>{(price / 100).toFixed(2)}</p>
    </article>
  );
}
```

### State

```tsx
const [count, setCount] = useState(0);
```

State updates trigger rendering. Don't directly mutate React state arrays/objects; produce new values. Hooks like `useState`, `useEffect`, `useMemo`, `useCallback`, `useRef`, `useContext`, `useReducer`, and custom hooks address different needs. Follow the Rules of Hooks.

### Fetch inside a component (simplified)

```tsx
type Product = { id: string; name: string };

function ProductList() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const response = await fetch('/api/products', { signal: controller.signal });
        if (!response.ok) throw new Error('Could not load products');
        setProducts(await response.json());
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          setError(error.message);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void load();
    return () => controller.abort();
  }, []);

  if (loading) return <p>Loading…</p>;
  if (error) return <p role="alert">{error}</p>;
  if (products.length === 0) return <p>No products yet.</p>;

  return <ul>{products.map(p => <li key={p.id}>{p.name}</li>)}</ul>;
}
```

This pattern teaches request states; for larger applications, use a dedicated data-fetching/query library or the framework's preferred data APIs to handle caching, retries and invalidation consistently.

### Forms/events/conditional rendering

```tsx
const [name, setName] = useState('');

<form onSubmit={handleSubmit}>
  <input value={name} onChange={e => setName(e.target.value)} />
  <button type="submit">Create</button>
</form>
```

Conditional rendering uses expressions:

```tsx
{loading ? <Spinner /> : error ? <ErrorMessage /> : <ProductList />}
```

Don't bury large business rules inside JSX; extract functions and components.

### React ecosystem tools
- Router: route transitions and nested pages.
- Query/data library: server-state caching, invalidation and mutation workflows.
- Form library: complex form state/validation.
- Schema validation: Zod or equivalent runtime validation.
- Testing: component tests plus browser/E2E tests.
- Component accessibility: keyboard behavior, labels and focus management.

Framework APIs change, so use the official React/Next.js docs for current recommended application setup. Create React App is deprecated; follow React's current installation guidance for new projects.

---

## 14. Frontend State, Forms and Navigation

### Distinguish three kinds of state
- **Local UI state:** open/closed modal, selected tab, typed input.
- **Server state:** products and users stored by an API; requires loading/error/cache/refetch strategies.
- **URL state:** filters, sort order, page, search query; often should survive reload/share.

Don't copy every server response into several separate local state stores. Define a source of truth and invalidation policy.

### Form workflow
1. Collect input.
2. Perform immediate usability validation.
3. Disable duplicate submissions while pending.
4. Submit to API.
5. Show field errors, success and server/network errors.
6. Update or invalidate server state.
7. Preserve user input if submission fails.

Front-end validation improves UX; back-end validation protects the system.

### Navigation
- Use anchors for navigation to a URL.
- Use buttons for actions.
- Use router links for client-side routes.
- Guard protected pages for UX, but enforce authorization on the backend.
- Handle unknown routes and unauthorized states.
- Avoid showing a fake button with no handler.

### Accessibility essentials
Use keyboard-reachable elements, proper labels, focus states, semantic headings, adequate contrast, reduced-motion handling, and accessible errors/status announcements.

---

## 15. Frontend-to-Backend Communication

### Use `fetch`

```ts
type Product = {
  id: string;
  name: string;
  priceCents: number;
};

async function getProducts(): Promise<Product[]> {
  const response = await fetch('http://localhost:4000/api/products');
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}
```

### Send JSON

```ts
async function createProduct(input: { name: string; priceCents: number }) {
  const response = await fetch('http://localhost:4000/api/products', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  const result = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(result?.message ?? `Request failed: ${response.status}`);
  }
  return result;
}
```

### Handle response categories
- `2xx`: successful.
- `4xx`: request/client/auth/permission issue.
- `5xx`: server/dependency failure.
- Network error: may be offline, DNS, blocked by CORS, TLS failure, or server unavailable.

`fetch()` does not reject merely because the server returned 404/500; check `response.ok` or status.

### CORS
Cross-Origin Resource Sharing controls whether browsers allow scripts from one origin to read another origin's response. Configure allowed origins on the backend. CORS is not authentication and doesn't protect an API from non-browser clients.

### API base URL
Use frontend environment configuration for a **public API base URL**, not private credentials. In many build tools, variables prefixed with a public/client prefix are embedded into the browser bundle.

---

## 16. HTTP, REST and API Design

### Core HTTP methods

| Method | Typical use |
|---|---|
| `GET` | Read resource(s) |
| `POST` | Create resource or trigger an action |
| `PUT` | Replace a resource representation |
| `PATCH` | Partially update a resource |
| `DELETE` | Delete resource |
| `OPTIONS` | Capability/CORS preflight |
| `HEAD` | Headers without response body |

### Example REST design

```text
GET    /api/products              list
GET    /api/products/:id          get one
POST   /api/products              create
PATCH  /api/products/:id          update
DELETE /api/products/:id          remove/archive
GET    /api/users/me              current user
POST   /api/auth/login            authenticate
POST   /api/auth/logout           sign out
```

Prefer plural nouns for resource collections and predictable behavior. Avoid making every endpoint a custom verb unless the action is genuinely not resource-shaped.

### HTTP status codes

| Status | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 202 | Accepted for async processing |
| 204 | Success with no body |
| 400 | Invalid request |
| 401 | Missing/invalid authentication |
| 403 | Caller is not allowed |
| 404 | Resource not found |
| 409 | State/uniqueness conflict |
| 422 | Semantically invalid input (API convention varies) |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error |
| 503 | Service temporarily unavailable |

### JSON response pattern

```json
{
  "data": {
    "id": "p123",
    "name": "Mechanical Keyboard",
    "priceCents": 4999
  }
}
```

A consistent error shape might be:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Please check the submitted fields",
    "fields": {
      "name": "Name is required"
    }
  }
}
```

Do not expose stack traces, internal SQL, secret values or private infrastructure details.

### Pagination/filtering/sorting

```text
GET /api/products?page=1&limit=20&search=keyboard&sort=createdAt&order=desc
```

Validate all query values, cap page size and allow-list sortable fields. Never inject a raw query parameter directly into an SQL `ORDER BY`.

---

## 17. Backend Fundamentals

### Core request path

A backend commonly uses:
- router/controller/handler: selects the code for a request;
- schema/DTO validator: checks input shape;
- middleware/guard: handles shared request processing/auth;
- service/use case: business logic;
- data access: ORM, repository, SQL driver;
- error handler/filter: consistent failure responses;
- logger/metrics: diagnostics and monitoring.

### Basic server responsibilities
- Parse request method/path/query/headers/body.
- Validate input size and shape.
- Authenticate the caller.
- Authorize the requested action and record scope.
- Apply business rules.
- Read/write persistent data safely.
- Return suitable status, headers and response body.
- Record actionable server diagnostics without leaking secrets.

### Important backend concepts
- **Stateless request handling:** servers may handle many concurrent requests; do not store user session in a global variable.
- **Concurrency:** simultaneous requests may race to update the same record.
- **Idempotency:** repeating a request should not accidentally duplicate a charge/order.
- **Transactions:** related database writes succeed or fail atomically.
- **Timeouts:** external dependencies must not hang forever.
- **Connection pooling:** reuse database connections safely.
- **Graceful shutdown:** stop receiving work and close clients/workers properly.

---

## 18. Node.js + Express

Node.js runs JavaScript outside the browser. Express is a minimal HTTP framework.

### Setup

```bash
mkdir api
cd api
npm init -y
npm install express
npm install --save-dev typescript tsx @types/node @types/express
```

For an actual TypeScript app, configure `tsconfig.json` and scripts in `package.json`; exact defaults vary by starter.

### Basic TypeScript server

```ts
import express from 'express';

const app = express();
app.use(express.json({ limit: '1mb' }));

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.listen(4000, () => {
  console.log('API listening on port 4000');
});
```

### Routes, params, query and body

```ts
app.get('/api/products/:id', (req, res) => {
  const { id } = req.params;
  res.json({ id });
});

app.get('/api/products', (req, res) => {
  const search = String(req.query.search ?? '');
  res.json({ search, items: [] });
});

app.post('/api/products', (req, res) => {
  const { name } = req.body ?? {};
  if (typeof name !== 'string' || !name.trim()) {
    return res.status(400).json({ message: 'Name is required' });
  }
  return res.status(201).json({ name: name.trim() });
});
```

This only demonstrates routing. Validate using a proper runtime schema, not ad hoc checks scattered through production routes.

### Middleware

```ts
app.use((req, _res, next) => {
  console.log(req.method, req.path);
  next();
});
```

Middleware is useful for request IDs, logging, body parsing and shared infrastructure. Do not log sensitive bodies or authorization tokens.

### Error middleware
Express has special error-handling middleware with four parameters `(err, req, res, next)`. Put it after the routes; pass errors forward using the framework-supported approach for your Express version. Return sanitized messages and log details server-side.

### Express best practices
- Split routes/controllers/services/data access.
- Validate parameters, query, body and external responses.
- Use parameterized database queries.
- Handle async errors according to the installed Express version and wrappers.
- Set request body limits, timeouts, security headers and rate limits.
- Avoid process-global per-user data.
- Use a process manager/platform health checks in production.

---

## 19. NestJS

NestJS is a structured Node.js/TypeScript framework built around dependency injection and modules.

### Main concepts
- `@Module()` groups a feature.
- `@Controller()` declares routes.
- `@Injectable()` marks injectable providers.
- DTO classes plus `ValidationPipe` validate inputs.
- Guards handle access decisions.
- Interceptors wrap handler execution.
- Exception filters format errors.
- Middleware performs early shared request processing.

### Controller/service shape

```ts
@Controller('products')
export class ProductsController {
  constructor(private readonly service: ProductsService) {}

  @Get()
  findAll() {
    return this.service.findAll();
  }

  @Post()
  create(@Body() dto: CreateProductDto) {
    return this.service.create(dto);
  }
}
```

```ts
@Injectable()
export class ProductsService {
  findAll() {
    // Query database through repository/ORM.
    return [];
  }

  create(dto: CreateProductDto) {
    // Apply business rules and persist.
    return dto;
  }
}
```

Register the controller and service in the owning `@Module()`. The shown return values are placeholders until connected to a real data layer.

### CLI

```bash
npm install --global @nestjs/cli
nest new api
nest g module products
nest g controller products
nest g service products
nest g resource products
npm run start:dev
```

### Global validation

```ts
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,
  forbidNonWhitelisted: true,
  transform: true,
}));
```

### Dependency injection
Nest resolves providers from module registration. Export services from their owning module if another module needs them, then import that module. Prefer constructor injection over manually creating service instances.

Nest is a good choice when you want a consistent modular architecture, testability, guards/interceptors and many official integration points. See the official docs for the full API and version-specific features.

---

## 20. Python: FastAPI and Django

Python is used in APIs, automation, data work and AI services.

### Syntax basics

```py
name: str = "Catalog"
price_cents: int = 4999
active: bool = True

def format_price(cents: int) -> str:
    return f"{cents / 100:.2f}"

products = [{"id": "p1", "name": "Keyboard"}]
active_products = [p for p in products if p["name"] != ""]
```

Learn functions, modules, packages, exceptions, classes, type hints, dictionaries/lists/sets, generators, context managers, `async`/`await`, tests and dependency isolation.

### FastAPI

FastAPI is suited to typed JSON APIs and OpenAPI documentation.

```py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    price_cents: int = Field(ge=0)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/products", status_code=201)
def create_product(dto: ProductCreate):
    return {"id": "temporary-id", **dto.model_dump()}
```

The ID above is a placeholder; persist records in a database for real CRUD. `async def` is useful when calling asynchronous libraries, but don't wrap blocking operations in async functions and assume they are non-blocking.

### Django

Django is a batteries-included framework with URL routing, views, templates, ORM, migrations, admin and authentication features.

Conceptual view:

```py
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok"})
```

Typical Django work involves:
- `models.py`: data models.
- `views.py`: request handlers.
- `urls.py`: URL mapping.
- templates: server-rendered HTML, if used.
- forms/serializers: validated input.
- migrations: schema changes.
- middleware and settings: application configuration.

Django REST Framework is commonly used to build REST APIs using serializers, viewsets, routers, authentication and permissions. Use `DEBUG=False`, secure secret settings, allowed hosts, HTTPS/cookie protections and production database configuration before deployment.

### FastAPI vs Django

| Choose FastAPI when… | Choose Django when… |
|---|---|
| API-first service, typed request/response schemas | You need a broad full-web framework |
| You prefer lightweight route composition | You need built-in admin/ORM/conventions |
| Async integrations are central | Server-rendered pages and admin workflows are important |

---

## 21. Java + Spring Boot

Java is strongly typed and commonly used for enterprise backend systems. Spring Boot simplifies configuration, dependency injection and server startup.

### Java basics

```java
public record ProductDto(String name, int priceCents) {}

public class PriceService {
    public int total(int priceCents, int quantity) {
        return priceCents * quantity;
    }
}
```

Learn classes, interfaces, generics, collections, exceptions, streams, records, annotations, packages, access modifiers, tests and build tools (Maven/Gradle).

### Typical Spring Boot layers
- `@RestController`: HTTP controller.
- `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@PatchMapping`, `@DeleteMapping`: route declarations.
- `@Service`: business logic.
- `@Repository`: persistence abstraction.
- `@Entity`: ORM entity for JPA.
- `@Configuration`: bean configuration.
- `@Autowired` / constructor injection: dependency wiring.
- Bean Validation annotations: input validation.
- Spring Security: authentication/authorization.

### Controller shape

```java
@RestController
@RequestMapping("/api/products")
public class ProductController {
    @GetMapping
    public List<ProductDto> list() {
        return List.of();
    }
}
```

This is a syntax sketch; a production app needs service/repository integration, DTO validation, error handling and security configuration. Spring Boot's official reference has separate guides for web, data access, testing, security and production features.

---

## 22. PHP + Laravel and Rust + Axum

### PHP + Laravel

Laravel provides routing, controllers, middleware, request validation, Eloquent ORM, migrations, queues, events, authentication helpers and testing tools.

Typical route syntax:

```php
Route::get('/api/products', [ProductController::class, 'index']);
Route::post('/api/products', [ProductController::class, 'store']);
Route::get('/api/products/{product}', [ProductController::class, 'show']);
Route::patch('/api/products/{product}', [ProductController::class, 'update']);
Route::delete('/api/products/{product}', [ProductController::class, 'destroy']);
```

Use Laravel validation/request classes for input, policies/gates for authorization, Eloquent or safe query APIs for persistence, migrations for schema changes, and configuration/secrets appropriate to the deployment. Route protection in the frontend is not enough.

### Rust + Axum

Rust emphasizes ownership, borrowing, explicit types and memory safety. Axum uses Tokio for async execution and often Serde for JSON serialization.

Basic Rust syntax:

```rust
#[derive(serde::Serialize)]
struct Product {
    id: String,
    name: String,
    price_cents: i64,
}
```

Common web stack concepts include `Router`, `route`, `get`, `post`, `State`, `Path`, `Query`, `Json`, `IntoResponse`, middleware/layers, async handlers and SQLx for database queries. Exact handler syntax and crate APIs depend on versions; consult Axum/Tokio/SQLx documentation before copying an older example.

### Which one should you learn first?
Choose the ecosystem that fits your goal, job market, deployment constraints and project requirements. Learning more languages is valuable, but mastering one end-to-end stack first gives a clearer foundation.

---

## 23. Databases: Core Concepts

### Relational databases
Organize data into tables with columns and rows. Tables connect through primary and foreign keys. Examples: PostgreSQL, MySQL, SQL Server, SQLite.

### Document databases
Store document-shaped records, often JSON-like. MongoDB is a common example.

### Cache/key-value storage
Redis can hold expiring values, counters, queues-related state, locks and other data structures. It is usually a supporting system, not automatically a replacement for the primary database.

### Vocabulary
- **Database:** a collection of data structures.
- **Table/collection:** stores rows/documents.
- **Row/document:** one record.
- **Column/field:** a value/property in a record.
- **Primary key:** unique row identifier.
- **Foreign key:** referential link between tables.
- **Index:** speeds up selected lookups at storage/write cost.
- **Constraint:** enforces integrity (NOT NULL, UNIQUE, CHECK, FK).
- **Transaction:** atomic group of database operations.
- **Migration:** versioned schema change.
- **Seed:** initial or development/test data.
- **Connection pool:** reuses database connections.
- **ORM:** maps application types/models to database operations.
- **Backup/restore:** recover after mistakes, outages or corruption.

### Design principles
- Choose appropriate types, including timezone-aware timestamps where appropriate.
- Add `NOT NULL`, `UNIQUE`, foreign-key and check constraints for important invariants.
- Index based on actual query patterns.
- Store money as integer minor units (such as cents/paise) or an exact decimal type, not ordinary floating-point.
- Decide delete behavior intentionally (cascade, restrict, soft delete).
- Do not store passwords in plaintext.
- Build backups and practice restores before production.

---

## 24. SQL Essentials

### Create database/table (syntax varies by DB)

```sql
CREATE TABLE products (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  description TEXT,
  price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

This identity/timestamp syntax is PostgreSQL-oriented. MySQL, SQL Server and SQLite use dialect-specific types/identity declarations.

### Insert

```sql
INSERT INTO products (name, description, price_cents)
VALUES ('Keyboard', 'Mechanical keyboard', 4999)
RETURNING id, name, price_cents;
```

`RETURNING` is supported by PostgreSQL and some other systems; MySQL syntax differs by operation/version.

### Select, filter, sort, limit

```sql
SELECT id, name, price_cents
FROM products
WHERE active = TRUE AND price_cents >= 1000
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

Always define an intentional sort when results must be stable. Validate and cap user-provided pagination values.

### Update and delete

```sql
UPDATE products
SET price_cents = 5299
WHERE id = 1;

DELETE FROM products
WHERE id = 1;
```

Never update/delete a production table without a suitable `WHERE` condition unless you intentionally want every row changed.

### Joins

```sql
SELECT orders.id, users.email, orders.total_cents
FROM orders
JOIN users ON users.id = orders.user_id;
```

- `INNER JOIN`: only matches.
- `LEFT JOIN`: keeps all rows on the left even without a match.
- `RIGHT JOIN`: keeps all rows on the right.
- `FULL JOIN`: keeps all rows from both sides where supported.

### Aggregates and grouping

```sql
SELECT active, COUNT(*) AS product_count, AVG(price_cents) AS average_cents
FROM products
GROUP BY active
HAVING COUNT(*) > 0;
```

Common aggregate functions include `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, plus database-specific aggregates.

### Common SQL concepts
- `WHERE`, `ORDER BY`, `GROUP BY`, `HAVING`, `DISTINCT`.
- `IN`, `BETWEEN`, `LIKE`, `ILIKE` (dialect-specific), `IS NULL`.
- `CASE WHEN ... THEN ... ELSE ... END`.
- Subqueries and common table expressions (`WITH`).
- Window functions such as `ROW_NUMBER`, `RANK`, `LAG`, `LEAD`.
- Views, indexes and constraints.
- `BEGIN`, `COMMIT`, `ROLLBACK` (driver/transaction APIs may manage these).
- `EXPLAIN` / query plan tools for performance analysis.

### Prevent SQL injection
Use parameterized queries:

```ts
const result = await pool.query(
  'SELECT id, name FROM products WHERE id = $1',
  [productId],
);
```

Do not create SQL like:

```ts
// Unsafe: never concatenate untrusted user input into SQL.
const sql = `SELECT * FROM products WHERE id = ${productId}`;
```

For SQL identifiers such as dynamic column names, use a strict allow-list; bind parameters normally represent values, not arbitrary table/column identifiers.

---

## 25. PostgreSQL and MySQL

### PostgreSQL
Good general-purpose relational database with strong SQL features, constraints, indexing, transactions and JSON support.

Common client/management tasks:
- Create database and application-specific database user.
- Configure network access and credentials.
- Run versioned migrations.
- Add indexes to observed slow queries.
- Use appropriate connection pool sizes.
- Back up and test restoration.
- Restrict app user permissions to required operations.

### MySQL
Widely used relational database in web hosting and application stacks. MySQL uses a different SQL dialect and feature/version support differs from PostgreSQL. Check exact documentation for types, constraints, transaction engine, index behavior and migrations.

### Connection string concept

```dotenv
DATABASE_URL=postgresql://app_user:replace_me@localhost:5432/app_db
```

Do not hard-code actual passwords in code or commit them into Git. Use environment configuration and secret management.

### When to use SQLite
SQLite is excellent for local tools, prototypes, tests and some smaller deployed applications. It differs from client/server databases in concurrency, hosting, permissions and operational model. Confirm it suits expected write volume and deployment storage.

---

## 26. MongoDB

MongoDB stores documents in collections.

### Example document

```json
{
  "_id": "p123",
  "name": "Mechanical Keyboard",
  "priceCents": 4999,
  "tags": ["keyboard", "gaming"],
  "active": true
}
```

### Mongo shell CRUD examples

```js
db.products.insertOne({
  name: 'Keyboard',
  priceCents: 4999,
  active: true
});

db.products.find({ active: true }).sort({ name: 1 }).limit(20);

db.products.updateOne(
  { _id: ObjectId('...') },
  { $set: { priceCents: 5299 } }
);

db.products.deleteOne({ _id: ObjectId('...') });
```

The placeholder ObjectId must be replaced with a valid ID in a real shell session. Driver-level API calls differ somewhat from the shell.

### Common query operators
- Comparison: `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`.
- Logical: `$and`, `$or`, `$not`, `$nor`.
- Array: `$elemMatch`, `$all`, `$size`.
- Update: `$set`, `$unset`, `$inc`, `$push`, `$addToSet`, `$pull`.
- Aggregation: `$match`, `$project`, `$group`, `$sort`, `$limit`, `$lookup`, `$unwind`.

Always build filters from validated allowed fields; don't pass arbitrary client-supplied Mongo query objects into your database layer. Design indexes around query patterns and understand document growth/embedding vs referencing tradeoffs.

---

## 27. Redis and Caching

Redis commonly supports short-lived caching, counters, rate limits, session state, queue systems and coordination mechanisms.

### Common command concepts

```text
SET key value
GET key
DEL key
EXPIRE key seconds
TTL key
INCR key
LPUSH key value
RPOP key
HSET key field value
HGET key field
SADD key member
SMEMBERS key
```

These are command examples; client-library APIs differ by programming language.

### Cache-aside pattern
1. App checks the cache for a key.
2. If present, use cached data.
3. If missing, read from the primary database.
4. Store a cache copy with an expiration.
5. On relevant writes, update or invalidate the cache.

### Cache risks
- Stale values.
- Accidentally sharing one user's private response with another.
- Cache stampedes if many requests miss simultaneously.
- Memory exhaustion if keys don't expire.
- Treating a cache as durable storage without correct configuration.

Include tenant/user identifiers in cache keys when authorization affects the result. Define invalidation behavior before shipping.

---

## 28. ORMs, Migrations and Data Access

An ORM maps application models to database records, but it doesn't eliminate the need to understand SQL, indexing, constraints or transactions.

### Popular choices
- TypeScript/Node: Prisma, TypeORM, Drizzle, Sequelize.
- Python: Django ORM, SQLAlchemy, SQLModel.
- Java: Spring Data JPA / Hibernate.
- PHP: Eloquent in Laravel.
- Rust: SQLx, Diesel, SeaORM.

### Common ORM benefits
- Typed or model-based query building.
- Object/record mapping.
- Relations and query conveniences.
- Migration tooling.
- Transaction helpers.
- Testable abstraction around persistence.

### Common ORM risks
- N+1 queries.
- Unbounded `findMany` / list calls.
- Accidentally loading unnecessary columns/relations.
- Hidden transaction assumptions.
- Query injection from raw SQL.
- Schema drift between environments.
- Leaking fields by serializing full database models.

### Migration workflow
1. Change the schema in code/migration definition.
2. Generate or write a migration.
3. Review generated SQL.
4. Apply to a clean local/test database.
5. Test the application against the new schema.
6. Back up important production data.
7. Apply migrations with the documented deployment process.
8. Verify deployment/rollback strategy.

Never make production schema changes manually without recording them in the project's migration history.

---

## 29. Authentication and Authorization

### The difference
- **Authentication:** establishes who the caller is.
- **Authorization:** establishes what that identity may do.

An authenticated user may still be forbidden to edit another user's record.

### Common models
- Server-side session with secure cookie.
- Access token plus a controlled refresh strategy.
- OAuth 2.0 / OpenID Connect with a trusted identity provider.
- Scoped API key for service-to-service use.

Choose based on the threat model; don't combine schemes without knowing why.

### Sign-in flow
1. Validate the submitted data.
2. Find the account.
3. Verify password using a password-hashing library.
4. Issue a session/token.
5. Return only safe user information.
6. Apply auth checks on protected backend routes.
7. Verify ownership/roles for each sensitive action.
8. Define logout, expiration, refresh, revocation and password-reset flows.

### Password storage
Never store plaintext passwords. Use a recognized password-hashing scheme such as Argon2id or scrypt with suitable parameters. Plain SHA-256 is not a password storage strategy.

### Cookie safety
Use HTTPS in production, `HttpOnly`, suitable `Secure` and `SameSite` settings, deliberate expiration/domain/path, and CSRF defenses where needed. Never log session IDs or tokens.

### JWT safety
A signed JWT is usually not encrypted. Do not put passwords or secrets in the payload. Validate signature, expiry, issuer and audience as required. Keep signing keys outside source code and rotate them carefully.

### Authorization examples
- Role-based access control (RBAC): role grants capabilities.
- Attribute-based access control (ABAC): policy depends on user/resource/context attributes.
- Ownership rules: user can access only their record.
- Tenant boundaries: one organization's data is isolated from another.

The server must enforce access rules for each operation; frontend route guards are only a UX layer.

---

## 30. Security for the Whole Stack

### Input validation
Validate request bodies, path parameters, query strings, uploaded files, webhook payloads and upstream API responses. Set length/range/format limits. Reject unexpected fields where practical.

### Common web risks
- Broken access control.
- Injection (SQL/NoSQL/command/template).
- Authentication and session weaknesses.
- Security misconfiguration.
- Vulnerable/outdated dependencies.
- Cryptographic and secret-management failures.
- Cross-site scripting (XSS).
- Cross-site request forgery (CSRF).
- Server-side request forgery (SSRF).
- Unrestricted file upload and resource consumption.

Use the current OWASP Top 10 and framework-specific security docs as checklists; no list replaces a threat model or security test.

### Security baseline
- Use HTTPS for deployed sites and APIs.
- Set security headers appropriate for your application.
- Configure CORS precisely.
- Use parameterized database queries.
- Limit request and upload size.
- Rate-limit sensitive/expensive endpoints.
- Use least-privilege database/service credentials.
- Keep dependencies patched and audit them.
- Hide internal exceptions from client responses.
- Avoid logging secrets or sensitive user payloads.
- Use secure defaults for cookies.
- Protect privileged actions with authorization and audit logs.
- Use CSRF defenses where required.
- Add timeouts and controlled retries to outbound API calls.
- Validate upload content, size, type and storage path.
- Backup databases and test restore procedures.

### Dependency hygiene
- Commit a lockfile.
- Prefer maintained packages from trusted sources.
- Remove packages that aren't needed.
- Review new dependencies for maintenance, license, transitive packages and security.
- Run automated audits and update through a controlled review process.

---

## 31. File Uploads and External APIs

### File upload pipeline
1. Authenticate caller and authorize upload capability.
2. Limit file bytes, number and accepted format.
3. Check actual content; don't trust browser-provided MIME/extension alone.
4. Generate a server-side file name.
5. Store outside executable/public code directories.
6. Use object storage for larger production assets.
7. Save metadata in the database.
8. Authorize downloads; use signed URLs where appropriate.
9. Scan files when the risk/use case requires it.
10. Clean up abandoned uploads and failed partial operations.

### External API call
- Put base URLs and credentials in server-side config.
- Set timeouts.
- Validate upstream response shape.
- Handle non-2xx status codes.
- Retry only safe operations or use idempotency keys.
- Add rate limits and circuit-breaker behavior if needed.
- Record useful logs without recording secrets.
- Respect upstream API terms and limits.

Never send private service credentials to the browser to let it call a privileged API directly.

### Webhooks
Verify signatures using the provider's official algorithm, reject replayed/stale events when supported, enforce body limits, process idempotently, and return the expected acknowledgment. Don't trust a webhook merely because its payload looks correct.

---

## 32. Testing and Debugging

### Test levels

| Test type | What it checks |
|---|---|
| Unit | One function/service in isolation |
| Component | UI component behavior |
| Integration | Multiple real parts working together |
| API/integration | Route + validation + data access behavior |
| E2E | User journey across browser/API/database |
| Load/performance | Behavior under target traffic |
| Security tests | Access boundaries, input attacks, misconfiguration |

### Example unit test idea (TypeScript/Jest-style)

```ts
describe('formatPrice', () => {
  it('formats cents as a decimal amount', () => {
    expect(formatPrice({ id: 'p1', name: 'Mouse', priceCents: 2499 }))
      .toBe('24.99');
  });
});
```

Adapt test runner/mocking APIs to the project (Vitest, Jest, Pytest, JUnit, PHPUnit, Rust test harness, etc.).

### What to test in CRUD
- Valid create/read/update/delete.
- Invalid data and unexpected fields.
- Missing records.
- Duplicate unique values.
- No auth / insufficient permission.
- Wrong resource owner / tenant.
- Database transaction rollback.
- Pagination bounds.
- Network/timeouts and upstream errors.
- Upload size/type restriction.
- Frontend loading/empty/error states.
- keyboard and form accessibility.

### Debugging workflow
1. Reproduce the problem.
2. Read the exact error and stack trace.
3. Identify whether it is UI, network, backend, database, environment or deployment.
4. Check browser Network tab for URL/method/status/body.
5. Check API logs with correlation/request ID.
6. Check database query/migration/constraints.
7. Make one targeted fix.
8. Add a regression test.
9. Run lint, type-check, unit/integration/E2E tests and production build.

Don't declare an issue fixed just because the UI looks right. Verify the underlying operation.

---

## 33. Git and GitHub Workflow

### Initial setup

```bash
git init
git status
git add .
git commit -m "Initial project"
git branch -M main
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

Replace placeholders with your actual repository. If a remote already exists, inspect it before adding another:

```bash
git remote -v
git remote set-url origin https://github.com/USERNAME/REPOSITORY.git
```

### Daily commands

```bash
git status
git diff
git diff --staged
git add path/to/file
git add .
git commit -m "Add product API"
git log --oneline --graph --decorate -12
git fetch
git pull --rebase
git push
```

### Branch workflow
1. Create a feature branch.
2. Commit small logical changes.
3. Push the branch.
4. Open a pull request/review.
5. Run automated tests.
6. Merge and delete old branch when appropriate.

### `.gitignore` basics

```gitignore
node_modules/
dist/
build/
coverage/
.env
.env.*
!.env.example
.venv/
__pycache__/
.DS_Store
```

Add framework/build/database-specific generated files as necessary. Don't commit real credentials, personal data or huge build outputs. Deleting a secret in a later commit does not erase it from history; rotate it immediately and clean history if appropriate.

---

## 34. Environment Variables and Secrets

### Example `.env.example`

```dotenv
NODE_ENV=development
PORT=4000
DATABASE_URL=postgresql://app_user:replace_me@localhost:5432/app_db
FRONTEND_ORIGIN=http://localhost:5173
SESSION_SECRET=replace-with-a-long-random-secret
```

`.env.example` documents required variable names with fake values. Keep actual `.env` files out of Git.

### Principles
- Read values through framework configuration.
- Validate required values at startup.
- Differentiate development/test/staging/production.
- Use a secret manager or runtime secret configuration in production.
- Rotate exposed credentials.
- Do not log entire environment/config objects.
- Do not name private secrets with a frontend-exposed prefix (for example, `VITE_*` variables are typically public in Vite builds).
- Avoid committing database URLs, JWT signing keys, cloud keys, OAuth client secrets or personal tokens.

---

## 35. Docker and Local Development

Docker packages applications and their runtime dependencies into images/containers. Docker Compose defines multi-container development/operations setups.

### Basic API Dockerfile concept

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 4000
CMD ["npm", "run", "start:prod"]
```

This is a starter example, not a production universal. For production, use a tested multi-stage build, compatible supported runtime, only needed production dependencies, non-root user, correct generated entry point, and appropriate health/shutdown behavior.

### `.dockerignore`

```gitignore
node_modules
dist
coverage
.git
.env
.env.*
!.env.example
```

Make sure files required by the build are not excluded.

### Compose idea (database)

```yaml
services:
  db:
    image: postgres:18
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: local_only_change_me
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Use only local/example credentials in development. For real deployments, use secret management, restrict database exposure and configure backups, health checks, private networks and upgrades carefully. Check the database image's official supported tags and version before using them.

### What Docker does not do automatically
It does not secure your app, create correct backups, migrate schemas, manage secrets safely, provide monitoring, or guarantee high availability without additional design.

---

## 36. Deployment and CI/CD

### Deployment options
- Static hosting/CDN for frontend assets.
- Managed app hosting or containers for backend.
- Managed relational/document database.
- Object storage for uploads.
- Redis/managed cache where useful.
- Reverse proxy/load balancer and TLS termination.
- CI/CD system to test/build/deploy on controlled events.

### Release pipeline
1. Fetch code.
2. Install dependencies from the lockfile.
3. Format/lint/type-check.
4. Run unit and integration tests.
5. Build frontend and backend.
6. Scan dependencies and validate configuration.
7. Build artifacts/container images.
8. Apply database migrations using a controlled job.
9. Deploy gradually.
10. Run smoke/health checks.
11. Monitor error/latency metrics.
12. Roll back when the release is unhealthy.

### Production checklist
- No development credentials or debug mode.
- HTTPS and correct CORS.
- Validated config/secret values.
- Compatible runtime and pinned dependencies.
- Database indexes, migrations and tested backups.
- Logs, metrics, traces, health checks and alerts.
- Resource limits and request timeouts.
- Rate limiting and security headers.
- Graceful shutdown and rollback plan.
- Privacy/data retention and legal requirements considered.
- Restore procedure tested rather than assumed.

---

## 37. Performance, SEO, Accessibility and UX

### Frontend performance
- Optimize images and use modern formats where appropriate.
- Avoid shipping unnecessary JavaScript.
- Split heavy routes/components and lazy-load suitable assets.
- Limit re-rendering only where profiling shows a problem.
- Reserve space for media to reduce layout shifts.
- Cache static assets with versioned filenames.
- Measure bundle size and web performance metrics.

### Backend performance
- Paginate responses and cap page size.
- Index and examine slow queries.
- Avoid N+1 data access.
- Use connection pools appropriately.
- Add request timeouts and concurrency bounds.
- Cache hot data only with a defined invalidation policy.
- Move slow non-interactive work to queues.
- Measure CPU, memory, latency and error rates before optimizing.

### SEO
- Use semantic HTML and meaningful titles/descriptions.
- Provide crawlable links and appropriate canonical/metadata.
- Render content in a way search engines can access, especially for pages needing indexing.
- Provide descriptive image alt text when informative.
- Ensure the site is fast and mobile-usable.

### Accessibility
- Keyboard access and visible focus.
- Labels and useful errors on forms.
- Correct semantic controls and heading order.
- Sufficient color contrast.
- Reduced motion preferences.
- Screen-reader-friendly status messages.
- Don't use color as the only indicator.
- Test with keyboard and assistive technology.

### UX states that every real screen needs
- Loading.
- Success.
- Empty result.
- Validation error.
- API/network error.
- Unauthorized/forbidden.
- Not found.
- Disabled/pending action.
- Retry/recovery route where appropriate.

---

## 38. A Working Mini Full-Stack CRUD Example

This section demonstrates how the parts connect. It is an educational starter, not a complete production-ready inventory system. It uses **React/TypeScript frontend + Express/TypeScript backend + PostgreSQL**. You can replace Express with NestJS later while keeping the API contract and database concepts.

### 38.1 API contract

```text
GET    /api/products
POST   /api/products
GET    /api/products/:id
PATCH  /api/products/:id
DELETE /api/products/:id
```

A product response:

```json
{
  "id": 1,
  "name": "Keyboard",
  "priceCents": 4999,
  "active": true
}
```

Create request:

```json
{
  "name": "Keyboard",
  "priceCents": 4999
}
```

### 38.2 Database schema (PostgreSQL)

```sql
CREATE TABLE products (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 38.3 Backend setup

```bash
mkdir api
cd api
npm init -y
npm install express pg cors dotenv
npm install --save-dev typescript tsx @types/node @types/express @types/pg @types/cors
```

Create a TypeScript config appropriate to the selected module system and scripts such as:
- `dev`: run `tsx watch src/server.ts`
- `build`: compile TypeScript into `dist`
- `start`: run the compiled output

Use a lockfile and check the installed package versions. Create `api/.env` locally (never commit it):

```dotenv
PORT=4000
DATABASE_URL=postgresql://app_user:local_password@localhost:5432/app_db
FRONTEND_ORIGIN=http://localhost:5173
```

### 38.4 Database connection

`api/src/db.ts`:

```ts
import pg from 'pg';
import 'dotenv/config';

const { Pool } = pg;

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30_000,
  connectionTimeoutMillis: 5_000,
});
```

Your PostgreSQL server/user/database must exist, and the connection string must match your local setup. For managed DBs, configure TLS options according to that provider's instructions.

### 38.5 Backend routes with parameterized SQL

`api/src/server.ts`:

```ts
import express from 'express';
import cors from 'cors';
import 'dotenv/config';
import { pool } from './db';

const app = express();

app.use(cors({
  origin: process.env.FRONTEND_ORIGIN,
}));
app.use(express.json({ limit: '1mb' }));

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.get('/api/products', async (_req, res, next) => {
  try {
    const result = await pool.query(
      `SELECT id, name, price_cents AS "priceCents", active
       FROM products
       ORDER BY id DESC
       LIMIT 100`
    );
    res.json(result.rows);
  } catch (error) {
    next(error);
  }
});

app.post('/api/products', async (req, res, next) => {
  try {
    const name = typeof req.body?.name === 'string' ? req.body.name.trim() : '';
    const priceCents = req.body?.priceCents;

    if (!name || name.length > 120) {
      return res.status(400).json({ message: 'Name must be 1–120 characters' });
    }
    if (!Number.isInteger(priceCents) || priceCents < 0) {
      return res.status(400).json({ message: 'priceCents must be a non-negative integer' });
    }

    const result = await pool.query(
      `INSERT INTO products (name, price_cents)
       VALUES ($1, $2)
       RETURNING id, name, price_cents AS "priceCents", active`,
      [name, priceCents],
    );

    return res.status(201).json(result.rows[0]);
  } catch (error) {
    return next(error);
  }
});

app.get('/api/products/:id', async (req, res, next) => {
  try {
    const id = Number(req.params.id);
    if (!Number.isSafeInteger(id) || id < 1) {
      return res.status(400).json({ message: 'Invalid product id' });
    }

    const result = await pool.query(
      `SELECT id, name, price_cents AS "priceCents", active
       FROM products WHERE id = $1`,
      [id],
    );
    if (result.rowCount === 0) {
      return res.status(404).json({ message: 'Product not found' });
    }
    return res.json(result.rows[0]);
  } catch (error) {
    return next(error);
  }
});

app.patch('/api/products/:id', async (req, res, next) => {
  try {
    const id = Number(req.params.id);
    const name = typeof req.body?.name === 'string' ? req.body.name.trim() : '';
    const priceCents = req.body?.priceCents;

    if (!Number.isSafeInteger(id) || id < 1) {
      return res.status(400).json({ message: 'Invalid product id' });
    }
    if (!name || name.length > 120) {
      return res.status(400).json({ message: 'Name must be 1–120 characters' });
    }
    if (!Number.isInteger(priceCents) || priceCents < 0) {
      return res.status(400).json({ message: 'priceCents must be a non-negative integer' });
    }

    const result = await pool.query(
      `UPDATE products
       SET name = $1, price_cents = $2
       WHERE id = $3
       RETURNING id, name, price_cents AS "priceCents", active`,
      [name, priceCents, id],
    );
    if (result.rowCount === 0) {
      return res.status(404).json({ message: 'Product not found' });
    }
    return res.json(result.rows[0]);
  } catch (error) {
    return next(error);
  }
});

app.delete('/api/products/:id', async (req, res, next) => {
  try {
    const id = Number(req.params.id);
    if (!Number.isSafeInteger(id) || id < 1) {
      return res.status(400).json({ message: 'Invalid product id' });
    }

    const result = await pool.query(
      'DELETE FROM products WHERE id = $1 RETURNING id',
      [id],
    );
    if (result.rowCount === 0) {
      return res.status(404).json({ message: 'Product not found' });
    }
    return res.status(204).end();
  } catch (error) {
    return next(error);
  }
});

// Sanitized error handler. In production, send structured details to server logs.
app.use((error: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  console.error('Request failed', error);
  res.status(500).json({ message: 'Internal server error' });
});

const port = Number(process.env.PORT ?? 4000);
app.listen(port, () => console.log(`API listening on ${port}`));

process.on('SIGTERM', async () => {
  await pool.end();
  process.exit(0);
});
```

**Sample limitations:** This demonstrates routes, validation, PostgreSQL pool access, parameterized queries, and basic error handling. It does not include production authentication, rate limiting, complete schema validation, CSRF/session setup, structured logging, graceful handling of every shutdown signal, migration tooling, or integration tests. Add those before exposing a real application to users.

### 38.6 Frontend setup

Create a React/Vite TypeScript frontend following the current Vite instructions, then add Tailwind if desired. Store the public API URL in frontend environment config, such as:

```dotenv
VITE_API_BASE_URL=http://localhost:4000
```

This URL is public and must not contain secrets.

### 38.7 Frontend API helper

`web/src/api/products.ts`:

```ts
export type Product = {
  id: number;
  name: string;
  priceCents: number;
  active: boolean;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:4000';

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.message ?? `Request failed: ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function listProducts(): Promise<Product[]> {
  return parseResponse<Product[]>(
    await fetch(`${API_BASE}/api/products`),
  );
}

export async function createProduct(input: {
  name: string;
  priceCents: number;
}): Promise<Product> {
  return parseResponse<Product>(
    await fetch(`${API_BASE}/api/products`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    }),
  );
}

export async function deleteProduct(id: number): Promise<void> {
  await parseResponse<void>(
    await fetch(`${API_BASE}/api/products/${id}`, { method: 'DELETE' }),
  );
}
```

A more advanced helper would add typed errors, abort handling, authentication/CSRF integration if used, request IDs and standardized error parsing.

### 38.8 React UI example

`web/src/App.tsx`:

```tsx
import { FormEvent, useEffect, useState } from 'react';
import {
  createProduct, deleteProduct, listProducts, Product,
} from './api/products';

export default function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [name, setName] = useState('');
  const [price, setPrice] = useState('4999');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    setLoading(true);
    setError(null);
    try {
      setProducts(await listProducts());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load products');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void reload();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    const priceCents = Number(price);

    if (!trimmed) {
      setError('Enter a product name.');
      return;
    }
    if (!Number.isInteger(priceCents) || priceCents < 0) {
      setError('Price must be a non-negative integer in cents.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const product = await createProduct({ name: trimmed, priceCents });
      setProducts(current => [product, ...current]);
      setName('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not save product');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    setError(null);
    try {
      await deleteProduct(id);
      setProducts(current => current.filter(product => product.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not delete product');
    }
  }

  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="text-3xl font-bold">Product inventory</h1>

      <form onSubmit={handleSubmit} className="my-6 flex flex-wrap gap-3">
        <label className="sr-only" htmlFor="product-name">Product name</label>
        <input
          id="product-name"
          value={name}
          onChange={event => setName(event.target.value)}
          maxLength={120}
          placeholder="Product name"
          className="min-w-0 flex-1 rounded border px-3 py-2"
        />

        <label className="sr-only" htmlFor="product-price">Price in cents</label>
        <input
          id="product-price"
          type="number"
          min="0"
          step="1"
          value={price}
          onChange={event => setPrice(event.target.value)}
          className="w-36 rounded border px-3 py-2"
        />

        <button
          type="submit"
          disabled={saving}
          className="rounded bg-indigo-600 px-4 py-2 font-semibold text-white disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Add product'}
        </button>
      </form>

      {error && <p role="alert" className="my-4 text-red-700">{error}</p>}
      {loading && <p>Loading products…</p>}
      {!loading && products.length === 0 && <p>No products yet.</p>}

      <ul className="divide-y">
        {products.map(product => (
          <li key={product.id} className="flex items-center justify-between gap-4 py-4">
            <div>
              <p className="font-semibold">{product.name}</p>
              <p className="text-sm text-slate-600">
                {(product.priceCents / 100).toFixed(2)}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void handleDelete(product.id)}
              className="rounded border px-3 py-2 hover:bg-slate-50"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </main>
  );
}
```

Depending on TypeScript/React settings, type imports may need `import type`. For a production app, separate loading/submit errors, add confirmation for destructive actions, add update/list pagination, handle races when reloading, use a schema validator, and test the components.

### 38.9 Run and verify

1. Start PostgreSQL and create the database/table.
2. Set `api/.env` with the local connection string.
3. Start the API using the scripts in the API `package.json`.
4. Check `GET http://localhost:4000/api/health`.
5. Check `GET http://localhost:4000/api/products`.
6. Start the frontend development server.
7. Create a product and verify a database row exists.
8. Refresh the page and confirm the row persists.
9. Try invalid values, a missing ID and a database outage.
10. Check browser Network tab for requests and responses.

The sample is a baseline for learning how layers connect, not a deploy-ready secure CRUD product.

---

## 39. Project Completion Checklist

### Planning
- [ ] Requirements and user roles are written down.
- [ ] Pages, entities and API contract are defined.
- [ ] Every button/form/filter has a real behavior or is clearly non-interactive.
- [ ] Data ownership/tenant rules are defined.

### Frontend
- [ ] Responsive on small, medium and large screens.
- [ ] Loading/empty/error/success states exist.
- [ ] Forms validate and show actionable errors.
- [ ] Keyboard navigation and visible focus work.
- [ ] API errors are not silently swallowed.
- [ ] No secrets appear in client bundle or browser storage without careful design.
- [ ] No broken links or fake buttons.

### Backend
- [ ] Every route validates input.
- [ ] Authentication is implemented where needed.
- [ ] Authorization and record ownership are checked server-side.
- [ ] API returns correct status codes and consistent error shapes.
- [ ] Requests, uploads and outbound calls have limits/timeouts.
- [ ] Secrets are outside source control.
- [ ] Errors are logged without leaking data.

### Database
- [ ] Constraints/indexes match business rules and queries.
- [ ] Migrations are tracked and repeatable.
- [ ] Queries are parameterized or safely built by an ORM.
- [ ] Pagination has limits.
- [ ] Transactions protect related updates.
- [ ] Backups exist and restore has been tested.

### Testing and delivery
- [ ] Unit, integration and E2E tests cover critical paths.
- [ ] Lint/type-check/build pass.
- [ ] Production configuration differs from development.
- [ ] Dependency audit and security checks run.
- [ ] Health/observability/rollback plan exists.
- [ ] Deployment is verified with smoke tests.

---

## 40. Learning Roadmap

### Phase 1 — Web fundamentals
1. HTML semantic structure and accessible forms.
2. CSS box model, flexbox, grid, responsive design and animation.
3. JavaScript values, functions, arrays, objects, modules, promises and `fetch`.
4. Browser DevTools, Network tab, console and errors.
5. Git basics and small commits.

### Phase 2 — Frontend application
1. TypeScript basics and strict typing.
2. React components, props, state, events and effects.
3. Routing and server-state/data-fetching strategy.
4. Tailwind CSS or organized component CSS.
5. Forms, loading/error/empty states and accessibility.
6. Build a responsive dashboard.

### Phase 3 — Backend and API
1. HTTP methods, status codes, JSON and REST.
2. Node.js plus Express or NestJS (choose one).
3. Request validation and exception handling.
4. Service/business logic separation.
5. API tests, logging and configuration.
6. Authentication/authorization concepts.

### Phase 4 — Database
1. Relational modelling, primary/foreign keys and constraints.
2. SQL `SELECT`, `INSERT`, `UPDATE`, `DELETE`, joins, indexes, transactions.
3. PostgreSQL or MySQL.
4. ORM, migrations and seed data.
5. Ownership rules, pagination and query optimization.

### Phase 5 — Production
1. Security checklist and dependency patching.
2. Unit/integration/E2E tests.
3. Docker/Compose for reproducible environments.
4. CI/CD, environment variables and secret storage.
5. Deployment, TLS, backups, logs, metrics and restore drills.
6. Performance profiling and resilience.

### Portfolio path
- Personal portfolio.
- CRUD task manager with authentication.
- Inventory or e-commerce backend.
- Dashboard with filters/pagination and roles.
- File upload or background notification system.
- Deploy a complete project and document setup, architecture, API, screenshots, tests and limitations.

---

## 41. Syntax and Tool Cheat Sheet

### Frontend
```html
<main><h1>Title</h1><button type="button">Action</button></main>
```

```css
.container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 1rem;
}
```

```ts
const response = await fetch('/api/products');
if (!response.ok) throw new Error('Request failed');
const data = await response.json();
```

### Backend API concepts
```text
GET    /api/items
POST   /api/items
GET    /api/items/:id
PATCH  /api/items/:id
DELETE /api/items/:id
```

### SQL
```sql
SELECT * FROM products WHERE active = TRUE ORDER BY id DESC LIMIT 20;
```

### Daily development commands
```bash
npm install
npm run dev
npm run build
npm test
git status
git diff
git add .
git commit -m "Describe the change"
git push
```

### Debug checklist
```text
Reproduce -> collect exact error -> locate layer -> inspect network/logs/query
-> make one fix -> add regression test -> run all checks -> verify again
```

### Remember
- Frontend validates for user experience; backend validates for security.
- Type annotations alone do not validate external data at runtime.
- SQL parameters protect values; never concatenate raw user input into SQL.
- Database migrations are part of application versioning.
- A successful compile does not prove the feature works.
- A beautiful UI does not prove the API/database is connected.
- Test denied access and invalid requests, not only happy paths.

---

## 42. Official Documentation

### Core web
- [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web)
- [HTML learning area](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content)
- [CSS styling and layout](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics)
- [JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)
- [Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)
- [HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview)

### TypeScript and frontend
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React docs](https://react.dev/learn)
- [Vite docs](https://vite.dev/guide/)
- [Tailwind CSS docs](https://tailwindcss.com/docs)
- [Angular docs](https://angular.dev/overview)
- [Vue docs](https://vuejs.org/guide/introduction.html)
- [Svelte docs](https://svelte.dev/docs)
- [Next.js docs](https://nextjs.org/docs)

### Backend
- [Node.js docs](https://nodejs.org/docs/latest/api/)
- [Express guide](https://expressjs.com/en/guide/routing.html)
- [NestJS docs](https://docs.nestjs.com/)
- [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Django docs](https://docs.djangoproject.com/)
- [Spring Boot reference](https://docs.spring.io/spring-boot/reference/)
- [Laravel docs](https://laravel.com/docs)
- [Axum docs](https://docs.rs/axum/latest/axum/)
- [Tokio docs](https://docs.rs/tokio/latest/tokio/)

### Database and data access
- [PostgreSQL documentation](https://www.postgresql.org/docs/current/)
- [MySQL documentation](https://dev.mysql.com/doc/)
- [SQLite documentation](https://www.sqlite.org/docs.html)
- [MongoDB manual](https://www.mongodb.com/docs/manual/)
- [Redis docs](https://redis.io/docs/latest/)
- [Prisma docs](https://www.prisma.io/docs)
- [TypeORM docs](https://typeorm.io/)
- [SQLAlchemy docs](https://docs.sqlalchemy.org/)
- [SQLx docs](https://docs.rs/sqlx/latest/sqlx/)

### Tooling and operations
- [Git documentation](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com/)
- [Docker docs](https://docs.docker.com/)
- [Docker Compose quickstart](https://docs.docker.com/compose/gettingstarted/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Web Content Accessibility Guidelines (WCAG)](https://www.w3.org/WAI/standards-guidelines/wcag/)
- [OpenAPI specification](https://spec.openapis.org/oas/latest.html)

---

## Final Notes

1. Learn one complete stack from UI to database before trying to master every language at once.
2. Separate the frontend, backend, and data layer; define the API contract between them.
3. Validate input at every trust boundary and enforce authorization in the backend.
4. Use parameterized SQL/safe ORM operations, migrations, tests and backups.
5. Build real loading/error/empty states and verify the whole user workflow.
6. Use official docs to confirm exact APIs, package versions and security guidance.
7. Treat example code as a learning scaffold; add project-specific auth, schema validation, tests, observability and deployment safeguards before production.
