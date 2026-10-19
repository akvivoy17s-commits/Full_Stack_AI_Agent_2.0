# Complete SQL Guide for Full-Stack Development
## SQL Syntax, Statements, Functions, Queries, Database Design, Security, and Performance

> **Purpose:** A broad practical reference for learning SQL and using relational databases in full-stack applications.
>
> **Important scope note:** “SQL” is not one perfectly uniform implementation. SQL standards and database products differ, and each product adds its own syntax, data types, functions, procedural language, and administrative commands. No single Markdown file can honestly guarantee every command/function in every database and every future release. This guide covers the major SQL concepts and commonly used syntax, plus dialect differences for PostgreSQL, MySQL, SQL Server (T-SQL), SQLite, and Oracle. Always verify syntax against the documentation for your actual database/version.
>
> **Examples:** Most query examples use broadly familiar SQL. Where syntax differs, the database/dialect is labelled. Do not assume that a PostgreSQL example runs unchanged in MySQL, SQL Server, SQLite, or Oracle.

---

## Table of Contents

1. What SQL Is
2. SQL Statement Categories
3. Database Clients and Safe Practice
4. SQL Syntax Rules, Comments, and Identifiers
5. Data Types
6. Create and Select a Database / Schema
7. CREATE TABLE and Table Design
8. Constraints and Keys
9. INSERT
10. SELECT: The Core Query
11. Aliases, DISTINCT, and Expressions
12. WHERE and Filter Conditions
13. Operators and Predicate Syntax
14. ORDER BY and Pagination
15. UPDATE
16. DELETE, TRUNCATE, and DROP
17. NULL Semantics
18. Built-in Scalar Functions
19. String Functions
20. Numeric and Mathematical Functions
21. Date and Time Functions
22. Conditional Expressions
23. Aggregate Functions
24. GROUP BY and HAVING
25. JOINs
26. Subqueries and EXISTS
27. Set Operations
28. Common Table Expressions (CTEs)
29. Recursive CTEs
30. Window Functions
31. INSERT/UPDATE/DELETE Returning Data
32. MERGE and Upsert Patterns
33. ALTER TABLE and Schema Changes
34. Views and Materialized Views
35. Indexes
36. Transactions and ACID
37. Isolation, Locks, and Concurrency
38. Normalization and Relationships
39. Foreign Keys and Cascading
40. Stored Procedures and User-Defined Functions
41. Triggers
42. Temporary Tables and Table Variables
43. JSON Data
44. Common Table Design Patterns
45. Security, Users, Roles, and GRANT
46. SQL Injection and Parameterized Queries
47. Query Plans and Performance Tuning
48. Backup, Restore, and Migration Concepts
49. Database-Specific Syntax Guide
50. Full CRUD Example
51. Query Patterns for Real Applications
52. Common Errors and Debugging
53. SQL Functions Reference by Category
54. Full-Stack Integration
55. Practice Projects
56. Quick Syntax Cheat Sheet
57. Official Documentation

---

# 1. What SQL Is

**SQL (Structured Query Language)** is used to define relational database structures, read and change data, control transactions, and manage permissions. SQL is declarative: you describe the result you need, and the database optimizer determines an execution plan.

Typical relational database engines:
- PostgreSQL
- MySQL
- Microsoft SQL Server
- SQLite
- Oracle Database

A full-stack application often uses this architecture:

```text
React / Angular frontend
        |
        | HTTP / JSON
        v
Backend API (Spring Boot / Node.js / Python / .NET)
        |
        | Parameterized SQL / ORM
        v
Relational database
```

Keep database credentials on the backend. A browser frontend should not connect directly to a production database using embedded credentials.

---

# 2. SQL Statement Categories

These categories are commonly used for learning; exact classification can vary by source/database.

| Category | Purpose | Common examples |
|---|---|---|
| DQL | Query data | `SELECT` |
| DML | Change data | `INSERT`, `UPDATE`, `DELETE`, `MERGE` |
| DDL | Define/change structures | `CREATE`, `ALTER`, `DROP`, `TRUNCATE` |
| DCL | Permissions | `GRANT`, `REVOKE` |
| TCL | Transactions | `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT` |

Additional SQL features include views, indexes, sequences, schemas, functions, procedures, triggers, policies, and administrative statements.

---

# 3. Database Clients and Safe Practice

Use the client that matches the chosen database: `psql` for PostgreSQL, MySQL Shell or `mysql` for MySQL, SQL Server Management Studio / `sqlcmd` for SQL Server, a SQLite client for SQLite, or SQL Developer for Oracle.

Create a practice database and experiment with sample data. Never test destructive queries against production data.

General connection settings normally include:
- Host and port
- Database or service name
- Username and password
- TLS/SSL requirements
- Connection timeout
- Pool settings for applications

Avoid placing live credentials in source code, screenshots, shell history, or a public repository.

---

# 4. SQL Syntax Rules, Comments, and Identifiers

## Statements and semicolons

```sql
SELECT 'Hello, SQL' AS message;

SELECT 1 + 2 AS total;
```

A semicolon commonly terminates a statement in SQL clients. Some clients accept statements without one.

## Comments

```sql
-- Single-line comment

/*
  Multi-line comment.
*/
```

## Identifiers

```sql
SELECT product_name
FROM products;
```

Avoid spaces and reserved words in names. Typical convention: lowercase `snake_case` names.

Delimited identifiers differ by database:
- Standard SQL/PostgreSQL: `"Order"`
- MySQL: backticks, e.g. `` `Order` `` (double quotes depend on SQL mode)
- SQL Server: `[Order]` (double quotes also possible under appropriate settings)
- SQLite: double quotes are supported; backticks and brackets are accepted for compatibility
- Oracle: double-quoted identifiers are case-sensitive

Prefer not to use reserved words as table or column names.

---

# 5. Data Types

Type names and behavior vary between engines. Choose types intentionally.

## Numeric types

Common families:
- Integers: `SMALLINT`, `INTEGER` / `INT`, `BIGINT`
- Exact decimal: `DECIMAL(p, s)` or `NUMERIC(p, s)`
- Approximate: `REAL`, `FLOAT`, `DOUBLE PRECISION`
- Product-specific variants such as MySQL `UNSIGNED`, PostgreSQL `SERIAL` legacy patterns, and SQL Server `BIT`

Examples:

```sql
quantity INTEGER NOT NULL,
price DECIMAL(12, 2) NOT NULL,
ratio DOUBLE PRECISION
```

For currency, use an exact decimal type such as `DECIMAL(12,2)` rather than floating-point storage. Define rounding rules in application logic.

## Character and text types

Common types:
- `CHAR(n)`: fixed-width character type
- `VARCHAR(n)`: bounded variable-length text
- `TEXT`: available in many but not all engines with identical behavior
- Unicode-related types differ by engine (for example, SQL Server `NVARCHAR`)

```sql
code CHAR(3),
name VARCHAR(120) NOT NULL,
description TEXT
```

## Date and time types

Common types include `DATE`, `TIME`, `TIMESTAMP` / `DATETIME`, and time-zone-aware forms whose names and behavior differ by engine.

```sql
birth_date DATE,
created_at TIMESTAMP
```

- PostgreSQL: `timestamp with time zone` / `timestamptz`
- MySQL: `DATETIME` and `TIMESTAMP` have different time-zone/storage semantics
- SQL Server: `datetime2`, `datetimeoffset`
- SQLite: commonly stores date/time values as text, numbers, or integers rather than a dedicated date storage class
- Oracle: `DATE`, `TIMESTAMP`, and time-zone-aware types

Document whether timestamps represent UTC instants or local wall-clock times.

## Boolean types

- PostgreSQL has `BOOLEAN`.
- MySQL commonly represents Boolean aliases using `TINYINT(1)` behavior.
- SQL Server commonly uses `BIT`.
- SQLite uses integer values conventionally (`0`/`1`) and recognizes `TRUE`/`FALSE` syntax.
- Oracle versions and compatibility features vary; check the selected release's type support.

## Binary and structured types

Depending on the database:
- `BINARY`, `VARBINARY`, `BLOB`, `BYTEA`
- `JSON`, `JSONB`
- UUID types or character/binary representations
- Spatial types and vendor-specific specialized types

Do not store files in a database merely because a binary type exists; choose database versus object storage based on size, transaction needs, retention, and operational design.

---

# 6. Create and Select a Database / Schema

Database creation syntax differs.

PostgreSQL/MySQL/SQL Server (with product-specific permission rules):

```sql
CREATE DATABASE store_db;
```

Switching databases is also product-specific:
- MySQL: `USE store_db;`
- SQL Server: `USE store_db;`
- PostgreSQL: connect to the database using the client/connection configuration
- SQLite: open a database file; `ATTACH DATABASE` can attach another file
- Oracle: databases/services and schemas are administered differently; a schema is typically associated with a user

Create a schema in PostgreSQL or SQL Server:

```sql
CREATE SCHEMA sales;
```

