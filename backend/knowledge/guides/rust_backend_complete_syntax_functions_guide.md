# Rust Backend Development: Complete Syntax, Functions, and Web API Guide
## Rust Language, Axum, Tokio, SQLx, Database Access, Authentication, Testing, and Deployment

> **Purpose:** A comprehensive reference for learning Rust for backend and full-stack application development, from core language syntax to production-oriented HTTP APIs.
>
> **Version baseline:** This guide uses the Rust 2024 edition, with examples compatible with modern stable Rust. Rust 1.99.1 was announced on October 15, 2026; check the official release feed for the exact currently installed toolchain. Web-backend examples use Axum 0.8.x and Tokio 1.x patterns. The current Axum docs identify Axum 0.8.9, and SQLx documentation identifies SQLx 0.9.0. Crates release independently, so confirm the exact compatible versions and feature flags before building.
>
> **Scope note:** Rust's standard library and backend ecosystem contain a very large number of functions, traits, types, macros, and APIs. “100% of every syntax and function” is not a finite, stable list, especially across all third-party crates and future releases. This guide covers core Rust syntax, ownership and type-system concepts, common standard-library APIs, and the major patterns for building real backend systems with Axum/Tokio, SQLx, security, testing, and deployment. The official versioned documentation linked at the end is the source of truth for exact signatures.

---

## Table of Contents

### Part I — Rust Language
1. Rust Backend Overview
2. Install Rust and Create a Project
3. Cargo and `Cargo.toml`
4. Source File and Module Structure
5. Comments, Statements, and Expressions
6. Variables, Constants, and Shadowing
7. Primitive Types and Type Conversion
8. Strings, Slices, and Formatting
9. Operators
10. Conditions and Loops
11. Functions and Methods
12. Ownership, Move, Copy, and Drop
13. Borrowing and References
14. Lifetimes
15. Structs and Tuple Structs
16. Enums and Pattern Matching
17. `Option`, `Result`, and Error Propagation
18. Collections: Vec, String, HashMap, HashSet
19. Iterators and Closures
20. Generics and Trait Bounds
21. Traits and Trait Objects
22. Modules, Crates, and Visibility
23. Macros and Attributes
24. Smart Pointers
25. Interior Mutability and Concurrency
26. Async/Await and Futures
27. Files, JSON, and Environment Variables
28. Testing, Documentation, and Code Quality

### Part II — Rust Backend Ecosystem
29. Choosing a Web Framework
30. Axum Setup and First Server
31. Routing and HTTP Methods
32. Request Extractors: Path, Query, JSON, Headers
33. Request and Response Types
34. Shared Application State
35. Validation and DTO Design
36. Error Handling for HTTP APIs
37. Middleware, CORS, and Tracing
38. Configuration and Secrets
39. SQL Databases with SQLx
40. CRUD API with Axum and SQLx
41. Database Migrations and Transactions
42. Authentication and Authorization
43. Password Hashing and Token Design
44. Rate Limiting, Timeouts, and Security
45. File Uploads and Downloads
46. External HTTP APIs
47. Background Jobs and Message Queues
48. WebSockets and Server-Sent Events
49. Redis and Caching
50. MongoDB Integration Overview
51. Serialization and API Documentation
52. Testing Backend APIs
53. Performance and Observability
54. Docker and Deployment
55. Actix Web and Rocket Overview
56. Common Rust Backend Crates
57. Common Commands and API Quick Reference
58. Practice Projects and Learning Roadmap
59. Official Documentation

---

# PART I — RUST LANGUAGE

# 1. Rust Backend Overview

Rust is a compiled systems programming language designed around memory safety, performance, and explicit handling of failures. It is used for command-line tools, services, network systems, data-intensive backends, and infrastructure software.

A typical backend architecture:

```text
Browser / React / Angular
        |
        | HTTP + JSON
        v
Router / Controller / Handler
        |
        +--> Validation / Authentication / Authorization
        |
        +--> Service layer (business rules)
        |
        +--> Repository / Database client
        |
        +--> External APIs / Queue / Cache
        |
        v
Database / External services
```

Rust is a language, not a web framework. Common backend building blocks include:
- **Axum:** HTTP routing and request handling, built around Tokio and Tower.
- **Tokio:** asynchronous runtime, networking, timers, tasks, and synchronization.
- **Serde:** serialization/deserialization framework.
- **SQLx:** async SQL toolkit supporting PostgreSQL, MySQL/MariaDB, and SQLite.
- **Tower / tower-http:** reusable service middleware, tracing, CORS, compression, timeout layers.
- **Tracing:** structured diagnostics.
- **Thiserror / anyhow:** common error-handling libraries.
- **Argon2-compatible crates and trusted token libraries:** authentication building blocks.
- **Diesel / SeaORM:** ORM alternatives.
- **MongoDB Rust driver:** document-database access.

No single backend stack is always best. This guide primarily uses **Axum + Tokio + Serde + SQLx** because it provides typed HTTP handlers, explicit async I/O, and SQL access without requiring a full ORM.

---

# 2. Install Rust and Create a Project

Install Rust using `rustup` from the official Rust installation instructions. Verify:

```bash
rustc --version
cargo --version
rustup show
```

Update stable:

```bash
rustup update stable
```

Create a project:

```bash
cargo new rust_backend
cd rust_backend
cargo run
```

Create a library project:

```bash
cargo new shared_types --lib
```

Common commands:

```bash
cargo check
cargo build
cargo build --release
cargo run
cargo test
cargo doc --open
cargo fmt
cargo clippy
```

Rust versions use editions. Modern new projects commonly use:

```toml
edition = "2024"
```

Rust editions collect language changes while preserving compatibility rules for existing editions. The 2024 edition is stable; consult the Edition Guide before migrating an older codebase.

---

# 3. Cargo and `Cargo.toml`

Cargo manages packages, dependencies, builds, tests, and workspaces.

Minimal project manifest:

```toml
[package]
name = "rust_backend"
version = "0.1.0"
edition = "2024"

[dependencies]
```

Add a crate:

```bash
cargo add serde --features derive
cargo add serde_json
```

A backend dependency set for the examples later in this file:

```toml
[package]
name = "rust_backend"
version = "0.1.0"
edition = "2024"

[dependencies]
axum = "0.8.9"
tokio = { version = "1", features = ["macros", "rt-multi-thread", "net", "signal", "time"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "2"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
tower-http = { version = "0.6", features = ["trace", "cors", "compression-gzip", "timeout"] }
dotenvy = "0.15"
sqlx = { version = "0.9.0", default-features = false, features = ["runtime-tokio", "tls-rustls-ring", "postgres", "macros", "migrate", "chrono", "uuid"] }
uuid = { version = "1", features = ["serde", "v4"] }
chrono = { version = "0.4", features = ["serde"] }
```

Notes:
- Crate versions and feature names can change. This feature set is an example for PostgreSQL over Tokio with Rustls; validate it against the selected SQLx release and your target platform.
- You do not need every dependency for every project. Start small, then add crates as needed.
- `Cargo.lock` records exact resolved versions for an application binary and should normally be committed for reproducible builds.
- Avoid using unreviewed dependencies in security-sensitive code.

Useful Cargo commands:

```bash
cargo tree
cargo update
cargo update -p serde
cargo add axum
cargo remove crate_name
cargo test
cargo test test_name
cargo run --release
cargo check --all-targets
cargo clippy --all-targets --all-features
cargo fmt --all
cargo audit
```

`cargo audit` requires the relevant auditing tool to be installed. It is not built into Cargo in all setups.

---

# 4. Source File and Module Structure

Hello world (`src/main.rs`):

```rust
fn main() {
    println!("Hello, Rust!");
}
```

Library entry point (`src/lib.rs`) is used to define reusable library code. A binary crate normally has `src/main.rs`; a library crate has `src/lib.rs`; a project can contain both.

Typical backend structure:

```text
rust_backend/
├── Cargo.toml
├── Cargo.lock
├── .env.example
├── migrations/
│   └── 0001_create_products.sql
└── src/
    ├── main.rs
    ├── config.rs
    ├── error.rs
    ├── models/
    │   └── product.rs
    ├── routes/
    │   └── products.rs
    ├── services/
    │   └── product_service.rs
    └── repository/
        └── product_repository.rs
```

A module can be declared with `mod` and referenced with paths. Public members must use `pub` or an appropriate visibility modifier when accessed outside their module.

```rust
mod config;
pub mod routes;
```

Rust source structure, module paths, and visibility have rules beyond simple file naming; use the module system deliberately to keep internal implementation private.

---

# 5. Comments, Statements, and Expressions

Comments:

