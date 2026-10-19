# Complete JavaScript Guide for Full-Stack Development

**A practical reference to JavaScript syntax, core language concepts, built-in functions, browser programming, Node.js, APIs, databases, testing, and security.**

> **Important about “100% JavaScript”:** JavaScript is an evolving language and there is no single finite, official checklist that permanently captures “100% of JavaScript.” This guide is a broad, structured learning reference covering the core language, widely used modern syntax, important built-ins, browser APIs, and the JavaScript skills commonly needed for full-stack development. Browser APIs, Node.js APIs, frameworks, and database libraries are platform tools—not part of the ECMAScript language itself. Consult the official references at the end for uncommon or newly added features.

## How to use this guide

1. Study Sections 1–21 for the language itself. Type every example and change the values to observe the result.
2. Study Sections 22–25 for frontend/browser programming and HTTP requests.
3. Study Sections 26–31 for Node.js, backend services, databases, authentication, testing, and production work.
4. Complete the practice projects and checklist at the end. Reading alone is not enough; build and debug working programs.

---

## Table of Contents

1. [JavaScript Setup and Execution](#1-javascript-setup-and-execution)
2. [Comments, Statements, and Strict Mode](#2-comments-statements-and-strict-mode)
3. [Variables and Bindings](#3-variables-and-bindings)
4. [Values, Types, and Type Checking](#4-values-types-and-type-checking)
5. [Operators and Expressions](#5-operators-and-expressions)
6. [Strings and Template Literals](#6-strings-and-template-literals)
7. [Numbers, Math, and BigInt](#7-numbers-math-and-bigint)
8. [Conditions and Control Flow](#8-conditions-and-control-flow)
9. [Loops and Iteration](#9-loops-and-iteration)
10. [Functions: Syntax and Patterns](#10-functions-syntax-and-patterns)
11. [Scope, Hoisting, Closures, and Execution](#11-scope-hoisting-closures-and-execution)
12. [Arrays and Array Methods](#12-arrays-and-array-methods)
13. [Objects and Object Methods](#13-objects-and-object-methods)
14. [Destructuring, Spread, and Rest](#14-destructuring-spread-and-rest)
15. [Map, Set, WeakMap, and WeakSet](#15-map-set-weakmap-and-weakset)
16. [Dates, Time, and Internationalization](#16-dates-time-and-internationalization)
17. [Regular Expressions](#17-regular-expressions)
18. [Errors and Exception Handling](#18-errors-and-exception-handling)
19. [Classes, Prototypes, and Inheritance](#19-classes-prototypes-and-inheritance)
20. [Symbols, Iterators, and Generators](#20-symbols-iterators-and-generators)
21. [Built-in Objects, JSON, and Reflection](#21-built-in-objects-json-and-reflection)
22. [Modules: import and export](#22-modules-import-and-export)
23. [Asynchronous JavaScript](#23-asynchronous-javascript)
24. [HTTP, fetch, and APIs](#24-http-fetch-and-apis)
25. [DOM, Events, Forms, and Browser APIs](#25-dom-events-forms-and-browser-apis)
26. [Node.js Fundamentals](#26-nodejs-fundamentals)
27. [npm and Project Configuration](#27-npm-and-project-configuration)
28. [Building a Backend with Express](#28-building-a-backend-with-express)
29. [Databases and Data Access](#29-databases-and-data-access)
30. [Authentication, Authorization, and Security](#30-authentication-authorization-and-security)
31. [Testing, Debugging, and Code Quality](#31-testing-debugging-and-code-quality)
32. [Performance and Memory](#32-performance-and-memory)
33. [Modern JavaScript Syntax Checklist](#33-modern-javascript-syntax-checklist)
34. [Common Patterns and Best Practices](#34-common-patterns-and-best-practices)
35. [Full-Stack Learning Order and Projects](#35-full-stack-learning-order-and-projects)
36. [Quick Syntax Reference](#36-quick-syntax-reference)
37. [Official Learning References](#37-official-learning-references)

---

# 1. JavaScript Setup and Execution

JavaScript runs in a browser or in a runtime such as Node.js. The language is standardized as **ECMAScript**; browser and Node.js runtimes add APIs for their environments.

### Run JavaScript in a browser

`index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JavaScript Practice</title>
  <script src="app.js" defer></script>
</head>
<body>
  <h1 id="heading">Hello</h1>
  <button id="change">Change heading</button>
</body>
</html>
```

`app.js`:

```js
console.log("Hello, JavaScript!");

const heading = document.querySelector("#heading");
const button = document.querySelector("#change");

button.addEventListener("click", () => {
  heading.textContent = "JavaScript is working!";
});
```

### Run JavaScript with Node.js

```bash
node --version
npm --version
node app.js
```

A simple `app.js`:

```js
const message = "Hello from Node.js";
console.log(message);
```

### Console methods

```js
console.log("general output");
console.info("information");
console.warn("warning");
console.error("error");
console.table([{ name: "Ada" }, { name: "Grace" }]);
console.time("work");
// code to measure
console.timeEnd("work");
```

Use browser DevTools or the Node.js debugger to inspect variables, pause execution, and read stack traces.

# 2. Comments, Statements, and Strict Mode

```js
// Single-line comment

/* Multi-line
   comment */

"use strict";
```

- A **statement** performs an action or declares something. An **expression** produces a value.
- JavaScript has automatic semicolon insertion, but consistent semicolons help avoid edge cases.
- Identifiers are case-sensitive: `userName` is different from `username`.
- Names usually start with a letter, `_`, or `$`; later characters can also include digits.
- Avoid reserved words as variable names.
- ES modules are automatically in strict mode. The directive enables strict mode in scripts and applicable function bodies.

```js
const total = 2 + 3; // expression in a variable declaration
if (total > 3) {     // control-flow statement
  console.log(total);
}
```

# 3. Variables and Bindings

```js
let age = 20;
age = 21; // reassignment is allowed

const country = "India";
// country = "Japan"; // TypeError: const binding cannot be reassigned

var legacyValue = "old style";
```

| Keyword | Reassign? | Scope | Hoisting behaviour | Preferred use |
|---|---|---|---|---|
| `const` | No | Block | Temporal dead zone before initialization | Default choice |
| `let` | Yes | Block | Temporal dead zone before initialization | Value must change |
| `var` | Yes | Function/global | Declaration is hoisted and initialized to `undefined` | Mostly legacy code |

`const` prevents rebinding, not mutation of an object:

```js
const settings = { theme: "dark" };
settings.theme = "light"; // allowed
// settings = {};         // not allowed
```

Use descriptive names such as `totalPrice`, `isLoading`, and `fetchUser`. Prefer `const` unless reassignment is necessary. Avoid `var` in most modern code.

# 4. Values, Types, and Type Checking

JavaScript primitive types are `string`, `number`, `bigint`, `boolean`, `undefined`, `symbol`, and `null`. Everything else is an object, including arrays and functions.

```js
const title = "Anime Portal";           // string
const score = 98.5;                     // number
const huge = 12345678901234567890n;     // bigint
const published = true;                 // boolean
let notAssigned;                        // undefined
const explicitlyEmpty = null;           // null
const key = Symbol("private-ish key");  // symbol
const user = { name: "Asha" };          // object
const numbers = [10, 20, 30];            // array object
const run = function () {};              // function object
```

### `typeof`

```js
typeof "hi";              // "string"
typeof 12;                // "number"
typeof true;              // "boolean"
typeof undefined;         // "undefined"
typeof 1n;                // "bigint"
typeof Symbol("id");      // "symbol"
typeof {};                // "object"
typeof [];                // "object"
typeof (() => {});        // "function"
typeof null;              // "object" (historical quirk)
```

Use `Array.isArray(value)` for arrays and `value === null` for `null`.

### Truthiness

Falsy values: `false`, `0`, `-0`, `0n`, `""`, `null`, `undefined`, and `NaN`. All other values are truthy, including empty arrays and empty objects.

```js
Boolean(0);       // false
Boolean("");      // false
Boolean("false"); // true
Boolean([]);      // true
Boolean({});      // true
```

### Conversion

```js
Number("42");          // 42
String(42);             // "42"
Boolean(1);             // true
parseInt("42px", 10);  // 42
parseFloat("3.14rem"); // 3.14
Number("");             // 0
Number("hello");       // NaN
```

Prefer explicit conversion to make intent clear. Be careful with implicit coercion and user input.

### Equality

```js
5 === 5;    // true
5 === "5";  // false
5 == "5";   // true: coercion happens
Object.is(NaN, NaN); // true
Object.is(0, -0);    // false
```

Prefer `===` and `!==`. `Object.is()` is useful for its specific equality semantics.

# 5. Operators and Expressions

### Arithmetic

```js
const a = 10;
const b = 3;

a + b;   // 13
a - b;   // 7
a * b;   // 30
a / b;   // 3.333...
a % b;   // 1 (remainder)
a ** b;  // 1000 (exponentiation)

let counter = 0;
counter++;
counter--;
```

### Assignment operators

```js
let n = 10;
n += 5;
n -= 2;
n *= 3;
n /= 2;
n %= 4;
n **= 2;
```

### Comparison operators

`<`, `<=`, `>`, `>=`, `===`, `!==`, `==`, `!=`.

```js
10 > 5;                 // true
"a" === "a";           // true
"5" !== 5;              // true
```

### Logical operators and short-circuiting

```js
true && false; // false
true || false; // true
!true;         // false

const displayName = inputName || "Guest";
const providedName = inputName ?? "Guest";
const result = user && user.profile;
const city = user?.address?.city;
```

- `&&` returns the first falsy operand, or the last operand if all are truthy.
- `||` returns the first truthy operand, or the last operand if all are falsy.
- `??` falls back only when the left value is `null` or `undefined`.
- `?.` safely accesses properties/calls when the value before it is `null` or `undefined`.

Do not mix `??` with `&&` or `||` without parentheses.

### Ternary operator

```js
const label = age >= 18 ? "adult" : "minor";
```

### Type and object operators

```js
typeof value;
"name" in user;
user instanceof Date;
delete user.temporaryProperty;
void someExpression;
```

`in` checks the object's property chain, not merely whether its value is non-`undefined`. `instanceof` checks a prototype relationship and has edge cases with iframes and custom `Symbol.hasInstance`. `delete` removes configurable object properties; it does not delete local variables.

### Bitwise operators

`&`, `|`, `^`, `~`, `<<`, `>>`, `>>>`, and assignment forms such as `&=`. They operate on 32-bit integer representations for ordinary Numbers. They are uncommon in typical business UI code but useful for bit flags and low-level operations.

### Operator precedence

Parentheses improve readability and prevent precedence mistakes:

```js
const result = (a + b) * c;
const isAllowed = isLoggedIn && (isAdmin || isOwner);
```

# 6. Strings and Template Literals

```js
const single = 'single quotes';
const double = "double quotes";
const name = "Ajmal";
const greeting = `Hello, ${name}!`;
const multiLine = `Line one
Line two`;
```

### Common string properties and methods

```js
const text = "  JavaScript Guide  ";

text.length;
text.trim();
text.trimStart();
text.trimEnd();
text.toUpperCase();
text.toLowerCase();
text.includes("Script");
text.startsWith("Java");
text.endsWith("Guide");
text.indexOf("Script");
text.lastIndexOf("a");
text.slice(0, 4);
text.substring(0, 4);
text.replace("Guide", "Course");
text.replaceAll("a", "A");
"a,b,c".split(",");
"ha".repeat(3);
"7".padStart(3, "0");
```

Strings are immutable: string methods return new strings rather than changing the original. Avoid using `innerHTML` with untrusted text; use `textContent` to insert plain text safely.

### Unicode note

JavaScript strings are UTF-16 sequences. A displayed character can consist of multiple code units or code points. `text.length` is not always the number of user-perceived characters. For grapheme-aware text handling, use `Intl.Segmenter` where supported.

# 7. Numbers, Math, and BigInt

### Number values and helpers

```js
Number.isFinite(12);       // true
Number.isNaN(NaN);         // true
Number.isInteger(12);      // true
Number.parseInt("12px", 10);
Number.parseFloat("2.5em");
Number.isSafeInteger(42);
Number.MAX_SAFE_INTEGER;
Number.EPSILON;
```

Use `Number.isNaN()` instead of the coercive global `isNaN()` when you need to test specifically for the `NaN` value.

### Math methods

```js
Math.abs(-5);
Math.round(2.6);
Math.floor(2.9);
Math.ceil(2.1);
Math.trunc(-2.9);
Math.min(4, 8, 1);
Math.max(4, 8, 1);
Math.pow(2, 3);
Math.sqrt(25);
Math.cbrt(27);
Math.random();
Math.sign(-10);
Math.log(10);
Math.exp(1);
Math.sin(Math.PI / 2);
Math.cos(0);
Math.PI;
Math.E;
```

For a random integer from `min` through `max` inclusive:

```js
function randomInt(min, max) {
  if (!Number.isInteger(min) || !Number.isInteger(max) || min > max) {
    throw new RangeError("Expected integers with min <= max");
  }
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
```

`Math.random()` is not cryptographically secure. Use `crypto.getRandomValues()` in a browser or `node:crypto` in Node.js for security-sensitive randomness.

### Floating-point precision

```js
0.1 + 0.2; // 0.30000000000000004
```

Binary floating-point cannot exactly represent many decimal fractions. Use a tolerance for approximate calculations or a decimal/money strategy (for example, integer minor currency units) for financial values.

### BigInt

```js
const bigA = 9007199254740993n;
const bigB = 2n;
const total = bigA + bigB;
// 1n + 1 is invalid: BigInt and Number arithmetic must be handled deliberately
```

BigInt is for integers larger than safe Number precision. It cannot be directly mixed with Number arithmetic and is not serialized by `JSON.stringify()` by default.

# 8. Conditions and Control Flow

### `if`, `else if`, and `else`

```js
if (score >= 90) {
  console.log("A");
} else if (score >= 75) {
  console.log("B");
} else {
  console.log("Keep practising");
}
```

### `switch`

```js
switch (role) {
  case "admin":
    openAdminPanel();
    break;
  case "member":
    openMemberPanel();
    break;
  default:
    openPublicPage();
}
```

`switch` compares cases using strict equality. `break` prevents fall-through; intentional fall-through should be clearly commented.

### Ternary

```js
const message = isOnline ? "Online" : "Offline";
```

Use ternaries for simple value selection, not deeply nested branching.

### Early return

```js
function getDiscount(user) {
  if (!user) return 0;
  if (!user.isMember) return 0;
  return 10;
}
```

Early returns can reduce nested conditions.

# 9. Loops and Iteration

### Classic `for`

```js
for (let i = 0; i < 5; i++) {
  console.log(i);
}
```

### `while` and `do...while`

```js
while (hasMoreWork()) {
  processNextItem();
}

do {
  askForInput();
} while (!inputIsValid());
```

A `do...while` loop always runs at least once.

### `for...of`

Iterates values from an iterable such as an array, string, map, set, or generator:

```js
for (const value of [10, 20, 30]) {
  console.log(value);
}
```

### `for...in`

Iterates enumerable string keys, including inherited enumerable keys:

```js
const product = { title: "Book", price: 10 };
for (const key in product) {
  if (Object.hasOwn(product, key)) {
    console.log(key, product[key]);
  }
}
```

For arrays, prefer `for...of`, array methods, or an indexed `for` loop rather than `for...in`.

### `break`, `continue`, and labels

```js
for (let i = 0; i < 10; i++) {
  if (i === 2) continue;
  if (i === 7) break;
  console.log(i);
}

outer: for (let row = 0; row < 3; row++) {
  for (let col = 0; col < 3; col++) {
    if (row === 1 && col === 1) break outer;
  }
}
```

Labels exist but are uncommon; avoid them unless they clearly simplify nested-loop control.

# 10. Functions: Syntax and Patterns

Functions are reusable blocks of code and first-class values: they can be stored in variables, passed as arguments, returned from other functions, and placed in objects.

### Function declaration

```js
function add(a, b) {
  return a + b;
}

add(2, 3); // 5
```

Declarations are generally available throughout their containing scope due to function hoisting. Avoid relying on obscure hoisting behaviour to make code run.

### Function expression

```js
const subtract = function (a, b) {
  return a - b;
};
```

A function expression can be anonymous or named:

```js
const factorial = function calculateFactorial(n) {
  if (n < 0) throw new RangeError("n must be non-negative");
  return n <= 1 ? 1 : n * calculateFactorial(n - 1);
};
```

### Arrow functions

```js
const square = (n) => n * n;
const greet = name => `Hello, ${name}`;
const makeUser = (name) => ({ name });
const logValue = () => {
  console.log("Called");
};
```

- One parameter can omit parentheses; zero or multiple parameters need parentheses.
- Use parentheses around an object literal returned implicitly.
- Arrow functions do not have their own `this`, `arguments`, or constructable `prototype`; do not use them as constructors.
- Use ordinary functions for object methods that require a dynamic `this` receiver.

### Parameters and arguments

```js
function divide(a, b) {
  return a / b;
}

divide(10, 2); // 5
```

- **Parameters** are names in the function definition.
- **Arguments** are values passed to a function call.

JavaScript does not enforce declared parameter types or counts. Missing arguments are `undefined`; extra arguments are available through rest parameters or, in non-arrow functions, `arguments`.

### Default parameters

```js
function createGreeting(name = "Guest", punctuation = "!") {
  return `Hello, ${name}${punctuation}`;
}
```

A default is used for `undefined`, not for `null`, `0`, `false`, or an empty string.

### Rest parameters

```js
function sum(...values) {
  return values.reduce((total, value) => total + value, 0);
}

sum(1, 2, 3, 4); // 10
```

A rest parameter must be last in the parameter list.

### Callback function

A callback is a function passed to another function:

```js
function doWork(value, callback) {
  callback(value * 2);
}

doWork(5, (result) => console.log(result)); // 10
```

Callbacks can be synchronous or asynchronous. Do not assume a callback will run later unless the API guarantees it.

### Higher-order functions

A higher-order function accepts a function, returns a function, or both:

```js
function multiplier(factor) {
  return (value) => value * factor;
}

const triple = multiplier(3);
triple(4); // 12
```

### Immediately Invoked Function Expression (IIFE)

```js
(() => {
  const localOnly = "inside this function scope";
  console.log(localOnly);
})();
```

IIFEs were often used for private scope before modules and block-scoped declarations became common. They are less necessary in modern modules.

### Methods

```js
const calculator = {
  add(a, b) {
    return a + b;
  },
  multiply: (a, b) => a * b
};
```

Be careful: an arrow function used as an object property does not receive `this` from the object. Use method syntax when a method needs the object as `this`.

### Recursion

A recursive function calls itself and needs a correct base case:

```js
function factorial(n) {
  if (!Number.isInteger(n) || n < 0) {
    throw new RangeError("n must be a non-negative integer");
  }
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}
```

Large recursion can exceed the call-stack limit. Consider iteration for deep or unbounded input.

### Pure functions and side effects

- A **pure function** returns the same output for the same inputs and does not change external state.
- A **side effect** changes outside state, performs I/O, writes to the DOM, or logs information.

Pure logic is usually easier to test:

```js
const calculateTotal = (price, quantity) => price * quantity;
```

### Function methods

```js
function show(prefix, value) {
  return `${prefix}: ${value}`;
}

show.call(null, "Value", 10);
show.apply(null, ["Value", 10]);
const showValue = show.bind(null, "Value");
showValue(10);
```

`call()` accepts individual arguments, `apply()` accepts an array-like arguments list, and `bind()` returns a new function with a bound `this` and optional leading arguments.

# 11. Scope, Hoisting, Closures, and Execution

### Scope types

- **Global scope:** values available in the global environment (with important differences between script and module contexts).
- **Module scope:** top-level bindings inside an ES module.
- **Function scope:** variables declared with `var` and function parameters.
- **Block scope:** variables declared with `let` and `const` inside `{}`.
- **Lexical scope:** variable access is determined by where code is written, not where a function is called.

```js
const outerValue = "outer";

function example() {
  const functionValue = "function";
  if (true) {
    const blockValue = "block";
    console.log(outerValue, functionValue, blockValue);
  }
  // blockValue is not available here
}
```

### Hoisting and the temporal dead zone

Function declarations can generally be called before their declaration in the same scope. `var` declarations are hoisted and initialized to `undefined`. `let` and `const` are hoisted but unavailable until their declaration is evaluated; that region is called the **temporal dead zone (TDZ)**.

```js
console.log(value); // undefined
var value = 5;

// console.log(count); // ReferenceError (TDZ)
let count = 1;
```

### Closures

A closure is a function together with access to its surrounding lexical environment:

```js
function createCounter() {
  let count = 0;
  return function increment() {
    count += 1;
    return count;
  };
}

const counter = createCounter();
counter(); // 1
counter(); // 2
```

Closures are useful for private state, callbacks, event handlers, and function factories. Long-lived closures can also retain memory, so avoid holding references to large objects unnecessarily.

### Execution concepts

Know these terms:

- **Execution context:** environment in which code runs.
- **Call stack:** tracks currently executing functions.
- **Lexical environment:** stores bindings and references to outer environments.
- **Stack overflow:** often caused by too-deep recursion.
- **Garbage collection:** runtime reclaims memory that is no longer reachable.

These are useful mental models; implementation details can differ between JavaScript engines.

# 12. Arrays and Array Methods

Arrays are ordered, zero-indexed objects and can contain mixed value types, though keeping a consistent type is often easier to maintain.

```js
const numbers = [10, 20, 30];
numbers[0];       // 10
numbers.length;   // 3
numbers[3] = 40;  // expands the array
```

### Create and inspect arrays

```js
const empty = [];
const values = [1, "two", true];
const fromIterable = Array.from("abc"); // ["a", "b", "c"]
const filled = Array(3).fill(0);         // [0, 0, 0]
Array.isArray(values);                   // true
Array.of(3);                             // [3]
```

Avoid `Array(3).map(...)` if you expect a callback for empty slots; use `Array.from({ length: 3 }, callback)` or fill first.

### Add and remove elements

```js
const items = [2, 3];
items.push(4);       // add to end; returns new length
items.pop();        // remove from end; returns removed value
items.unshift(1);   // add to start
items.shift();      // remove from start
items.splice(1, 1); // mutate: remove one element at index 1
```

### Non-mutating selection and copying

```js
const items = [10, 20, 30, 40];
items.slice(1, 3);          // [20, 30]
items.concat([50, 60]);      // new array
items.includes(20);          // true
items.indexOf(30);           // 2
items.at(-1);                 // 40
[...items];                   // shallow copy
```

`slice()` does not mutate the source; `splice()` does.

### Transform and filter

```js
const nums = [1, 2, 3, 4];

nums.map(n => n * 2);                 // [2, 4, 6, 8]
nums.filter(n => n % 2 === 0);        // [2, 4]
nums.reduce((sum, n) => sum + n, 0);   // 10
nums.flatMap(n => [n, n * 2]);         // flattened mapped output
nums.flat();                           // flatten one level by default
```

### Search and tests

```js
const users = [{ id: 1 }, { id: 2 }];
users.find(user => user.id === 2);        // matching object or undefined
users.findIndex(user => user.id === 2);   // 1
users.some(user => user.id === 2);        // true
users.every(user => user.id > 0);         // true
```

`findLast()` and `findLastIndex()` are available in modern runtimes, but check compatibility if supporting older browsers.

### Iterate

```js
nums.forEach((value, index) => {
  console.log(index, value);
});

for (const value of nums) {
  console.log(value);
}
```

`forEach()` does not wait for async callbacks in the way many people expect. For sequential async work, use `for...of` with `await`.

### Sort and reverse

```js
const words = ["pear", "apple", "banana"];
words.sort(); // mutates source; default sort compares string forms

const scores = [100, 9, 20];
scores.sort((a, b) => a - b); // numeric ascending
scores.sort((a, b) => b - a); // numeric descending
```

Use `toSorted()`, `toReversed()`, `toSpliced()`, and `with()` where supported to get non-mutating alternatives:

```js
const original = [3, 1, 2];
const sorted = original.toSorted((a, b) => a - b);
const reversed = original.toReversed();
const changed = original.with(0, 99);
```

### Mutating vs non-mutating quick reference

- Usually mutating: `push`, `pop`, `shift`, `unshift`, `splice`, `sort`, `reverse`, `fill`, `copyWithin`.
- Usually non-mutating: `map`, `filter`, `slice`, `concat`, `flat`, `flatMap`, `toSorted`, `toReversed`, `toSpliced`, `with`.

### Array destructuring

```js
const [first, second, ...remaining] = [10, 20, 30, 40];
```

### Array-like and iterable conversion

```js
const chars = Array.from("hello");
const copiedSet = Array.from(new Set([1, 1, 2]));
const nodeList = document.querySelectorAll("p");
const paragraphs = Array.from(nodeList);
```

# 13. Objects and Object Methods

Objects store key-value properties. Most ordinary object keys are strings or symbols; other keys are converted to strings.

### Object literal

```js
const user = {
  name: "Ajmal",
  age: 27,
  isAdmin: false,
  greet() {
    return `Hello, ${this.name}`;
  }
};

user.name;          // dot access
user["age"];        // bracket access
user.city = "Chennai";
delete user.city;
user.greet();
```

### Computed property names and shorthand

```js
const key = "theme";
const theme = "dark";
const config = {
  [key]: theme,
  theme // shorthand for theme: theme
};
```

### Property testing

```js
Object.hasOwn(user, "name"); // checks own property
"name" in user;              // checks own or inherited property
Object.keys(user);            // own enumerable string keys
Object.values(user);          // own enumerable values
Object.entries(user);         // [key, value] pairs
Object.fromEntries([["a", 1], ["b", 2]]);
```

Prefer `Object.hasOwn(obj, key)` over calling `obj.hasOwnProperty(key)`, because the latter can be shadowed or missing.

### Copying and merging

```js
const copy = { ...user };
const merged = { ...defaults, ...user };
const assignCopy = Object.assign({}, user);
```

These are **shallow** copies: nested objects remain shared references.

### Freeze, seal, and prevent extensions

```js
Object.freeze(user);              // prevents changes to own properties
Object.seal(user);                // prevents adding/removing properties
Object.preventExtensions(user);   // prevents adding properties
Object.isFrozen(user);
Object.isSealed(user);
```

`Object.freeze()` is shallow. It does not automatically freeze nested objects, and it is not a security boundary for untrusted code.

### Property descriptors

```js
const object = {};
Object.defineProperty(object, "id", {
  value: 123,
  writable: false,
  enumerable: true,
  configurable: false
});

Object.getOwnPropertyDescriptor(object, "id");
Object.getOwnPropertyDescriptors(object);
Object.getOwnPropertyNames(object);
Object.getOwnPropertySymbols(object);
```

### Getters and setters

```js
const person = {
  firstName: "Ada",
  lastName: "Lovelace",
  get fullName() {
    return `${this.firstName} ${this.lastName}`;
  },
  set fullName(value) {
    const parts = value.split(" ");
    this.firstName = parts[0] ?? "";
    this.lastName = parts.slice(1).join(" ");
  }
};

person.fullName;
person.fullName = "Grace Hopper";
```

### Object creation and prototype access

```js
const noPrototype = Object.create(null);
const regular = Object.create({ inheritedValue: 1 });
Object.getPrototypeOf(regular);
Object.setPrototypeOf(regular, null); // generally avoid changing prototypes after creation
```

Changing prototypes at runtime can make performance and reasoning harder. Classes or `Object.create()` are usually clearer.

# 14. Destructuring, Spread, and Rest

### Object destructuring

```js
const account = { username: "ajmal", role: "admin", active: true };
const { username, role } = account;
const { active: isActive } = account;
const { city = "Unknown" } = account;
```

### Array destructuring

```js
const [first, second, , fourth] = [10, 20, 30, 40];
const [head, ...tail] = [1, 2, 3, 4];
let a = 1, b = 2;
[a, b] = [b, a];
```

### Nested destructuring

```js
const response = {
  data: {
    user: { name: "Asha" }
  }
};
const { data: { user: { name } } } = response;
```

### Rest syntax

Rest gathers remaining values or properties:

```js
const { id, ...publicInfo } = { id: 1, name: "Asha", city: "Chennai" };
const [first, ...others] = [1, 2, 3];
function join(separator, ...parts) {
  return parts.join(separator);
}
```

### Spread syntax

Spread expands iterable values or enumerable own properties:

```js
const base = [2, 3];
const extended = [1, ...base, 4];
const userCopy = { ...user, active: true };
Math.max(...[2, 9, 4]);
```

Spread makes shallow copies, not deep clones. Avoid using `JSON.parse(JSON.stringify(value))` as a universal deep-clone function because it loses or changes many value types. For supported structured data, consider `structuredClone(value)`; some values cannot be cloned and functions are not cloneable.

# 15. Map, Set, WeakMap, and WeakSet

### `Map`

A `Map` stores key-value pairs with keys of any value type and preserves insertion order.

```js
const map = new Map();
map.set("name", "Asha");
map.set(1, "numeric key");
map.get("name");
map.has(1);
map.delete(1);
map.size;

for (const [key, value] of map) {
  console.log(key, value);
}
```

Useful methods: `set`, `get`, `has`, `delete`, `clear`, `keys`, `values`, `entries`, and `forEach`.

### `Set`

A `Set` stores unique values:

```js
const set = new Set([1, 2, 2, 3]);
set.add(4);
set.has(2);     // true
set.delete(1);
set.size;

const unique = [...new Set([1, 1, 2, 3, 3])];
```

### `WeakMap` and `WeakSet`

Weak collections can hold objects (and, in supported current specifications, non-registered symbols) weakly, so membership does not by itself keep an object alive. They are not enumerable and have no `size`, because their contents can disappear during garbage collection.

```js
const privateData = new WeakMap();
const instance = {};
privateData.set(instance, { secret: "stored separately" });
privateData.get(instance);

const visited = new WeakSet();
visited.add(instance);
visited.has(instance);
```

Use a weak collection when attaching metadata to object lifetimes. Do not use it when you need iteration over all entries.

# 16. Dates, Time, and Internationalization

### `Date`

```js
const now = new Date();
const explicitUtc = new Date("2026-01-15T10:00:00Z");
Date.now();
now.getFullYear();
now.getMonth();       // 0–11, not 1–12
now.getDate();        // day of month
now.getDay();         // day of week: 0 is Sunday
now.getHours();
now.toISOString();
now.toLocaleString();
now.getTime();        // milliseconds since Unix epoch
```

Date parsing of non-standard strings can vary. Prefer ISO 8601 timestamps with an explicit timezone for API data. UTC and local-time methods differ; daylight-saving changes can matter for local dates.

### `Intl`

```js
new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR"
}).format(12345.5);

new Intl.DateTimeFormat("en-IN", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Asia/Kolkata"
}).format(new Date());

new Intl.Collator("en", { sensitivity: "base" }).compare("a", "B");
new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(-1, "day");
new Intl.PluralRules("en").select(2);
```

`Intl` includes locale-aware number/date formatting, collation, plural rules, relative time, list formatting, display names, and segmenter APIs in modern runtimes. Check browser compatibility where needed.

# 17. Regular Expressions

Regular expressions match or replace text patterns.

```js
const re = /hello/i;
re.test("Hello world"); // true

const digits = /\d+/g;
"order 123, item 456".match(digits); // ["123", "456"]

"a1b2".replace(/\d/g, ""); // "ab"
"red, green blue".split(/[, ]+/); // ["red", "green", "blue"]
```

### Common pattern elements

- `.` any character except line terminators by default
- `\d` digit; `\w` word-like ASCII character; `\s` whitespace
- `\D`, `\W`, `\S` are their opposites
- `^` beginning; `$` end
- `*` zero or more; `+` one or more; `?` optional
- `{n}`, `{n,}`, `{n,m}` repetition counts
- `[abc]` character class; `[^abc]` negated class
- `(group)` capture group; `(?:group)` non-capturing group
- `a|b` alternation
- `\b` word boundary
- Lookarounds: `(?=...)`, `(?!...)`, `(?<=...)`, `(?<!...)`

### Flags

- `g`: global matches
- `i`: case-insensitive
- `m`: multiline `^`/`$`
- `s`: dot-all
- `u`: Unicode-aware mode
- `y`: sticky matching at `lastIndex`
- `d`: match indices in runtimes that support it

Be careful with global (`g`) and sticky (`y`) regular expressions: repeated `.test()` calls can change `lastIndex`. Do not rely on a regex alone for security-sensitive validation; validate semantic constraints as well.

# 18. Errors and Exception Handling

### Throwing errors

```js
function withdraw(balance, amount) {
  if (amount <= 0) {
    throw new RangeError("Amount must be positive");
  }
  if (amount > balance) {
    throw new Error("Insufficient balance");
  }
  return balance - amount;
}
```

Built-in error types include `Error`, `TypeError`, `ReferenceError`, `SyntaxError`, `RangeError`, `URIError`, `EvalError` (largely historical), and `AggregateError`.

### `try`, `catch`, and `finally`

```js
try {
  const data = JSON.parse('{"ok": true}');
  console.log(data.ok);
} catch (error) {
  console.error("Could not parse JSON:", error.message);
} finally {
  console.log("Runs whether the try succeeds or throws");
}
```

### Create a custom error

```js
class ValidationError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = "ValidationError";
    this.details = details;
  }
}
```

Best practices:

- Throw `Error` objects rather than strings.
- Catch errors where you can handle them meaningfully; do not silently swallow them.
- Do not send stack traces or internal secrets to end users in production.
- In async code, rejected promises must be handled; `try/catch` catches an awaited rejection inside its `try` block.

# 19. Classes, Prototypes, and Inheritance

### Class syntax

```js
class User {
  static userCount = 0;

  constructor(name, email) {
    this.name = name;
    this.email = email;
    User.userCount += 1;
  }

  greet() {
    return `Hello, ${this.name}`;
  }

  get contact() {
    return this.email;
  }

  set contact(value) {
    this.email = value;
  }

  static createGuest() {
    return new User("Guest", "guest@example.invalid");
  }
}

const user = new User("Asha", "asha@example.invalid");
user.greet();
User.userCount;
```

### Inheritance and `super`

```js
class Admin extends User {
  constructor(name, email, permissions = []) {
    super(name, email);
    this.permissions = permissions;
  }

  can(permission) {
    return this.permissions.includes(permission);
  }
}
```

A derived class constructor must call `super()` before using `this`.

### Private fields and methods

```js
class BankAccount {
  #balance = 0;

  deposit(amount) {
    if (!Number.isFinite(amount) || amount <= 0) {
      throw new RangeError("Deposit must be positive");
    }
    this.#balance += amount;
  }

  get balance() {
    return this.#balance;
  }
}
```

Private fields use `#` and are enforced by the language. They differ from properties named with `_`, which are only a naming convention.

### Static fields and methods

Static properties belong to the class, not each instance. Static initialization blocks are also available in modern ECMAScript:

```js
class Registry {
  static items = new Map();
  static {
    this.items.set("default", true);
  }
  static has(key) {
    return this.items.has(key);
  }
}
```

### Prototype model

JavaScript objects can delegate property lookup to a prototype. Class syntax is built on this prototype system.

```js
const base = {
  greet() { return "hello"; }
};
const child = Object.create(base);
child.greet();
Object.getPrototypeOf(child) === base; // true
```

Relevant concepts: `prototype` property on constructor functions, an object's internal prototype, prototype chain lookup, method inheritance, shadowing, `Object.getPrototypeOf()`, `Object.create()`, and `instanceof`.

Avoid changing prototypes casually. Do not extend built-in prototypes in application code.

# 20. Symbols, Iterators, and Generators

### Symbols

```js
const id1 = Symbol("id");
const id2 = Symbol("id");
id1 === id2; // false

const internal = Symbol("internal");
const object = { [internal]: 123 };
object[internal];
Object.getOwnPropertySymbols(object);
```

`Symbol.for(key)` uses a global symbol registry; `Symbol.keyFor(symbol)` looks up a registered symbol's key. Symbols can be used for non-string property keys but are not a substitute for authorization or private fields.

Well-known symbols customize language protocols, including `Symbol.iterator`, `Symbol.asyncIterator`, `Symbol.toPrimitive`, `Symbol.hasInstance`, `Symbol.toStringTag`, `Symbol.species`, `Symbol.match`, `Symbol.replace`, `Symbol.search`, `Symbol.split`, `Symbol.isConcatSpreadable`, and `Symbol.unscopables`.

### Iterables and iterators

An iterable supplies a `[Symbol.iterator]()` method that returns an iterator. An iterator's `next()` returns `{ value, done }`.

```js
const iterable = {
  values: [10, 20, 30],
  [Symbol.iterator]() {
    let index = 0;
    const values = this.values;
    return {
      next() {
        if (index < values.length) {
          return { value: values[index++], done: false };
        }
        return { value: undefined, done: true };
      }
    };
  }
};

for (const value of iterable) console.log(value);
```

Built-in iterables include arrays, strings, maps, sets, typed arrays, and many DOM collections.

### Generators

```js
function* idGenerator() {
  let id = 1;
  while (true) {
    yield id++;
  }
}

const ids = idGenerator();
ids.next(); // { value: 1, done: false }
ids.next(); // { value: 2, done: false }
```

`yield` pauses and resumes a generator. `yield*` delegates to another iterable or generator. Generators are useful for custom iteration and lazy sequences.

### Async iterators and async generators

```js
async function* streamValues() {
  yield "first";
  await new Promise(resolve => setTimeout(resolve, 10));
  yield "second";
}

async function consume() {
  for await (const value of streamValues()) {
    console.log(value);
  }
}
```

`for await...of` consumes asynchronous iterables and can also consume ordinary synchronous iterables in supported contexts.

# 21. Built-in Objects, JSON, and Reflection

### Common built-ins

- `Object`: object creation, property descriptors, keys, freezing, prototypes.
- `Function`: function objects and `call`, `apply`, `bind`.
- `Array`: ordered collections and array transformations.
- `String`: text processing.
- `Number`, `BigInt`, `Boolean`: primitive wrapper constructors and helpers; generally use primitive values rather than `new String()` or `new Number()`.
- `Math`: numeric functions and constants.
- `Date`: timestamps and date components.
- `RegExp`: pattern matching.
- `Map`, `Set`, `WeakMap`, `WeakSet`: collection types.
- `Symbol`: unique primitive identifiers and protocols.
- `Promise`: asynchronous result representation.
- `ArrayBuffer`, `SharedArrayBuffer`, `DataView`, typed arrays: binary data.
- `Intl`: locale-aware formatting and comparison.
- `Error`, `AggregateError`: errors.
- `Reflect`, `Proxy`: meta-programming.
- `JSON`: JSON serialization and parsing.
- `Atomics`: operations for shared memory and supported typed arrays.
- `FinalizationRegistry` and `WeakRef`: advanced weak-reference facilities; use sparingly.

### JSON

```js
const user = { id: 1, name: "Asha" };
const jsonText = JSON.stringify(user);
const parsed = JSON.parse(jsonText);
```

Optional formatting:

```js
JSON.stringify(user, null, 2);
```

JSON supports objects, arrays, strings, numbers, booleans, and `null`. It does not directly represent `undefined`, functions, symbols, BigInt, Map, Set, or object reference cycles. A replacer/reviver can customize supported serialization cases.

### Proxy

A `Proxy` intercepts operations on a target object through traps:

```js
const target = { name: "Asha" };
const proxy = new Proxy(target, {
  get(object, property, receiver) {
    console.log("Reading", String(property));
    return Reflect.get(object, property, receiver);
  }
});
proxy.name;
```

### Reflect

`Reflect` provides functions for many object meta-operations:

```js
Reflect.get(target, "name");
Reflect.set(target, "name", "Maya");
Reflect.has(target, "name");
Reflect.deleteProperty(target, "name");
Reflect.ownKeys(target);
```

Proxies and reflection are advanced topics, useful for reactive systems, validation layers, and frameworks, but unnecessary for many everyday tasks.

### Typed arrays and binary data

Common types include `Int8Array`, `Uint8Array`, `Uint8ClampedArray`, `Int16Array`, `Uint16Array`, `Int32Array`, `Uint32Array`, `Float32Array`, `Float64Array`, `BigInt64Array`, and `BigUint64Array`.

```js
const bytes = new Uint8Array([65, 66, 67]);
const text = new TextDecoder().decode(bytes); // "ABC"
const encoded = new TextEncoder().encode("ABC");
```

`ArrayBuffer` stores raw binary memory; `DataView` provides controlled reads/writes; typed arrays give typed views over binary data.

# 22. Modules: import and export

Modules separate code into files and define explicit interfaces. ES modules are strict mode and have their own top-level scope.

### Named exports

`math.js`:

```js
export const pi = Math.PI;
export function add(a, b) {
  return a + b;
}
```

`app.js`:

```js
import { pi, add } from "./math.js";
console.log(add(2, 3), pi);
```

### Default export

```js
// logger.js
export default function log(message) {
  console.log(message);
}

// app.js
import log from "./logger.js";
```

### Aliasing, namespace, re-export

```js
import { add as sum } from "./math.js";
import * as MathHelpers from "./math.js";
export { add } from "./math.js";
export * from "./other.js";
export * as helpers from "./math.js";
```

### Dynamic import

```js
async function loadEditor() {
  const module = await import("./editor.js");
  module.openEditor();
}
```

Dynamic import returns a promise and is often used for lazy loading. A module specifier must resolve according to the browser or runtime's module rules and the build tool configuration.

### Browser module script

```html
<script type="module" src="./app.js"></script>
```

### CommonJS in Node.js

```js
// CommonJS export
module.exports = { add: (a, b) => a + b };

// CommonJS import
const math = require("./math.cjs");
```

Node.js supports both ES modules and CommonJS, with behaviour determined by file extensions and `package.json` settings such as `"type": "module"`. Avoid mixing the two systems without understanding the interoperability rules.

# 23. Asynchronous JavaScript

JavaScript code in a given agent generally runs one piece of JavaScript at a time on that agent, but runtimes coordinate timers, I/O, events, workers, and other tasks. “Asynchronous” means work can complete later without blocking the current flow.

### Timer APIs

Browser and Node.js provide timer APIs, though exact scheduling details are host-specific:

```js
const timerId = setTimeout(() => {
  console.log("Runs after a delay (not an exact guarantee)");
}, 500);

const intervalId = setInterval(() => {
  console.log("Repeats");
}, 1000);

clearTimeout(timerId);
clearInterval(intervalId);
```

Use `setInterval()` carefully; asynchronous work can overlap. For polling, a loop that awaits each task may be safer.

### Callback style

```js
function getValue(callback) {
  setTimeout(() => callback(null, 42), 100);
}

getValue((error, value) => {
  if (error) {
    console.error(error);
    return;
  }
  console.log(value);
});
```

Callbacks with error-first arguments are common in Node.js APIs. Promises and `async`/`await` are often easier to compose.

### Promise basics

A promise can be pending, fulfilled, or rejected. Once fulfilled or rejected, its state does not change.

```js
const promise = new Promise((resolve, reject) => {
  const ok = true;
  if (ok) resolve("success");
  else reject(new Error("failed"));
});

promise
  .then(value => console.log(value))
  .catch(error => console.error(error))
  .finally(() => console.log("finished"));
```

`then()` returns a new promise. Return the next value or promise from `.then()` so that the chain waits for it.

### `async` and `await`

```js
async function loadUser() {
  try {
    const response = await fetch("https://jsonplaceholder.typicode.com/users/1");
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    const user = await response.json();
    return user;
  } catch (error) {
    console.error("Could not load user:", error);
    throw error;
  }
}

loadUser().then(user => console.log(user.name));
```

- An `async` function always returns a promise.
- `await` pauses that async function until the awaited value settles; it does not block the entire JavaScript runtime.
- `await` can be used at top level in ES modules where supported.
- `try/catch` handles a rejected promise when the rejection is awaited inside the `try` block.

### Sequential versus concurrent work

Sequential (second request starts after the first finishes):

```js
const first = await fetch("/api/first");
const second = await fetch("/api/second");
```

Concurrent (both start before waiting):

```js
const [first, second] = await Promise.all([
  fetch("/api/first"),
  fetch("/api/second")
]);
```

Use concurrency when tasks are independent. Remember that `fetch()` resolves for HTTP error statuses such as 404; check `response.ok`.

### Promise combinators

```js
await Promise.all([taskA(), taskB()]);
await Promise.allSettled([taskA(), taskB()]);
await Promise.race([taskA(), taskB()]);
await Promise.any([taskA(), taskB()]);
```

- `Promise.all`: fulfills when all fulfill; rejects when one rejects.
- `Promise.allSettled`: waits for all to settle and returns each outcome.
- `Promise.race`: settles with the first promise to settle.
- `Promise.any`: fulfills with the first fulfilled promise, rejecting with `AggregateError` if all reject.

Other methods: `Promise.resolve(value)`, `Promise.reject(reason)`, and `Promise.withResolvers()` in runtimes that support it.

### Event loop mental model

Understand these terms:

- **Call stack:** current synchronous execution.
- **Task/macrotask:** examples can include timer callbacks and some event callbacks, depending on the host.
- **Microtask:** promise reactions and `queueMicrotask()` callbacks.
- **Event loop:** host scheduling model that coordinates jobs and tasks.
- **Web Worker / worker thread:** separate execution context for work that should not block the main UI thread.

```js
console.log("A");
setTimeout(() => console.log("timer"), 0);
Promise.resolve().then(() => console.log("promise reaction"));
console.log("B");
// Typical order: A, B, promise reaction, timer
```

Exact host scheduling has additional details, but this example illustrates that timers do not run before the current synchronous stack finishes and that promise reactions are commonly queued as microtasks.

### Cancellation with `AbortController`

```js
const controller = new AbortController();

const request = fetch("/api/items", { signal: controller.signal });
controller.abort();

try {
  await request;
} catch (error) {
  if (error.name === "AbortError") {
    console.log("Request was cancelled");
  } else {
    throw error;
  }
}
```

Pass the same abort signal to APIs that support it, and define how your UI should handle cancellation.

# 24. HTTP, fetch, and APIs

An API is a contract for exchanging data. A common web API uses HTTP and JSON.

### HTTP methods

- `GET`: read a resource.
- `POST`: submit/create or trigger an operation.
- `PUT`: replace a resource representation.
- `PATCH`: partially update a resource.
- `DELETE`: delete a resource.

Common status codes include `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `401 Unauthorized` (not authenticated), `403 Forbidden` (not allowed), `404 Not Found`, `409 Conflict`, `422 Unprocessable Content`, `429 Too Many Requests`, and `500 Internal Server Error`.

### GET JSON with `fetch`

```js
async function getProducts() {
  const response = await fetch("/api/products");
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`);
  }
  return response.json();
}
```

### POST JSON

```js
async function createProduct(product) {
  const response = await fetch("/api/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(product)
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Create failed: ${response.status} ${message}`);
  }

  return response.status === 204 ? null : response.json();
}
```

### URL and query parameters

```js
const url = new URL("https://example.com/api/products");
url.searchParams.set("page", "2");
url.searchParams.set("search", "anime");
url.searchParams.get("page");
```

### Headers and response body

```js
const response = await fetch(url, {
  headers: { Accept: "application/json" }
});
response.status;
response.ok;
response.headers.get("content-type");
const text = await response.text();
// Other body readers: response.json(), response.blob(), response.arrayBuffer(), response.formData()
```

A response body is generally consumed once; clone the response first if you need to read it more than once and cloning is valid.

### CORS and credentials

Cross-Origin Resource Sharing (CORS) is a browser-enforced policy controlled by server response headers. A frontend cannot fix a server's incorrect CORS configuration by adding a random request header. Credentials and cookies require deliberate `credentials` settings and correct server policies. CORS is not authentication.

### API design topics to learn

- REST resource naming and predictable methods.
- Pagination, filtering, sorting, and search.
- Input validation and clear error responses.
- Authentication and authorization.
- Rate limiting and request timeouts.
- Idempotency for retry-safe operations where needed.
- Versioning and documentation (for example, OpenAPI).
- Logging and correlation/request IDs.

# 25. DOM, Events, Forms, and Browser APIs

The **Document Object Model (DOM)** is the browser's object representation of an HTML document. DOM APIs are browser APIs, not core ECMAScript syntax.

### Select elements

```js
const heading = document.querySelector("h1");
const allCards = document.querySelectorAll(".card");
const byId = document.getElementById("heading");
```

`querySelector()` returns the first match or `null`; `querySelectorAll()` returns a static NodeList. Check for `null` before using a possibly missing element.

### Change content and classes

```js
heading.textContent = "New title";
heading.setAttribute("aria-live", "polite");
heading.classList.add("active");
heading.classList.remove("hidden");
heading.classList.toggle("selected");
heading.classList.contains("active");
```

Use `textContent` for plain text. Only use `innerHTML` with trusted or properly sanitized markup; inserting untrusted values can create cross-site scripting (XSS) vulnerabilities.

### Create and remove elements

```js
const item = document.createElement("li");
item.textContent = "New item";
document.querySelector("ul")?.append(item);
item.remove();
```

Useful APIs include `append`, `prepend`, `before`, `after`, `replaceWith`, `replaceChildren`, `remove`, and `cloneNode`. Prefer constructing elements and setting text safely rather than concatenating untrusted HTML.

### Event listeners

```js
const button = document.querySelector("button");
button?.addEventListener("click", (event) => {
  console.log("Clicked", event.currentTarget);
});
```

Event listener options include `{ once: true }`, `{ passive: true }`, and `{ capture: true }` where relevant. Remove listeners using the same function reference or an `AbortSignal` when appropriate.

### Event propagation

Events may capture down the tree, target an element, then bubble up. Learn:

- `event.target`: original event target in common bubbling cases.
- `event.currentTarget`: element whose listener is currently running.
- `event.preventDefault()`: prevents the browser's default action when allowed.
- `event.stopPropagation()`: stops propagation to further nodes.

Do not call `stopPropagation()` reflexively; it can interfere with other components.

### Event delegation

```js
const list = document.querySelector("#items");
list?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Element)) return;
  const button = target.closest("button[data-id]");
  if (!button || !list.contains(button)) return;
  console.log("Clicked item", button.dataset.id);
});
```

Delegation handles events from child elements added later, and can reduce the number of listeners.

### Forms and validation

```js
const form = document.querySelector("#signup");
form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const email = String(formData.get("email") ?? "").trim();
  if (!email) {
    console.error("Email is required");
    return;
  }
  // Send validated input to the server. Server-side validation is still required.
});
```

HTML form controls include `input`, `select`, `textarea`, `button`, `FormData`, and native validation APIs such as `checkValidity()`, `reportValidity()`, and `setCustomValidity()`.

### Browser storage

```js
localStorage.setItem("theme", "dark");
const theme = localStorage.getItem("theme");
localStorage.removeItem("theme");
sessionStorage.setItem("draft", "text");

const data = { name: "Asha" };
localStorage.setItem("user", JSON.stringify(data));
const restored = JSON.parse(localStorage.getItem("user") ?? "null");
```

Storage values are strings and can be unavailable or throw in restricted browser contexts. Do not store passwords, secret API keys, or sensitive authentication tokens in web storage without carefully assessing the security model. Any script running in the origin may be able to read it.

### Other browser APIs to recognize

- `window`, `document`, `navigator`, `location`, `history`.
- `URL`, `URLSearchParams`, `URLPattern` where supported.
- `setTimeout`, `setInterval`, `requestAnimationFrame`.
- `IntersectionObserver`, `ResizeObserver`, `MutationObserver`.
- `AbortController`, `AbortSignal`.
- `File`, `Blob`, `FileReader` (legacy in some uses), `FormData`, object URLs.
- `Canvas` and WebGL for graphics.
- `WebSocket` and `EventSource` for persistent connections/server-sent events.
- `Web Workers` for CPU-heavy work off the UI thread.
- `Clipboard`, `Geolocation`, notifications, media, and other APIs subject to permissions and secure-context requirements.
- `IndexedDB` for larger structured client-side data.
- Accessibility concepts: semantic HTML, keyboard support, focus management, accessible labels, ARIA only where needed, and readable error messages.

Always check support, permissions, HTTPS requirements, and user-consent expectations for platform APIs.

# 26. Node.js Fundamentals

Node.js executes JavaScript outside the browser. It exposes APIs such as filesystem, networking, process management, streams, and cryptography.

### Read environment and process information

```js
console.log(process.version);
console.log(process.platform);
console.log(process.cwd());
console.log(process.argv);
console.log(process.env.NODE_ENV);
```

Keep secrets in environment variables or a secret manager—not source control. Validate required environment variables at application startup.

### ES module filesystem example

```js
import { readFile, writeFile } from "node:fs/promises";

const text = await readFile("./input.txt", "utf8");
await writeFile("./output.txt", text.toUpperCase(), "utf8");
```

### Paths

```js
import path from "node:path";

path.join("data", "users.json");
path.resolve("data", "users.json");
path.basename("/tmp/report.txt");
path.extname("report.txt");
```

Use `node:path` rather than manually concatenating path separators. When accepting a user-supplied path, validate it to prevent path traversal and unauthorized file access.

### Working with directories

```js
import { mkdir, readdir, stat } from "node:fs/promises";

await mkdir("./data", { recursive: true });
const files = await readdir("./data");
const info = await stat("./data");
```

Node.js built-ins have separate modules such as `node:fs`, `node:path`, `node:os`, `node:crypto`, `node:http`, `node:stream`, `node:events`, `node:util`, `node:url`, `node:assert`, `node:test`, `node:worker_threads`, `node:child_process`, and `node:timers/promises`.

### EventEmitter

```js
import { EventEmitter } from "node:events";

const events = new EventEmitter();
events.on("userCreated", (user) => console.log(user.id));
events.emit("userCreated", { id: 1 });
```

EventEmitter is synchronous when emitting listeners; listeners can start asynchronous operations, but the emitter does not automatically wait for promises returned by listeners.

### Streams

Streams process data in chunks and are useful for large files or network data. Main categories: readable, writable, duplex, and transform. Learn backpressure and `stream.pipeline()` rather than loading every large file into memory.

### Child processes and worker threads

`node:child_process` runs external processes; `node:worker_threads` can run JavaScript in parallel threads. Treat user-supplied commands and arguments as untrusted. Avoid shell command construction with untrusted input; use safe argument arrays and strict validation.

### CommonJS vs ES modules

CommonJS commonly uses `require()` and `module.exports`. ES modules use `import` and `export`. Prefer one clear module system in a project and understand the `package.json` and file-extension rules.

# 27. npm and Project Configuration

### Common npm commands

```bash
npm init -y
npm install express
npm install --save-dev eslint
npm uninstall package-name
npm run dev
npm test
npm audit
```

`npm install` normally uses the dependency manifest and lockfile. Commit `package.json` and the relevant lockfile (`package-lock.json`) for reproducible installs. Do not commit `node_modules/` or `.env` files containing secrets.

### Basic `package.json`

```json
{
  "name": "my-app",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "node src/server.js",
    "dev": "node --watch src/server.js",
    "test": "node --test"
  },
  "dependencies": {},
  "devDependencies": {}
}
```

The `"type": "module"` setting makes `.js` files in that package scope use ES modules unless overridden by extension/package rules. Check Node.js support before choosing runtime-specific flags or scripts.

### Environment variables

```js
const port = Number(process.env.PORT ?? 3000);
if (!Number.isInteger(port) || port < 1 || port > 65535) {
  throw new Error("PORT must be a valid TCP port");
}
```

A `.env` file is often loaded through a package or runtime-specific feature. Never assume it is automatically loaded in every Node.js setup. Add secret-bearing files to `.gitignore` and use `.env.example` for non-secret variable names.

### Typical project structure

```text
my-app/
  src/
    app.js
    server.js
    routes/
    controllers/
    services/
    repositories/
    middleware/
    validators/
  tests/
  .env                 # local secret values; do not commit
  .env.example         # safe example keys; commit if useful
  .gitignore
  package.json
  package-lock.json
```

# 28. Building a Backend with Express

Express is a third-party web framework for Node.js, not part of the JavaScript language.

### Minimal server

Install Express:

```bash
npm install express
```

`src/server.js`:

```js
import express from "express";

const app = express();
const port = Number(process.env.PORT ?? 3000);

app.use(express.json({ limit: "100kb" }));

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.get("/api/greetings/:name", (req, res) => {
  res.json({ message: `Hello, ${req.params.name}` });
});

app.use((req, res) => {
  res.status(404).json({ error: "Not found" });
});

app.use((error, req, res, next) => {
  console.error(error);
  if (res.headersSent) return next(error);
  res.status(500).json({ error: "Internal server error" });
});

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
```

### Routes and HTTP methods

```js
app.get("/api/products", listProducts);
app.get("/api/products/:id", getProduct);
app.post("/api/products", createProduct);
app.patch("/api/products/:id", updateProduct);
app.delete("/api/products/:id", deleteProduct);
```

The handlers above must be defined, validate inputs, and use the persistence layer. Use `express.Router()` to split routes into modules.

### Middleware

Middleware receives `req`, `res`, and `next`. It can inspect or modify the request/response, end the response, or pass control onward.

```js
function requestLogger(req, res, next) {
  console.log(req.method, req.path);
  next();
}
app.use(requestLogger);
```

Middleware order matters. Register parsing and security middleware before routes as appropriate, not-found handling after routes, and error middleware last.

### Request data

- `req.params`: route parameters, e.g. `/users/:id`.
- `req.query`: URL query parameters.
- `req.body`: parsed body if suitable middleware is installed.
- `req.headers`: request headers.

Everything from a client is untrusted. Validate type, size, shape, and permissions before use. Do not trust a user ID or role just because it was sent in the request body.

### Service and controller separation

A maintainable request path often looks like:

`Router → Middleware → Controller → Service → Repository/Database → Response`

- Router: method/path mapping.
- Middleware: authentication, authorization, request IDs, logging, rate limits.
- Controller: HTTP input/output handling.
- Service: business logic.
- Repository/data-access layer: database operations.
- Validator: checks incoming parameters and body shape.

Do not put all application logic into one route callback as the project grows.

# 29. Databases and Data Access

JavaScript can work with relational databases such as PostgreSQL/MySQL/SQLite or document databases such as MongoDB. The database is separate from the JavaScript language.

### Core database concepts

Learn:

- Tables/collections, rows/documents, columns/fields.
- Primary keys and foreign keys.
- Relationships: one-to-one, one-to-many, many-to-many.
- Constraints, indexes, uniqueness, and nullability.
- CRUD: create, read, update, delete.
- SQL `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `JOIN`, `WHERE`, `ORDER BY`, `GROUP BY`.
- Transactions, isolation, concurrency, migrations, backups, and connection pooling.
- ORM vs query builder vs parameterized SQL.

### Parameterized SQL example with PostgreSQL (`pg` package)

```js
import pg from "pg";
const { Pool } = pg;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

export async function findUserByEmail(email) {
  const result = await pool.query(
    "SELECT id, email, display_name FROM users WHERE email = $1",
    [email]
  );
  return result.rows[0] ?? null;
}
```

Use parameterized queries; never build SQL by concatenating untrusted values. Configure connection strings and credentials outside source code. Close pools cleanly when shutting down if the runtime requires it.

### Data access rules

- Validate before persisting.
- Enforce authorization on the server for every protected operation.
- Use transactions for related changes that must succeed or fail together.
- Add migrations instead of manually changing production schemas without tracking.
- Add indexes for measured query needs; indexes also have write and storage costs.
- Paginate large result sets.
- Do not expose password hashes, reset tokens, internal flags, or private columns in API output.

# 30. Authentication, Authorization, and Security

**Authentication** answers “Who are you?” **Authorization** answers “What are you allowed to do?” They are different checks.

### Topics to learn

- Password hashing using a purpose-built password hashing algorithm and reputable library.
- Session cookies and session stores.
- Secure cookie flags: `HttpOnly`, `Secure`, and appropriate `SameSite` policy.
- Access tokens and refresh-token lifecycle if using tokens.
- Role-based and resource/owner-based authorization.
- Server-side validation and output encoding.
- CSRF risks for cookie-authenticated applications.
- XSS, SQL injection, path traversal, SSRF, request smuggling, and insecure file uploads.
- CORS, Content Security Policy, TLS/HTTPS, rate limiting, and security headers.
- Dependency updates, audits, secrets management, backups, and logging.

### Essential security rules

1. Never trust frontend-only authorization. Check permission on the server for every protected request.
2. Never store plaintext passwords. Use a vetted password-hashing library with safe parameters; do not invent your own hash scheme.
3. Do not hard-code API secrets in code or ship private server keys to the browser.
4. Use parameterized database queries or safe ORM methods.
5. Set maximum request body/file sizes and validate uploads, MIME/content, and storage permissions.
6. Avoid rendering untrusted HTML. Prefer `textContent`, context-aware escaping, and vetted sanitization where HTML is truly required.
7. Avoid `eval()` and `new Function()` for external input.
8. Use HTTPS in production and secure cookie settings appropriate to your authentication model.
9. Keep packages current, review security notices, and remove unused dependencies.
10. Return generic production error messages; keep detailed diagnostic data in access-controlled logs.

### Password hash concept (not a home-made implementation)

Use the selected library's documented API, with unique salts and settings supported by that library. A conceptual flow is:

```js
// Pseudocode only: choose and follow a maintained password-hashing library's API.
const passwordHash = await passwordHasher.hash(password);
const isValid = await passwordHasher.verify(passwordHash, candidatePassword);
```

Do not replace `passwordHasher` with plain SHA-256 or a custom algorithm for password storage.

# 31. Testing, Debugging, and Code Quality

### Debugging basics

```js
console.log("value", value);
console.assert(2 + 2 === 4, "Math check failed");
debugger; // pauses in an attached debugger
```

Also learn browser DevTools, Node.js inspector, breakpoints, watch expressions, stack traces, source maps, and how to create a minimal reproducible example.

### Node.js built-in test runner

`math.js`:

```js
export const add = (a, b) => a + b;
```

`math.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { add } from "./math.js";

test("add sums two numbers", () => {
  assert.equal(add(2, 3), 5);
});
```

Run with:

```bash
node --test
```

### Test types

- Unit tests: individual functions or modules.
- Integration tests: multiple components, such as a route and database.
- End-to-end tests: a complete user journey through the application.
- Regression tests: prevent a known bug from returning.
- Load/performance tests: validate behaviour under expected traffic.
- Accessibility tests: keyboard flow, semantic structure, focus, and assistive technology support.

### Test quality

Test normal cases, edge cases, invalid input, permission failures, network errors, empty results, concurrency, and regressions. Tests should be reliable and avoid depending on accidental timing. Mock only where it provides real value; integration tests should still exercise important real boundaries.

### Linting and formatting

Use a formatter such as Prettier and a linter such as ESLint. Configure rules consistently across the project, and add scripts such as `lint`, `format`, `typecheck` (if using TypeScript), and `test`. Linting finds many common problems but is not a substitute for tests and code review.

# 32. Performance and Memory

### Fundamentals

- Choose clear algorithms and data structures first; learn Big O notation (`O(1)`, `O(log n)`, `O(n)`, `O(n log n)`, `O(n²)`).
- Avoid repeated expensive work inside loops when it can be safely reused.
- Use pagination/streaming for large data rather than loading everything at once.
- Avoid blocking the browser's main thread with heavy synchronous work.
- Use Web Workers or Node.js worker threads for appropriate CPU-heavy tasks.
- Profile before optimizing. Use browser Performance tools, memory snapshots, and Node.js profiling tools.
- Understand memory leaks from retained DOM nodes, global references, timers, event listeners, and closures.

### Debouncing and throttling

Debounce waits for calls to pause; throttle limits how often a function runs. Here is a simple debounce:

```js
function debounce(callback, delayMs) {
  let timerId;
  return function (...args) {
    clearTimeout(timerId);
    timerId = setTimeout(() => callback.apply(this, args), delayMs);
  };
}
```

For UI code, consider cleanup and cancellation when the component or page is no longer active.

### Avoid fragile optimization

Do not assume `for` loops are always faster than array methods or that caching every value improves performance. Measure the actual bottleneck on representative workloads.

# 33. Modern JavaScript Syntax Checklist

Recognize and practise these commonly used modern features:

```js
// let and const
const user = { name: "Asha" };

// Arrow functions
const double = n => n * 2;

// Template literals
const message = `Hello, ${user.name}`;

// Destructuring
const { name } = user;
const [first, second] = [10, 20];

// Default parameters
function greet(who = "Guest") { return `Hi, ${who}`; }

// Rest and spread
function addAll(...numbers) { return numbers.reduce((a, b) => a + b, 0); }
const expanded = [...[1, 2], 3];
const merged = { ...user, active: true };

// Optional chaining and nullish coalescing
const city = user.profile?.city ?? "Unknown";

// Object shorthand and computed keys
const key = "role";
const object = { name, [key]: "member" };

// Classes and private fields
class Example { #value = 1; getValue() { return this.#value; } }

// Modules
import { add } from "./math.js";
export const version = 1;

// Promises and async/await
const response = await fetch("/api/data");

// Map and Set
const uniqueIds = new Set([1, 1, 2]);
const labels = new Map([["ok", true]]);

// Dynamic import
const module = await import("./feature.js");

// Promise combinators
const results = await Promise.all([taskA(), taskB()]);

// Logical assignment
let config = {};
config.timeout ??= 5000;
config.enabled ||= true;
config.retries &&= 3;

// Numeric separators
const billion = 1_000_000_000;

// BigInt
const largeId = 12345678901234567890n;

// Async iteration
for await (const item of asyncIterable) { console.log(item); }

// Structured clone for supported data
const cloned = structuredClone({ nested: { value: 1 } });
```

Other features and topics to recognize include optional catch binding (`catch {}`), object rest properties, `Promise.allSettled`, `Promise.any`, dynamic import, `import.meta`, top-level `await` in modules, `Error` cause (`new Error("failed", { cause })` in supporting runtimes), private fields/methods, static class fields, static initialization blocks, Unicode property escapes in regex, and new non-mutating array methods. Availability depends on the runtime version.

# 34. Common Patterns and Best Practices

### Guard clauses and validation

```js
function calculatePrice(price, quantity) {
  if (!Number.isFinite(price) || price < 0) {
    throw new TypeError("price must be a non-negative finite number");
  }
  if (!Number.isInteger(quantity) || quantity < 0) {
    throw new TypeError("quantity must be a non-negative integer");
  }
  return price * quantity;
}
```

### Immutable update of an object

```js
const updatedUser = { ...user, name: "Maya" };
```

### Immutable array update

```js
const updatedItems = items.map(item =>
  item.id === targetId ? { ...item, done: true } : item
);
```

### Separate concerns

Avoid mixing display, business logic, persistence, and network access in one function. Prefer small modules with clear responsibilities and explicit input/output contracts.

### Common mistakes to avoid

- Using `==` unintentionally instead of `===`.
- Assuming `const` makes an object immutable.
- Assuming spread syntax performs a deep copy.
- Using `for...in` to iterate array values.
- Forgetting that `sort()` mutates and sorts by string conversion by default.
- Forgetting to check `response.ok` after `fetch()`.
- Assuming a promise rejection is caught when no `catch` or `try/catch` handles it.
- Writing `array.forEach(async item => ...)` and expecting it to wait for all callbacks.
- Using `await` sequentially for independent work when concurrency is appropriate.
- Trusting frontend validation as the only server-side validation.
- Concatenating untrusted input into SQL or shell commands.
- Putting secrets in browser code or Git.
- Inserting untrusted strings via `innerHTML`.
- Building one enormous file instead of modular code.
- Shipping without tests, logs, validation, and error handling.

### Async `forEach` trap

Avoid this when you need to wait for every task:

```js
// Usually wrong for waiting on async work:
items.forEach(async item => {
  await saveItem(item);
});
```

Sequential alternative:

```js
for (const item of items) {
  await saveItem(item);
}
```

Concurrent alternative:

```js
await Promise.all(items.map(item => saveItem(item)));
```

Choose concurrency based on API limits, ordering requirements, and memory pressure.

# 35. Full-Stack Learning Order and Projects

The roadmap below connects JavaScript concepts to practical full-stack work. It is an approximate sequence, not a deadline.

## Stage 1 — Core language

Learn variables, primitive types, operators, conditions, loops, functions, scope, arrays, objects, destructuring, spread/rest, errors, modules, and debugging.

**Practice:** calculator, number guessing game, grade calculator, expense summary, array/object data processor.

## Stage 2 — Modern JavaScript and asynchronous work

Learn promises, `async`/`await`, `fetch`, JSON, URL/query parameters, error handling, cancellation, event loop basics, and module imports.

**Practice:** API user search, paginated product list, weather dashboard using a public API, loading/error/empty states.

## Stage 3 — Browser programming

Learn semantic HTML and CSS alongside DOM selection, events, forms, client-side validation, local storage, accessibility, responsive layouts, and safe rendering.

**Practice:** to-do list with filters, form validation, searchable anime catalogue, notes app with persistence.

## Stage 4 — Frontend framework

Choose a framework such as React after core JavaScript is comfortable. Learn components, props, state, effects/lifecycle, routing, forms, data fetching, error/loading states, accessibility, and build tooling. Framework syntax is additional knowledge; it does not replace JavaScript fundamentals.

**Practice:** dashboard with search/filter/sort, reusable components, API integration, protected-looking UI backed by real server authorization (not client-only checks).

## Stage 5 — Node.js and backend basics

Learn the Node runtime, modules, npm, environment variables, files and paths, HTTP, Express, middleware, routes, request validation, status codes, logging, error handling, and testing.

**Practice:** REST API for users/products/tasks with input validation and predictable errors.

## Stage 6 — Database

Learn SQL or document-database fundamentals, schema design, indexes, relations, migrations, parameterized queries, transactions, pooling, and data-access separation.

**Practice:** connect your API to a database, then implement pagination, filtering, updates, deletion, and owner-scoped access.

## Stage 7 — Auth and production readiness

Learn sessions or token-based flows, password hashing with a maintained library, authorization policies, CORS, CSRF/XSS/SQL injection protection, rate limits, secrets, HTTPS, uploads, logging, deployment, backups, CI, and monitoring.

**Practice:** login/register, role-checked admin routes, profile updates, tests for forbidden access, deployed staging environment.

## Stage 8 — Professional workflow

Learn Git, code reviews, automated formatting/linting, unit/integration/e2e tests, environment separation, API documentation, accessibility, performance profiling, and incident debugging.

**Suggested portfolio projects:**

1. Responsive personal portfolio with accessible navigation and a working contact flow.
2. Searchable catalogue with API integration, sorting, pagination, and saved favourites.
3. Full-stack task manager with users, database persistence, authorization, validation, and tests.
4. E-commerce prototype with products, cart, orders, database transactions, and protected admin endpoints.
5. Real-time chat or activity feed using WebSocket/SSE, authentication, rate limits, and reconnect handling.

---

# 36. Quick Syntax Reference

| Need | Syntax |
|---|---|
| Declare a binding | `const value = 10;` |
| Reassign a binding | `let value = 10; value = 20;` |
| Interpolate a string | `` `Hello, ${name}` `` |
| Condition | `if (condition) { ... } else { ... }` |
| Select a case | `switch (value) { case "x": ...; break; default: ... }` |
| Loop values | `for (const item of items) { ... }` |
| Loop object keys | `for (const key in object) { ... }` |
| Declare function | `function add(a, b) { return a + b; }` |
| Arrow function | `const add = (a, b) => a + b;` |
| Default parameter | `function greet(name = "Guest") { ... }` |
| Rest parameters | `function collect(...args) { ... }` |
| Object destructuring | `const { name } = user;` |
| Array destructuring | `const [first, second] = list;` |
| Spread array | `const copy = [...items];` |
| Spread object | `const copy = { ...object };` |
| Optional chaining | `user?.profile?.name` |
| Nullish fallback | `value ?? fallback` |
| Array transformation | `items.map(item => ...)` |
| Array filter | `items.filter(item => ...)` |
| Array aggregation | `items.reduce((acc, item) => ..., initial)` |
| Catch an error | `try { ... } catch (error) { ... }` |
| Class | `class User { constructor(name) { this.name = name; } }` |
| Named export | `export function work() {}` |
| Named import | `import { work } from "./work.js";` |
| Async function | `async function load() { return await task(); }` |
| Promise chain | `task().then(handle).catch(handleError);` |
| Fetch JSON | `const r = await fetch(url); if (!r.ok) throw new Error(); const data = await r.json();` |
| Add event | `element.addEventListener("click", handler);` |
| Select DOM element | `document.querySelector(".card")` |
| Serialize JSON | `JSON.stringify(value)` |
| Parse JSON | `JSON.parse(text)` |
| Map key/value | `map.set(key, value); map.get(key);` |
| Set uniqueness | `[...new Set(items)]` |
| Throw an error | `throw new Error("Something failed");` |
| Run Node file | `node app.js` |
| Install package | `npm install package-name` |
| Run npm script | `npm run dev` |
| Run Node tests | `node --test` |

# 37. Official Learning References

Use these primary references to verify exact syntax, compatibility, and details that change over time:

- **MDN JavaScript Guide:** https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide
- **MDN JavaScript Reference:** https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference
- **ECMAScript language specification:** https://tc39.es/ecma262/
- **TC39 proposals and status:** https://github.com/tc39/proposals
- **Node.js documentation:** https://nodejs.org/docs/latest/api/
- **npm documentation:** https://docs.npmjs.com/
- **Express documentation:** https://expressjs.com/
- **MDN Web APIs:** https://developer.mozilla.org/en-US/docs/Web/API
- **MDN HTTP overview:** https://developer.mozilla.org/en-US/docs/Web/HTTP
- **OWASP Cheat Sheet Series:** https://cheatsheetseries.owasp.org/

---

## Final Checklist

You are ready to move beyond JavaScript fundamentals when you can, without copying a tutorial:

- Explain primitive types, references, equality, truthiness, scope, hoisting, and closures.
- Write and test functions using parameters, defaults, rest, callbacks, and arrow syntax.
- Transform arrays and objects without accidentally mutating shared data.
- Use classes/prototypes where they make sense and understand module boundaries.
- Handle errors, promises, async/await, cancellation, and concurrent operations.
- Build accessible browser interactions and make safe HTTP requests.
- Create a Node.js server with routes, validation, middleware, logging, and consistent errors.
- Use a database safely with parameterized queries, transactions where needed, and migrations.
- Implement authentication and server-side authorization without trusting the client.
- Add tests, linting, formatting, environment configuration, and secure deployment practices.

**Learning principle:** You do not need to memorize every built-in method. Learn the concepts, practise the frequently used syntax, understand the documentation, and build projects that force you to apply them.