Schema names organize objects and can provide a namespace/security boundary. A database may have one or more schemas depending on the engine.

---

# 7. CREATE TABLE and Table Design

A general table definition:

```sql
CREATE TABLE products (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    price DECIMAL(12, 2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_products_price CHECK (price >= 0)
);
```

**Compatibility note:** The identity syntax and Boolean type above are not accepted identically by every database. See Section 49 for dialect-specific identity examples.

Create another table:

```sql
CREATE TABLE customers (
    id BIGINT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Inspect table metadata through your database client or system catalog. Commands such as `DESCRIBE`, `SHOW CREATE TABLE`, `sp_help`, and catalog queries are product-specific.

Good table design:
- Give every entity a primary key or a clear candidate key.
- Use `NOT NULL` when a value is required.
- Add constraints for invariants that the database can enforce.
- Select lengths and numeric precision thoughtfully.
- Store relationships as keys, not repeated free-form names.
- Avoid duplicating derived data unless there is a measured reason.
- Define time-zone and text-collation requirements.

---

# 8. Constraints and Keys

## Primary key

```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);
```

A primary key uniquely identifies each row and cannot be `NULL`. Some products automatically create an index for a primary key.

## Unique constraint

```sql
ALTER TABLE customers
ADD CONSTRAINT uq_customers_email UNIQUE (email);
```

A `UNIQUE` constraint's treatment of `NULL` differs among databases. Do not assume every engine permits exactly the same number of null values in unique columns.

## Not null

```sql
ALTER TABLE products
ALTER COLUMN name SET NOT NULL; -- PostgreSQL syntax; differs elsewhere
```

## Check constraint

```sql
ALTER TABLE products
ADD CONSTRAINT chk_price_nonnegative CHECK (price >= 0);
```

## Foreign key

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    order_date DATE NOT NULL,
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id) REFERENCES customers(id)
);
```

A foreign key protects referential integrity. Referenced and referencing column types/keys must be compatible under the database's rules.

## Composite key

```sql
CREATE TABLE order_items (
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12, 2) NOT NULL CHECK (unit_price >= 0),
    PRIMARY KEY (order_id, product_id)
);
```

A composite key consists of multiple columns. Decide whether the combination genuinely identifies one row, and index foreign-key columns where query patterns justify it.

---

# 9. INSERT

Insert explicit values:

```sql
INSERT INTO products (name, description, price, is_active)
VALUES ('Keyboard', 'Mechanical keyboard', 2499.00, TRUE);
```

Insert multiple rows:

```sql
INSERT INTO products (name, price)
VALUES
    ('Mouse', 799.00),
    ('Monitor', 12999.00),
    ('USB Hub', 999.00);
```

Insert only selected columns; omitted columns use defaults or `NULL` if allowed.

```sql
INSERT INTO customers (id, full_name, email)
VALUES (1001, 'Asha Kumar', 'asha@example.com');
```

Insert based on another query:

```sql
INSERT INTO archived_products (id, name, price)
SELECT id, name, price
FROM products
WHERE is_active = FALSE;
```

Some databases support `DEFAULT VALUES` or slightly different syntax for inserting a row of defaults. Identity columns are usually omitted from ordinary inserts unless an explicit override is supported and intended.

Always bind untrusted values as parameters in your application rather than concatenating user input into SQL.

---

# 10. SELECT: The Core Query

```sql
SELECT name, price
FROM products;
```

Select all columns for exploration (avoid in many application endpoints):

```sql
SELECT *
FROM products;
```

Use a filter:

```sql
SELECT name, price
FROM products
WHERE price < 1000;
```

A useful mental model of query clauses:

```sql
SELECT [DISTINCT] expression_list
FROM source_tables
[JOIN ... ON ...]
[WHERE row_filter]
[GROUP BY grouping_expressions]
[HAVING group_filter]
[WINDOW window_definitions]
[ORDER BY sort_expressions]
[OFFSET ... ROWS] [FETCH FIRST ... ROWS ONLY];
```

The complete grammar and exact row-limiting syntax differ among engines. A query's **logical** processing order is often explained as `FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT/OFFSET`, though the optimizer may execute operations in another physical order.

---

# 11. Aliases, DISTINCT, and Expressions

```sql
SELECT
    name AS product_name,
    price,
    price * 1.18 AS price_with_tax
FROM products;
```

Column aliases can make returned field names clearer. Alias visibility in `WHERE`, `GROUP BY`, and `HAVING` is dialect/context-specific; do not assume a `SELECT` alias can be used in every earlier clause.

Remove duplicates:

```sql
SELECT DISTINCT category_id
FROM products;
```

Multiple expressions:

```sql
SELECT DISTINCT category_id, is_active
FROM products;
```

`DISTINCT` applies to the selected row combinations, not one arbitrary column if multiple columns are selected.

Literal expressions:

```sql
SELECT
    1 AS one_value,
    'active' AS status,
    CURRENT_TIMESTAMP AS query_time;
```

---

# 12. WHERE and Filter Conditions

Equality and comparisons:

```sql
SELECT *
FROM products
WHERE price = 999;

SELECT *
FROM products
WHERE price >= 500 AND price < 5000;

SELECT *
FROM products
WHERE is_active = TRUE;
```

`BETWEEN` includes both endpoints:

```sql
SELECT *
FROM products
WHERE price BETWEEN 500 AND 2000;
```

`IN`:

```sql
SELECT *
FROM products
WHERE id IN (1, 2, 3, 8);
```

`NOT IN` with `NULL` in its input can produce surprising unknown results. Consider `NOT EXISTS` for anti-match logic where null handling matters.

Pattern matching:

```sql
SELECT *
FROM customers
WHERE full_name LIKE 'A%';
```

- `%`: zero or more characters in `LIKE`.
- `_`: one character in `LIKE`.
- Case sensitivity depends on database/collation/operator.
- Escape wildcard characters when searching for them literally.
- Regex operators/functions are vendor-specific.

Combine conditions with parentheses:

```sql
SELECT *
FROM products
WHERE is_active = TRUE
  AND (price < 1000 OR name LIKE 'Pro%');
```

---

# 13. Operators and Predicate Syntax

Common operators and predicates:

| Syntax | Meaning |
|---|---|
| `=`, `<>`, `!=` | Equal / not equal (support varies for `!=`) |
| `<`, `<=`, `>`, `>=` | Comparison |
| `AND`, `OR`, `NOT` | Logical combination |
| `IN (...)` | Match one of a set |
| `BETWEEN a AND b` | Inclusive range |
| `LIKE` | Pattern match |
| `IS NULL` | Null test |
| `IS NOT NULL` | Non-null test |
| `EXISTS (subquery)` | True if rows exist |
| `ANY` / `SOME` | Compare with any subquery value |
| `ALL` | Compare with every subquery value |
| `CASE` | Conditional expression |
| `CAST(value AS type)` | Explicit type conversion |
| Concatenation | Operator/function differs by engine |
| JSON operators | Vendor-specific |

Examples:

```sql
SELECT *
FROM employees
WHERE salary > ALL (
    SELECT salary FROM employees WHERE department_id = 10
);
```

This returns rows whose salary is greater than every value produced by the subquery, subject to SQL's null semantics.

Prefer explicit parentheses when a filter combines `AND` and `OR`.

---

# 14. ORDER BY and Pagination

```sql
SELECT id, name, price
FROM products
ORDER BY price ASC, name DESC;
```

`ASC` means ascending; `DESC` means descending. NULL sort position differs among products and can often be controlled with `NULLS FIRST`/`NULLS LAST` where supported.

Pagination examples:

PostgreSQL/MySQL/SQLite:

```sql
SELECT id, name
FROM products
ORDER BY id
LIMIT 20 OFFSET 40;
```

Standard-style syntax supported by several engines:

```sql
SELECT id, name
FROM products
ORDER BY id
OFFSET 40 ROWS FETCH NEXT 20 ROWS ONLY;
```

SQL Server often uses `ORDER BY ... OFFSET ... FETCH` for pagination. Oracle supports row limiting in modern releases and also provides other mechanisms in older versions.

Always use a deterministic `ORDER BY` for paged data. For deep pagination, keyset/cursor pagination may be more efficient than a large offset.

---

# 15. UPDATE

Update matching rows:

```sql
UPDATE products
SET price = 2799.00
WHERE id = 1;
```

Update multiple columns:

```sql
UPDATE products
SET price = 2699.00,
    is_active = TRUE
WHERE id = 1;
```

Update based on a calculation:

```sql
UPDATE products
SET price = price * 1.05
WHERE category_id = 3;
```

Important: an `UPDATE` without a `WHERE` clause affects every row in the table.

Some databases allow joined updates or `UPDATE ... FROM`; the grammar differs by engine. If the operation depends on multiple tables, test the exact dialect and ensure the source join gives a deterministic target row.

---

# 16. DELETE, TRUNCATE, and DROP

Delete selected rows:

```sql
DELETE FROM products
WHERE id = 10;
```