```rust
// Single-line comment

/*
   Multi-line comment.
*/

/// Documentation comment for an item.
/// Appears in rustdoc output.
pub fn greet() {}
```

Inner documentation comments include `//!` for the enclosing module/crate.

Rust distinguishes statements from expressions. Many blocks return their final expression when it has no trailing semicolon:

```rust
let result = {
    let a = 10;
    let b = 20;
    a + b
};

println!("{result}");
```

Adding a semicolon changes an expression into a statement returning unit `()` in this context. This is a frequent source of return-type mistakes.

---

# 6. Variables, Constants, and Shadowing

Variables are immutable by default:

```rust
let count = 10;
// count = 11; // Does not compile
```

Mutable binding:

```rust
let mut count = 10;
count = 11;
```

Constant:

```rust
const MAX_CONNECTIONS: usize = 100;
```

Constants require an explicit type and a compile-time evaluable value. `static` declares a static item and has distinct rules, especially for mutable statics.

Shadowing:

```rust
let value = "42";
let value: i32 = value.parse().expect("valid integer");
```

Shadowing creates a new binding and can use a different type; it is not the same as assigning to a mutable variable.

---

# 7. Primitive Types and Type Conversion

Common primitive types:
- Signed integers: `i8`, `i16`, `i32`, `i64`, `i128`, `isize`
- Unsigned integers: `u8`, `u16`, `u32`, `u64`, `u128`, `usize`
- Floating point: `f32`, `f64`
- Boolean: `bool`
- Unicode scalar value: `char`
- Unit type: `()`

Examples:

```rust
let count: i32 = 42;
let large: u64 = 10_000_000;
let ratio: f64 = 0.75;
let active: bool = true;
let letter: char = 'R';
let nothing: () = ();
```

Type conversion:

```rust
let a: i32 = 10;
let b: i64 = i64::from(a);
let c = a as i64;
```

Use `as` carefully; narrowing numeric conversions may truncate or wrap according to Rust's rules. Parsing:

```rust
let number: i32 = "123".parse()?;
```

This requires the surrounding function to return a compatible `Result`. Explicit numeric types help avoid inference ambiguity.

Rust has no implicit general numeric coercion like some dynamic languages. You may need explicit conversion between related types.

---

# 8. Strings, Slices, and Formatting

Rust's common string types:
- `String`: owned, growable UTF-8 string.
- `&str`: borrowed string slice.

```rust
let owned: String = String::from("Rust backend");
let borrowed: &str = "API";

let combined = format!("{owned} {borrowed}");
println!("{combined}");
```

Common string operations:

```rust
let text = String::from("  Hello Rust  ");

text.len();             // UTF-8 bytes, not necessarily user-perceived characters
text.is_empty();
text.trim();
text.to_lowercase();
text.to_uppercase();
text.contains("Rust");
text.starts_with("  H");
text.replace("Rust", "Axum");
text.split_whitespace().collect::<Vec<_>>();
```

String methods often return a value/slice; `String` is UTF-8, so arbitrary byte-index slicing can panic if indices are not character boundaries. Use `.chars()`, `.char_indices()`, or a Unicode-aware library when working with graphemes/user-perceived characters.

Formatting macros:

```rust
let user = "Asha";
let score = 98.5;

println!("User: {user}");
println!("User: {}", user);
println!("Score: {:.1}", score);
println!("Debug: {:?}", user);
println!("Pretty debug: {:#?}", vec![1, 2, 3]);
```

Important macros include `format!`, `print!`, `println!`, `eprint!`, `eprintln!`, `write!`, `writeln!`, `format_args!`.

---

# 9. Operators

Arithmetic:
- `+`, `-`, `*`, `/`, `%`

Comparisons:
- `==`, `!=`, `<`, `<=`, `>`, `>=`

Logical:
- `&&`, `||`, `!`

Bitwise:
- `&`, `|`, `^`, `!`, `<<`, `>>`

Assignments:
- `=`, `+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `<<=`, `>>=`

Borrow/deref:
- `&value`: borrow
- `&mut value`: mutable borrow
- `*reference`: dereference in applicable contexts

Range syntax:
- `start..end`: end-exclusive
- `start..=end`: end-inclusive
- `..end`, `start..`, `..=end`, `..`: range forms

Rust does not have an implicit truthiness system; conditions must evaluate to `bool`.

---

# 10. Conditions and Loops

## `if` / `else`

```rust
let score = 85;

let grade = if score >= 90 {
    "A"
} else if score >= 75 {
    "B"
} else {
    "C"
};
```

All branches of an `if` expression must return compatible types.

## `loop`

```rust
let mut attempts = 0;

let result = loop {
    attempts += 1;
    if attempts == 3 {
        break attempts;
    }
};
```

`break` can return a value from a `loop`.

## `while`

```rust
let mut count = 0;
while count < 5 {
    count += 1;
}
```

## `for`

```rust
for number in 0..5 {
    println!("{number}");
}
```

Loop labels, `break`, and `continue` are supported. Prefer clear iterator loops when they express the intention more simply.

## `match`

```rust
let status = 200;

let message = match status {
    200 => "OK",
    201 => "Created",
    400..=499 => "Client error",
    500..=599 => "Server error",
    _ => "Other",
};
```

`match` is exhaustive unless a wildcard/catch-all pattern covers the remaining cases. It supports enum variants, tuples, structs, guards, and destructuring patterns.

---

# 11. Functions and Methods

Function:

```rust
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

The last expression is the return value. Explicit return:

```rust
fn multiply(a: i32, b: i32) -> i32 {
    return a * b;
}
```

Unit return:

```rust
fn log_message(message: &str) {
    println!("{message}");
}
```

Generic function:

```rust
fn identity<T>(value: T) -> T {
    value
}
```

Methods are implemented in `impl` blocks:

```rust
struct User {
    name: String,
}

impl User {
    fn new(name: impl Into<String>) -> Self {
        Self { name: name.into() }
    }

    fn name(&self) -> &str {
        &self.name
    }
}
```

Receivers:
- `&self`: shared borrow of the instance.
- `&mut self`: mutable borrow.
- `self`: takes ownership.
- Associated functions without a receiver, often used as constructors.

Rust supports function pointers (`fn` types), closures, generic methods, trait methods, and async functions. There is no method overloading by argument types in the same manner as Java/C++; use different names, traits, generics, or enums.

---

# 12. Ownership, Move, Copy, and Drop

Ownership is a core Rust feature:
- Each value has one owner.
- When the owner goes out of scope, its value is dropped.
- Moving a non-`Copy` value usually transfers ownership.
- Borrowing allows temporary access without taking ownership.
- The compiler enforces rules intended to prevent use-after-free and data races in safe Rust.

Move example:

```rust
let first = String::from("hello");
let second = first;
// println!("{first}"); // Does not compile after move
```

Copy example:

```rust
let first = 10;
let second = first;
println!("{first}, {second}");
```

Many small fixed-size primitive types implement `Copy`, while `String` and `Vec<T>` generally do not.

Clone:

```rust
let first = String::from("hello");
let second = first.clone();
```

`clone()` may allocate/copy significant data. Avoid cloning blindly; borrow where suitable.

Drop behavior is based on scope and ownership. `Drop` can be implemented for custom cleanup, but avoid depending on an exact drop order across unrelated values when the language/API does not guarantee what you need.

---

# 13. Borrowing and References

Shared reference:

```rust
fn length(text: &str) -> usize {
    text.len()
}
```

Mutable reference:

```rust
fn append_suffix(text: &mut String) {
    text.push_str("!");
}
```

Rules, simplified:
- Multiple shared immutable references can coexist.
- A mutable reference generally requires exclusive access during its borrow.
- References must not outlive the data they borrow.
- Rust's borrow checker verifies these rules in safe code.

Example:

```rust
let mut message = String::from("Hello");
append_suffix(&mut message);
println!("{message}");
```

Slices:
- `&[T]`: borrowed slice of elements
- `&str`: borrowed string slice

Use references to avoid unnecessary ownership transfer and allocation, while respecting lifetimes and aliasing restrictions.

---

# 14. Lifetimes

Lifetimes describe how long references are valid. Many lifetimes are inferred, but function signatures may need explicit relationships.

```rust
fn longer<'a>(left: &'a str, right: &'a str) -> &'a str {
    if left.len() >= right.len() { left } else { right }
}
```

The `'a` annotation states that the returned reference is valid for a lifetime no longer than the shared lifetime of the inputs. It does not extend the lifetime of the underlying data.

Struct with borrowed data:

```rust
struct MessageView<'a> {
    content: &'a str,
}
```

Static lifetime:

```rust
let text: &'static str = "compiled string literal";
```

Do not use `'static` to hide an ownership/lifetime design problem. For backend APIs, owned request DTOs and response models are often simpler than retaining borrowed request data for a long time.

