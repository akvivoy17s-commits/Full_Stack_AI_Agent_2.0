# React + TypeScript Complete Guide for Full-Stack Web Development

**A practical reference to React, JSX, React Hooks, React DOM, TypeScript syntax, typed components, forms, API calls, testing, performance, and production patterns.**

> **Scope and version note (18 October 2026):** The official React reference currently documents React 19.3. This guide focuses on modern function components and current React APIs, with notes where an API depends on a framework or build tool. TypeScript is an evolving language. There is no official, finite list that can honestly be called “100% of React and TypeScript”: the language, browser platform, frameworks, and libraries keep growing. This guide is designed to be a broad, practical learning reference, not a copy of every specification page or every third-party API.

## How to use this guide

- Work through the chapters in order, and type the examples yourself.
- JavaScript examples use `.jsx`; TypeScript examples containing JSX use `.tsx`.
- React is a UI library. TypeScript adds compile-time type checking. Neither replaces HTML, CSS, HTTP knowledge, backend code, database design, accessibility, testing, or security.
- Items marked **ecosystem** (router, server framework, query library, test runner) are separate packages, not built-in React APIs.

## Table of contents

1. [React and TypeScript overview](#1-react-and-typescript-overview)
2. [Project setup](#2-project-setup)
3. [JSX and TSX syntax](#3-jsx-and-tsx-syntax)
4. [Components, props, children, and composition](#4-components-props-children-and-composition)
5. [Rendering conditions and lists](#5-rendering-conditions-and-lists)
6. [State and rendering](#6-state-and-rendering)
7. [Forms and events](#7-forms-and-events)
8. [React Hooks: full practical reference](#8-react-hooks-full-practical-reference)
9. [Effects, cleanup, and external systems](#9-effects-cleanup-and-external-systems)
10. [Context and shared state](#10-context-and-shared-state)
11. [Refs and DOM access](#11-refs-and-dom-access)
12. [Reducers and state machines](#12-reducers-and-state-machines)
13. [Async UI, Actions, transitions, and optimistic updates](#13-async-ui-actions-transitions-and-optimistic-updates)
14. [Suspense, lazy loading, error boundaries, and portals](#14-suspense-lazy-loading-error-boundaries-and-portals)
15. [React built-in components and APIs](#15-react-built-in-components-and-apis)
16. [Server rendering and Server Components](#16-server-rendering-and-server-components)
17. [TypeScript fundamentals](#17-typescript-fundamentals)
18. [TypeScript functions and advanced type syntax](#18-typescript-functions-and-advanced-type-syntax)
19. [TypeScript utility types and type manipulation](#19-typescript-utility-types-and-type-manipulation)
20. [Typing React components](#20-typing-react-components)
21. [Typing Hooks and React events](#21-typing-hooks-and-react-events)
22. [Typing forms, refs, context, and API data](#22-typing-forms-refs-context-and-api-data)
23. [Modules, project structure, and reusable code](#23-modules-project-structure-and-reusable-code)
24. [Routing and data fetching ecosystem](#24-routing-and-data-fetching-ecosystem)
25. [Styling approaches](#25-styling-approaches)
26. [Testing and debugging](#26-testing-and-debugging)
27. [Accessibility, security, and production quality](#27-accessibility-security-and-production-quality)
28. [Performance and React Compiler](#28-performance-and-react-compiler)
29. [Common errors and fixes](#29-common-errors-and-fixes)
30. [Full-stack integration patterns](#30-full-stack-integration-patterns)
31. [Project exercises](#31-project-exercises)
32. [Learning checklist](#32-learning-checklist)
33. [API and syntax index](#33-api-and-syntax-index)
34. [Official reference links](#34-official-reference-links)

---

# 1. React and TypeScript overview

## 1.1 What is React?

React is a JavaScript library for composing interfaces from reusable components. A component describes what the interface should look like for the current props and state. React decides when to render it and updates the DOM when needed.

## 1.2 What is JSX?

JSX is a syntax extension that lets you write markup-like expressions inside JavaScript or TypeScript. Tooling transforms JSX into JavaScript calls understood by React. Browsers do not execute raw JSX directly without a build step or a suitable tool.

## 1.3 What is TypeScript?

TypeScript is JavaScript with a static type system. Type checks happen during development/build; types are erased from the emitted JavaScript. Types do **not** validate untrusted API responses at runtime.

## 1.4 Typical stack

- **UI:** React + JSX/TSX.
- **Types:** TypeScript.
- **Build:** Vite, or a framework such as Next.js / Remix / another React framework.
- **Routing:** a router package or the framework's routing system.
- **Server:** Node.js with Express/Fastify/Nest, or another backend technology.
- **Database:** PostgreSQL, MySQL, SQLite, MongoDB, or a managed service.
- **Testing:** Vitest/Jest plus React Testing Library; browser end-to-end tests are commonly done with Playwright or Cypress.

These tools are not all part of React itself. Select versions compatible with your application and follow their official installation instructions.

---

# 2. Project setup

## 2.1 Create a JavaScript React project with Vite

```bash
npm create vite@latest my-react-app -- --template react
cd my-react-app
npm install
npm run dev
```

## 2.2 Create a TypeScript React project with Vite

```bash
npm create vite@latest my-react-ts-app -- --template react-ts
cd my-react-ts-app
npm install
npm run dev
```

Common scripts are `dev`, `build`, and `preview`; inspect the generated `package.json` to see the scripts for your template. For a production build:

```bash
npm run build
npm run preview
```

## 2.3 Typical project shape

```text
my-react-ts-app/
├── public/                 # Static files served as-is
├── src/
│   ├── assets/              # Imported images/fonts
│   ├── components/          # Reusable UI components
│   ├── features/            # Feature-oriented modules
│   ├── hooks/               # Custom Hooks
│   ├── lib/                 # API client and shared utilities
│   ├── types/               # Shared TypeScript types
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

A JavaScript template normally uses `.jsx` and `.js`; TypeScript JSX files use `.tsx`, and TypeScript files without JSX use `.ts`.

## 2.4 Minimal entry point

```tsx
// src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

const container = document.getElementById('root');
if (!container) throw new Error('Root element #root was not found');

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

`createRoot` is for client-rendered apps. For server-rendered HTML, use `hydrateRoot` rather than creating a second root over the server HTML.

---

# 3. JSX and TSX syntax

## 3.1 Return one root node

```jsx
function Welcome() {
  return (
    <main>
      <h1>Hello, React!</h1>
      <p>One component can contain many elements.</p>
    </main>
  );
}
```

Use a Fragment when you do not need an extra DOM element:

```jsx
function Welcome() {
  return (
    <>
      <h1>Hello</h1>
      <p>Welcome back.</p>
    </>
  );
}
```

A keyed Fragment can be written as `<Fragment key={item.id}>...</Fragment>` after importing `Fragment` from `react`; the shorthand `<>...</>` cannot take a key.

## 3.2 JavaScript expressions inside JSX

```jsx
const name = 'Asha';
const total = 3 * 7;

function Greeting() {
  return <p>Hello, {name}. Total: {total}.</p>;
}
```

Curly braces allow expressions, not statements such as a normal `if` block or `for` loop. Move complex logic into a variable or function before returning JSX.

## 3.3 JSX attributes differ slightly from HTML

```jsx
<label htmlFor="email">Email</label>
<input id="email" className="field" autoComplete="email" />
<button onClick={handleClick}>Save</button>
```

Common differences: `className` instead of `class`, `htmlFor` instead of `for`, camel-cased React event props such as `onClick`, and JavaScript values enclosed in braces.

## 3.4 Inline styles

```jsx
const panelStyle = {
  color: '#fff',
  backgroundColor: '#151515',
  padding: '1rem',
  borderRadius: 12,
};

function Panel() {
  return <section style={panelStyle}>Panel content</section>;
}
```

The style prop receives an object. CSS property names are camelCase; numeric values are generally interpreted as pixel values for CSS properties that accept lengths, while unitless properties remain unitless. Prefer CSS classes for larger stylesheets.

## 3.5 Attribute spreading

```jsx
function TextInput(props) {
  return <input {...props} />;
}

<TextInput id="search" placeholder="Search" aria-label="Search" />;
```

Use spread thoughtfully. Explicitly overwrite a prop after spreading if you need to enforce a value: `<input {...props} type="search" />`.

## 3.6 JSX comments

```jsx
function App() {
  return (
    <div>
      {/* This is a JSX comment. */}
      <p>Hello</p>
    </div>
  );
}
```

## 3.7 Rendering booleans and empty values

`false`, `true`, `null`, and `undefined` do not create visible text nodes. The number `0` **does** render, which can surprise developers using `items.length && ...`.

```jsx
{items.length > 0 && <ItemList items={items} />}
```

This is safer than `{items.length && <ItemList items={items} />}` when `items.length` might be zero.

---

# 4. Components, props, children, and composition

## 4.1 Function components

```jsx
function PageTitle() {
  return <h1>Dashboard</h1>;
}

export default function App() {
  return <PageTitle />;
}
```

Component names start with an uppercase letter. Render components with JSX, such as `<PageTitle />`; do not call a component like an ordinary function (`PageTitle()`), because React must control when and how components render.

## 4.2 Props

Props are read-only values supplied by a parent.

```jsx
function Greeting({ name, role }) {
  return <p>{name} — {role}</p>;
}

function App() {
  return <Greeting name="Asha" role="Developer" />;
}
```

Use default values in parameter destructuring:

```jsx
function Avatar({ name, size = 48 }) {
  return <img width={size} height={size} alt={`${name}'s avatar`} />;
}
```

Do not modify `props` or objects passed through them.

## 4.3 `children` and composition

```jsx
function Card({ title, children }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  );
}

<Card title="Profile">
  <p>Card body</p>
  <button>Open</button>
</Card>
```

Composition often works better than deeply nested configuration props. Components can accept React elements, functions, labels, or data, depending on the purpose.

## 4.4 Passing callbacks upward

```jsx
function SaveButton({ onSave }) {
  return <button onClick={onSave}>Save</button>;
}

function Editor() {
  function saveDocument() {
    console.log('Document saved');
  }
  return <SaveButton onSave={saveDocument} />;
}
```

Pass the function itself (`onClick={saveDocument}`), not its return value (`onClick={saveDocument()}`), unless you intentionally need to call it immediately.

## 4.5 Component identity and state reset

React associates state with a component's position and key in the render tree. A changed `key` can intentionally reset a component's state:

```jsx
<ProfileEditor key={selectedUserId} userId={selectedUserId} />
```

Do not define a component function inside another component when it should preserve a stable identity; define reusable components at module scope.

---

# 5. Rendering conditions and lists

## 5.1 Conditional rendering

```jsx
function Status({ isLoading, error, user }) {
  if (isLoading) return <p>Loading…</p>;
  if (error) return <p role="alert">Could not load data.</p>;
  if (!user) return <p>No user selected.</p>;
  return <h1>Welcome, {user.name}</h1>;
}
```

Alternative syntax:

```jsx
{isLoggedIn ? <Dashboard /> : <Login />}
{showHelp && <HelpPanel />}
```

## 5.2 Lists and keys

```jsx
function UserList({ users }) {
  return (
    <ul>
      {users.map((user) => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

Use stable, unique keys from data (`id`, UUID, database key). Avoid array indexes when items can be inserted, deleted, reordered, or filtered. Keys are for React's reconciliation; a `key` is not passed to the component as an ordinary prop.

## 5.3 Filter, sort, and derive lists without mutating state

```jsx
const visibleUsers = users
  .filter((user) => user.active)
  .toSorted((a, b) => a.name.localeCompare(b.name));
```

`toSorted` is a modern non-mutating array method. If your runtime does not support it, sort a copy: `[...users].sort(...)`. Do not call mutating `sort`, `reverse`, `splice`, or `push` directly on arrays held in React state.

---

# 6. State and rendering

## 6.1 `useState`

```jsx
import { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Add one</button>
    </div>
  );
}
```

- `count` is the current state snapshot for that render.
- `setCount` requests a future render; it does not change `count` inside the already running handler.
- Updates are batched where appropriate.
- State should be treated as immutable.

## 6.2 Functional state updates

When the next state depends on the previous state, use the updater form:

```jsx
setCount((current) => current + 1);
setCount((current) => current + 1);
```

These two updater calls correctly increase the count twice. `setCount(count + 1); setCount(count + 1);` usually adds only one because both expressions use the same render's snapshot.

## 6.3 Updating object state immutably

```jsx
const [user, setUser] = useState({ name: 'Asha', city: 'Chennai' });

function changeCity(city) {
  setUser((current) => ({ ...current, city }));
}
```

For a nested property, copy each level that changes:

```jsx
setUser((current) => ({
  ...current,
  address: {
    ...current.address,
    city: 'Chennai',
  },
}));
```

Consider a reducer or an immutable update helper when nested updates become complicated.

## 6.4 Updating arrays in state

```jsx
setTodos((current) => [...current, newTodo]);
setTodos((current) => current.filter((todo) => todo.id !== id));
setTodos((current) => current.map((todo) =>
  todo.id === id ? { ...todo, done: !todo.done } : todo
));
```

## 6.5 Derived state

Do not store a value in state if it can be calculated from other state/props and is inexpensive to calculate:

```jsx
const [items, setItems] = useState([]);
const [query, setQuery] = useState('');
const matchingItems = items.filter((item) =>
  item.name.toLowerCase().includes(query.toLowerCase())
);
```

Avoid adding a second state variable for `matchingItems` and synchronizing it in an effect unless you have a specific reason.

## 6.6 State structure principles

- Group values that always change together.
- Avoid contradictory state (for example, `isLoading`, `isSuccess`, and `isError` all true together).
- Avoid duplicate state that can drift out of sync.
- Keep state as close as practical to the components that use it.
- Lift state up when sibling components must share it.
- Use a reducer when updates have many related actions.
- Use context when data must be accessed by many distant descendants.

---

# 7. Forms and events

## 7.1 Event handlers

```jsx
function Actions() {
  function handleClick(event) {
    console.log('Clicked', event.currentTarget);
  }

  return <button onClick={handleClick}>Click me</button>;
}
```

React event props use camel case, for example `onClick`, `onChange`, `onSubmit`, `onKeyDown`, `onFocus`, and `onBlur`. Pass a function reference rather than calling it during render.

## 7.2 Controlled text input

```jsx
function SearchBox() {
  const [query, setQuery] = useState('');

  return (
    <label>
      Search
      <input value={query} onChange={(event) => setQuery(event.target.value)} />
    </label>
  );
}
```

If an input receives `value`, provide a change handler or make it intentionally read-only. A controlled text input should normally start with a string, not switch between `undefined` and a string.

## 7.3 Checkbox

```jsx
const [accepted, setAccepted] = useState(false);

<input
  type="checkbox"
  checked={accepted}
  onChange={(event) => setAccepted(event.target.checked)}
/>
```

Use `checked` for controlled checkboxes; use `value` for the associated form value.

## 7.4 Form submission

```jsx
function LoginForm() {
  const [email, setEmail] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    console.log('Submitting', email);
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="email">Email</label>
      <input
        id="email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        required
      />
      <button type="submit">Continue</button>
    </form>
  );
}
```

Client-side validation improves UX but does not replace server-side validation. Never trust browser input for authorization or sensitive decisions.

## 7.5 Controlled vs uncontrolled forms

- **Controlled:** React state stores the value (`value`/`checked` with handlers). Useful for live validation and reactive UI.
- **Uncontrolled:** the DOM holds the value; read it using `FormData`, a ref, or native form submission. Useful for simple forms and progressive enhancement.

```jsx
function SimpleForm() {
  function submit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    console.log(data.get('email'));
  }

  return (
    <form onSubmit={submit}>
      <input name="email" type="email" required />
      <button type="submit">Send</button>
    </form>
  );
}
```

---

# 8. React Hooks: full practical reference

Hooks are functions that let function components use React features. Call standard Hooks at the top level of a function component or custom Hook—not inside loops, conditions, nested callbacks, or event handlers. A notable special case is React's `use` API, which can read a Promise or Context and may be called conditionally or in loops; it still must be used within a component or Hook, and it has its own constraints.

## 8.1 State Hooks

### `useState(initialState)`

```jsx
const [value, setValue] = useState('');
const [count, setCount] = useState(() => expensiveInitialValue());
```

Use the lazy initializer form for an expensive initial calculation. Setter forms: `setValue(nextValue)` or `setValue(previous => nextValue)`.

### `useReducer(reducer, initialState)`

```jsx
function reducer(state, action) {
  switch (action.type) {
    case 'increment': return { count: state.count + 1 };
    case 'reset': return { count: 0 };
    default: throw new Error(`Unknown action: ${action.type}`);
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, { count: 0 });
  return (
    <>
      <p>{state.count}</p>
      <button onClick={() => dispatch({ type: 'increment' })}>Add</button>
      <button onClick={() => dispatch({ type: 'reset' })}>Reset</button>
    </>
  );
}
```

Use `useReducer` when transitions need to be explicit or the update logic is complex. Reducers should be pure; do not perform network requests inside reducers.

## 8.2 Context Hook

### `useContext(SomeContext)`

Reads the nearest matching provider's current value. See [Context and shared state](#10-context-and-shared-state). Context is not automatically a database or a replacement for all state management.

## 8.3 Ref Hooks

### `useRef(initialValue)`

```jsx
const inputRef = useRef(null);

function focusInput() {
  inputRef.current?.focus();
}

return <input ref={inputRef} />;
```

A ref object persists between renders. Changing `ref.current` does not trigger a render. Do not use refs for information that must appear in the UI; use state instead.

### `useImperativeHandle(ref, createHandle, dependencies)`

Lets a component expose a controlled imperative API through a ref. It is rarely necessary; prefer declarative props when possible. React 19 allows `ref` to be passed as a prop to function components, while `forwardRef` remains relevant for compatibility with older React versions and some library APIs.

## 8.4 Effect Hooks

### `useEffect(setup, dependencies?)`

Runs after React commits a render and is used to synchronize with an external system, such as a subscription, timer, browser API, or third-party widget. The setup function may return a cleanup function.

```jsx
useEffect(() => {
  const id = setInterval(() => setSeconds((s) => s + 1), 1000);
  return () => clearInterval(id);
}, []);
```

See [Effects, cleanup, and external systems](#9-effects-cleanup-and-external-systems).

### `useLayoutEffect(setup, dependencies?)`

Runs after DOM mutation but before the browser repaints. Use it for layout measurement that must happen before paint. It can block painting, so prefer `useEffect` when possible. Server rendering has no browser layout to measure.

### `useInsertionEffect(setup, dependencies?)`

Primarily intended for CSS-in-JS library authors to insert styles before layout Effects. Most application code should not use it.

### `useEffectEvent(callback)`

Creates an Effect Event for logic called from an Effect that needs access to the latest props/state without making those values trigger the Effect to re-synchronize. Use only according to the current React documentation; it is not a general replacement for event handlers or correct dependency management.

## 8.5 Performance Hooks

### `useMemo(calculateValue, dependencies)`

Caches a calculation result between renders when dependencies are unchanged.

```jsx
const sortedUsers = useMemo(
  () => [...users].sort((a, b) => a.name.localeCompare(b.name)),
  [users],
);
```

Do not use it to make incorrect code work. A cached value must be safe to recompute. React Compiler can automatically memoize many values in supported setups, reducing the need for manual memoization.

### `useCallback(fn, dependencies)`

Caches a function reference between renders. It is useful when reference stability matters to a memoized child or Hook dependency; do not wrap every function in it by default.

```jsx
const handleSelect = useCallback((id) => {
  setSelectedId(id);
}, []);
```

### `useTransition()`

```jsx
const [isPending, startTransition] = useTransition();

function chooseTab(nextTab) {
  startTransition(() => setTab(nextTab));
}
```

Marks non-urgent UI updates as Transitions. It does not automatically make arbitrary synchronous CPU work faster, and it does not replace request-level loading/error handling.

### `useDeferredValue(value)`

Returns a deferred version of a value so a non-urgent UI can lag behind an urgent input value. It is useful when expensive results can update after the input stays responsive. It is not a debounce timer and does not itself prevent network requests.

## 8.6 Other Hooks

### `useId()`

Creates stable IDs useful for associating form labels and accessible descriptions. Do not use it for list keys.

### `useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot?)`

Subscribes to an external data store in a way compatible with concurrent rendering. This is usually for library authors or integrating with an existing store; ordinary component state should usually use React state Hooks.

### `useDebugValue(value, format?)`

Adds a label for a custom Hook in React DevTools. Mainly useful when authoring reusable Hooks.

### `useActionState(action, initialState, permalink?)`

Manages the result/state of an Action, often for forms. It returns `[state, dispatchAction, isPending]`. The action receives the previous state and the action argument (commonly `FormData` for form actions).

```jsx
import { useActionState } from 'react';

async function saveName(previousState, formData) {
  const name = String(formData.get('name') ?? '').trim();
  if (!name) return { error: 'Name is required' };
  // In a real app, send this to the server and validate there too.
  return { error: null, name };
}

function NameForm() {
  const [state, formAction, isPending] = useActionState(saveName, {
    error: null,
    name: '',
  });

  return (
    <form action={formAction}>
      <input name="name" required />
      <button disabled={isPending}>{isPending ? 'Saving…' : 'Save'}</button>
      {state.error && <p role="alert">{state.error}</p>}
      {state.name && <p>Saved: {state.name}</p>}
    </form>
  );
}
```

### `useOptimistic(state, updateFn)`

Produces an optimistic state for an Action while a mutation is pending. The UI can show the expected result before the server confirms it; application logic must still handle failure and reconcile with the real result.

### `use(resource)`

React's `use` API can read a Promise or Context during rendering. A pending Promise can suspend rendering; a rejected Promise can be handled by an Error Boundary. Promise identity and caching matter: do not create a new uncached Promise on every render without an appropriate framework/cache strategy. `use` is distinct from most Hooks because it can be used conditionally and in loops, but only inside a component or Hook.

### Custom Hooks

A custom Hook is a JavaScript/TypeScript function whose name begins with `use` and that composes other Hooks.

```jsx
function useOnlineStatus() {
  const [online, setOnline] = useState(navigator.onLine);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  }, []);

  return online;
}
```

Custom Hooks share **logic**, not one shared state instance. Each component calling the Hook normally has its own Hook state unless the Hook connects to a shared store/context.

---

# 9. Effects, cleanup, and external systems

## 9.1 Effects are for synchronization

A good use of an Effect is keeping an external system in sync with React state/props: subscriptions, timers, sockets, browser APIs, maps, media players, and similar integrations.

```jsx
useEffect(() => {
  const connection = createConnection(roomId);
  connection.connect();
  return () => connection.disconnect();
}, [roomId]);
```

## 9.2 Dependency arrays

- No second argument: Effect can run after every committed render.
- `[]`: setup on mount, cleanup on unmount (and in development Strict Mode, an extra setup/cleanup cycle can expose bugs).
- `[a, b]`: re-synchronize when a dependency changes by `Object.is` comparison.

The dependency list must describe the reactive values used by the Effect. Do not silence exhaustive-deps warnings just to force a desired timing; restructure the code instead.

## 9.3 Fetching data with an Effect

```jsx
function UserProfile({ userId }) {
  const [state, setState] = useState({ status: 'loading', user: null, error: null });

  useEffect(() => {
    const controller = new AbortController();

    async function loadUser() {
      setState({ status: 'loading', user: null, error: null });
      try {
        const response = await fetch(`/api/users/${userId}`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const user = await response.json();
        setState({ status: 'success', user, error: null });
      } catch (error) {
        if (error?.name !== 'AbortError') {
          setState({ status: 'error', user: null, error });
        }
      }
    }

    loadUser();
    return () => controller.abort();
  }, [userId]);

  if (state.status === 'loading') return <p>Loading…</p>;
  if (state.status === 'error') return <p role="alert">Unable to load user.</p>;
  return <h1>{state.user?.name}</h1>;
}
```

This is an illustrative pattern. Production applications often use a router loader, framework data API, or query/cache library for deduplication, retries, caching, and race-condition handling. Parse and validate external data before trusting it.

## 9.4 Avoid unnecessary Effects

Usually do **not** use Effects to:

- Compute values from props/state that can be calculated during render.
- Respond to a user click that should be handled directly in the click handler.
- Reset all state when a changed key or component identity would express the reset more simply.
- Copy props into state without a deliberate synchronization requirement.

## 9.5 Strict Mode

`<StrictMode>` enables development-only checks. React may render components or repeat Effect setup/cleanup in development to find impure rendering and missing cleanup. This does not mean production intentionally runs every Effect twice. Fix the underlying impurity/cleanup issue rather than removing Strict Mode as the first solution.

---

# 10. Context and shared state

## 10.1 Create a context

```tsx
import { createContext, useContext, useState, type ReactNode } from 'react';

type Theme = 'light' | 'dark';
type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('dark');
  const value = {
    theme,
    toggleTheme: () => setTheme((current) => current === 'dark' ? 'light' : 'dark'),
  };

  return <ThemeContext value={value}>{children}</ThemeContext>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === null) throw new Error('useTheme must be used inside ThemeProvider');
  return context;
}
```

In current React, the context object can be used as the provider (`<ThemeContext value={value}>`). `<ThemeContext.Provider value={value}>` remains familiar in older code and is appropriate when supporting older React versions. Context values should be kept stable where necessary; a new object value can re-render consumers.

## 10.2 When to use context

Suitable examples include theme, current authenticated-user display state, locale, or configuration. For high-frequency large state, think about context splitting, colocating state, selectors, or an external state library.

## 10.3 State libraries

External libraries such as Redux Toolkit, Zustand, Jotai, and others may help with complex shared state. They are not React built-ins. Choose one only when the application's requirements justify it.

---

# 11. Refs and DOM access

## 11.1 Focus or measure a DOM node

```tsx
import { useRef } from 'react';

function SearchInput() {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div>
      <input ref={inputRef} aria-label="Search" />
      <button onClick={() => inputRef.current?.focus()}>Focus</button>
    </div>
  );
}
```

## 11.2 Store a timer ID or mutable non-UI value

```jsx
const timeoutRef = useRef(null);

function startDelay() {
  clearTimeout(timeoutRef.current);
  timeoutRef.current = setTimeout(() => console.log('Done'), 500);
}

useEffect(() => () => clearTimeout(timeoutRef.current), []);
```

When using TypeScript in a browser project, timer typings depend on the installed `lib` and Node type definitions. Prefer letting TypeScript infer the timer type or use `ReturnType<typeof setTimeout>` if you need to name it.

## 11.3 Refs in React 19

React 19 supports passing `ref` as a prop to function components. Libraries supporting earlier React versions may still use `forwardRef`. Do not expose a large imperative surface unless it solves a real integration need.

---

# 12. Reducers and state machines

## 12.1 Discriminated state model

```tsx
type LoadState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; message: string };
```

This type prevents impossible combinations such as `status: 'success'` with no data, provided the code respects the type. It is often safer than multiple independent booleans.

## 12.2 Typed reducer

```tsx
type Todo = { id: string; title: string; done: boolean };
type TodoAction =
  | { type: 'add'; todo: Todo }
  | { type: 'toggle'; id: string }
  | { type: 'remove'; id: string };

function todoReducer(state: Todo[], action: TodoAction): Todo[] {
  switch (action.type) {
    case 'add':
      return [...state, action.todo];
    case 'toggle':
      return state.map((todo) => todo.id === action.id
        ? { ...todo, done: !todo.done }
        : todo);
    case 'remove':
      return state.filter((todo) => todo.id !== action.id);
    default: {
      const exhaustive: never = action;
      return exhaustive;
    }
  }
}
```

The `never` assignment helps TypeScript flag a newly added action that was not handled by the reducer.

---

# 13. Async UI, Actions, transitions, and optimistic updates

## 13.1 Pending UI with a form Action

React 19 supports passing a function to the form `action` prop. The function can receive `FormData`; a Server Function setup depends on the framework/build environment and must be configured correctly.

```jsx
async function submitMessage(formData) {
  const message = String(formData.get('message') ?? '').trim();
  if (!message) return;
  // Send to a trusted server endpoint in a real application.
}

function MessageForm() {
  return (
    <form action={submitMessage}>
      <input name="message" required />
      <button type="submit">Send</button>
    </form>
  );
}
```

Do not confuse an ordinary client Action with a server-side function. Server Actions/Server Functions require framework or bundler support and appropriate authorization, input validation, and CSRF/security controls.

## 13.2 `useFormStatus` from `react-dom`

Use it in a descendant of the form it observes:

```jsx
import { useFormStatus } from 'react-dom';

function SubmitButton() {
  const { pending, data, method, action } = useFormStatus();
  return <button disabled={pending}>{pending ? 'Sending…' : 'Submit'}</button>;
}

function ContactForm() {
  return <form action={submitMessage}><input name="message" /><SubmitButton /></form>;
}
```

The Hook does not read the status of a form rendered by the same component that calls it; use it in a nested component inside that form.

## 13.3 Optimistic UI

```jsx
import { useOptimistic, useState, useTransition } from 'react';

function LikeButton({ initialLiked, saveLike }) {
  const [liked, setLiked] = useState(initialLiked);
  const [optimisticLiked, setOptimisticLiked] = useOptimistic(liked);
  const [isPending, startTransition] = useTransition();

  function toggleLike() {
    startTransition(async () => {
      setOptimisticLiked(!liked);
      try {
        await saveLike(!liked);
        setLiked(!liked);
      } catch {
        // The optimistic UI falls back to the actual `liked` state.
      }
    });
  }

  return <button disabled={isPending} onClick={toggleLike}>{optimisticLiked ? 'Liked' : 'Like'}</button>;
}
```

Optimistic state is a UI technique, not proof that the server saved a change. Handle network errors and reconcile confirmed state.

---

# 14. Suspense, lazy loading, error boundaries, and portals

## 14.1 `lazy` and `Suspense`

```jsx
import { lazy, Suspense } from 'react';

const SettingsPage = lazy(() => import('./SettingsPage'));

function App() {
  return (
    <Suspense fallback={<p>Loading settings…</p>}>
      <SettingsPage />
    </Suspense>
  );
}
```

`lazy` defers loading a component's module until it is rendered. Suspense can show a fallback while a supported child suspends. For ordinary requests made inside a hand-written Effect, Suspense does not automatically catch the request unless the data integration is built to suspend.

## 14.2 Error boundaries

Error boundaries catch many rendering errors in descendant components and can display fallback UI. They do not replace `try/catch` for ordinary event-handler code or asynchronous callbacks. A basic error boundary is traditionally a class component:

```jsx
import { Component } from 'react';

class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('UI error', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) return <p role="alert">Something went wrong.</p>;
    return this.props.children;
  }
}
```

For a TypeScript application, add a type for props and state as shown later in the TypeScript examples. Frameworks may provide an error-boundary mechanism or route-level error UI.

## 14.3 Portals

```jsx
import { createPortal } from 'react-dom';

function Modal({ children }) {
  const root = document.getElementById('modal-root');
  if (!root) return null;
  return createPortal(<div className="modal-backdrop">{children}</div>, root);
}
```

Portals are useful for dialogs, overlays, and tooltips. A real modal also needs focus management, focus restoration, keyboard handling (including Escape when appropriate), accessible labeling, and correct background interaction behavior.

## 14.4 Built-in components

- `<Fragment>` / `<>...</>`: group children without an extra DOM node.
- `<StrictMode>`: development checks.
- `<Suspense fallback={...}>`: fallback while supported children suspend.
- `<Profiler>`: programmatic render profiling.
- `<Activity>`: allows hiding/restoring a subtree while preserving its internal state in supported React versions.
- `<ViewTransition>`: coordinates supported view-transition animations with React transitions/Suspense; use only after checking current browser and React support.

The final two are newer APIs. Consult current React documentation and test compatibility before depending on them for essential behavior.

---

# 15. React built-in components and APIs

This section is an index, not a replacement for the official API reference.

## 15.1 Core React package

- `Children`: legacy utility for manipulating `children`; composition is generally preferred.
- `Component`, `PureComponent`: class-component base APIs; function components and Hooks are the usual default for new code.
- `createContext`: creates a Context object.
- `createElement`: creates an element programmatically; JSX is the normal syntax.
- `Fragment`: groups elements.
- `isValidElement`: checks whether a value is a React element.
- `lazy`: code-splits a component using dynamic import.
- `memo`: can skip rendering when props are unchanged; use when profiling/architecture warrants it.
- `Profiler`: measures rendering performance.
- `startTransition`: marks state updates as non-urgent.
- `use`: reads a supported resource, such as a Promise or Context.
- Hooks listed in [chapter 8](#8-react-hooks-full-practical-reference).

Advanced APIs documented for supported React runtimes/build systems include `cache`, `cacheSignal`, `captureOwnerStack`, and `addTransitionType`. These are not universal replacements for application-level caching, logging, or state management; check the current official reference for environment constraints.

## 15.2 React DOM package

Common web-specific APIs:

- `createRoot` from `react-dom/client`: initialize a client-rendered root.
- `hydrateRoot` from `react-dom/client`: hydrate pre-rendered HTML.
- `createPortal` from `react-dom`: render children into another DOM node.
- `flushSync` from `react-dom`: force an update to flush synchronously; use rarely.
- `useFormStatus` from `react-dom`: read form submission status from a descendant.
- Resource hints such as `preconnect`, `prefetchDNS`, `preload`, `preloadModule`, `preinit`, and `preinitModule` are advanced performance APIs. Frameworks often manage these for you.
- Server rendering functions are listed in [chapter 16](#16-server-rendering-and-server-components).

Do not use removed APIs such as `ReactDOM.render`, `ReactDOM.hydrate`, `findDOMNode`, or `unmountComponentAtNode` in modern React code. Use `createRoot`, `hydrateRoot`, refs, and `root.unmount()` as appropriate.

---

# 16. Server rendering and Server Components

## 16.1 Client rendering, SSR, and hydration

- **Client-side rendering (CSR):** browser JavaScript renders the UI.
- **Server-side rendering (SSR):** a server produces the initial HTML; React hydrates it to attach client interactivity.
- **Static generation/prerendering:** HTML is generated ahead of a request/build or in a supported prerender stage.
- **Streaming:** HTML can be sent in chunks using supported server APIs.

You do not need to call low-level server rendering APIs directly in most framework applications.

## 16.2 Server rendering APIs

From `react-dom/server`, common APIs include:

- `renderToString`: renders a React tree to a string, with limits compared with streaming approaches.
- `renderToStaticMarkup`: renders non-interactive static HTML.
- `renderToPipeableStream`: streaming API for Node.js streams.
- `renderToReadableStream`: streaming API for Web Streams runtimes.
- `prerender`, `prerenderToNodeStream`, and resume-related APIs are available in supported current environments. Use the current reference to select the appropriate API for your runtime.

## 16.3 Server Components and directives

React Server Components require framework/bundler support; they are not enabled by putting arbitrary files on a basic static web server.

- `'use client'` marks a module/client boundary in compatible React Server Components setups.
- `'use server'` marks Server Functions in compatible setups.
- Props crossing server/client boundaries must be serializable according to the environment's rules.
- A Server Function must authenticate/authorize every sensitive operation and validate arguments. A hidden button or client-side role check is not security.
- Keep database credentials and private API keys on the server. Never bundle secrets into client-side environment variables.

For a first React SPA, learn components, state, forms, effects, routing, APIs, and TypeScript before diving into Server Components internals.

---

# 17. TypeScript fundamentals

TypeScript checks relationships between values. It does not change JavaScript runtime behavior and most type annotations are removed during compilation.

## 17.1 Basic types and inference

```ts
let userName: string = 'Asha';
let age: number = 22;
let isAdmin: boolean = false;
let ids: number[] = [1, 2, 3];
let tags: Array<string> = ['react', 'typescript'];
let maybeName: string | undefined;
let unknownValue: unknown = 'data';
```

TypeScript often infers obvious types, so avoid adding redundant annotations everywhere:

```ts
const pageSize = 20; // inferred as number literal/number depending on context
const greeting = 'Hello';
```

## 17.2 `any`, `unknown`, `never`, and `void`

- `any`: disables many checks; avoid unless migrating or bridging a genuinely untyped area.
- `unknown`: can hold any value but requires narrowing before use; preferred for uncertain data.
- `never`: represents values that cannot occur, such as a function that always throws or an exhaustive impossible case.
- `void`: commonly describes a function whose return value is not used.

```ts
function logMessage(message: string): void {
  console.log(message);
}

function fail(message: string): never {
  throw new Error(message);
}

function printUnknown(value: unknown) {
  if (typeof value === 'string') console.log(value.toUpperCase());
}
```

## 17.3 Arrays, tuples, and readonly

```ts
const names: string[] = ['Asha', 'Ravi'];
const point: [x: number, y: number] = [10, 20];
const coordinate: readonly [number, number] = [10, 20];
const readonlyNames: ReadonlyArray<string> = ['Asha'];
```

## 17.4 Object types

```ts
type User = {
  id: string;
  name: string;
  email?: string;          // optional
  readonly createdAt: Date;
};

const user: User = { id: 'u1', name: 'Asha', createdAt: new Date() };
```

`readonly` is a compile-time restriction. It does not deep-freeze an object at runtime.

## 17.5 `type` aliases and `interface`

```ts
type Id = string | number;
type Point = { x: number; y: number };

interface Named {
  name: string;
}
interface Admin extends Named {
  permissions: string[];
}
```

Both can describe object shapes. Interfaces can be declaration-merged and extended. Type aliases can represent unions, intersections, primitives, tuples, conditional types, and other type expressions. Use a consistent style for your team.

## 17.6 Union and intersection types

```ts
type Status = 'idle' | 'loading' | 'success' | 'error';
type HasId = { id: string };
type HasTimestamp = { updatedAt: Date };
type RecordMeta = HasId & HasTimestamp;
```

A union means “one of these alternatives”; an intersection means a value must satisfy all combined types.

## 17.7 Literal types and `as const`

```ts
const directions = ['up', 'down', 'left', 'right'] as const;
type Direction = typeof directions[number];

const config = {
  mode: 'dark',
  retries: 3,
} as const;
```

`as const` preserves literal types and makes the object's properties/array tuple readonly at the type level.

## 17.8 Type narrowing

```ts
function formatId(id: string | number): string {
  if (typeof id === 'number') return id.toFixed(0);
  return id.toUpperCase();
}
```

Narrowing tools include `typeof`, `instanceof`, equality checks, `in`, truthiness checks, discriminated unions, user-defined type predicates, and control-flow analysis.

## 17.9 Type guards and predicates

```ts
function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isUser(value: unknown): value is User {
  if (typeof value !== 'object' || value === null) return false;
  const record = value as Record<string, unknown>;
  return typeof record.id === 'string' && typeof record.name === 'string';
}
```

Type guards help TypeScript reason about a value. Runtime validation is still needed for untrusted input. For complex data, a schema-validation library can be useful.

## 17.10 Enums and alternatives

```ts
enum DirectionEnum {
  Up = 'UP',
  Down = 'DOWN',
}
```

Enums are part of TypeScript. In many UI applications, string-literal unions are simpler and avoid emitted enum code:

```ts
type Direction = 'UP' | 'DOWN';
```

---

# 18. TypeScript functions and advanced type syntax

## 18.1 Function parameter and return types

```ts
function add(a: number, b: number): number {
  return a + b;
}

const multiply = (a: number, b: number): number => a * b;
```

## 18.2 Optional and default parameters

```ts
function greet(name: string, punctuation = '!'): string {
  return `Hello ${name}${punctuation}`;
}

function findUser(id: string, includeArchived?: boolean) {
  // includeArchived may be undefined
}
```

## 18.3 Function types

```ts
type Formatter = (value: number) => string;
const formatCurrency: Formatter = (value) => `$${value.toFixed(2)}`;

type ClickHandler = (event: MouseEvent) => void;
```

## 18.4 Rest parameters

```ts
function sum(...values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}
```

## 18.5 Function overloads

```ts
function parse(value: string): string[];
function parse(value: number): number[];
function parse(value: string | number): string[] | number[] {
  if (typeof value === 'string') return value.split(',');
  return [value];
}
```

Overloads express related call signatures. Keep the implementation signature compatible with the overload declarations.

## 18.6 Generics

```ts
function identity<T>(value: T): T {
  return value;
}

const a = identity<string>('hello');
const b = identity(123); // inferred as number
```

Constrain a generic when it requires specific properties:

```ts
function getLength<T extends { length: number }>(value: T): number {
  return value.length;
}
```

## 18.7 Generic interfaces and API results

```ts
interface ApiResult<T> {
  data: T;
  requestId: string;
}

const result: ApiResult<User> = {
  data: { id: 'u1', name: 'Asha', createdAt: new Date() },
  requestId: 'req-1',
};
```

## 18.8 `keyof`, `typeof`, and indexed access types

```ts
type Person = { id: string; age: number; active: boolean };
type PersonKey = keyof Person; // 'id' | 'age' | 'active'
type Age = Person['age'];     // number

const defaults = { pageSize: 20, theme: 'dark' } as const;
type Defaults = typeof defaults;
```

## 18.9 Mapped types

```ts
type Optional<T> = { [K in keyof T]?: T[K] };
type ReadonlyShape<T> = { readonly [K in keyof T]: T[K] };
```

## 18.10 Conditional types and `infer`

```ts
type IsString<T> = T extends string ? true : false;
type UnwrapPromise<T> = T extends Promise<infer Value> ? Value : T;

type A = UnwrapPromise<Promise<User>>; // User
```

Conditional types distribute over union types when the checked type is a naked type parameter; sometimes wrapping both sides in square brackets prevents distribution: `[T] extends [U] ? X : Y`.

## 18.11 Template literal types

```ts
type EventName = 'click' | 'change';
type HandlerName = `on${Capitalize<EventName>}`; // 'onClick' | 'onChange'
```

## 18.12 `satisfies`, assertions, and non-null assertion

```ts
const routes = {
  home: '/',
  settings: '/settings',
} satisfies Record<string, `/${string}`>;

const input = document.querySelector('#email') as HTMLInputElement | null;
const fixed = input!.value; // `!` asserts non-null; unsafe if the element is missing
```

`satisfies` checks compatibility without replacing the expression's inferred type. A type assertion (`as SomeType`) does not perform runtime checking; do not use it to pretend unvalidated server data is safe. Avoid non-null assertions when a real null check is practical.

## 18.13 `unknown` catch values

With strict settings, treat caught errors carefully:

```ts
try {
  // operation
} catch (error: unknown) {
  const message = error instanceof Error ? error.message : 'Unknown error';
  console.error(message);
}
```

## 18.14 Namespaces, declaration merging, and decorators

TypeScript supports namespaces, declaration merging, and decorators in defined configurations. Modern module-based applications generally prefer ES modules over namespaces. Decorator syntax/semantics depend on the supported TypeScript version and configuration; learn it when the framework/library you use requires it rather than adding decorators everywhere.

---

# 19. TypeScript utility types and type manipulation

Built-in utility types transform existing types. Common examples:

```ts
type User = {
  id: string;
  name: string;
  email: string;
  active: boolean;
};

type PartialUser = Partial<User>;                 // every property optional
type RequiredUser = Required<PartialUser>;        // every property required
type ReadonlyUser = Readonly<User>;               // properties readonly
type UserName = Pick<User, 'id' | 'name'>;        // selected properties
type UserWithoutEmail = Omit<User, 'email'>;       // all except email
type UserDictionary = Record<string, User>;       // keys to values
type ActiveFlag = Extract<'active' | 'disabled', 'active'>;
type NonActiveFlag = Exclude<'active' | 'disabled', 'active'>;
type NonNullableValue = NonNullable<string | null | undefined>;
type Result = ReturnType<typeof getUser>;
type Args = Parameters<typeof getUser>;
type FirstArg = ConstructorParameters<typeof SomeClass>[0];
type AwaitedData = Awaited<Promise<Promise<User>>>; // User
```

Additional built-in utility types include `ThisParameterType`, `OmitThisParameter`, `ThisType`, and others depending on the TypeScript version and library definitions. Use the current TypeScript Handbook's Utility Types reference for the exact set available in your installed version.

---

# 20. Typing React components

## 20.1 Define props with a `type` or `interface`

```tsx
type ButtonProps = {
  label: string;
  disabled?: boolean;
  onClick?: () => void;
};

export function Button({ label, disabled = false, onClick }: ButtonProps) {
  return <button type="button" disabled={disabled} onClick={onClick}>{label}</button>;
}
```

TypeScript infers many types from context, so you do not need to annotate every local variable. Explicit prop types are helpful at reusable component boundaries.

## 20.2 Children

```tsx
import type { ReactNode } from 'react';

type CardProps = {
  title: string;
  children: ReactNode;
};

function Card({ title, children }: CardProps) {
  return <section className="card"><h2>{title}</h2>{children}</section>;
}
```

`ReactNode` is a broad type for renderable React content. `ReactElement` is narrower and represents a React element object. Avoid assuming children are always one element or always a string.

## 20.3 Extending native element props

```tsx
import type { ComponentProps } from 'react';

type IconButtonProps = ComponentProps<'button'> & {
  icon: ReactNode;
  label: string;
};

function IconButton({ icon, label, ...buttonProps }: IconButtonProps) {
  return (
    <button aria-label={label} {...buttonProps}>
      {icon}
    </button>
  );
}
```

Related types include `ComponentPropsWithRef`, `ComponentPropsWithoutRef`, `ElementRef` in applicable type versions, and component types such as `ComponentType<P>`. Prefer the least complicated type that correctly describes your API.

## 20.4 Union props for mutually exclusive options

```tsx
type LinkOrButtonProps =
  | { kind: 'link'; href: string; onClick?: never; children: ReactNode }
  | { kind: 'button'; href?: never; onClick: () => void; children: ReactNode };

function LinkOrButton(props: LinkOrButtonProps) {
  if (props.kind === 'link') return <a href={props.href}>{props.children}</a>;
  return <button onClick={props.onClick}>{props.children}</button>;
}
```

A discriminant such as `kind` allows safe narrowing and makes invalid combinations harder to express.

## 20.5 Typed component with generic data

```tsx
type ListProps<T> = {
  items: T[];
  getKey: (item: T) => string;
  renderItem: (item: T) => ReactNode;
};

function List<T>({ items, getKey, renderItem }: ListProps<T>) {
  return <ul>{items.map((item) => <li key={getKey(item)}>{renderItem(item)}</li>)}</ul>;
}
```

Use generics for reusable components that truly work with different item types.

## 20.6 Avoid overusing `React.FC`

Modern React + TypeScript does not require `React.FC` for function components. A plain function with explicitly typed props is straightforward. Use `React.FC` only when it offers a concrete benefit for your project's conventions.

## 20.7 Typing class components

Function components are usually the default, but legacy code and Error Boundaries may use classes:

```tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';

type BoundaryProps = { children: ReactNode };
type BoundaryState = { failed: boolean };

class Boundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { failed: false };

  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(error, info.componentStack);
  }

  render() {
    return this.state.failed ? <p role="alert">Unable to display this section.</p> : this.props.children;
  }
}
```

---

# 21. Typing Hooks and React events

## 21.1 `useState<T>`

```tsx
const [count, setCount] = useState<number>(0);
const [user, setUser] = useState<User | null>(null);
type RequestStatus = 'idle' | 'loading' | 'success' | 'error';
const [status, setStatus] = useState<RequestStatus>('idle');
const [items, setItems] = useState<Todo[]>([]);
```

Type inference works for straightforward initial values. Add a generic when the initial value cannot express the full future type, such as `null` before loading a `User`.

## 21.2 `useReducer`

Type the state, action union, reducer parameters, and initial state. TypeScript usually infers `dispatch` from the reducer:

```tsx
const initialState: { count: number } = { count: 0 };
const [state, dispatch] = useReducer(reducer, initialState);
```

## 21.3 Event-handler types

Inline handlers are usually inferred:

```tsx
<input onChange={(event) => console.log(event.currentTarget.value)} />
```

For extracted handlers, annotate event types:

```tsx
function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
  setValue(event.currentTarget.value);
}

function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
  event.preventDefault();
}

function handleButtonClick(event: React.MouseEvent<HTMLButtonElement>) {
  console.log(event.currentTarget.disabled);
}
```

Useful React event types include `ChangeEvent`, `FormEvent`, `MouseEvent`, `KeyboardEvent`, `FocusEvent`, `PointerEvent`, `DragEvent`, `ClipboardEvent`, `WheelEvent`, `TouchEvent`, and corresponding handler types such as `ChangeEventHandler<HTMLInputElement>`.

## 21.4 Typed callback functions

```tsx
type SaveHandler = (value: string) => Promise<void>;

function Editor({ onSave }: { onSave: SaveHandler }) {
  const [value, setValue] = useState('');
  return (
    <form onSubmit={async (event) => {
      event.preventDefault();
      await onSave(value);
    }}>
      <input value={value} onChange={(event) => setValue(event.currentTarget.value)} />
      <button>Save</button>
    </form>
  );
}
```

## 21.5 Typed custom Hook

```tsx
function useLocalStorageState<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = window.localStorage.getItem(key);
      return raw === null ? initialValue : (JSON.parse(raw) as T);
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    window.localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue] as const;
}
```

**Important:** `JSON.parse(raw) as T` is a compile-time assertion, not validation. For untrusted or changing stored data, validate the parsed value before using it. In an SSR app, guard access to `window` because it does not exist on the server.

---

# 22. Typing forms, refs, context, and API data

## 22.1 Refs

```tsx
const inputRef = useRef<HTMLInputElement>(null);
const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
```

The DOM ref starts as `null` because the element does not exist before mounting. Check `inputRef.current` before use.

## 22.2 Context with a safe custom Hook

```tsx
type AuthUser = { id: string; displayName: string };
type AuthContextValue = {
  user: AuthUser | null;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
```

This avoids pretending a meaningful default auth value exists. A context provider and a runtime guard enforce the intended usage better than an unsafe non-null assertion.

## 22.3 Type API response data

```tsx
type Product = {
  id: string;
  name: string;
  price: number;
};

async function getProducts(signal?: AbortSignal): Promise<Product[]> {
  const response = await fetch('/api/products', { signal });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  const data: unknown = await response.json();
  if (!Array.isArray(data)) throw new Error('Invalid product response');
  // For production, validate each item and each property, or use a schema validator.
  return data as Product[];
}
```

Do not use `as Product[]` as a substitute for real runtime validation. API contracts can be wrong, stale, or malicious. A schema validator such as Zod or Valibot is an external option; use a compatible, maintained package when appropriate.

## 22.4 Data fetch Hook with discriminated result

```tsx
type AsyncState<T> =
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error };

function useProducts() {
  const [state, setState] = useState<AsyncState<Product[]>>({ status: 'loading' });

  useEffect(() => {
    const controller = new AbortController();
    getProducts(controller.signal)
      .then((data) => setState({ status: 'success', data }))
      .catch((cause: unknown) => {
        if (cause instanceof Error && cause.name === 'AbortError') return;
        const error = cause instanceof Error ? cause : new Error('Unknown error');
        setState({ status: 'error', error });
      });
    return () => controller.abort();
  }, []);

  return state;
}
```

A framework loader/query library may be a better fit when the app needs caching, retries, invalidation, pagination, deduplication, or sophisticated race handling.

---

# 23. Modules, project structure, and reusable code

## 23.1 Named and default exports

```ts
// math.ts
export function add(a: number, b: number): number {
  return a + b;
}
export const TAX_RATE = 0.18;
export type Point = { x: number; y: number };

// app.ts
import { add, TAX_RATE, type Point } from './math';
```

Default export syntax:

```tsx
export default function App() {
  return <main>Hello</main>;
}

import App from './App';
```

Use type-only import/export when appropriate, such as `import type { User } from './types'`.

## 23.2 Keep modules cohesive

Separate UI components, data access, shared types, custom Hooks, formatting functions, and routing by responsibility. Avoid a single giant `App.tsx` file. Organize by feature as a project grows.

## 23.3 Example API client

```ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<T>;
}
```

This generic helper gives compile-time convenience only. It cannot prove that JSON is actually `T`. Validate important data at the boundary. In Vite, client-exposed environment variables typically use the `VITE_` prefix and are public once bundled—never put secrets in them.

---

# 24. Routing and data fetching ecosystem

React core does not provide a full route system or general-purpose server data cache. Choose framework features or maintained libraries for those jobs.

## 24.1 Routing concepts

Learn:

- Route definitions and nested layouts.
- Path params (for example `/products/:productId`).
- Query parameters and URL state.
- Navigation links and programmatic navigation.
- Not-found routes and error routes.
- Protected UI routes paired with **server-side authorization**.
- Loaders/actions if supported by the router/framework.
- Lazy route modules and code splitting.

A client-side route guard is UX only. The backend must still check permissions for every protected resource.

## 24.2 Data fetching concepts

Learn loading, success, empty, and error states; aborting stale fetches; retries; caching; invalidation; pagination; infinite scrolling; optimistic mutations; and request de-duplication. Framework loaders or libraries such as TanStack Query are common options, but they are external to React.

## 24.3 URL state vs component state

State that should be shareable/bookmarkable—search terms, filters, sorting, page number, selected entity ID—often belongs in URL search params/path params. Temporary UI details—whether a popover is open or a local draft is being edited—often belong in component state.

---

# 25. Styling approaches

React does not require one styling system. Common approaches:

1. Regular CSS files and classes.
2. CSS Modules.
3. Utility CSS frameworks (external packages).
4. CSS-in-JS libraries (external packages; some integrate with React insertion Effects).
5. Design systems/component libraries.

## 25.1 CSS class toggle

```tsx
function Panel({ active }: { active: boolean }) {
  return <section className={active ? 'panel panel--active' : 'panel'}>Content</section>;
}
```

For complex combinations, a helper or class-name utility may improve readability. Use semantic HTML and keep focus states visible.

## 25.2 CSS custom properties with inline style

```tsx
type StyleVars = React.CSSProperties & { '--accent'?: string };

function AccentPanel() {
  const style: StyleVars = { '--accent': '#e50914' };
  return <section style={style} className="accent-panel">Hello</section>;
}
```

Avoid injecting user-controlled content into raw HTML. Prefer normal JSX text rendering and safe, structured attributes.

---

# 26. Testing and debugging

## 26.1 Types are not runtime tests

TypeScript catches certain mistakes before running, but it does not verify UI behavior, network integrations, permissions, or actual rendered output. Use tests and browser checks too.

## 26.2 Unit/component test example (ecosystem)

Example in a setup using Vitest and React Testing Library:

```tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('renders its label', () => {
    render(<Button label="Save" />);
    expect(screen.getByRole('button', { name: 'Save' })).toBeTruthy();
  });
});
```

Configure the test environment and setup file according to the versions of your installed packages. Prefer testing user-visible behavior and accessibility roles over implementation details.

## 26.3 What to test

- Rendering: content, empty state, loading state, error state.
- Interactions: click, typing, form submission, keyboard actions.
- Network states: success, server error, timeout/abort.
- Accessibility: accessible labels, focus order, dialogs, keyboard access.
- Authorization-relevant flows: verify behavior at the server too.
- Regression tests for bugs already fixed.

## 26.4 Debugging workflow

1. Reproduce the bug in a small, reliable way.
2. Read the full error and inspect the first relevant stack frame.
3. Check browser DevTools Console and Network tabs.
4. Inspect props/state and the component tree with React DevTools.
5. Check request URL, status code, response body, CORS configuration, and authentication.
6. Run TypeScript checks, lint, tests, and production build.
7. Add a regression test where practical.

Helpful tools include browser DevTools, React DevTools, ESLint with the React Hooks plugin, TypeScript language services, and your framework/build tool's diagnostics.

---

# 27. Accessibility, security, and production quality

## 27.1 Accessibility essentials

- Prefer semantic HTML (`button`, `nav`, `main`, `label`, `fieldset`, headings) over clickable generic elements.
- Every form field needs an accessible name.
- All actions must be keyboard-operable.
- Keep visible focus indicators.
- Use correct heading hierarchy and meaningful alternative text for informative images.
- Announce async errors/status appropriately when needed (`role="alert"`, `aria-live`).
- Ensure dialogs manage focus and have an accessible name.
- Do not use color alone to communicate status.

## 27.2 Security essentials

- Validate and authorize all sensitive operations on the server.
- Never ship private API keys, database credentials, or privileged service secrets to client code.
- Client-side route guards and hidden controls do not secure APIs.
- Treat all client input and server responses as untrusted.
- Render text normally rather than assigning untrusted `innerHTML`/`dangerouslySetInnerHTML`.
- If HTML injection is an actual product requirement, use a careful sanitization and threat-modeling approach.
- Use secure authentication/session handling appropriate to the backend; protect cookies and state-changing operations according to your framework's security guidance.
- Do not log passwords, session tokens, private personal data, or secrets.

## 27.3 Production checks

Before releasing, verify production build, type checking, linting, tests, mobile layout, keyboard behavior, empty/error/loading states, API failures, permissions, environment variables, monitoring, and deployment configuration.

---

# 28. Performance and React Compiler

## 28.1 First measure

Use React DevTools Profiler and browser performance tools to identify actual bottlenecks. Avoid premature optimization.

## 28.2 Main approaches

- Keep state local where possible.
- Avoid unnecessary state duplication and Effects.
- Split large screens into meaningful components.
- Use stable keys for lists.
- Lazy-load infrequently used routes/components.
- Virtualize very large lists when appropriate.
- Optimize images, fonts, and assets.
- Avoid redundant API calls and use caching where suitable.
- Use `memo`, `useMemo`, and `useCallback` only when there is a concrete performance reason and they fit the architecture.

## 28.3 React Compiler

React Compiler is a build-time optimization tool for supported setups that can automatically memoize components and values. It depends on compatible tooling and coding patterns; it is not something to assume is active in every project. Follow its current setup guide, use the React Hooks ESLint plugin, and verify output/performance rather than adding manual memoization everywhere.

## 28.4 Common causes of slow UI

- Re-rendering too much expensive work.
- Huge lists without virtualization.
- Too many network requests or large responses.
- Large bundles and missing code splitting.
- Heavy synchronous computation during rendering.
- Effects that create loops or repeated fetches.
- Unstable object/function props passed to heavily memoized children without a clear reason.

---

# 29. Common errors and fixes

| Problem | Likely cause | Fix |
|---|---|---|
| `Objects are not valid as a React child` | Trying to render an object directly | Render a field or map object data to elements. |
| Missing key warning | A list item has no stable key | Add a data-derived `key`. |
| State seems one click behind | Reading a state snapshot in the current handler | Use a functional updater when based on prior state. |
| Input changes from uncontrolled to controlled | `value` changes from `undefined` to a string | Initialize consistently, often with `''` or a deliberate optional state model. |
| Infinite render/effect loop | State update causes the Effect dependency to change repeatedly | Revisit state derivation and dependencies; remove unnecessary Effect. |
| Hook order error | A Hook is called conditionally or in a nested callback | Call Hooks at the component/custom-Hook top level. |
| `window is not defined` | Browser-only API used during server rendering | Move access to a client-only context/Effect or guard appropriately. |
| TypeScript says possibly null | A value may be missing | Check it or use an explicit safe fallback. |
| Type passes but runtime API data is wrong | Types were asserted without validation | Validate external data at runtime. |
| CORS error | Server doesn't permit the browser origin/method/headers | Fix server CORS policy; don't treat CORS as a frontend-only bypass. |
| Protected route is accessible by API | Only UI was guarded | Enforce authentication/authorization on the backend. |
| React list item state appears to move | Unstable or index-based key for mutable list | Use a stable identity key. |
| Effect runs extra times in development | Strict Mode checks or impure/missing-cleanup logic | Make render pure and Effect setup/cleanup correct. |

---

# 30. Full-stack integration patterns

## 30.1 Frontend calls a backend API

```tsx
async function createTodo(title: string): Promise<Todo> {
  const response = await fetch('/api/todos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error(`Could not create todo (${response.status})`);
  }

  const result: unknown = await response.json();
  // Validate result before using it in a real application.
  return result as Todo;
}
```

If frontend and backend run on different origins during development, configure the dev proxy or backend CORS settings correctly. In production, decide whether to serve them from one origin or configure cross-origin behavior deliberately.

## 30.2 Keep responsibilities separate

- Component: renders UI and coordinates simple interactions.
- Hook: reuses stateful UI logic.
- API module: performs HTTP requests and handles transport concerns.
- Schema/parser: validates external input/data at runtime.
- Backend service: applies business rules.
- Database layer: performs persistence and query work.

Do not put database credentials or raw database access in React browser components. The browser is not a trusted environment.

## 30.3 Authentication flow concept

Typical flow: user submits credentials → backend verifies them → backend establishes a secure session or returns an appropriately designed token → frontend updates its display state → every protected backend request is authenticated and authorized by the backend. Exact implementation depends on your backend framework and threat model. Never treat a React `isAdmin` boolean as an access-control boundary.

## 30.4 Environment variables

- Frontend build-time variables are generally public once shipped to the browser.
- Backend-only environment variables can contain secrets if properly managed.
- Keep `.env` files out of version control where they contain local secrets; commit a `.env.example` with placeholder values.
- Rotate any credential accidentally committed or exposed.

---

# 31. Project exercises

Build these in increasing difficulty; use TypeScript after understanding the JavaScript version.

1. **Counter and theme toggle:** `useState`, handlers, CSS classes.
2. **Todo list:** object/array state, add/edit/delete/toggle, stable keys.
3. **Searchable catalogue:** controlled input, `filter`, derived state, empty states.
4. **Validated registration form:** typed events, validation, accessible errors.
5. **API user browser:** `fetch`, `AbortController`, loading/success/error states, runtime data validation.
6. **Reusable component library:** typed buttons, inputs, cards, modal, table, generic list.
7. **Dashboard:** routing, nested layouts, URL filters, charts, API pagination.
8. **Authentication UI with real backend integration:** error handling and permissions enforced on the server.
9. **E-commerce frontend:** product list, detail, cart, optimistic UX, forms, typed server responses.
10. **Admin content manager:** role-aware UI, upload progress, server-side authorization, audit-friendly errors.
11. **Tested production app:** component tests, browser tests, type checking, linting, production build, deployment.

For each project, verify that buttons do something real, forms handle errors, keyboard navigation works, and the server validates every important operation.

---

# 32. Learning checklist

## React foundation

- [ ] Create and run a project.
- [ ] Understand JSX/TSX syntax and function components.
- [ ] Pass props and compose children.
- [ ] Render conditions and arrays using stable keys.
- [ ] Use `useState` and immutable state updates.
- [ ] Handle events and forms.
- [ ] Understand controlled and uncontrolled form controls.
- [ ] Use Effects for external synchronization and clean up correctly.
- [ ] Create custom Hooks.
- [ ] Use refs, context, and reducers where appropriate.
- [ ] Understand transitions, Actions, Suspense, and lazy loading.
- [ ] Understand error boundaries and debugging.

## TypeScript

- [ ] Annotate variables, parameters, return types, and component props.
- [ ] Understand union/intersection and literal types.
- [ ] Narrow `unknown` safely.
- [ ] Use interfaces/type aliases, generics, and utility types.
- [ ] Type event handlers, refs, context, reducers, and API results.
- [ ] Use discriminated unions for status/action models.
- [ ] Understand that type assertions do not validate data at runtime.
- [ ] Enable strict compiler checks and resolve errors instead of bypassing them.

## Full-stack quality

- [ ] Use routing and data-loading tools appropriate to the project.
- [ ] Keep secrets and privileged logic on the server.
- [ ] Validate input and authorize sensitive operations in the backend.
- [ ] Test user-visible behavior and failure paths.
- [ ] Check accessibility, performance, responsive behavior, and production builds.

---

# 33. API and syntax index

This index is a revision checklist. Exact details and availability should be verified in the current official reference for the version used by the project.

## JSX syntax

- Elements and components: `<div />`, `<MyComponent />`
- Expressions: `{value}`, `{calculate()}`
- Fragments: `<>...</>` and `<Fragment key={...}>...</Fragment>`
- Conditional display: `condition ? <A /> : <B />`, `condition && <A />`
- Lists: `items.map(item => <Row key={item.id} item={item} />)`
- Props: `title="text"`, `count={count}`, `{...props}`
- Children: `<Panel><p>Text</p></Panel>`
- Style: `style={{ backgroundColor: 'black' }}`
- Events: `onClick={handler}`, `onChange={handler}`, `onSubmit={handler}`

## Hook index

- State: `useState`, `useReducer`
- Context: `useContext`
- Refs: `useRef`, `useImperativeHandle`
- Effects: `useEffect`, `useLayoutEffect`, `useInsertionEffect`, `useEffectEvent`
- Performance/priority: `useMemo`, `useCallback`, `useTransition`, `useDeferredValue`
- Other: `useId`, `useSyncExternalStore`, `useDebugValue`, `useActionState`, `useOptimistic`, `use`
- Custom: functions beginning with `use`, following Hook rules
- React DOM form Hook: `useFormStatus`

## Common React exports and DOM APIs

`Children`, `Component`, `PureComponent`, `Fragment`, `StrictMode`, `Suspense`, `Activity`, `ViewTransition`, `Profiler`, `createContext`, `createElement`, `isValidElement`, `lazy`, `memo`, `startTransition`, `act`, `cache`, `cacheSignal`, `captureOwnerStack`, `addTransitionType`, `createRoot`, `hydrateRoot`, `createPortal`, `flushSync`, `preconnect`, `prefetchDNS`, `preload`, `preloadModule`, `preinit`, `preinitModule`, and server-rendering APIs. Advanced APIs can vary by runtime/build support; consult the official reference before use.

## TypeScript syntax index

- Primitives: `string`, `number`, `boolean`, `bigint`, `symbol`, `null`, `undefined`
- Special types: `unknown`, `any`, `never`, `void`, `object`
- Arrays/tuples: `T[]`, `Array<T>`, `[string, number]`, `readonly T[]`
- Objects: `type`, `interface`, optional `?`, readonly properties
- Composition: union `|`, intersection `&`, literal types, discriminated unions
- Narrowing: `typeof`, `instanceof`, `in`, equality checks, predicates `value is T`
- Functions: parameter types, return types, optional/default/rest parameters, overloads
- Generics: `<T>`, constraints `extends`, defaults, generic functions/classes/interfaces
- Type operators: `keyof`, `typeof`, indexed access `T[K]`, conditional `T extends U ? X : Y`
- Type generation: mapped types, template literal types, `infer`, recursive types
- Assertions: `as`, `as const`, `satisfies`, non-null `!` (use carefully)
- Modules: `import`, `export`, `import type`, `export type`
- Utilities: `Partial`, `Required`, `Readonly`, `Pick`, `Omit`, `Record`, `Exclude`, `Extract`, `NonNullable`, `ReturnType`, `Parameters`, `ConstructorParameters`, `Awaited`, and others from the installed TS library
- Configuration topics: `strict`, `noImplicitAny`, `strictNullChecks`, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`, `target`, `module`, `moduleResolution`, `lib`, and `jsx`

---

# 34. Official reference links

Use the live documentation for exact signatures, constraints, current APIs, and version-specific details.

## React

- [React Learn](https://react.dev/learn)
- [React API Reference](https://react.dev/reference/react)
- [Built-in Hooks](https://react.dev/reference/react/hooks)
- [Using TypeScript with React](https://react.dev/learn/typescript)
- [Built-in Components](https://react.dev/reference/react/components)
- [Built-in React APIs](https://react.dev/reference/react/apis)
- [React DOM APIs](https://react.dev/reference/react-dom)
- [Client APIs: `createRoot` and `hydrateRoot`](https://react.dev/reference/react-dom/client)
- [Server rendering APIs](https://react.dev/reference/react-dom/server)
- [Rules of React](https://react.dev/reference/rules)
- [React Hooks ESLint plugin](https://react.dev/reference/eslint-plugin-react-hooks)

## TypeScript

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)
- [Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html)
- [Object Types](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)
- [Creating Types from Types](https://www.typescriptlang.org/docs/handbook/2/types-from-types.html)
- [Utility Types](https://www.typescriptlang.org/docs/handbook/utility-types.html)
- [Modules](https://www.typescriptlang.org/docs/handbook/modules.html)
- [JSX in TypeScript](https://www.typescriptlang.org/docs/handbook/jsx.html)

---

**End of guide.** Keep this file as a study checklist and use the linked official references whenever an API is new, environment-specific, or version-sensitive.