Delete all rows while retaining the table:

```sql
DELETE FROM products;
```

`TRUNCATE TABLE products;` may remove all rows more efficiently, but its transaction behavior, triggers, identity-reset behavior, foreign-key restrictions, and permissions differ among engines.

Drop the structure:

```sql
DROP TABLE products;
```

Drop only if it exists (common pattern, syntax varies in some contexts):

```sql
DROP TABLE IF EXISTS products;
```

Differences:
- `DELETE`: removes selected rows; often row-by-row trigger behavior.
- `TRUNCATE`: removes all rows and has product-specific semantics.
- `DROP`: removes the table object itself.

Before destructive operations:
1. Verify the selected database/environment.
2. Confirm the predicate with a matching `SELECT`.
3. Use a transaction when supported and appropriate.
4. Back up important data and understand cascade behavior.
5. Avoid relying on rollback for DDL operations because transaction support differs.

---

# 17. NULL Semantics

`NULL` usually means missing, unknown, or not applicable; it is not the same as zero or an empty string.

Wrong:

```sql
WHERE deleted_at = NULL
```

Correct:

```sql
WHERE deleted_at IS NULL
```

Use:

```sql
WHERE deleted_at IS NOT NULL
```

Three-valued logic:
- `TRUE`
- `FALSE`
- `UNKNOWN` (often produced by comparisons involving `NULL`)

Example:

```sql
SELECT *
FROM products
WHERE price <> 0;
```

Rows with `price IS NULL` do not pass this condition. If you want them included, write the intended logic explicitly.

Common null-handling functions:
- `COALESCE(a, b, ...)`: return first non-null argument; broadly standardized.
- `NULLIF(a, b)`: returns `NULL` when arguments are equal.
- `ISNULL` is a SQL Server function with product-specific behavior.
- `IFNULL` is used by MySQL/SQLite.
- `NVL` is associated with Oracle.
- `NVL2` is Oracle-specific.

Examples:

```sql
SELECT COALESCE(nickname, full_name, 'Guest') AS display_name
FROM customers;

SELECT numerator / NULLIF(denominator, 0) AS ratio
FROM metrics;
```

Be careful: division-by-zero behavior and type coercion can vary by database.

---

# 18. Built-in Scalar Functions

Scalar functions compute a value from each input row (or from constant expressions).

General shape:

```sql
SELECT FUNCTION_NAME(argument1, argument2)
FROM some_table;
```

Function names, argument rules, result types, locale behavior, and null handling vary. SQL functions can often be nested:

```sql
SELECT LOWER(TRIM(full_name))
FROM customers;
```

Common categories:
- String/text
- Numeric/math
- Date/time
- Conditional/null handling
- Type conversion
- JSON
- Regular expression
- System/session information
- Vendor-specific utility functions

---

# 19. String Functions

Common or commonly available string functions include:

| Function | Typical purpose |
|---|---|
| `LOWER(text)` | Convert to lowercase |
| `UPPER(text)` | Convert to uppercase |
| `LENGTH(text)` / `LEN(text)` | String length; name/semantics vary |
| `CHAR_LENGTH(text)` | Character count in engines supporting it |
| `TRIM(text)` | Remove surrounding spaces/characters |
| `LTRIM(text)` | Remove leading spaces |
| `RTRIM(text)` | Remove trailing spaces |
| `SUBSTRING(text, start, length)` | Return a substring; argument rules vary |
| `REPLACE(text, old, new)` | Replace occurrences |
| `CONCAT(a, b, ...)` | Concatenate values in supported engines |
| `POSITION(sub IN text)` / `INSTR` / `CHARINDEX` | Find substring; dialect-specific |
| `LEFT(text, n)` / `RIGHT(text, n)` | Return leading/trailing characters in supported engines |
| `REPEAT(text, n)` / `REPLICATE` | Repeat text; dialect-specific |
| `REVERSE(text)` | Reverse characters in supported engines |
| `LPAD` / `RPAD` | Pad to a length where available |
| `SPLIT_PART` / split functions | Split text in vendor-specific ways |
| `FORMAT` | Formatting; type/locale behavior varies |

Examples:

```sql
SELECT
    UPPER(full_name) AS uppercase_name,
    LOWER(email) AS normalized_email,
    TRIM(full_name) AS cleaned_name
FROM customers;

SELECT CONCAT(first_name, ' ', last_name) AS full_name
FROM customer_names;
```

Concatenation differences:
- PostgreSQL uses `||` and also offers `concat`.
- MySQL commonly uses `CONCAT`; `||` normally means logical OR unless SQL mode changes its meaning.
- SQL Server uses `+` and/or `CONCAT` depending on expression needs.
- SQLite supports `||` and `concat` in supported versions.
- Oracle supports `||`.

String length may count bytes, code points, or characters according to the function and encoding. For Unicode and multi-byte text, read your database's documentation.

Case conversion is not the same as complete internationalized case-insensitive comparison. Collation and locale are important.

---

# 20. Numeric and Mathematical Functions

Common functions (availability and naming differ):

| Function | Typical meaning |
|---|---|
| `ABS(x)` | Absolute value |
| `ROUND(x, d)` | Round to a specified precision where supported |
| `CEIL(x)` / `CEILING(x)` | Round upward |
| `FLOOR(x)` | Round downward |
| `TRUNC` / `TRUNCATE` | Truncate numeric values; name/semantics vary |
| `MOD(a,b)` or `%` | Remainder; operator/function varies |
| `POWER(x,y)` / `POW` | Exponentiation |
| `SQRT(x)` | Square root |
| `SIGN(x)` | Sign of a number |
| `EXP(x)` | e raised to a power |
| `LN(x)` / `LOG(x)` | Logarithm; base varies |
| `LOG10(x)` | Base-10 logarithm where supported |
| `PI()` | Pi in supported engines |
| `RAND()` / `RANDOM()` | Pseudorandom number; dialect-specific |
| `GREATEST` / `LEAST` | Select greatest/least argument where supported |

Examples:

```sql
SELECT
    ABS(-12) AS absolute_value,
    ROUND(17.456, 2) AS rounded_value,
    CEILING(4.2) AS rounded_up,
    FLOOR(4.8) AS rounded_down;
```

The exact rules for rounding halves and how precision parameters work may depend on type and engine. Don't use approximate float types for precise money arithmetic.

---

# 21. Date and Time Functions

Common tasks:
- Current date/time
- Extract year/month/day or other parts
- Add/subtract an interval
- Calculate a difference
- Truncate to a day/month
- Format or parse a date
- Convert time zones

Examples using common syntax (adapt for your database):

```sql
SELECT CURRENT_DATE;
SELECT CURRENT_TIME;
SELECT CURRENT_TIMESTAMP;
```

Extract a date part (supported syntax varies):

```sql
SELECT EXTRACT(YEAR FROM created_at) AS created_year
FROM orders;
```

Date arithmetic examples differ strongly:
- PostgreSQL: `created_at + INTERVAL '7 days'`
- MySQL: `DATE_ADD(created_at, INTERVAL 7 DAY)`
- SQL Server: `DATEADD(day, 7, created_at)`
- SQLite: `datetime(created_at, '+7 days')` for compatible stored formats
- Oracle: date arithmetic and `INTERVAL` syntax have Oracle-specific rules.

Date difference functions also differ:
- MySQL uses `DATEDIFF` for a specific day-difference meaning.
- SQL Server uses `DATEDIFF(datepart, start, end)`.
- PostgreSQL can subtract date/time values and provides `age`.
- SQLite provides `julianday`, `unixepoch`, and date/time functions.
- Oracle provides date arithmetic and functions such as `MONTHS_BETWEEN`.

Formatting functions differ (`TO_CHAR`, `FORMAT`, `DATE_FORMAT`, `strftime`). Avoid storing dates as arbitrary formatted text when a suitable temporal representation exists. For timestamps, specify your intended time-zone policy.

---

# 22. Conditional Expressions

## CASE expression

```sql
SELECT
    name,
    price,
    CASE
        WHEN price >= 10000 THEN 'Premium'
        WHEN price >= 2000 THEN 'Mid-range'
        ELSE 'Budget'
    END AS price_band
FROM products;
```

Simple CASE:

```sql
SELECT
    CASE status
        WHEN 'PAID' THEN 'Complete'
        WHEN 'PENDING' THEN 'Waiting'
        ELSE 'Other'
    END AS status_label
FROM orders;
```

`CASE` is an expression and returns a value.

Other conditional functions:
- `COALESCE`: first non-null argument.
- `NULLIF`: null if two expressions compare equal.
- `IIF`: available in selected products (for example, SQL Server; SQLite also has a form).
- `IF`: MySQL stored-program/control syntax and function usage differ from standard `CASE`.
- `DECODE`: Oracle-specific historical conditional function.

Prefer standard `CASE` when portability matters.

---

# 23. Aggregate Functions

Aggregate functions summarize rows into one value per group (or one result for an entire filtered set).