---

# 15. Structs and Tuple Structs

```rust
struct Product {
    id: i64,
    name: String,
    price_cents: i64,
}
```

Construction:

```rust
let product = Product {
    id: 1,
    name: String::from("Keyboard"),
    price_cents: 249_900,
};
```

Field access:

```rust
println!("{}", product.name);
```

Mutable struct:

```rust
let mut product = Product {
    id: 2,
    name: "Mouse".into(),
    price_cents: 79_900,
};

product.price_cents = 74_900;
```

Struct update syntax:

```rust
let another = Product {
    id: 3,
    ..product
};
```

This may move non-`Copy` fields from `product`; use it only when the ownership effect is intended.

Tuple struct:

```rust
struct UserId(u64);
struct RGB(u8, u8, u8);
```

Unit-like struct:

```rust
struct AppMarker;
```

Named structs, tuple structs, and unit structs provide different useful data shapes.

---

# 16. Enums and Pattern Matching

Enum:

```rust
enum ApiStatus {
    Pending,
    Success,
    Failed(String),
}
```

Use:

```rust
let status = ApiStatus::Failed("timeout".into());

match status {
    ApiStatus::Pending => println!("Waiting"),
    ApiStatus::Success => println!("Done"),
    ApiStatus::Failed(message) => println!("Failed: {message}"),
}
```

Enums can carry data and model alternatives explicitly. Useful in backend code for API errors, job states, authentication outcomes, and domain events.

`if let`:

```rust
if let ApiStatus::Failed(message) = status {
    println!("{message}");
}
```

`let ... else` (stable in modern Rust):

```rust
let Some(user_id) = maybe_user_id else {
    return Err("missing user id");
};
```

Other pattern concepts:
- `match`
- `if let` / `while let`
- destructuring
- `@` bindings
- match guards
- `..` in struct/tuple patterns
- reference patterns (use carefully with ownership)

---

# 17. `Option`, `Result`, and Error Propagation

`Option<T>` represents `Some(value)` or `None`.

```rust
let maybe_name: Option<String> = Some("Asha".into());

match maybe_name {
    Some(name) => println!("{name}"),
    None => println!("No name"),
}
```

Common methods:
- `is_some`, `is_none`
- `unwrap_or`, `unwrap_or_else`
- `map`, `and_then`, `filter`
- `ok_or`, `ok_or_else`
- `as_ref`, `as_mut`
- `take`, `replace`
- `flatten`, `transpose` where type-appropriate

Avoid using `unwrap()` in request-handling paths for untrusted input or normal failure cases; it can panic.

`Result<T, E>`:

```rust
fn parse_count(text: &str) -> Result<i32, std::num::ParseIntError> {
    text.parse::<i32>()
}
```

Propagate errors with `?`:

```rust
fn parse_twice(text: &str) -> Result<i32, std::num::ParseIntError> {
    let value = text.parse::<i32>()?;
    Ok(value * 2)
}
```

Common result methods:
- `is_ok`, `is_err`
- `unwrap_or`, `unwrap_or_else`
- `map`, `map_err`
- `and_then`, `or_else`
- `ok`, `err`
- `as_ref`, `as_mut`
- `inspect`, `inspect_err` where supported in the chosen standard library

The `?` operator returns early on an error; the caller's return type must support conversion from that error.

---

# 18. Collections: Vec, String, HashMap, HashSet

## Vector

```rust
let mut numbers = vec![1, 2, 3];
numbers.push(4);
numbers.pop();
numbers.len();
numbers.is_empty();
numbers.contains(&2);
numbers.sort();
numbers.reverse();
```

Common vector methods include `push`, `pop`, `insert`, `remove`, `retain`, `clear`, `extend`, `len`, `capacity`, `reserve`, `truncate`, `dedup`, `sort`, `sort_by`, `sort_by_key`, `binary_search`, `iter`, `iter_mut`, `into_iter`.

## HashMap

```rust
use std::collections::HashMap;

let mut scores = HashMap::new();
scores.insert(String::from("Asha"), 95);
scores.insert(String::from("Ravi"), 88);

let score = scores.get("Asha");
scores.entry(String::from("Maya")).or_insert(0);
scores.remove("Ravi");
```

Common methods:
- `new`, `with_capacity`
- `insert`, `get`, `get_mut`
- `entry`, `or_insert`, `and_modify`
- `contains_key`, `remove`
- `keys`, `values`, `values_mut`, `iter`, `iter_mut`
- `retain`, `clear`, `len`, `is_empty`, `drain`, `into_iter`

## HashSet

```rust
use std::collections::HashSet;

let mut ids = HashSet::new();
ids.insert(10);
ids.insert(20);
ids.contains(&10);
ids.remove(&20);
```

Set operations include union, intersection, difference, symmetric difference, `is_subset`, `is_superset`, and `is_disjoint` where used through the collection API/iterators.

Collection method names/types can differ; refer to the standard library API for the exact type.

---

# 19. Iterators and Closures

Iterator chain:

```rust
let values = vec![1, 2, 3, 4, 5];

let doubled: Vec<i32> = values
    .iter()
    .map(|value| value * 2)
    .filter(|value| *value > 4)
    .collect();
```

Common iterator methods:
- `map`
- `filter`
- `filter_map`
- `flat_map`
- `flatten`
- `fold`
- `reduce`
- `scan`
- `take`, `take_while`
- `skip`, `skip_while`
- `enumerate`
- `zip`
- `chain`
- `inspect`
- `any`, `all`
- `find`, `position`
- `min`, `max`, `min_by`, `max_by`
- `sum`, `product`
- `count`
- `collect`
- `partition`
- `cloned`, `copied`
- `by_ref`

Closures:

```rust
let multiply = |a: i32, b: i32| a * b;
let result = multiply(3, 4);
```

Closures may borrow or capture values by reference, mutable reference, or move depending on usage and the `move` keyword. Trait categories include `Fn`, `FnMut`, and `FnOnce`.

Use iterator pipelines where they improve clarity. For complex side effects or error paths, an explicit loop may be easier to understand.

---

# 20. Generics and Trait Bounds

Generic function:

```rust
fn identity<T>(value: T) -> T {
    value
}
```

Trait bound:

```rust
use std::fmt::Display;

fn print_value<T: Display>(value: T) {
    println!("{value}");
}
```

`where` clause:

```rust
fn compare_and_show<T>(left: T, right: T)
where
    T: PartialOrd + Display,
{
    if left < right {
        println!("{left} is smaller");
    } else {
        println!("{right} is not greater than {left}");
    }
}
```

Traits define shared behavior, rather than classical inheritance of data. Generic functions are commonly monomorphized by the compiler; trait objects (`dyn Trait`) use dynamic dispatch where appropriate.

---

# 21. Traits and Trait Objects

Define a trait:

```rust
trait Repository {
    fn count(&self) -> usize;
}
```

Implement:

```rust
struct MemoryRepository {
    count: usize,
}

impl Repository for MemoryRepository {
    fn count(&self) -> usize {
        self.count
    }
}
```

Trait objects:

```rust
fn report(repository: &dyn Repository) {
    println!("{}", repository.count());
}
```

Common standard traits:
- `Debug`
- `Display`
- `Clone`
- `Copy`
- `Default`
- `PartialEq`, `Eq`
- `PartialOrd`, `Ord`
- `Hash`
- `Iterator`
- `IntoIterator`
- `From`, `Into`
- `TryFrom`, `TryInto`
- `AsRef`, `AsMut`
- `Borrow`
- `Read`, `Write`
- `Send`, `Sync`
- `Future`
- `FromStr`
- `Drop`

Derive common traits:

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
struct User {
    id: u64,
    name: String,
}
```

Not every trait can be derived for every type. Add traits based on actual needs rather than deriving them blindly.

---

# 22. Modules, Crates, and Visibility

In `main.rs`:

```rust
mod config;
mod routes;

use crate::config::Settings;
```

Example `src/config.rs`:

```rust
pub struct Settings {
    pub port: u16,
}
```

Visibility:
- Private by default.
- `pub` makes an item publicly accessible through its module path.
- `pub(crate)` exposes within the current crate.
- `pub(super)` exposes to the parent module.
- `pub(in path)` restricts visibility to an ancestor path where supported by the visibility rules.

Useful crate concepts:
- Binary crate
- Library crate
- Workspace
- Dependency
- Feature
- `Cargo.lock`
- Semantic versioning
- Build profiles (`dev`, `release`, custom profiles)

Use modules to separate routes, application state, validation, domain logic, repositories, and error types. Prefer a clear boundary over importing everything with `use module::*` across a large codebase.

---

# 23. Macros and Attributes

Rust macro examples:

```rust
println!("Hello");
format!("Hello, {}", "Rust");
vec![1, 2, 3];
assert_eq!(2 + 2, 4);
dbg!(value);
```

Macros are invoked with `!`. They can generate code at compile time. Common macro families:
- Declarative `macro_rules!`
- Derive macros such as `#[derive(Serialize, Deserialize)]`
- Attribute macros such as `#[tokio::main]`, `#[test]`, or framework route/test attributes
- Function-like procedural macros such as SQLx `query!` (when configured)

Attributes:

```rust
#[derive(Debug)]
struct Sample;

#[allow(dead_code)]
fn helper() {}
```

Avoid macros that obscure simple logic. When a proc macro fails, read the compiler diagnostic and confirm the relevant dependency features are enabled.

---

# 24. Smart Pointers

Common smart pointers:
- `Box<T>`: heap allocation and ownership
- `Rc<T>`: single-threaded reference counting
- `Arc<T>`: thread-safe reference counting
- `Cell<T>` / `RefCell<T>`: interior mutability for single-threaded designs
- `Mutex<T>` / `RwLock<T>`: synchronization
- `Cow<'a, T>`: borrowed-or-owned representation
- `Pin<T>`: constrains moving the pinned value under its guarantees; often appears in async implementation details

Example shared state:

```rust
use std::sync::Arc;

#[derive(Clone)]
struct AppState {
    app_name: Arc<str>,
}
```

Arc cloning increments a reference count; it doesn't deep-clone the inner data. For async workloads, prefer async-aware synchronization if locking can wait; never hold a blocking mutex guard across an `.await` without understanding the consequences.

---

# 25. Interior Mutability and Concurrency

Rust's type system separates data-race prevention from general correctness. Thread-safe types often implement `Send` and `Sync`.

Standard synchronization examples:

```rust
use std::sync::{Arc, Mutex};
use std::thread;

let counter = Arc::new(Mutex::new(0));

let worker_counter = Arc::clone(&counter);
let worker = thread::spawn(move || {
    let mut value = worker_counter.lock().expect("mutex poisoned");
    *value += 1;
});

worker.join().expect("worker panicked");
```

Async code commonly uses Tokio primitives such as `tokio::sync::Mutex`, `RwLock`, `Semaphore`, `mpsc`, `broadcast`, and `watch`. Choose based on the required communication pattern.

Common concurrency concepts:
- `thread::spawn`
- `JoinHandle`
- `Arc`
- `Mutex`, `RwLock`
- Channels (`mpsc`)
- Atomics
- `Send` / `Sync`
- Deadlocks, lock contention, cancellation
- Backpressure and queue limits

Do not assume a thread-safe data structure makes all operations logically correct. Define locking boundaries and avoid holding locks around slow external calls.

---

# 26. Async/Await and Futures

An async function returns a future. It does not automatically run unless driven by an executor/runtime. Tokio is widely used for backend I/O.

```rust
async fn fetch_value() -> i32 {
    42
}
```

Use `.await` from an async context:

```rust
#[tokio::main]
async fn main() {
    let value = fetch_value().await;
    println!("{value}");
}
```

Tokio commonly uses:
- `#[tokio::main]`
- `tokio::spawn`
- `tokio::join!`
- `tokio::select!`
- `tokio::time::sleep`
- `tokio::sync`
- `tokio::net`
- `tokio::signal`
- `tokio::task::spawn_blocking`

Calling async functions returns a future; `.await` is the point where that future is polled as part of the enclosing async operation. Use async equivalents for network/file/database I/O where available. Blocking CPU-heavy work should not run uncontrolled on the async executor.

---

# 27. Files, JSON, and Environment Variables

Read environment variables:

```rust
let port = std::env::var("PORT")
    .unwrap_or_else(|_| "3000".to_string());
```

Read text files:

```rust
let content = std::fs::read_to_string("config.txt")?;
```

The `?` requires a compatible enclosing error return type.

Serde JSON:

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct User {
    id: u64,
    name: String,
}
```

Serialize:

```rust
let user = User { id: 1, name: "Asha".into() };
let json = serde_json::to_string(&user)?;
```

Deserialize:

```rust
let parsed: User = serde_json::from_str(&json)?;
```

Use `Result` handling in real code rather than panicking on invalid files or incoming JSON. Avoid exposing filesystem paths or raw parsing internals to API clients.

---

# 28. Testing, Documentation, and Code Quality

Unit test:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds_values() {
        assert_eq!(2 + 3, 5);
    }
}
```

Common test macros:
- `assert!`
- `assert_eq!`
- `assert_ne!`

Run:

```bash
cargo test
cargo test test_name
cargo test -- --nocapture
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
```

Documentation comments:
- `///` for an item
- `//!` for the containing module/crate

Rustdoc examples in documentation can be compiled as doctests if written in the expected format.

Use automated tests for handler responses, validation, authorization, database behavior, and error cases. Don't test only the happy path.

---

# PART II — RUST BACKEND ECOSYSTEM

# 29. Choosing a Web Framework

## Axum
- Uses Tokio and Hyper and integrates with Tower services/middleware.
- Routes are assembled with `Router`.
- Handler arguments use extractors.
- Responses implement `IntoResponse`.
- Shared state is commonly passed with `State`.

## Actix Web
- Mature web framework with its own handler/extractor/middleware ecosystem.
- Common APIs include `HttpServer`, `App`, `web::get`, `web::post`, `web::Data`, `web::Json`, `web::Path`, and `web::Query`.
- See the current Actix Web reference for its exact route/middleware APIs.

## Rocket
- Framework built around route attributes, managed state, and request guards.
- APIs include `#[get]`, `#[post]`, `#[launch]`, `State`, and responder types.
- Use the guide for the exact Rocket release; its API conventions differ from Axum/Actix.

## Recommendation for this guide
Use Axum with Tokio, Serde, `tower-http`, and SQLx for the main examples. Do not mix Axum route syntax with Actix Web or Rocket syntax in a single handler.

---

# 30. Axum Setup and First Server

Axum docs currently describe the 0.8.x release family, with 0.8.9 listed in the current docs at the time of preparation. Axum 0.8 uses brace-style path parameters such as `/{id}`.

## `Cargo.toml`

```toml
[package]
name = "rust_backend"
version = "0.1.0"
edition = "2024"

[dependencies]
axum = "0.8.9"
tokio = { version = "1", features = ["macros", "rt-multi-thread", "net", "signal"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
tower-http = { version = "0.6", features = ["trace", "cors"] }
```

Check dependency compatibility with `cargo check`; crate releases may change after this guide is generated.

## `src/main.rs`

```rust
use axum::{routing::get, Json, Router};
use serde_json::{json, Value};
use tokio::net::TcpListener;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

async fn health() -> Json<Value> {
    Json(json!({ "status": "ok" }))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| "info".into()))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let app = Router::new().route("/health", get(health));
    let listener = TcpListener::bind("0.0.0.0:3000").await?;

    tracing::info!("Listening on {}", listener.local_addr()?);

    axum::serve(listener, app)
        .with_graceful_shutdown(async {
            let _ = tokio::signal::ctrl_c().await;
        })
        .await?;

    Ok(())
}
```

Run:

```bash
cargo run
```

Then request:

```bash
curl http://127.0.0.1:3000/health
```

The `#[tokio::main]` macro requires the corresponding Tokio features. Axum 0.8 uses `axum::serve` when the necessary features are enabled.

---

# 31. Routing and HTTP Methods

Axum route example:

```rust
use axum::{
    routing::{get, post},
    Router,
};

async fn list_items() -> &'static str {
    "items"
}

async fn create_item() -> &'static str {
    "created"
}

let app = Router::new()
    .route("/items", get(list_items).post(create_item));
```

Common routing helpers:
- `get(handler)`
- `post(handler)`
- `put(handler)`
- `patch(handler)`
- `delete(handler)`
- `head(handler)`
- `options(handler)`
- `any(handler)` where appropriate
- `Router::new()`
- `.route(path, method_router)`
- `.nest(prefix, router)`
- `.merge(router)`
- `.route_layer(layer)`
- `.layer(layer)`
- `.with_state(state)`
- `.fallback(handler)` / method-not-allowed configuration as supported by the installed version

Path parameters in Axum 0.8:

```rust
.route("/items/{id}", get(get_item))
```

Use the path syntax matching the Axum version. Older examples may use colon-prefixed path syntax which is not the recommended Axum 0.8 route format.

---

# 32. Request Extractors: Path, Query, JSON, Headers

Axum extractors convert parts of an HTTP request into typed handler arguments.

## Path