Common aggregates:
- `COUNT(*)`
- `COUNT(expression)`
- `COUNT(DISTINCT expression)`
- `SUM(expression)`
- `AVG(expression)`
- `MIN(expression)`
- `MAX(expression)`
- `STRING_AGG` / `GROUP_CONCAT` / `LISTAGG` for concatenating values (dialect-specific)
- Boolean/bit aggregates, statistical aggregates, percentile aggregates, and JSON aggregates in selected engines

Example:

```sql
SELECT
    COUNT(*) AS product_count,
    AVG(price) AS average_price,
    MIN(price) AS minimum_price,
    MAX(price) AS maximum_price,
    SUM(price) AS sum_of_prices
FROM products;
```

`COUNT(*)` counts rows. `COUNT(column)` generally counts non-null values in that column. Most other aggregates ignore null inputs; empty-group behavior can differ by function and vendor. `SUM` and `AVG` may return `NULL` when there are no non-null inputs.

Distinct count:

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

Do not assume aggregate concatenation order is stable unless an explicit ordering clause is provided in the supported syntax.

---

# 24. GROUP BY and HAVING

`GROUP BY` creates groups; aggregates summarize each group.

```sql
SELECT category_id, COUNT(*) AS product_count
FROM products
GROUP BY category_id;
```

Multiple grouping columns:

```sql
SELECT category_id, is_active, AVG(price) AS average_price
FROM products
GROUP BY category_id, is_active;
```

`HAVING` filters groups after aggregation:

```sql
SELECT customer_id, COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 3;
```

Difference:
- `WHERE` filters rows before grouping.
- `HAVING` filters grouped results.

Avoid selecting an ungrouped column that has no valid aggregate or functional dependency under the engine's rules. Some products accept extensions that make query results ambiguous or nondeterministic.

---

# 25. JOINs

Suppose tables `customers(id, full_name)` and `orders(id, customer_id, total)` exist.

## INNER JOIN

Only matched rows:

```sql
SELECT c.full_name, o.id AS order_id, o.total
FROM customers AS c
INNER JOIN orders AS o ON o.customer_id = c.id;
```

## LEFT JOIN

All rows from the left side, plus matches from the right:

```sql
SELECT c.full_name, o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o ON o.customer_id = c.id;
```

## RIGHT JOIN

All rows from the right side and matching left rows where supported:

```sql
SELECT c.full_name, o.id
FROM customers AS c
RIGHT JOIN orders AS o ON o.customer_id = c.id;
```

A query can often be rewritten using a left join with the tables reversed. `RIGHT JOIN` support varies by engine/version.

## FULL OUTER JOIN

Keep matched and unmatched rows from both sides where supported:

```sql
SELECT c.full_name, o.id
FROM customers AS c
FULL OUTER JOIN orders AS o ON o.customer_id = c.id;
```

MySQL does not have a native `FULL OUTER JOIN` in its ordinary SELECT syntax; alternatives need carefully written `UNION` logic. SQLite/PostgreSQL/SQL Server/Oracle support depends on product/version.

## CROSS JOIN

Every row paired with every row:

```sql
SELECT c.full_name, p.name
FROM customers AS c
CROSS JOIN products AS p;
```

This can create a very large result.

## SELF JOIN

Join a table to itself:

```sql
SELECT employee.full_name, manager.full_name AS manager_name
FROM employees AS employee
LEFT JOIN employees AS manager
    ON manager.id = employee.manager_id;
```

## Multiple joins

```sql
SELECT c.full_name, o.id, p.name, oi.quantity
FROM customers c
JOIN orders o ON o.customer_id = c.id
JOIN order_items oi ON oi.order_id = o.id
JOIN products p ON p.id = oi.product_id;
```

**Important outer-join rule:** A right-table filter placed in `WHERE` may remove rows with no match, effectively changing the result of a `LEFT JOIN`. When appropriate, put the filter in the `ON` clause.

---

# 26. Subqueries and EXISTS

A subquery is a query nested within another query.

## Scalar subquery

```sql
SELECT name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products);
```

## IN subquery

```sql
SELECT full_name
FROM customers
WHERE id IN (SELECT customer_id FROM orders);
```

## EXISTS

```sql
SELECT c.id, c.full_name
FROM customers c
WHERE EXISTS (
    SELECT 1
    FROM orders o
    WHERE o.customer_id = c.id
);
```

`EXISTS` checks whether the subquery produces at least one row. The database optimizer may transform equivalent query shapes; choose the clearest correct one and measure for performance.

## NOT EXISTS / anti-join

```sql
SELECT c.id, c.full_name
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);
```

This often expresses “customers without orders” more safely than `NOT IN` when nulls may be present.

## Correlated subquery

A correlated subquery references a row from the outer query, as in the `EXISTS` examples above. Conceptually it depends on the outer row, though the optimizer may decorrelate it.

---

# 27. Set Operations

Set operations combine query results. Corresponding columns must have compatible types, and result columns align by position.

```sql
SELECT email FROM customers
UNION
SELECT email FROM newsletter_subscribers;
```

- `UNION`: combines and removes duplicates.
- `UNION ALL`: preserves duplicates and is often cheaper.
- `INTERSECT`: keeps rows present in both results (support varies by product/version).
- `EXCEPT`: keeps rows in the first result that are absent from the second (Oracle often uses `MINUS` in its SQL vocabulary).
- Parenthesize complex combinations when order is important.

Example:

```sql
SELECT customer_id FROM orders_2025
UNION ALL
SELECT customer_id FROM orders_2026;
```

Set-operation ordering generally belongs to the combined query's final `ORDER BY`; consult dialect grammar for per-branch ordering/limiting.

---

# 28. Common Table Expressions (CTEs)

A CTE names a subquery for use within a single statement.

```sql
WITH expensive_products AS (
    SELECT id, name, price
    FROM products
    WHERE price > 5000
)
SELECT *
FROM expensive_products
ORDER BY price DESC;
```

Multiple CTEs:

```sql
WITH
active_products AS (
    SELECT * FROM products WHERE is_active = TRUE
),
product_counts AS (
    SELECT COUNT(*) AS total FROM active_products
)
SELECT * FROM product_counts;
```

CTEs improve readability and can help express complex transformations. They are not guaranteed to materialize or make a query faster; optimizer behavior differs by engine and syntax. Use CTEs for clarity first, then inspect the query plan.

---

# 29. Recursive CTEs

Recursive CTEs are useful for hierarchies such as categories, folders, employees, and dependency trees. Syntax and cycle handling vary by database.

PostgreSQL-style example:

```sql
WITH RECURSIVE category_tree AS (
    SELECT id, parent_id, name, 0 AS depth
    FROM categories
    WHERE id = 1

    UNION ALL

    SELECT child.id, child.parent_id, child.name, parent.depth + 1
    FROM categories child
    JOIN category_tree parent ON child.parent_id = parent.id
    WHERE parent.depth < 20
)
SELECT *
FROM category_tree
ORDER BY depth, id;
```

The depth condition provides a simple bound but does not replace careful cycle handling. Some databases use different recursive CTE syntax or provide `CYCLE`/hierarchical-query features. Do not run an unbounded recursive query on uncertain data.

---

# 30. Window Functions

Window functions compute values across related rows while leaving individual rows visible. They commonly use `OVER(...)`.

## Ranking

```sql
SELECT
    name,
    category_id,
    price,
    ROW_NUMBER() OVER (
        PARTITION BY category_id
        ORDER BY price DESC
    ) AS row_number,
    RANK() OVER (
        PARTITION BY category_id
        ORDER BY price DESC
    ) AS price_rank,
    DENSE_RANK() OVER (
        PARTITION BY category_id
        ORDER BY price DESC
    ) AS dense_price_rank
FROM products;
```

Functions:
- `ROW_NUMBER()`
- `RANK()`
- `DENSE_RANK()`
- `NTILE(n)`
- `LAG(expression, offset, default)`
- `LEAD(expression, offset, default)`
- `FIRST_VALUE`, `LAST_VALUE`, `NTH_VALUE`
- Aggregate functions used with `OVER`, such as `SUM` and `AVG`

## Running total

```sql
SELECT
    order_date,
    total,
    SUM(total) OVER (
        ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders;
```

## Previous row

```sql
SELECT
    customer_id,
    order_date,
    total,
    LAG(total) OVER (
        PARTITION BY customer_id
        ORDER BY order_date
    ) AS previous_order_total
FROM orders;
```

Window concepts:
- `PARTITION BY`: split rows into independent partitions.
- `ORDER BY`: order rows within the window.
- Frame: the subset of the partition considered for frame-sensitive functions.
- `ROWS`, `RANGE`, and in some databases `GROUPS`: window-frame modes.

Be deliberate about window-frame defaults, especially with `LAST_VALUE` and running calculations. Add an explicit frame where necessary. Tie-breaking columns should be included in `ORDER BY` when deterministic ranking is required.

---