```rust
use axum::extract::Path;

async fn get_item(Path(id): Path<u64>) -> String {
    format!("item id: {id}")
}
```

Route:

```rust
.route("/items/{id}", get(get_item))
```

## Query

```rust
use axum::extract::Query;
use serde::Deserialize;

#[derive(Deserialize)]
struct ListParams {
    page: Option<u32>,
    limit: Option<u32>,
}

async fn list_items(Query(params): Query<ListParams>) -> String {
    format!("page={:?}, limit={:?}", params.page, params.limit)
}
```

## JSON body

```rust
use axum::Json;
use serde::Deserialize;

#[derive(Deserialize)]
struct CreateItem {
    name: String,
    price_cents: i64,
}

async fn create_item(Json(payload): Json<CreateItem>) -> Json<CreateItem> {
    Json(payload)
}
```

The `Json` extractor requires the appropriate Axum JSON feature and that the body type implements `Deserialize`.

## Headers

```rust
use axum::http::HeaderMap;

async fn show_headers(headers: HeaderMap) -> String {
    headers
        .get("user-agent")
        .and_then(|value| value.to_str().ok())
        .unwrap_or("unknown")
        .to_string()
}
```

Do not assume a supplied authorization header is valid just because it is present. Use a trusted authentication validator.

Other extractors include `State`, `Extension`, `Form`, `Multipart` when enabled, `ConnectInfo`, `OriginalUri`, `MatchedPath`, request/body extractors, and custom extractors using the relevant traits. Extractor ordering/body consumption rules matter; check the Axum reference for the exact types and traits.

---

# 33. Request and Response Types

Axum handlers can return any value implementing `IntoResponse`.

Plain text:

```rust
async fn hello() -> &'static str {
    "Hello"
}
```

JSON:

```rust
use axum::Json;
use serde_json::json;

async fn info() -> Json<serde_json::Value> {
    Json(json!({"status": "ok"}))
}
```

Tuple response:

```rust
use axum::{http::StatusCode, Json};
use serde_json::json;

async fn created() -> (StatusCode, Json<serde_json::Value>) {
    (
        StatusCode::CREATED,
        Json(json!({"created": true})),
    )
}
```

Use a typed response model for production APIs rather than an unstructured JSON value for every endpoint.

Common response-related types:
- `Json<T>`
- `StatusCode`
- `Response`
- `IntoResponse`
- `HeaderMap`
- `Redirect` when using the corresponding Axum response API/version
- `Body`
- `Bytes`
- `Result<T, E>` when `E` can be converted into a response

The exact response types and helpers are documented by Axum and the `http` ecosystem.

---

# 34. Shared Application State

Use `State` to share services, database pools, configuration, and clients.

```rust
use axum::{extract::State, routing::get, Router};
use std::sync::Arc;

#[derive(Clone)]
struct AppState {
    app_name: Arc<str>,
}

async fn get_app_name(State(state): State<AppState>) -> String {
    state.app_name.to_string()
}

fn make_router(state: AppState) -> Router {
    Router::new()
        .route("/app-name", get(get_app_name))
        .with_state(state)
}
```

For a SQLx pool, cloning the pool handle is generally cheap and meant for shared use, subject to the driver docs.

Prefer `State` for typed application state. `Extension` can share request extensions added by middleware, but forgetting to add an expected extension can lead to runtime errors. Use `Arc<T>` for shared ownership when required; do not add `Arc<Mutex<_>>` everywhere without a concrete concurrency need.

---

# 35. Validation and DTO Design

Serde deserializes request JSON into Rust types, but deserialization is not the same as full business validation.

```rust
#[derive(serde::Deserialize)]
struct CreateUser {
    username: String,
    email: String,
    age: Option<u8>,
}
```

Validate explicitly:

```rust
fn validate_username(value: &str) -> Result<(), &'static str> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return Err("username cannot be empty");
    }
    if trimmed.len() > 50 {
        return Err("username is too long");
    }
    Ok(())
}
```

Validation crate options include crates such as `validator`; check their current APIs and macro features before adding them.

Good API model patterns:
- Separate request types from database/domain types.
- Avoid exposing password hashes/internal fields.
- Require fields needed for create requests.
- Use `Option<T>` deliberately for optional/null fields and patch semantics.
- Limit string lengths and arrays/body sizes.
- Validate email/URL formats only with a suitable library and clear business rules.
- Check authorization/ownership after syntax validation.
- Make errors stable and safe for clients.

For PATCH APIs, distinguish a missing field from an explicit JSON `null` when the business contract needs both. A simple `Option<T>` can collapse those states depending on deserialization setup; use a presence-aware type/custom deserializer if required.

---

# 36. Error Handling for HTTP APIs

Define a domain/API error type and map it to safe HTTP responses.

```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;

#[derive(Debug)]
enum ApiError {
    NotFound,
    BadRequest(String),
    Internal,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            ApiError::NotFound => (StatusCode::NOT_FOUND, "Not found".to_string()),
            ApiError::BadRequest(message) => (StatusCode::BAD_REQUEST, message),
            ApiError::Internal => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Internal server error".to_string(),
            ),
        };

        (status, Json(json!({"error": message}))).into_response()
    }
}
```

In production, log detailed internal errors securely with `tracing`, but do not return SQL errors, secrets, stack traces, or private data to clients.

Use `thiserror` for defining typed error enums. `anyhow` can be convenient for application-level error context, but don't blindly expose its error chain as an HTTP response.

Common error patterns:
- `Result<T, E>`
- `?` error propagation
- `map_err`
- `ok_or` / `ok_or_else`
- `thiserror::Error`
- `anyhow::Context` for context on application errors
- `IntoResponse` implementations for API errors

---

# 37. Middleware, CORS, and Tracing

Axum uses Tower/Tower HTTP ecosystem middleware.

Add tracing and CORS (example; configure actual origins):

```rust
use axum::Router;
use tower_http::{
    cors::{Any, CorsLayer},
    trace::TraceLayer,
};
use http::Method;
```

If you use `http::Method`, add a direct `http` dependency compatible with Axum's version or import the corresponding re-export supported by the chosen version.

Build layers:

```rust
let cors = CorsLayer::new()
    .allow_origin("https://app.example.com".parse::<axum::http::HeaderValue>()?)
    .allow_methods([Method::GET, Method::POST])
    .allow_headers([axum::http::header::CONTENT_TYPE]);

let app = Router::new()
    .route("/health", axum::routing::get(|| async { "ok" }))
    .layer(TraceLayer::new_for_http())
    .layer(cors);
```

The example assumes compatible `tower-http` CORS APIs and imports. Avoid enabling all origins/headers/methods with credentials in production without a justified design.

Tracing setup:

```rust
tracing_subscriber::fmt()
    .with_env_filter("info")
    .init();
```

Middleware/layers may be used for:
- Request tracing
- CORS
- Compression
- Timeouts
- Authentication/authorization
- Request IDs
- Load shedding/concurrency limits

Layer order matters. Authentication should be correctly applied to the protected routes; security rules should be tested, not assumed.

---

# 38. Configuration and Secrets

Environment variables:

```rust
let port: u16 = std::env::var("PORT")
    .unwrap_or_else(|_| "3000".to_string())
    .parse()?;
```

`.env` file loading commonly uses `dotenvy` for development:

```rust
dotenvy::dotenv().ok();
```

Keep `.env` out of Git. Use a production secrets manager or orchestrator-provided environment/secret mechanism. Validate configuration at startup and fail clearly if required values are absent.

Configuration should include:
- Bind address and port
- Database URL/pool limits
- Service API URLs/timeouts
- Log level
- Request/response size limits
- Authentication issuer/audience/key source
- Graceful shutdown settings
- Feature flags appropriate to deployment

Never hard-code signing keys, database passwords, private API keys, or production credentials.

---

# 39. SQL Databases with SQLx

SQLx is an async SQL toolkit supporting PostgreSQL, MySQL/MariaDB, and SQLite. Its feature flags select the runtime, TLS backend, database drivers, and optional integrations. The current SQLx docs list 0.9.0 and runtime features such as `runtime-tokio`, with separate TLS features.

Cargo example for PostgreSQL + Tokio + Rustls (check exact feature support for your chosen SQLx release):

```toml
sqlx = {
    version = "0.9.0",
    default-features = false,
    features = [
        "runtime-tokio",
        "tls-rustls-ring",
        "postgres",
        "macros",
        "migrate",
        "chrono",
        "uuid"
    ]
}
```

Connection pool:

```rust
use sqlx::postgres::PgPoolOptions;

let pool = PgPoolOptions::new()
    .max_connections(10)
    .connect(&database_url)
    .await?;
```

SQLx's key APIs include:
- `PgPoolOptions`, `MySqlPoolOptions`, `SqlitePoolOptions`
- `query`
- `query_as`
- `query_scalar`
- `query_file`
- `query!`, `query_as!`, `query_scalar!` macros where features/database metadata are configured
- `.bind(...)`
- `.execute(...)`
- `.fetch_one(...)`
- `.fetch_optional(...)`
- `.fetch_all(...)`
- `.fetch(...)`
- `.begin()`, transaction `commit()` and `rollback()`
- `migrate!()` / migrator APIs when enabled and configured
- `FromRow`, `Encode`, `Decode`, database `Type` conversions

Use bound parameters instead of string concatenation. Query macros may require a live build-time database or offline metadata depending on your setup.

---

# 40. CRUD API with Axum and SQLx

This tutorial section uses PostgreSQL and Axum 0.8-style routing. Create the table through a migration:

`migrations/0001_create_products.sql`:

```sql
CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL CHECK (price >= 0)
);
```

For precise monetary values, use a suitable decimal/numeric mapping rather than floating-point values. The example uses `f64` only to keep the small demonstration straightforward.

Cargo dependencies should include Axum, Tokio, Serde, SQLx with PostgreSQL/Tokio/TLS/derive features, and tracing as shown earlier.

`src/main.rs` example:

```rust
use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::get,
    Json,
    Router,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use sqlx::{FromRow, PgPool};
use sqlx::postgres::PgPoolOptions;
use std::env;
use tracing::error;

#[derive(Clone)]
struct AppState {
    pool: PgPool,
}

#[derive(Debug, Serialize, FromRow)]
struct Product {
    id: i64,
    name: String,
    price: f64,
}

#[derive(Debug, Deserialize)]
struct ProductInput {
    name: String,
    price: f64,
}

#[derive(Debug)]
enum ApiError {
    NotFound,
    BadRequest(&'static str),
    Database(sqlx::Error),
}

impl From<sqlx::Error> for ApiError {
    fn from(error: sqlx::Error) -> Self {
        Self::Database(error)
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            Self::NotFound => (StatusCode::NOT_FOUND, "Product not found"),
            Self::BadRequest(message) => (StatusCode::BAD_REQUEST, message),
            Self::Database(error) => {
                error!(?error, "Database request failed");
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error")
            }
        };

        (status, Json(json!({ "error": message }))).into_response()
    }
}

async fn list_products(
    State(state): State<AppState>,
) -> Result<Json<Vec<Product>>, ApiError> {
    let products = sqlx::query_as::<_, Product>(
        "SELECT id, name, price FROM products ORDER BY id"
    )
    .fetch_all(&state.pool)
    .await?;

    Ok(Json(products))
}

async fn get_product(
    State(state): State<AppState>,
    Path(id): Path<i64>,
) -> Result<Json<Product>, ApiError> {
    let product = sqlx::query_as::<_, Product>(
        "SELECT id, name, price FROM products WHERE id = $1"
    )
    .bind(id)
    .fetch_optional(&state.pool)
    .await?
    .ok_or(ApiError::NotFound)?;

    Ok(Json(product))
}

async fn create_product(
    State(state): State<AppState>,
    Json(input): Json<ProductInput>,
) -> Result<(StatusCode, Json<Product>), ApiError> {
    let name = input.name.trim();
    if name.is_empty() {
        return Err(ApiError::BadRequest("name cannot be empty"));
    }
    if !input.price.is_finite() || input.price < 0.0 {
        return Err(ApiError::BadRequest("price must be non-negative and finite"));
    }

    let product = sqlx::query_as::<_, Product>(
        "INSERT INTO products (name, price) VALUES ($1, $2) RETURNING id, name, price"
    )
    .bind(name)
    .bind(input.price)
    .fetch_one(&state.pool)
    .await?;

    Ok((StatusCode::CREATED, Json(product)))
}

async fn update_product(
    State(state): State<AppState>,
    Path(id): Path<i64>,
    Json(input): Json<ProductInput>,
) -> Result<Json<Product>, ApiError> {
    let name = input.name.trim();
    if name.is_empty() {
        return Err(ApiError::BadRequest("name cannot be empty"));
    }
    if !input.price.is_finite() || input.price < 0.0 {
        return Err(ApiError::BadRequest("price must be non-negative and finite"));
    }

    let product = sqlx::query_as::<_, Product>(
        "UPDATE products SET name = $1, price = $2 WHERE id = $3 RETURNING id, name, price"
    )
    .bind(name)
    .bind(input.price)
    .bind(id)
    .fetch_optional(&state.pool)
    .await?
    .ok_or(ApiError::NotFound)?;

    Ok(Json(product))
}

async fn delete_product(
    State(state): State<AppState>,
    Path(id): Path<i64>,
) -> Result<StatusCode, ApiError> {
    let result = sqlx::query("DELETE FROM products WHERE id = $1")
        .bind(id)
        .execute(&state.pool)
        .await?;

    if result.rows_affected() == 0 {
        return Err(ApiError::NotFound);
    }

    Ok(StatusCode::NO_CONTENT)
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    dotenvy::dotenv().ok();

    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info".into())
        )
        .init();

    let database_url = env::var("DATABASE_URL")?;
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .connect(&database_url)
        .await?;

    let state = AppState { pool };

    let app = Router::new()
        .route("/health", get(|| async { "ok" }))
        .route(
            "/api/products",
            get(list_products).post(create_product),
        )
        .route(
            "/api/products/{id}",
            get(get_product).put(update_product).delete(delete_product),
        )
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    tracing::info!("Listening on {}", listener.local_addr()?);

    axum::serve(listener, app)
        .with_graceful_shutdown(async {
            let _ = tokio::signal::ctrl_c().await;
        })
        .await?;

    Ok(())
}
```

Run:

```bash
DATABASE_URL="postgres://appuser:password@localhost:5432/appdb" cargo run
```

In PowerShell, set `$env:DATABASE_URL = "..."` before running, or use a local `.env` file through `dotenvy`. Do not use production credentials in command history or a public file.

This example is a learning baseline. A real service should use migrations, suitable decimal types, authentication/authorization, connection/timeouts policy, request size limits, rate limiting where relevant, structured error IDs, tests, and a managed secret source.

---

# 41. Database Migrations and Transactions

SQLx migration files are commonly organized under `migrations/`, named with a version and description, such as:

```text
migrations/
├── 0001_create_products.sql
└── 0002_add_created_at.sql
```

If using SQLx's migration macro, enable the appropriate feature and add the migration directory to the project. Exact macro setup depends on the chosen SQLx release.

Conceptual migration execution:

```rust
// With a configured SQLx Migrator:
// sqlx::migrate!("./migrations").run(&pool).await?;
```

Transaction:

```rust
let mut transaction = pool.begin().await?;

sqlx::query("UPDATE accounts SET balance = balance - $1 WHERE id = $2")
    .bind(100)
    .bind(1_i64)
    .execute(&mut *transaction)
    .await?;

sqlx::query("UPDATE accounts SET balance = balance + $1 WHERE id = $2")
    .bind(100)
    .bind(2_i64)
    .execute(&mut *transaction)
    .await?;

transaction.commit().await?;
```

This is a shape example; real transfer logic must validate balance and handle concurrency/rollback. A failed transaction should be rolled back and errors handled. Keep DB transactions short and do not hold them across slow external HTTP/model calls without a strong reason.

Migration best practices:
- Version migrations in Git.
- Test migration forward/backward strategy.
- Use expand-and-contract for deployments requiring rolling compatibility.
- Back up important production data.
- Avoid manual schema changes that drift from tracked migrations.

---

# 42. Authentication and Authorization

Authentication verifies identity; authorization verifies whether the identity may perform a specific action.

Common approaches:
- Server-side sessions
- OAuth 2.0 / OpenID Connect
- Validated JWT bearer tokens
- API keys for appropriate service-to-service cases
- Mutual TLS in certain service environments

Secure practices:
- Use a trusted identity provider or reviewed authentication library.
- Validate token signature, issuer, audience, expiry, and intended algorithm.
- Enforce scopes/roles and object ownership on the server.
- Keep signing keys in a secret manager.
- Rotate keys and define token lifetimes.
- Rate-limit authentication endpoints and log safely.
- Never trust role names supplied in request JSON.
- Never rely solely on hiding frontend UI controls.

Do not hand-roll cryptography or accept any token merely because its payload decodes. If using JWTs, use a maintained library compatible with the expected issuer and algorithm configuration.

---

# 43. Password Hashing and Token Design

If the application manages passwords, store **adaptive password hashes**, not plaintext or reversible-encrypted passwords. Use a well-reviewed password hashing implementation such as Argon2id (when supported/configured) or a suitable alternative for your platform/security requirements.