# 31. INSERT/UPDATE/DELETE Returning Data

Some databases return modified rows directly; syntax differs.

PostgreSQL and SQLite versions supporting `RETURNING`:

```sql
INSERT INTO products (name, price)
VALUES ('Desk', 5999.00)
RETURNING id, name, price;
```

PostgreSQL update:

```sql
UPDATE products
SET price = price * 1.10
WHERE id = 5
RETURNING id, price;
```

SQL Server often uses the `OUTPUT` clause:

```sql
INSERT INTO products (name, price)
OUTPUT inserted.id, inserted.name
VALUES ('Desk', 5999.00);
```

Other engines and versions have their own methods. Confirm your database's supported syntax before using it in an application.

---

# 32. MERGE and Upsert Patterns

**Upsert** means insert if absent or update when a matching row exists. Concurrency and unique-key behavior matter; use a database-supported atomic mechanism rather than a naïve “check then insert” race.

PostgreSQL:

```sql
INSERT INTO inventory (sku, quantity)
VALUES ('ABC-100', 25)
ON CONFLICT (sku)
DO UPDATE SET quantity = EXCLUDED.quantity;
```

MySQL:

```sql
INSERT INTO inventory (sku, quantity)
VALUES ('ABC-100', 25)
ON DUPLICATE KEY UPDATE quantity = VALUES(quantity);
```

Check current-version guidance for the preferred incoming-row reference syntax in MySQL; some historical forms are deprecated in newer releases.

SQL Server and Oracle support `MERGE` with product-specific syntax and caveats. `MERGE` semantics and concurrency behavior differ; review your engine's guidance and test concurrent writes.

A unique constraint/index should enforce the key that defines a conflict. Without the right unique constraint, “upsert” logic may create duplicates.

---

# 33. ALTER TABLE and Schema Changes

Add a column (syntax often similar):

```sql
ALTER TABLE products
ADD COLUMN sku VARCHAR(40);
```

Change a value/default/constraint using dialect-specific syntax.

PostgreSQL-style examples:

```sql
ALTER TABLE products
ALTER COLUMN sku SET NOT NULL;

ALTER TABLE products
ALTER COLUMN is_active SET DEFAULT TRUE;

ALTER TABLE products
RENAME COLUMN sku TO product_sku;
```

Drop a column:

```sql
ALTER TABLE products
DROP COLUMN product_sku;
```

These forms are not portable to every engine exactly as written. SQL Server commonly uses `ALTER TABLE ... ALTER COLUMN`; MySQL uses `MODIFY` or `CHANGE` for certain alterations; Oracle has its own DDL grammar.

Plan schema changes carefully:
- Determine whether the change locks or rewrites the table.
- Add compatible nullable/defaulted changes when possible.
- Backfill large tables in bounded batches.
- Deploy code in a way compatible with old and new schemas during rolling deployment.
- Use migration files and review them.
- Test with production-like data volume.

---

# 34. Views and Materialized Views

A view is a saved query definition.

```sql
CREATE VIEW active_products AS
SELECT id, name, price
FROM products
WHERE is_active = TRUE;
```

Query it like a table:

```sql
SELECT * FROM active_products;
```

Replace or alter view syntax differs by product. Drop a view with `DROP VIEW ...` where supported.

A **materialized view** stores a query result and usually needs refreshing:
- PostgreSQL supports `CREATE MATERIALIZED VIEW` and `REFRESH MATERIALIZED VIEW`.
- Some products have indexed views or other materialization features instead.
- Refresh rules and freshness guarantees vary.

Views can simplify permissions and reuse, but they are not automatically a security boundary unless privileges and underlying object access are configured correctly.

---

# 35. Indexes

Indexes can make lookups and joins faster but consume storage and add work to inserts, updates, and deletes.

## Create index

```sql
CREATE INDEX idx_products_name
ON products (name);
```

Composite index:

```sql
CREATE INDEX idx_products_active_price
ON products (is_active, price);
```

Unique index:

```sql
CREATE UNIQUE INDEX uq_products_sku
ON products (sku);
```

Index design considerations:
- Column order matters for composite indexes.
- Selectivity and actual query patterns matter.
- Functions or casts applied to a column may prevent use of a conventional index unless a matching expression/generated-column index is available.
- Index foreign keys when workload and engine behavior warrant it.
- Avoid adding many duplicate indexes.
- Unique constraints are both data-integrity rules and often backed by indexes.
- Partial/filtered indexes and specialized index types are vendor-specific.

PostgreSQL offers multiple index methods such as B-tree, GIN, GiST, and BRIN for different workloads. Other databases provide different types (for example, SQL Server columnstore and full-text indexes).

Drop index syntax varies. PostgreSQL-style:

```sql
DROP INDEX IF EXISTS idx_products_name;
```

Check the query plan before and after index changes; an index is not always used and does not guarantee faster execution.

---

# 36. Transactions and ACID

A transaction groups operations into a unit of work.

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE id = 2;

COMMIT;
```

If a failure occurs before commit, use `ROLLBACK` where the transaction is still active.

Some clients/databases use `START TRANSACTION` or a product-specific equivalent. In applications, the framework/database driver may manage transaction boundaries for you.

ACID:
- **Atomicity:** all operations in the transaction succeed together or are rolled back.
- **Consistency:** constraints and invariants remain satisfied.
- **Isolation:** concurrent transactions are controlled according to an isolation level.
- **Durability:** committed work survives failures within the database's guarantees.

Savepoints:

```sql
SAVEPOINT before_optional_step;

-- Run another operation.

ROLLBACK TO SAVEPOINT before_optional_step;
RELEASE SAVEPOINT before_optional_step;
```

Savepoint syntax/support and DDL transaction behavior vary by database. Avoid holding transactions open during slow user interactions or long external network calls.

---

# 37. Isolation, Locks, and Concurrency

Common isolation levels:
- `READ UNCOMMITTED`
- `READ COMMITTED`
- `REPEATABLE READ`
- `SERIALIZABLE`

Actual support and semantics differ. PostgreSQL, MySQL/InnoDB, SQL Server, and Oracle implement their own locking/MVCC details. SQLite has a different concurrency model.

Illustrative syntax (support varies):

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

Possible concurrency issues:
- Dirty reads
- Non-repeatable reads
- Phantom rows
- Lost updates
- Write skew
- Deadlocks

Locking examples are database-specific. SQL Server has table hints such as `UPDLOCK`; PostgreSQL supports `SELECT ... FOR UPDATE`; other engines have their own rules. Avoid adding locks without understanding blocking and deadlock effects.

Strategies:
- Keep transactions short.
- Apply constraints so invalid states cannot be committed.
- Use optimistic concurrency (`version` columns) where suitable.
- Retry only recognized transient failures and only when the whole operation is safe to retry.
- Define deadlock handling in application code.
- Test realistic concurrent requests.

---

# 38. Normalization and Relationships

Relational design reduces unintended duplication and maintains integrity.

## One-to-one

One row in table A relates to at most one row in table B. Often enforced by a foreign key with a unique constraint.

## One-to-many

One customer can have many orders; each order references one customer.

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id)
);
```

## Many-to-many

Use a junction table:

```sql
CREATE TABLE student_courses (
    student_id BIGINT NOT NULL REFERENCES students(id),
    course_id BIGINT NOT NULL REFERENCES courses(id),
    enrolled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, course_id)
);
```

Normalization concepts:
- First Normal Form (1NF): values/columns follow the model's atomicity and row identity expectations.
- Second Normal Form (2NF): no partial dependency on part of a composite candidate key.
- Third Normal Form (3NF): reduce inappropriate transitive dependencies.
- BCNF: a stronger determinant/candidate-key condition.

Normalization definitions have formal details; use them to identify update/insert/delete anomalies. Denormalization can be reasonable for measured performance needs, but document how duplicated data stays consistent.

---

# 39. Foreign Keys and Cascading

Foreign keys can specify actions on update/delete:

```sql
CREATE TABLE order_items (
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);
```

Common actions:
- `CASCADE`
- `SET NULL`
- `SET DEFAULT` (support and restrictions vary)
- `RESTRICT`
- `NO ACTION`

Use cascades deliberately. A cascade can delete a large set of dependent rows; `SET NULL` requires the child column to permit null. SQL Server uses some different terminology/behavior for `NO ACTION` and does not support every combination found elsewhere.

---

# 40. Stored Procedures and User-Defined Functions

Procedural SQL extends ordinary queries with variables, branches, loops, exception handlers, and database-side routines. This is one of the least portable areas of SQL.

## Conceptual function signature

```sql
CREATE FUNCTION function_name(parameters)
RETURNS return_type
-- body syntax is database-specific
```

## PostgreSQL-style function

```sql
CREATE OR REPLACE FUNCTION add_numbers(a INTEGER, b INTEGER)
RETURNS INTEGER
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT a + b;
$$;
```

Call:

```sql
SELECT add_numbers(2, 3);
```

## PostgreSQL-style PL/pgSQL function