Token design should specify:
- Issuer and audience
- Expiry and clock tolerance
- Signing algorithm and key rotation
- Refresh/revocation behavior
- Claims/scopes and authorization policy
- Where browser clients store tokens
- Logout and session invalidation strategy

Prefer established OAuth/OIDC flows when they fit the product. Avoid storing long-lived secrets in frontend code or logs.

---

# 44. Rate Limiting, Timeouts, and Security

Backend security checklist:
- Validate all user-supplied input.
- Restrict body, file, and response sizes.
- Use request timeouts and concurrency limits.
- Apply authentication and authorization to protected routes.
- Protect database queries through bound parameters.
- Use TLS for sensitive communication.
- Keep dependencies patched.
- Avoid logging credentials or sensitive payloads.
- Configure CORS to explicit trusted origins.
- Set safe response headers where appropriate.
- Avoid exposing stack traces.
- Use least-privilege database/service accounts.
- Monitor abuse/error rates.
- Consider idempotency for retried write operations.
- Ensure dependency failures fail safely.

Axum middleware can be composed with Tower layers. Use the specific timeout/rate-limit middleware package/API compatible with your dependency versions. A timeout should not be mistaken for cancellation of every underlying database/external operation; understand each library's cancellation/cleanup behavior.

---

# 45. File Uploads and Downloads

Axum supports multipart extraction with the appropriate feature enabled.

Conceptual multipart endpoint:

```rust
// Add axum's multipart feature in Cargo.toml when using Multipart.
use axum::extract::Multipart;

async fn upload(mut multipart: Multipart) -> Result<&'static str, ApiError> {
    while let Some(field) = multipart.next_field().await.map_err(|_| ApiError::BadRequest("invalid multipart form"))? {
        let name = field.name().unwrap_or("file").to_string();
        // Validate expected field, content, and size.
        // Stream/store safely rather than loading an unbounded upload into memory.
        let _ = name;
    }

    Ok("received")
}
```

Exact error type and extractors need to match your own API error mapping. This snippet demonstrates the API shape rather than a complete safe storage implementation.

Upload checklist:
- Enforce size limits.
- Validate actual file contents and allowed formats.
- Generate storage keys server-side.
- Avoid path traversal/overwrites.
- Stream large files if possible.
- Store private files outside publicly accessible paths or use private object storage.
- Restrict download by authorization.
- Add malware scanning/retention controls where appropriate.

---

# 46. External HTTP APIs

Rust HTTP client options include `reqwest` and other crates. API calls should use timeouts, safe URL handling, response status checks, and explicit error mapping.

Cargo:

```toml
reqwest = { version = "0.12", features = ["json", "rustls-tls"] }
```

The latest compatible version/feature names can change; confirm the current reqwest documentation.

Example pattern:

```rust
use reqwest::Client;
use serde::Deserialize;

#[derive(Deserialize)]
struct RemoteStatus {
    status: String,
}

async fn fetch_status(client: &Client, base_url: &str) -> Result<RemoteStatus, reqwest::Error> {
    client
        .get(format!("{base_url}/status"))
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await?
        .error_for_status()?
        .json::<RemoteStatus>()
        .await
}
```

For production:
- Reuse a configured HTTP client.
- Avoid blindly retrying non-idempotent requests.
- Set connection/overall/request timeouts.
- Treat remote responses as untrusted input.
- Validate URLs and block access to internal metadata/private networks where user-controlled destinations could cause SSRF.
- Do not log API tokens.
- Bound response size when consuming untrusted services.

---

# 47. Background Jobs and Message Queues

A Tokio task can run concurrent async work:

```rust
tokio::spawn(async move {
    // Execute bounded, monitored async work.
});
```

In-process tasks:
- Do not automatically survive restarts.
- Need error logging/handling.
- Need cancellation/shutdown behavior.
- Can consume memory/CPU if launched without limits.
- May need a bounded queue or semaphore.

Durable jobs/message brokers are better for reliable work such as emails, file processing, reports, large AI inference, or retries across process restarts. Options depend on project needs and available crates/services. Design idempotency, retry backoff, dead-letter behavior, monitoring, and authorization.

---

# 48. WebSockets and Server-Sent Events

Axum supports WebSockets with its `ws` feature.

Cargo example:

```toml
axum = { version = "0.8.9", features = ["ws"] }
```

Shape:

```rust
use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    response::IntoResponse,
};

async fn websocket_handler(ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
}

async fn handle_socket(mut socket: WebSocket) {
    while let Some(Ok(message)) = socket.recv().await {
        if let Message::Text(text) = message {
            if socket.send(Message::Text(text)).await.is_err() {
                break;
            }
        }
    }
}
```

WebSocket `Message` payload types and conversions can differ subtly with crate versions; verify the installed Axum 0.8 API if the snippet needs adaptation.

Production needs:
- Authenticate before granting access.
- Authorize channel/subscription actions.
- Validate message size/schema.
- Rate-limit and bound connections.
- Handle disconnect, cancellation, heartbeat, and reconnect.
- Use shared pub/sub or a broker when several application instances must broadcast.
- Persist important messages when durability is required.

Server-Sent Events (SSE) are a one-way server-to-client alternative in supported Axum versions. Use SSE if the client does not need to send messages on the same persistent connection.

---

# 49. Redis and Caching

Redis can be used for caching, rate-limit counters, pub/sub, locks (with careful distributed-systems design), sessions, and short-lived jobs/state.

Rust Redis libraries provide sync or async APIs with version-dependent behavior. Use:
- Connection/multiplexed connection pooling as documented.
- Explicit timeouts.
- TTL for expiring cache entries.
- Namespaced keys.
- Serialization formats that are versioned where long-lived data is stored.
- Careful invalidation rules.
- Least-privilege credentials and TLS where required.

A cache is not the source of truth unless the product is deliberately designed for that. Be careful with user-specific data: a cache-key bug can become a cross-user data leak.

---

# 50. MongoDB Integration Overview

MongoDB Rust driver can access documents and collections; choose its async API and version from the official Rust driver reference.

Common operations:
- Connect client
- Select database/collection
- `insert_one`, `insert_many`
- `find`, `find_one`
- `update_one`, `update_many`
- `replace_one`
- `delete_one`, `delete_many`
- `aggregate`
- Index creation/listing
- Transactions/session APIs where supported

Use BSON/Serde-compatible data models and validate user input. Create indexes around query patterns. Avoid passing an arbitrary user-controlled MongoDB filter object directly to a public endpoint. Authentication and object-level authorization remain application responsibilities.

---

# 51. Serialization and API Documentation

Serde commonly provides:
- `Serialize`
- `Deserialize`
- `#[serde(rename = "...")]`
- `#[serde(skip)]`
- `#[serde(default)]`
- `#[serde(flatten)]`
- `#[serde(with = "...")]`
- `#[serde(rename_all = "...")]`

Example:

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ProductResponse {
    product_id: i64,
    display_name: String,
}
```

API docs:
- Axum itself is a routing/HTTP library; OpenAPI support is usually integrated through a compatible third-party crate such as `utoipa` or generated from other tooling.
- Document request/response DTOs, status codes, auth requirements, and errors.
- Validate generated docs against the actual endpoint behavior.

Do not confuse Serde's serialized property names with Rust field names; serde attributes control naming/conversion rules.

---

# 52. Testing Backend APIs

## Unit tests

```rust
#[test]
fn price_is_valid() {
    assert!(is_valid_price(10.0));
    assert!(!is_valid_price(-1.0));
}
```

`is_valid_price` is a function you define for the domain logic.

## Async tests with Tokio

```rust
#[tokio::test]
async fn async_example() {
    let result = async { 42 }.await;
    assert_eq!(result, 42);
}
```

## Axum router test pattern

Axum tests often use `tower::ServiceExt::oneshot`, an HTTP request builder, and body utilities. Dev dependencies/feature flags depend on your version, for example Tower's `util` feature and compatible HTTP body utilities.

Test checklist:
- Status codes and JSON bodies
- Missing/invalid fields
- Not-found/conflict cases
- Authentication and ownership rules
- Database test isolation and migrations
- Transactions/rollback
- External API timeout/failure
- Upload size/type limits
- WebSocket disconnect/authorization behavior
- Graceful shutdown and resource cleanup

Use a dedicated test database and never let tests mutate production data.

---

# 53. Performance and Observability

Use `tracing` for structured, contextual diagnostics.

```rust
use tracing::{info, warn, error};

info!(route = "/health", "Request received");
warn!(attempt = 2, "Retrying dependency");
error!(error = ?err, "Operation failed");
```

A common `tracing-subscriber` setup:

```rust
tracing_subscriber::fmt()
    .with_env_filter("info")
    .init();