```sql
CREATE OR REPLACE FUNCTION product_is_available(p_product_id BIGINT)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    active_value BOOLEAN;
BEGIN
    SELECT is_active
    INTO active_value
    FROM products
    WHERE id = p_product_id;

    RETURN COALESCE(active_value, FALSE);
END;
$$;
```

Stored procedures are distinct from functions in several database products. Syntax, transaction restrictions, return values, and invocation commands differ.

Examples of procedural language ecosystems:
- PostgreSQL: SQL and PL/pgSQL (plus supported extensions/languages).
- MySQL: stored programs with `BEGIN ... END`, `DECLARE`, handlers and cursors.
- SQL Server: T-SQL stored procedures and functions.
- Oracle: PL/SQL procedures, functions, packages, and triggers.
- SQLite does not have the same server-side stored-procedure system as traditional client/server RDBMSs; application-defined functions may be registered through its API.

Use routines when they provide a clear data-boundary, permission, or operational benefit; don't move logic into the database by default without considering testability and portability.

---

# 41. Triggers

A trigger executes in response to certain table/database events. Syntax and supported event/timing combinations are vendor-specific.

Typical concepts:
- `BEFORE` trigger
- `AFTER` trigger
- `INSTEAD OF` trigger (supported in some contexts/products)
- Row-level versus statement-level
- Insert/update/delete events
- `OLD` and `NEW` row values or product-specific equivalents

Triggers are used for auditing, derived values, enforcing complex rules, and integration with database-side behavior. They can also create hidden side effects or recursion. Document them and include their effects in testing.

Audit table example (table definition is deliberately omitted):

```sql
-- Pseudocode only: trigger declaration and body differ by database.
-- On product update, write old/new values and timestamp to product_audit.
```

Do not copy trigger syntax from one database into another without adapting it.

---

# 42. Temporary Tables and Table Variables

Temporary table syntax varies.

PostgreSQL/MySQL-style pattern:

```sql
CREATE TEMPORARY TABLE temp_ids (
    id BIGINT PRIMARY KEY
);

INSERT INTO temp_ids (id) VALUES (1), (2), (3);

SELECT p.*
FROM products p
JOIN temp_ids t ON t.id = p.id;
```

SQL Server supports local/global temporary tables with names such as `#temp_ids` / `##temp_ids` and also supports table variables. Lifetime, transaction behavior, indexes, statistics, and scope vary by engine.

Temporary objects can help stage complex operations, but CTEs, derived tables, or regular staging tables may be better depending on size and reuse.

---

# 43. JSON Data

Relational databases increasingly support JSON types and functions, but JSON syntax differs widely.

Generic storage pattern (use the native JSON type supported by your engine where appropriate):

```sql
CREATE TABLE event_logs (
    id BIGINT PRIMARY KEY,
    event_data JSON
);
```

The `JSON` type above is not portable to all versions/engines. PostgreSQL supports `json`/`jsonb`; MySQL has `JSON`; SQL Server commonly works with JSON text plus JSON functions (the exact native type support varies by version); SQLite provides JSON functions in supported builds/extensions; Oracle has version-dependent JSON data type/features.

Common JSON tasks:
- Validate JSON
- Extract a scalar or object
- Query nested values
- Modify/remove a property
- Expand an array to rows
- Build JSON from columns

Examples are vendor-specific:
- PostgreSQL: operators such as `->`, `->>`, and functions such as `jsonb_build_object`.
- MySQL: functions such as `JSON_EXTRACT`, `JSON_SET`, `JSON_OBJECT`.
- SQL Server: functions such as `JSON_VALUE`, `JSON_QUERY`, `JSON_MODIFY`, `OPENJSON`.
- SQLite: functions such as `json_extract`, `json_object`, `json_each`, when available.
- Oracle: SQL/JSON functions such as `JSON_VALUE`, `JSON_QUERY`, and `JSON_TABLE`, subject to version.

Use relational columns for fields that require constraints, joins, and frequent filtering; use JSON for suitably variable or document-oriented attributes. Index JSON expressions only when the database supports the required index type and workload justifies it.

---

# 44. Common Table Design Patterns

## Audit timestamps

A common design includes `created_at` and `updated_at`; automatic update syntax differs by engine. In many applications the backend sets audit timestamps, or the database uses triggers/generated mechanisms.

## Soft delete

```sql
ALTER TABLE products ADD COLUMN deleted_at TIMESTAMP NULL;
```

Queries then filter active records:

```sql
SELECT *
FROM products
WHERE deleted_at IS NULL;
```

Soft deletion needs a consistent policy for uniqueness, foreign keys, restore behavior, and data retention. It is not a replacement for access control.

## Optimistic locking

```sql
ALTER TABLE products ADD COLUMN version BIGINT NOT NULL DEFAULT 0;
```

A version-controlled update may look like this:

```sql
UPDATE products
SET price = :new_price,
    version = version + 1
WHERE id = :id
  AND version = :expected_version;
```

Here `:name` is an illustrative parameter placeholder; exact placeholder syntax depends on your driver/framework/client. The application should detect an affected-row count of zero as a conflict when the protocol requires it.

## Idempotency key

For APIs that must avoid duplicate operations, persist a unique request key and operation outcome within a transaction. A unique constraint often protects the idempotency key; exact schema and workflow depend on the use case.

---

# 45. Security, Users, Roles, and GRANT

SQL permissions are product-specific, but common ideas include:
- Database users/logins
- Roles/groups
- Object-level privileges
- Schema privileges
- Least privilege
- Revocation and auditing

Illustrative syntax (adapt to your engine and administrative model):

```sql
GRANT SELECT, INSERT ON products TO app_role;
REVOKE INSERT ON products FROM app_role;
```

User/role creation differs significantly. Some products distinguish server-level logins and database users; others manage roles at different scopes.

Application database accounts should have only the required permissions. A read-only reporting service should not use a schema-owner/admin account. Protect DDL/administrative privileges, secrets, and backups.

Row-level security policies exist in some database engines and can offer an additional access layer, but policy behavior and role context are database-specific. They do not remove the need to secure the application API.

---

# 46. SQL Injection and Parameterized Queries

**Never concatenate untrusted user input into SQL text.** Use parameterized queries, prepared statements, or a safe query builder/ORM.

Unsafe pattern (do not use):

```text
"SELECT * FROM users WHERE email = '" + userInput + "'"
```

Safe conceptual SQL:

```sql
SELECT id, email
FROM users
WHERE email = :email;
```

`:email` is a named placeholder used by some libraries; it is not the universal placeholder syntax of all SQL clients.

Prepared statement example in JDBC:

```java
String sql = "SELECT id, email FROM users WHERE email = ?";
try (PreparedStatement statement = connection.prepareStatement(sql)) {
    statement.setString(1, email);
    try (ResultSet result = statement.executeQuery()) {
        while (result.next()) {
            System.out.println(result.getLong("id"));
        }
    }
}
```

Parameterized values cannot generally stand in for table names, column names, or sort-direction keywords. For dynamic identifiers, select from a strict allowlist and quote according to the target database. Parameterization does not replace authorization or input validation.

---

# 47. Query Plans and Performance Tuning

Read the query plan using your engine's tools:
- PostgreSQL: `EXPLAIN`, and `EXPLAIN ANALYZE` when safe/appropriate.
- MySQL: `EXPLAIN`, plus version-specific `EXPLAIN ANALYZE` functionality.
- SQL Server: execution plans and `SET STATISTICS IO/TIME`.
- SQLite: `EXPLAIN QUERY PLAN`.
- Oracle: execution plan tooling and `DBMS_XPLAN`.

Illustrative query:

```sql
EXPLAIN
SELECT id, name
FROM products
WHERE category_id = 5
ORDER BY name;
```

`EXPLAIN` syntax is not exactly the same across all engines. Some forms actually execute the statement or have specific impact; understand the mode before using it on a production system.

Performance checklist:
1. Select only necessary columns.
2. Filter early when logically appropriate.
3. Index frequently used join/filter/order columns based on workload.
4. Avoid N+1 query patterns in application code.
5. Use pagination and server-side filtering.
6. Check actual query plans and row estimates.
7. Avoid unnecessary casts and functions around indexed columns.
8. Keep statistics maintained according to the engine.
9. Use connection pooling in typical backend applications.
10. Measure before optimizing; do not presume an index is beneficial.
11. Watch locks, waits, temp storage, memory, and network round trips.
12. Beware of very large `IN` lists and repeated round trips.

A **full table scan** is not always a problem; it may be optimal for small tables or when a query needs most rows.

---

# 48. Backup, Restore, and Migration Concepts

Backups and schema migrations are not interchangeable:
- **Backup/restore** protects or reproduces database state.
- **Migration** changes the schema/data in a controlled, versioned sequence.
- **Replication** copies changes to another node/system and is not a substitute for a tested backup.

Use tools for the selected engine. Examples include `pg_dump`/`pg_restore` for PostgreSQL, `mysqldump` or native backup tooling for MySQL, SQL Server backup/restore commands and tools, SQLite file-aware backup mechanisms, and Oracle RMAN/export tooling.

Operational checklist:
- Automate backups.
- Encrypt backup files and restrict access.
- Store backups separately from the primary environment.
- Define recovery point objective (RPO) and recovery time objective (RTO).
- Test restores regularly.
- Keep migration scripts in version control.
- Review whether migration locks/rewrites could cause downtime.
- Back up before destructive data migrations.
- Have a rollback or forward-fix plan.

Exact backup commands require database-specific options; check official documentation for your engine/version and environment.

---

# 49. Database-Specific Syntax Guide

This section highlights portability traps. It is not an exhaustive comparison of every vendor feature.

## 49.1 Auto-generated identity columns

PostgreSQL modern identity example:

```sql
CREATE TABLE users (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL
);
```

MySQL:

```sql
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL
);
```

SQL Server:

```sql
CREATE TABLE users (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(120) NOT NULL
);
```

SQLite:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
```

In SQLite, `INTEGER PRIMARY KEY` has rowid/identity behavior; `AUTOINCREMENT` has additional semantics and should not be added automatically without a reason.

Oracle supports identity columns in modern versions, for example:

```sql
CREATE TABLE users (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name VARCHAR2(120) NOT NULL
);
```

Check the selected Oracle release and compatibility level.

## 49.2 Row limit

PostgreSQL/MySQL/SQLite:

```sql
SELECT * FROM products LIMIT 10;
```

SQL Server:

```sql
SELECT TOP (10) * FROM products ORDER BY id;
```

Standard-style/modern forms (supported by several products):

```sql
SELECT *
FROM products
ORDER BY id
FETCH FIRST 10 ROWS ONLY;
```

Use `ORDER BY` whenever the intended first/next rows matter.

## 49.3 Upsert

- PostgreSQL: `INSERT ... ON CONFLICT ... DO UPDATE`
- MySQL: `INSERT ... ON DUPLICATE KEY UPDATE`
- SQLite: supports `ON CONFLICT` / UPSERT syntax in modern versions
- SQL Server: may use a carefully reviewed `MERGE` or transactional update/insert pattern
- Oracle: supports `MERGE`

Confirm current-version concurrency guidance before choosing an upsert strategy.

## 49.4 String concatenation

- PostgreSQL: `a || b`, `CONCAT(a, b)`
- MySQL: `CONCAT(a, b)`; `||` normally behaves as logical OR unless SQL mode alters it
- SQL Server: `CONCAT(a, b)` or `+` with null/type considerations
- SQLite: `a || b` and supported `concat` function
- Oracle: `a || b`

## 49.5 Null fallback

- Standard-style: `COALESCE(a, b)`
- MySQL / SQLite: `IFNULL(a, b)` is available
- SQL Server: `ISNULL(a, b)` or `COALESCE`
- Oracle: `NVL(a, b)` or `COALESCE`

`ISNULL` and `NVL` are not exact interchangeable type/semantics substitutes in all cases.

## 49.6 Date/time syntax

Date arithmetic and formatting functions are especially non-portable. Compare Section 21 and consult the function reference for the actual engine. Prefer parameters or typed date values over building date strings manually.

## 49.7 Stored routines and procedural languages

PostgreSQL PL/pgSQL, MySQL stored programs, SQL Server T-SQL, and Oracle PL/SQL have distinct variables, flow control, exception handling, delimiter/client rules, routine syntax, and transaction behavior. They should be learned from their own references.

## 49.8 Transaction control and DDL

Some DDL statements commit implicitly in some engines; others participate in transactions in selected engines/contexts. Do not assume a DDL statement can always be rolled back.

---

# 50. Full CRUD Example

This example describes a simple `products` table and basic CRUD. Adapt identity syntax, data types, and Boolean values to the actual database.

## Create the table (PostgreSQL-style identity)

```sql
CREATE TABLE products (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    price DECIMAL(12, 2) NOT NULL CHECK (price >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Create

```sql
INSERT INTO products (name, description, price)
VALUES ('Mechanical Keyboard', 'Compact keyboard', 2499.00);
```

## Read all active products

```sql
SELECT id, name, price
FROM products
WHERE is_active = TRUE
ORDER BY name
LIMIT 20;
```

Replace `LIMIT` and Boolean literal syntax if the target dialect differs.

## Read one product

```sql
SELECT id, name, description, price, is_active
FROM products
WHERE id = :product_id;
```

`:product_id` is a placeholder notation used by some clients/frameworks; use the parameter syntax supported by your database driver.

## Update

```sql
UPDATE products
SET price = :new_price
WHERE id = :product_id;
```

## Soft-delete example

```sql
ALTER TABLE products ADD COLUMN deleted_at TIMESTAMP NULL;

UPDATE products
SET deleted_at = CURRENT_TIMESTAMP
WHERE id = :product_id
  AND deleted_at IS NULL;
```

## Hard delete

```sql
DELETE FROM products
WHERE id = :product_id;
```

Always define which delete strategy the application uses and how dependent rows are handled.

---

# 51. Query Patterns for Real Applications

## Search by optional text

```sql
SELECT id, name, price
FROM products
WHERE is_active = TRUE
  AND name LIKE :pattern
ORDER BY name;
```

The application should bind `:pattern` as a parameter and decide how to handle wildcard characters and case sensitivity. Do not concatenate raw text into SQL.

## Filter by a set of values

```sql
SELECT id, name
FROM products
WHERE category_id IN (:category_ids);
```

Many drivers cannot bind an arbitrary list into a single placeholder in this exact form; use your driver's supported array/list binding, a table-valued parameter, JSON/table expansion, or a safe dynamically sized placeholder list.

## Count records per customer

```sql
SELECT customer_id, COUNT(*) AS orders_count
FROM orders
GROUP BY customer_id
ORDER BY orders_count DESC;
```

## Customers with no orders

```sql
SELECT c.id, c.full_name
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);
```

## Latest order per customer (window function)

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY order_date DESC, id DESC
        ) AS rn
    FROM orders o
)
SELECT *
FROM ranked_orders
WHERE rn = 1;
```

## Monthly total (date extraction varies)

For a database that supports the shown syntax:

```sql
SELECT
    EXTRACT(YEAR FROM order_date) AS order_year,
    EXTRACT(MONTH FROM order_date) AS order_month,
    SUM(total) AS monthly_total
FROM orders
GROUP BY
    EXTRACT(YEAR FROM order_date),
    EXTRACT(MONTH FROM order_date)