```

Observability layers:
- Structured logs with request/correlation IDs
- Request duration and latency percentiles
- Success/error rate
- Database pool wait/usage
- External HTTP latency/error rates
- CPU, memory, thread/runtime behavior
- Queue depth and job processing rate
- Model inference latency, memory/GPU, and quality where applicable
- Traces/metrics integration compatible with your deployment

Avoid logging secrets, full bearer tokens, passwords, sensitive request bodies, or private documents. Use tracing spans to connect request-level logs and underlying calls.

Performance guidelines:
- Avoid unnecessary allocations/clones for large payloads.
- Use connection pools.
- Set timeouts and body limits.
- Avoid blocking work on the async runtime.
- Bound concurrency and background work.
- Use database indexes and query plans.
- Measure before optimizing.

---

# 54. Docker and Deployment

Example Dockerfile for a compiled Rust application:

```dockerfile
FROM rust:1.99 AS builder
WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY migrations ./migrations

RUN cargo build --release

FROM debian:stable-slim AS runtime
WORKDIR /app

RUN useradd --system --create-home appuser
COPY --from=builder /app/target/release/rust_backend /app/rust_backend

USER appuser
EXPOSE 3000
ENTRYPOINT ["/app/rust_backend"]
```

Adapt:
- The base image and target platform.
- Binary name to match the Cargo package.
- Runtime shared-library dependencies.
- Certificates/TLS roots needed by database or HTTPS clients.
- Migration packaging.
- Non-root user creation for the selected base-image OS.
- The Rust version to a supported patch level and reproducible build policy.

For a minimal image, use a multi-stage build with a carefully chosen runtime base or target. Do not assume a statically linked binary unless the target/toolchain supports it and all dependencies are built appropriately.

Deployment checklist:
- Configuration and secrets supplied externally.
- Database migrations run safely.
- Health/readiness endpoint implemented.
- TLS/proxy setup configured.
- Logs/metrics/traces collected.
- Graceful shutdown and connection cleanup.
- CPU/memory/request limits planned.
- Image and dependencies scanned.
- CI tests run.
- Rollback and backup plans documented.

---

# 55. Actix Web and Rocket Overview

## Actix Web
Common patterns include:
- `HttpServer::new(...)`
- `App::new()`
- `web::get()`, `web::post()`, `web::put()`, `web::delete()`
- `web::Path<T>`, `web::Query<T>`, `web::Json<T>`
- `web::Data<T>` for shared state
- `HttpResponse`
- Extractors and middleware/service configuration

The exact method/trait signatures and extractor rules vary by Actix Web release.

## Rocket
Common patterns include:
- Route attributes such as `#[get]`, `#[post]`
- Application startup macro/configuration such as `#[launch]` where supported
- Managed state
- Request guards
- Responder types
- Data guards for request bodies

See the official docs for the selected Rocket release. Don't combine route macro syntax from Rocket with Axum/Actix handlers.

---

# 56. Common Rust Backend Crates

| Purpose | Common crates / options |
|---|---|
| HTTP routing | Axum, Actix Web, Rocket |
| Async runtime | Tokio |
| HTTP middleware/services | Tower, tower-http |
| Serialization | Serde, serde_json |
| SQL access | SQLx |
| ORM | SeaORM, Diesel |
| MongoDB | Official MongoDB Rust driver |
| HTTP client | reqwest |
| Configuration | std::env, dotenvy, config crates |
| Errors | thiserror, anyhow |
| Logging/tracing | tracing, tracing-subscriber |
| Validation | validator and domain-specific validation |
| Password hashing | argon2 and other well-reviewed implementations |
| Token/JWT | Maintained, properly configured JWT/OAuth ecosystem crates |
| OpenAPI | utoipa and other maintained integration tooling |
| Testing | built-in Rust test harness, tokio::test, Tower test utilities |
| Metrics | Prometheus/OpenTelemetry integrations, as required |
| Cache | redis crate |
| File uploads | Axum multipart or framework-specific APIs |
| CLI | clap |
| Time | chrono or time crate |
| IDs | uuid |

Crates are third-party components. Review release status, dependency count, licensing, security advisories, and compatibility before selecting them.

---

# 57. Common Commands and API Quick Reference

## Cargo

```bash
cargo new app_name
cargo new crate_name --lib
cargo check
cargo build
cargo build --release
cargo run
cargo test
cargo doc --open
cargo fmt
cargo clippy
cargo tree
cargo add crate_name
cargo remove crate_name
cargo update
```

## Rust compiler/tools

```bash
rustc --version
cargo --version
rustup show
rustup update stable
rustfmt --version
```

## Axum

- `Router::new()`
- `.route(path, method_router)`
- `.nest(prefix, router)`
- `.merge(router)`
- `.layer(layer)`
- `.route_layer(layer)`
- `.with_state(state)`
- extractors: `Path`, `Query`, `Json`, `State`, `Extension`, `Form`, `Multipart`, `ConnectInfo`
- response types/traits: `Json`, `Response`, `StatusCode`, `IntoResponse`
- runtime: `tokio::net::TcpListener`, `axum::serve`

## SQLx

- Pools: `PgPoolOptions`, `MySqlPoolOptions`, `SqlitePoolOptions`
- `query`, `query_as`, `query_scalar`
- `query!`, `query_as!`, `query_scalar!` (when configured)
- `.bind`, `.execute`, `.fetch_one`, `.fetch_optional`, `.fetch_all`
- `begin`, `commit`, `rollback`
- Migrations with supported `migrate` APIs/macros

This is a selective practical reference, not all functions/types in each crate.

---

# 58. Practice Projects and Learning Roadmap

Learning order:
1. Rust ownership and error handling.
2. Cargo, modules, traits, generics, collections.
3. Async/await and Tokio.
4. Axum routes/extractors/responses.
5. Application state and error mapping.
6. Serde DTOs and validation.
7. SQLx + PostgreSQL and migration files.
8. Authentication/authorization.
9. Tests, tracing, and operational endpoints.
10. Docker, CI, deployment, and monitoring.
11. External services, Redis, WebSockets, and jobs as needed.

Projects:
- Health-check API
- Product CRUD API
- SQL-backed catalog API with pagination/search
- Authentication and role-based access
- File metadata/upload service
- WebSocket chat with persistent messages
- AI inference endpoint
- RAG API with source-aware retrieval
- Backend with background jobs, retries, and idempotency
- Production-ready service with CI, migrations, observability and deployment

For each project, define request/response types, error contracts, access rules, database schema, timeouts, test cases, and a repeatable deploy process.

---

# 59. Official Documentation

## Rust
- [Rust stable release announcements](https://blog.rust-lang.org/releases/)
- [The Rust Programming Language](https://doc.rust-lang.org/stable/book/)
- [Rust Reference](https://doc.rust-lang.org/reference/)
- [Standard Library API](https://doc.rust-lang.org/std/)
- [Rust 2024 Edition Guide](https://doc.rust-lang.org/edition-guide/rust-2024/index.html)
- [Cargo Book](https://doc.rust-lang.org/cargo/)

## Backend framework/runtime
- [Axum documentation](https://docs.rs/axum/latest/axum/)
- [Axum examples](https://github.com/tokio-rs/axum/tree/main/examples)
- [Tokio tutorial](https://tokio.rs/tokio/tutorial)
- [Tower documentation](https://docs.rs/tower/latest/tower/)
- [tower-http documentation](https://docs.rs/tower-http/latest/tower_http/)

## Database and serialization
- [SQLx documentation](https://docs.rs/sqlx/latest/sqlx/)
- [Serde documentation](https://serde.rs/)
- [serde_json documentation](https://docs.rs/serde_json/latest/serde_json/)
- [SeaORM documentation](https://www.sea-ql.org/SeaORM/)
- [Diesel documentation](https://diesel.rs/)
- [MongoDB Rust driver](https://www.mongodb.com/docs/drivers/rust/current/)

## Other useful references
- [reqwest documentation](https://docs.rs/reqwest/latest/reqwest/)
- [Tracing documentation](https://docs.rs/tracing/latest/tracing/)
- [Thiserror documentation](https://docs.rs/thiserror/latest/thiserror/)
- [Anyhow documentation](https://docs.rs/anyhow/latest/anyhow/)
- [RustSec Advisory Database](https://rustsec.org/)

---

## Final Note

Rust's standard library and backend crates expose a huge evolving API surface. No single Markdown file can guarantee that it lists literally every current and future syntax form, function, trait, macro, or external crate API. Use this as a comprehensive learning reference, pin and test your crate versions, and consult the matching official documentation for exact signatures, feature flags, and security-sensitive behavior before deploying.