ORDER BY order_year, order_month;
```

For large tables, consider a date-range filter on the original column so a normal index can be used effectively.

---

# 52. Common Errors and Debugging

| Symptom | Common cause to inspect |
|---|---|
| Syntax error | SQL dialect/version mismatch, misspelled keyword, missing comma/parenthesis |
| Table/column not found | Wrong schema/database, case-sensitive quoted name, migration not applied |
| Duplicate key | Unique or primary-key conflict |
| Foreign-key violation | Parent row missing or dependent rows block the operation |
| Cannot insert NULL | `NOT NULL` constraint or omitted required column |
| Data truncation | String length or numeric precision too small |
| Type conversion error | Unexpected input type/date format/implicit conversion |
| Group-by error | Selected expression is neither grouped nor properly aggregated |
| Ambiguous column | Same column name in joined tables; qualify with alias |
| More rows than expected | Join cardinality issue or missing join condition |
| Fewer rows than expected | Inner join/filter/null logic, misplaced outer-join condition |
| Slow query | Missing or unsuitable index, poor plan, large sort, locks, repeated queries |
| Deadlock | Concurrent transactions acquire locks in conflicting orders |
| Migration fails | Schema drift, incompatible DDL, existing invalid data |
| `NULL` results from comparison | SQL three-valued logic; use `IS NULL` and explicit fallback |
| Unique conflict with nullable values | Product-specific handling of NULL in unique columns |

Helpful practice:
1. Reproduce the query with a small dataset.
2. Confirm the connected database and schema.
3. Inspect the exact error message and database version.
4. Start with a smaller `SELECT`.
5. Check row counts at each join/filter step.
6. Inspect the execution plan for performance problems.
7. Test constraints and transaction rollback in a non-production environment.

---

# 53. SQL Functions Reference by Category

This is a practical category-based shortlist of common functions. It is intentionally not claimed to be an exhaustive inventory of every function in every product.

## Aggregate functions

| Function | Typical purpose |
|---|---|
| `COUNT(*)` | Count rows |
| `COUNT(expr)` | Count non-null values |
| `COUNT(DISTINCT expr)` | Count distinct non-null values |
| `SUM(expr)` | Add values |
| `AVG(expr)` | Average |
| `MIN(expr)` / `MAX(expr)` | Minimum / maximum |
| `STRING_AGG` / `GROUP_CONCAT` / `LISTAGG` | Concatenate group values; dialect-specific |
| `BOOL_AND` / `BOOL_OR` | Boolean aggregation in supported engines |
| `VAR_POP` / `VAR_SAMP` | Population/sample variance where available |
| `STDDEV_POP` / `STDDEV_SAMP` | Population/sample standard deviation where available |
| Percentile functions | Statistical percentile; syntax and availability differ |

## Window functions

`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`, `NTH_VALUE`, and aggregates with `OVER(...)`.

## String functions

`LOWER`, `UPPER`, `TRIM`, `LTRIM`, `RTRIM`, `LENGTH`, `CHAR_LENGTH`, `SUBSTRING`, `REPLACE`, `CONCAT`, `POSITION`/`INSTR`/`CHARINDEX`, `LEFT`, `RIGHT`, `REPEAT`/`REPLICATE`, `LPAD`, `RPAD`, `REVERSE`, `SPLIT_PART`, `FORMAT`.

## Numeric functions

`ABS`, `ROUND`, `CEIL`/`CEILING`, `FLOOR`, `TRUNC`/`TRUNCATE`, `MOD`, `POWER`/`POW`, `SQRT`, `SIGN`, `EXP`, `LN`, `LOG`, `LOG10`, `PI`, `RAND`/`RANDOM`, `GREATEST`, `LEAST`.

## Date and time functions

`CURRENT_DATE`, `CURRENT_TIME`, `CURRENT_TIMESTAMP`, `EXTRACT`, `DATEADD`, `DATEDIFF`, `DATE_ADD`, `DATE_SUB`, `DATE_TRUNC`, `TO_CHAR`, `DATE_FORMAT`, `STRFTIME`, `MONTHS_BETWEEN`, `AGE`, `DATE_PART`. **Availability and argument syntax are dialect-specific.**

## Conditional and null-handling functions

`CASE`, `COALESCE`, `NULLIF`, `IIF`, `IF`, `IFNULL`, `ISNULL`, `NVL`, `NVL2`, `DECODE`. Do not assume vendor-specific functions exist elsewhere.

## Conversion functions

`CAST(expr AS type)` is the standard-style form. `CONVERT` and `TRY_CONVERT` are used in specific dialects; parsing/formatting functions also vary. Prefer typed parameters from application code instead of converting arbitrary strings repeatedly inside a query.

## JSON functions

Examples by engine include PostgreSQL `jsonb_*` functions/operators, MySQL `JSON_*`, SQL Server `JSON_VALUE` / `JSON_QUERY` / `JSON_MODIFY` / `OPENJSON`, SQLite `json_*`, and Oracle SQL/JSON functions. Consult each engine's JSON reference.

## Information and utility functions

Functions for current user, session identity, database/server version, generated IDs, sequence values, and system metadata differ by engine. Examples include PostgreSQL `current_user`, MySQL `CURRENT_USER()`, and SQL Server `SUSER_SNAME()` / `DB_NAME()`. Use the proper documented function for your engine.

## Regular expressions and full-text search

PostgreSQL regex operators/functions, MySQL regex functions, SQL Server full-text search, SQLite optional/extension features, and Oracle regex functions do not share one portable syntax. Learn these only after basic query/filter/index skills.

For an authoritative complete function list, use the official reference for the exact database product/version in Section 57.

---

# 54. Full-Stack Integration

A backend API often uses SQL through:
- JDBC / prepared statements
- Spring JDBC or `JdbcTemplate`
- Spring Data JPA / Hibernate
- Node.js database drivers and query builders
- Python database drivers/ORMs
- .NET data providers / Entity Framework
- Other language-specific client libraries

Best practices:
1. Keep credentials and database access on the server.
2. Bind request values as query parameters.
3. Validate incoming data and enforce authorization.
4. Use transactions for multi-step business operations.
5. Avoid selecting/returning columns that the caller does not need.
6. Use DTOs/API schemas rather than leaking internal table structure.
7. Paginate and filter large result sets at the database layer.
8. Define migration scripts and test them in CI.
9. Add indexes based on query plans and real workload.
10. Protect sensitive data in logs, traces, errors, backups, and test fixtures.
11. Use a least-privilege database role per service where practical.
12. Test failure conditions, concurrent requests, and rollback behavior.

An ORM does not eliminate the need to understand SQL. Learn the generated queries and transaction behavior of your framework.

---

# 55. Practice Projects

Build projects in increasing complexity:

1. **Student records:** table creation, constraints, insert, update, delete, filtering.
2. **Library database:** authors, books, members, loans, joins, aggregate reports.
3. **Online shop:** products, categories, customers, orders, order items, foreign keys.
4. **Expense tracker:** dates, categories, totals, grouping, monthly reports.
5. **Anime catalog:** series, seasons, episodes, genres, search, pagination.
6. **Discussion platform:** users, posts, comments, moderation records, indexes.
7. **Inventory service:** stock transactions, locking, optimistic concurrency, audit history.
8. **Analytics dashboard:** CTEs, window functions, materialized/reporting summaries.
9. **Multi-tenant SaaS database:** tenant boundaries, permissions, tenant-aware constraints.
10. **Production-style backend:** migrations, backup/restore drills, tests, observability, query-plan review.

Every project should have a schema diagram, migration scripts, seeded test data, constraints, safe parameterized queries, and tests for expected and invalid behavior.

---

# 56. Quick Syntax Cheat Sheet

```sql
-- Create a table (adapt identity/type syntax to your database)
CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    price DECIMAL(12, 2) NOT NULL CHECK (price >= 0)
);

-- Insert
INSERT INTO products (id, name, price)
VALUES (1, 'Keyboard', 2499.00);

-- Read
SELECT id, name, price
FROM products
WHERE price < 5000
ORDER BY price DESC;

-- Update
UPDATE products
SET price = 1999.00
WHERE id = 1;

-- Delete
DELETE FROM products
WHERE id = 1;

-- Count / group
SELECT COUNT(*) AS total
FROM products;

SELECT price, COUNT(*) AS item_count
FROM products
GROUP BY price
HAVING COUNT(*) > 1;

-- Join
SELECT c.full_name, o.id
FROM customers c
JOIN orders o ON o.customer_id = c.id;

-- Subquery / existence
SELECT c.id
FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id
);

-- CTE
WITH active AS (
    SELECT * FROM products WHERE is_active = TRUE
)
SELECT * FROM active;

-- Window function
SELECT
    id,
    name,
    ROW_NUMBER() OVER (ORDER BY name) AS row_number
FROM products;

-- Transaction (client/database syntax may vary)
BEGIN;
UPDATE accounts SET balance = balance - 10 WHERE id = 1;
COMMIT;

-- Index
CREATE INDEX idx_products_name ON products(name);

-- View
CREATE VIEW active_products AS
SELECT id, name, price
FROM products
WHERE is_active = TRUE;
```

---

# 57. Official Documentation

Choose the documentation matching the database engine and release you actually run.

- **PostgreSQL**
  - [SQL Syntax](https://www.postgresql.org/docs/current/sql-syntax.html)
  - [SQL Commands](https://www.postgresql.org/docs/current/sql-commands.html)
  - [Functions and Operators](https://www.postgresql.org/docs/current/functions.html)
  - [Queries / SELECT](https://www.postgresql.org/docs/current/queries.html)
  - [Indexes](https://www.postgresql.org/docs/current/indexes.html)
  - [Transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)

- **MySQL 8.4**
  - [MySQL Reference Manual](https://dev.mysql.com/doc/refman/8.4/en/)
  - [SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/sql-statements.html)
  - [Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/functions.html)
  - [Data Types](https://dev.mysql.com/doc/refman/8.4/en/data-types.html)

- **Microsoft SQL Server / T-SQL**
  - [Transact-SQL Reference](https://learn.microsoft.com/en-us/sql/t-sql)
  - [T-SQL Statements](https://learn.microsoft.com/en-us/sql/t-sql/statements/statements)
  - [Functions](https://learn.microsoft.com/en-us/sql/t-sql/functions/functions)

- **SQLite**
  - [SQL Language Reference](https://sqlite.org/lang.html)
  - [SQL Expressions](https://sqlite.org/lang_expr.html)
  - [Core Functions](https://sqlite.org/lang_corefunc.html)
  - [Aggregate Functions](https://sqlite.org/lang_aggfunc.html)
  - [Date and Time Functions](https://sqlite.org/lang_datefunc.html)

- **Oracle Database**
  - [SQL Language Reference](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/index.html)
  - [SQL Functions Quick Reference](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlqr/SQL-Functions.html)

- **SQL Standard**
  - SQL standards are published by ISO/IEC and access may require purchase. Vendor documentation explains the exact implementation and extensions.

---

## Final Note

Use this guide as a broad learning reference, then practice in a disposable local database. SQL syntax and behavior differ across engines, especially in identity columns, date arithmetic, pagination, string concatenation, JSON, upserts, stored routines, transactions, and administration. The authoritative source for an exact syntax or full function inventory is the documentation for the database product and version you use.
