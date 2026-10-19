# MongoDB Complete Guide for Full-Stack Development
## MongoDB Query Language, `mongosh` Methods, CRUD, Aggregation Operators, Indexes, Transactions, Security, and Drivers

> **Purpose:** A comprehensive learning/reference file for using MongoDB in full-stack applications.
>
> **Important scope note:** MongoDB is not just a single query syntax. It includes BSON data types, the MongoDB Query Language (MQL), CRUD methods, aggregation pipeline stages and expressions, database commands, indexes, transactions, change streams, security, Atlas services, plus separate APIs for `mongosh` and programming-language drivers. These APIs evolve across server, shell, and driver versions. No honest single Markdown file can guarantee every method and every present/future feature. This guide covers the core language and major production patterns; use the official versioned documentation linked at the end for exact signatures and compatibility.
>
> **Examples:** Shell examples use modern `mongosh` JavaScript-style syntax. Node.js examples use the official MongoDB Node.js driver. `mongosh` helpers are not identical to Node.js driver APIs.

---

## Table of Contents

1. MongoDB Overview
2. Installation, Atlas, and `mongosh`
3. Connecting to a Deployment
4. BSON Types and Documents
5. Database and Collection Basics
6. Create Collections and Validation Rules
7. Insert Documents
8. Find Documents: Basic Queries
9. Query Comparison Operators
10. Logical, Element, Array, and Evaluation Operators
11. Projection, Sorting, Limit, and Skip
12. Update Documents
13. Update Operators
14. Update Pipelines and Array Updates
15. Replace Documents
16. Delete Documents
17. Upserts and Bulk Writes
18. Aggregation Pipeline Fundamentals
19. Common Aggregation Stages
20. Aggregation Expression Operators
21. Array Operators
22. String, Numeric, Date, and Conditional Expressions
23. Grouping and Accumulators
24. Lookup, Unwind, Facets, and Multi-Collection Aggregation
25. Window Functions and Set Operators
26. Aggregation Performance
27. Indexes and Index Types
28. Query Plans and Explain
29. Data Modeling and Schema Design
30. Embedding vs Referencing
31. Atomicity and Transactions
32. Read/Write Concern and Read Preference
33. Validation, Schema Rules, and Data Integrity
34. Geospatial Queries
35. Text Search, Atlas Search, and Vector Search
36. Change Streams and Event-Driven Systems
37. Security, Roles, and Access Control
38. Backup, Restore, Import, and Export
39. `mongosh` Methods and Shell Helpers
40. Node.js Driver Integration
41. Mongoose Overview
42. Python Driver Integration
43. MongoDB with Spring Boot / Java Overview
44. Monitoring, Troubleshooting, and Performance
45. Full CRUD Example
46. Common Query Patterns
47. MongoDB Operator and Method Quick Reference
48. Practice Projects and Learning Roadmap
49. Official Documentation

---

# 1. MongoDB Overview

MongoDB is a document-oriented database. It stores BSON documents in collections, grouped under databases.

Relational terminology vs MongoDB:

| Relational database | MongoDB |
|---|---|
| Database | Database |
| Table | Collection |
| Row | Document |
| Column | Field |
| Primary key | Usually `_id` |
| Join table / relation | References, embedding, or `$lookup` |
| SQL | MongoDB Query Language (MQL) and aggregation pipeline |

Example document:

```javascript
{
  _id: ObjectId("65f000000000000000000001"),
  title: "Example Anime",
  year: 2025,
  genres: ["Action", "Fantasy"],
  rating: 8.7,
  isActive: true,
  studio: {
    name: "Example Studio",
    country: "Japan"
  }
}
```

MongoDB is flexible-schema by default, but production collections should still have deliberate data models, validation, indexes, access control, and migration procedures.

Important:
- Documents are BSON, a binary representation with additional types beyond JSON.
- Each document has a unique `_id` within its collection; MongoDB normally creates one if omitted.
- Single-document writes are atomic.
- Multi-document transactions are available on supported deployment configurations.
- Aggregation pipelines transform and summarize data.
- Indexes can improve queries but add storage and write overhead.

---

# 2. Installation, Atlas, and `mongosh`

Options:
- MongoDB Community Server installed locally.
- MongoDB Atlas managed deployment.
- A containerized MongoDB deployment for development/testing.
- A development environment supplied by a project/team.

`mongosh` is the modern MongoDB shell. It supports JavaScript syntax and shell helpers, but it is not the same thing as the legacy `mongo` shell or an application's official database driver.

Check client version:

```bash
mongosh --version
```

Connect to local default deployment:

```bash
mongosh
```

Connect with an explicit connection string:

```bash
mongosh "mongodb://localhost:27017"
```

Atlas URI template:

```bash
mongosh "mongodb+srv://<cluster-host>/<database>" --username <database-user>
```

Replace placeholders with values from your own deployment configuration. Never publish passwords or complete credential-bearing connection strings.

Within `mongosh`:

```javascript
db
show dbs
show collections
help
db.help()
db.products.help()
```

Commands such as `show dbs` are shell helpers, not ordinary database methods in the same sense as `find()`.

---

# 3. Connecting to a Deployment

Common URI shapes:

```text
mongodb://hostname:27017/database
mongodb://user:password@hostname:27017/database?authSource=admin
mongodb+srv://hostname/database
```

Real connection strings may include options for replica sets, TLS, authentication, read preference, timeouts, and other settings. Use the URI provided by your administrator/Atlas setup and the documentation for your driver.

Security checklist:
- Use a dedicated database user with least privilege.
- Enable TLS for network paths that require it.
- Restrict network access to known clients.
- Store secrets in environment variables or a secrets manager.
- Rotate leaked credentials immediately.
- Never put database credentials in frontend JavaScript or a public repository.
- Use connection pooling through a long-lived driver client.
- Avoid creating one database client per incoming HTTP request.

---

# 4. BSON Types and Documents

Common BSON types exposed by MongoDB include:

- `String`
- `Double`
- `Decimal128`
- `Int32`
- `Long`
- `Boolean`
- `ObjectId`
- `Date`
- `Timestamp` (MongoDB internal/logical timestamp type; not interchangeable with ordinary date/time values)
- `Null`
- `Array`
- `Object` / embedded document
- `Binary`
- `Regular Expression`
- `MinKey`, `MaxKey`
- `JavaScript` and some legacy BSON types with limited/deprecated usage

Example:

```javascript
{
  name: "Asha",
  age: 22,
  active: true,
  score: 93.5,
  tags: ["python", "ai"],
  address: {
    city: "Chennai",
    country: "India"
  },
  createdAt: new Date()
}
```

## ObjectId

```javascript
const id = new ObjectId();
db.users.findOne({ _id: id });
```

In `mongosh`, `ObjectId()` is available. Driver applications generally import ObjectId from their driver package.

Do not assume that ObjectId's timestamp component is an authoritative business timestamp or that IDs are secret. Use explicit timestamps for business events.

## Date

```javascript
const now = new Date();
const specific = ISODate("2025-01-01T00:00:00Z"); // Shell helper
```

In application drivers, construct dates using the host language's date/time API and preserve the intended UTC/time-zone semantics.

## Field names and nesting

```javascript
{
  "profile.displayName": "Asha",  // A literal dotted field name is not the same as a nested path
  profile: {
    displayName: "Asha"
  }
}
```

In a query, `"profile.displayName"` normally means the nested field path. Avoid field names containing `.` or beginning with `$` for ordinary application documents unless using a documented special case.

---

# 5. Database and Collection Basics

Select or create a database in `mongosh`:

```javascript
use anime_portal
```

The database may not appear in `show dbs` until it contains data or metadata as appropriate.

List collection names:

```javascript
show collections
db.getCollectionNames()
```

Access a collection:

```javascript
db.users
db.getCollection("users")
```

The latter is useful for collection names that do not work naturally with property access.

Drop a collection:

```javascript
db.temporary_data.drop()
```

Drop current database:

```javascript
db.dropDatabase()
```

**Danger:** `drop()` and `dropDatabase()` are destructive. Confirm environment and backups before executing them.

Create a collection explicitly:

```javascript
db.createCollection("products")
```

Explicit collection creation is useful when configuring validation, capped collections, time-series options, or other collection options. Ordinary inserts can create a collection implicitly in many situations.

---

# 6. Create Collections and Validation Rules

Basic creation:

```javascript
db.createCollection("products")
```

Collection with a JSON Schema validator:

```javascript
db.createCollection("products", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "price"],
      properties: {
        name: {
          bsonType: "string",
          minLength: 1,
          maxLength: 120,
          description: "Product name is required"
        },
        price: {
          bsonType: ["int", "long", "double", "decimal"],
          minimum: 0
        },
        isActive: {
          bsonType: "bool"
        }
      }
    }
  },
  validationLevel: "strict",
  validationAction: "error"
})
```

Validation options include:
- `validationLevel`: commonly `strict` or `moderate`.
- `validationAction`: commonly `error` or `warn`.
- `$jsonSchema`: document schema validation rules.

Exact options and behavior are version-dependent. Database validation is a useful integrity layer but does not replace application-level authorization or all business validation.

Modify a collection validator (check the selected server version/permissions):

```javascript
db.runCommand({
  collMod: "products",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name"],
      properties: {
        name: { bsonType: "string" }
      }
    }
  }
})
```

---

# 7. Insert Documents

## `insertOne()`

```javascript
db.products.insertOne({
  name: "Keyboard",
  price: 2499,
  isActive: true,
  createdAt: new Date()
})
```

MongoDB generates `_id` if it is omitted.

## `insertMany()`

```javascript
db.products.insertMany([
  { name: "Mouse", price: 799, isActive: true },
  { name: "Monitor", price: 12999, isActive: true },
  { name: "USB Hub", price: 999, isActive: false }
])
```

The operation is ordered by default in common driver/shell behavior: an error can stop later ordered inserts. Unordered insertion can continue processing eligible operations after individual errors, but exact handling should be checked in the API documentation.

## Insert with explicit `_id`

```javascript
db.users.insertOne({
  _id: "user-1001",
  name: "Asha",
  email: "asha@example.com"
})
```

`_id` must be unique within the collection. Its type need not always be ObjectId, but using one stable ID type per collection simplifies application logic.

---

# 8. Find Documents: Basic Queries

## All documents

```javascript
db.products.find()
```

## Match a field

```javascript
db.products.find({ isActive: true })
db.products.find({ category: "Books" })
```

## Exact embedded document matching

```javascript
db.users.find({
  address: {
    city: "Chennai",
    country: "India"
  }
})
```

Embedded-document equality can depend on exact document contents and field order. To match individual embedded fields, use dot notation:

```javascript
db.users.find({
  "address.city": "Chennai"
})
```

## Nested document fields

```javascript
db.users.find({
  "profile.displayName": "Asha"
})
```

## Find one

```javascript
db.products.findOne({ name: "Keyboard" })
```

Without a deterministic sort, a “first” matching document does not necessarily mean the oldest/newest record.

## Query arrays by exact value

```javascript
db.products.find({ tags: "wireless" })
```

For an array field, this commonly matches documents where the array contains that value.

---

# 9. Query Comparison Operators

MongoDB comparison operators are usually expressed as field-value documents.

| Operator | Meaning |
|---|---|
| `$eq` | Equal |
| `$ne` | Not equal |
| `$gt` | Greater than |
| `$gte` | Greater than or equal |
| `$lt` | Less than |
| `$lte` | Less than or equal |
| `$in` | Value matches one of a list |
| `$nin` | Value does not match list, with MongoDB's missing-field behavior |

Examples:

```javascript
db.products.find({ price: { $gt: 1000 } })
db.products.find({ price: { $gte: 500, $lte: 5000 } })
db.products.find({ category: { $in: ["Books", "Games"] } })
db.products.find({ category: { $nin: ["Archived"] } })
db.users.find({ age: { $ne: 18 } })
```

Important: `$ne` and `$nin` can match documents where the field is missing. Add `$exists: true` if the logic requires an existing field.

---

# 10. Logical, Element, Array, and Evaluation Operators

## Logical operators

- `$and`
- `$or`
- `$nor`
- `$not`

```javascript
db.products.find({
  $and: [
    { isActive: true },
    { price: { $lt: 5000 } }
  ]
})
```

Equivalent straightforward conditions on distinct fields can usually be written as:

```javascript
db.products.find({
  isActive: true,
  price: { $lt: 5000 }
})
```

```javascript
db.products.find({
  $or: [
    { category: "Books" },
    { price: { $lt: 500 } }
  ]
})
```

```javascript
db.products.find({
  price: { $not: { $gt: 5000 } }
})
```

`$not` applies to an operator expression; its treatment of missing fields can be surprising. Prefer precise conditions and test the edge cases.

## Element operators

- `$exists`: field exists
- `$type`: field has a BSON type or matches one of specified types

```javascript
db.users.find({ phone: { $exists: true } })
db.users.find({ age: { $type: "int" } })
db.users.find({ score: { $type: ["int", "double", "decimal"] } })
```

## Evaluation operators

- `$regex`
- `$expr`
- `$jsonSchema`
- `$mod`
- `$text` (text index/search behavior)
- `$where` exists in some contexts but executing server-side JavaScript has restrictions/performance/security implications; do not use it as a normal replacement for indexed query operators.

Regex examples:

```javascript
db.users.find({ name: { $regex: "^ash", $options: "i" } })
db.users.find({ email: { $regex: "@example\\.com$" } })
```

Regex syntax and index performance depend on the pattern and collation. Avoid catastrophic/backtracking-prone untrusted patterns.

`$expr` compares or calculates expressions inside a query:

```javascript
db.products.find({
  $expr: { $gt: ["$price", "$cost"] }
})
```

`$mod`:

```javascript
db.products.find({
  quantity: { $mod: [2, 0] }
})
```

This matches even quantities.

---

# 11. Projection, Sorting, Limit, and Skip

Projection chooses which fields to include or exclude.

```javascript
db.products.find(
  { isActive: true },
  { name: 1, price: 1 }
)
```

Exclude fields:

```javascript
db.users.find(
  {},
  { passwordHash: 0 }
)
```

In many projection forms, inclusion and exclusion cannot be mixed except for `_id`. Verify projection rules for more complex nested cases.

Sort:

```javascript
db.products.find().sort({ price: 1 })
db.products.find().sort({ price: -1, name: 1 })
```

- `1`: ascending
- `-1`: descending

Limit and skip:

```javascript
db.products.find().sort({ _id: 1 }).skip(20).limit(10)
```

For large collections and deep pages, keyset/range pagination using a stable indexed sort key is often more efficient than large `skip()` values.

---

# 12. Update Documents

## `updateOne()`

```javascript
db.products.updateOne(
  { _id: ObjectId("65f000000000000000000001") },
  { $set: { price: 2799, isActive: true } }
)
```

## `updateMany()`

```javascript
db.products.updateMany(
  { isActive: false },
  { $set: { archived: true } }
)
```

Without a matching filter, an update may match no documents or may affect many/all documents depending on the method. Review the filter before running a bulk update.

## Update results

Typical results include fields such as:
- matched count
- modified count
- upserted ID

A matched document may not count as modified if the updated values do not actually change.

---

# 13. Update Operators

Update operators change document fields without requiring a full replacement.

## Field updates

- `$set`: set a value
- `$unset`: remove a field
- `$rename`: rename a field
- `$setOnInsert`: set fields only when an upsert inserts a new document
- `$currentDate`: set a field to the current date/timestamp form

```javascript
db.users.updateOne(
  { _id: 1001 },
  {
    $set: { displayName: "Asha K" },
    $unset: { oldField: "" },
    $currentDate: { updatedAt: true }
  }
)
```

## Numeric updates

- `$inc`: increment/decrement
- `$mul`: multiply
- `$min`: set only if specified value is less than current value or current field is missing
- `$max`: set only if specified value is greater than current value or current field is missing

```javascript
db.inventory.updateOne(
  { sku: "ABC-100" },
  { $inc: { quantity: -1 } }
)
```

Add a condition if quantity must not become negative; a bare decrement does not enforce that business rule.

## Arrays

- `$push`
- `$addToSet`
- `$pop`
- `$pull`
- `$pullAll`

```javascript
db.users.updateOne(
  { _id: 1001 },
  { $addToSet: { interests: "AI" } }
)
```

Push an item:

```javascript
db.users.updateOne(
  { _id: 1001 },
  { $push: { history: { action: "login", at: new Date() } } }
)
```

Modifiers used with `$push` where supported:
- `$each`
- `$position`
- `$slice`
- `$sort`

```javascript
db.users.updateOne(
  { _id: 1001 },
  {
    $push: {
      scores: {
        $each: [75, 82, 91],
        $sort: -1,
        $slice: 10
      }
    }
  }
)
```

`$addToSet` prevents adding a duplicate array element under document equality rules; it does not generally deduplicate pre-existing array content.

---

# 14. Update Pipelines and Array Updates

MongoDB supports aggregation-pipeline updates in supported server versions. They use pipeline stages such as `$set`/`$addFields`, `$project`, `$unset`, `$replaceRoot`, and `$replaceWith` according to the update-pipeline rules.

```javascript
db.products.updateMany(
  { isActive: true },
  [
    {
      $set: {
        priceWithTax: { $multiply: ["$price", 1.18] }
      }
    }
  ]
)
```

This is different from the update-operator document `{$set: {field: value}}`; in a pipeline update, `$set` is an aggregation stage and values are expressions.

## Array filters

```javascript
db.orders.updateOne(
  { _id: 5001 },
  { $set: { "items.$[item].status": "packed" } },
  { arrayFilters: [{ "item.sku": "ABC-100" }] }
)
```

Positional array update forms:
- `$`: first matching array element for supported query/update cases
- `$[]`: all array elements
- `$[identifier]`: array elements matching an `arrayFilters` predicate

The positional `$` operator requires an appropriate array-match condition and has restrictions. Check the server manual for nested arrays and ambiguous matches.

---

# 15. Replace Documents

`replaceOne()` replaces the matched document's fields with the replacement document (apart from identifier handling rules); it is not the same as `$set`.

```javascript
db.products.replaceOne(
  { _id: ObjectId("65f000000000000000000001") },
  {
    name: "Keyboard Pro",
    price: 2999,
    isActive: true
  }
)
```

Fields omitted from the replacement are removed. This can accidentally delete important fields, so prefer `$set`/`$unset` updates for partial changes.

---

# 16. Delete Documents

Delete one matching document:

```javascript
db.products.deleteOne({ _id: 1001 })
```

Delete all matching documents:

```javascript
db.products.deleteMany({ isActive: false })
```

Delete every document in a collection:

```javascript
db.products.deleteMany({})
```

Delete the collection itself:

```javascript
db.products.drop()
```

Before bulk deletion, preview the filter with `find()` and `countDocuments()`. Understand backups, retention, and access policies. `deleteMany({})` is not the same as dropping a collection; deleting all documents retains the collection and its indexes.

---

# 17. Upserts and Bulk Writes

Upsert inserts a document if the filter matches none; otherwise it updates a matching document.

```javascript
db.settings.updateOne(
  { key: "theme" },
  {
    $set: { value: "dark" },
    $setOnInsert: { createdAt: new Date() }
  },
  { upsert: true }
)
```

Bulk write example:

```javascript
db.products.bulkWrite([
  {
    insertOne: {
      document: { sku: "A100", name: "Mouse", price: 799 }
    }
  },
  {
    updateOne: {
      filter: { sku: "A100" },
      update: { $set: { price: 749 } }
    }
  },
  {
    deleteOne: {
      filter: { sku: "OLD-001" }
    }
  }
])
```

Bulk APIs can reduce round trips. Ordered/unordered execution, write errors, and result structures differ by API/options. Use unique indexes to enforce the keys that define duplicate/upsert conflicts.

---

# 18. Aggregation Pipeline Fundamentals

Aggregation pipelines process documents through an ordered sequence of stages:

```javascript
db.orders.aggregate([
  { $match: { status: "PAID" } },
  { $group: { _id: "$customerId", totalSpent: { $sum: "$total" } } },
  { $sort: { totalSpent: -1 } },
  { $limit: 10 }
])
```

A stage usually takes documents in and emits transformed documents out. Stage order matters.

Common stages:
- `$match`
- `$project`
- `$set` / `$addFields`
- `$unset`
- `$group`
- `$sort`
- `$limit`
- `$skip`
- `$count`
- `$unwind`
- `$lookup`
- `$facet`
- `$bucket`, `$bucketAuto`
- `$replaceRoot`, `$replaceWith`
- `$sortByCount`
- `$sample`
- `$unionWith`
- `$graphLookup`
- `$setWindowFields`
- `$densify`, `$fill` (availability/version-specific)
- `$merge`, `$out`
- `$documents` and administrative/collectionless features where supported

Use the documentation for exact stage syntax and version support. Some stages have restrictions in transactions, sharded deployments, views, or Atlas services.

---

# 19. Common Aggregation Stages

## `$match`

Filter documents early in the pipeline where possible:

```javascript
{ $match: { status: "PAID", total: { $gte: 100 } } }
```

## `$project`

Choose/rename fields or compute expressions:

```javascript
{
  $project: {
    _id: 1,
    customerName: "$customer.name",
    total: 1,
    tax: { $multiply: ["$total", 0.18] }
  }
}
```

## `$set` / `$addFields`

Add or overwrite fields:

```javascript
{
  $set: {
    fullName: { $concat: ["$firstName", " ", "$lastName"] }
  }
}
```

## `$unset`

```javascript
{ $unset: ["passwordHash", "internalNotes"] }
```

## `$sort`, `$skip`, `$limit`

```javascript
{ $sort: { createdAt: -1, _id: -1 } },
{ $skip: 0 },
{ $limit: 20 }
```

A sort can require memory or disk resources; indexes and pipeline shape affect efficiency.

## `$count`

```javascript
{ $count: "totalOrders" }
```

If no documents reach the stage, the pipeline returns no count document rather than a document with zero in all contexts. Handle empty aggregation results in the application.

## `$unwind`

Convert array elements to individual documents:

```javascript
{
  $unwind: {
    path: "$items",
    preserveNullAndEmptyArrays: true
  }
}
```

Simple form: `{ $unwind: "$items" }`. By default, missing/null/empty arrays are dropped; `preserveNullAndEmptyArrays` changes this.

## `$replaceRoot` / `$replaceWith`

```javascript
{ $replaceWith: "$profile" }
```

The target must resolve to a suitable document; handle missing or non-document values appropriately.

---

# 20. Aggregation Expression Operators

Aggregation expressions appear inside stages such as `$project`, `$set`, and `$group`.

## Arithmetic expressions

- `$add`
- `$subtract`
- `$multiply`
- `$divide`
- `$mod`
- `$abs`
- `$ceil`
- `$floor`
- `$round`
- `$trunc`
- `$pow`
- `$sqrt`
- `$log`, `$log10`, `$ln`
- `$exp`
- `$sin`, `$cos`, `$tan` and related trigonometric functions where supported
- `$min`, `$max` depending on the expression/accumulator context

Example:

```javascript
{
  $project: {
    total: 1,
    discounted: { $multiply: ["$total", 0.9] }
  }
}
```

## Comparison expressions

- `$eq`
- `$ne`
- `$gt`
- `$gte`
- `$lt`
- `$lte`
- `$cmp`
- `$in`

These expressions compare values in aggregation contexts; don't confuse them with query predicates, even when operator names overlap.

## Logical expressions

- `$and`
- `$or`
- `$not`

```javascript
{
  $set: {
    isEligible: {
      $and: [
        { $gte: ["$score", 70] },
        { $eq: ["$active", true] }
      ]
    }
  }
}
```

## Conditional expressions

- `$cond`
- `$ifNull`
- `$switch`
- `$isNumber`
- `$type`

```javascript
{
  $set: {
    priceBand: {
      $switch: {
        branches: [
          { case: { $gte: ["$price", 10000] }, then: "premium" },
          { case: { $gte: ["$price", 2000] }, then: "midrange" }
        ],
        default: "budget"
      }
    }
  }
}
```

## Type conversion

- `$convert`
- `$toString`
- `$toInt`
- `$toLong`
- `$toDouble`
- `$toDecimal`
- `$toBool`
- `$toDate`
- `$toObjectId`
- `$toUpper`/`$toLower` (text conversion rather than type conversion)

`$convert` can support `onError` and `onNull` to control conversion failures/null input where documented.

---

# 21. Array Operators

Arrays are central to document data. Operator families differ by query versus aggregation context.

## Query operators

- `$all`: array must contain all specified values
- `$elemMatch`: at least one array element matches multiple conditions
- `$size`: exact array length
- `$in`, `$nin`: matching values
- Positional update operators: `$`, `$[]`, `$[identifier]`

```javascript
db.products.find({ tags: { $all: ["wireless", "bluetooth"] } })

db.orders.find({
  items: {
    $elemMatch: {
      sku: "A100",
      quantity: { $gte: 2 }
    }
  }
})

db.users.find({ roles: { $size: 3 } })
```

## Aggregation array operators

Common operators include:
- `$arrayElemAt`
- `$arrayToObject`
- `$objectToArray`
- `$concatArrays`
- `$filter`
- `$first`, `$last` (context/version-dependent meaning)
- `$in`
- `$indexOfArray`
- `$isArray`
- `$map`
- `$maxN`, `$minN` where supported
- `$range`
- `$reduce`
- `$reverseArray`
- `$size`
- `$slice`
- `$sortArray`
- `$zip`

Example `$map`:

```javascript
{
  $project: {
    scores: 1,
    doubledScores: {
      $map: {
        input: "$scores",
        as: "score",
        in: { $multiply: ["$$score", 2] }
      }
    }
  }
}
```

Example `$filter`:

```javascript
{
  $project: {
    highScores: {
      $filter: {
        input: "$scores",
        as: "score",
        cond: { $gte: ["$$score", 80] }
      }
    }
  }
}
```

Handle null/non-array inputs according to the operator's documented behavior.

---

# 22. String, Numeric, Date, and Conditional Expressions

## String aggregation expressions

Common examples:
- `$concat`
- `$concatArrays` (array operation)
- `$toLower`, `$toUpper`
- `$substr` / `$substrBytes` / `$substrCP` (legacy/version-specific nuances)
- `$strLenBytes`, `$strLenCP`
- `$split`
- `$indexOfBytes`, `$indexOfCP`
- `$replaceOne`, `$replaceAll`
- `$trim`, `$ltrim`, `$rtrim`
- `$regexFind`, `$regexFindAll`, `$regexMatch`

Example:

```javascript
{
  $project: {
    normalizedEmail: { $toLower: { $trim: { input: "$email" } } }
  }
}
```

UTF-8 byte length and Unicode code-point length are different. Choose the appropriate operator for international text.

## Date expressions

Common operator families:
- `$year`, `$month`, `$dayOfMonth`, `$dayOfWeek`, `$dayOfYear`
- `$hour`, `$minute`, `$second`, `$millisecond`
- `$dateAdd`, `$dateSubtract`, `$dateDiff`, `$dateTrunc`
- `$dateFromParts`, `$dateToParts`, `$dateFromString`, `$dateToString`
- `$isoWeek`, `$isoWeekYear`, `$isoDayOfWeek`
- `$toDate`
- `$timestamp`/system timestamp concepts are distinct from regular date expressions

Example:

```javascript
{
  $project: {
    year: { $year: "$createdAt" },
    month: { $month: "$createdAt" },
    readable: {
      $dateToString: {
        format: "%Y-%m",
        date: "$createdAt",
        timezone: "UTC"
      }
    }
  }
}
```

Check the server version for newer date operators and exact timezone behavior. Store timestamps consistently and avoid mixing local wall-clock time with UTC instants without a policy.

## Conditional expressions

- `$cond`
- `$switch`
- `$ifNull`
- `$ifNull` behavior with multiple inputs depends on server version; check docs.
- `$let` for scoped variables in expressions.

Example:

```javascript
{
  $set: {
    finalPrice: {
      $cond: [
        { $gte: ["$quantity", 10] },
        { $multiply: ["$price", 0.9] },
        "$price"
      ]
    }
  }
}
```

---

# 23. Grouping and Accumulators

`$group` groups documents by an `_id` expression.

```javascript
db.orders.aggregate([
  {
    $group: {
      _id: "$customerId",
      orderCount: { $sum: 1 },
      totalSpent: { $sum: "$total" },
      averageOrder: { $avg: "$total" },
      smallestOrder: { $min: "$total" },
      largestOrder: { $max: "$total" }
    }
  },
  { $sort: { totalSpent: -1 } }
])
```

Common accumulator operators include:
- `$sum`
- `$avg`
- `$min`
- `$max`
- `$first`
- `$last`
- `$push`
- `$addToSet`
- `$stdDevPop`, `$stdDevSamp`
- `$top`, `$topN`, `$bottom`, `$bottomN` (version-specific availability)
- `$firstN`, `$lastN`, `$maxN`, `$minN` (context/version-specific)
- `$accumulator` for custom JavaScript-based accumulator behavior where supported and permitted; use carefully and check server restrictions

For `$first` and `$last`, make the ordering explicit with a prior `$sort` when the intended first/last item matters.

---

# 24. Lookup, Unwind, Facets, and Multi-Collection Aggregation

## `$lookup`

Join-like enrichment from another collection:

```javascript
db.orders.aggregate([
  {
    $lookup: {
      from: "customers",
      localField: "customerId",
      foreignField: "_id",
      as: "customer"
    }
  }
])
```

The result field is an array. Use `$unwind` if the desired output is a single customer document per matching order, while deciding how unmatched orders should behave.

Pipeline form (details may vary):

```javascript
db.orders.aggregate([
  {
    $lookup: {
      from: "products",
      let: { skuFromOrder: "$sku" },
      pipeline: [
        { $match: { $expr: { $eq: ["$sku", "$$skuFromOrder"] } } },
        { $project: { name: 1, price: 1 } }
      ],
      as: "product"
    }
  }
])
```

Optimize `$lookup` with matching indexes and reasonable collection design. Equality, correlated subquery, sharding, collation, and index usage details depend on pipeline/query form.

## `$facet`

Run multiple pipeline branches on the same input:

```javascript
db.products.aggregate([
  {
    $facet: {
      items: [
        { $match: { isActive: true } },
        { $sort: { name: 1 } },
        { $limit: 20 }
      ],
      summary: [
        { $group: { _id: null, count: { $sum: 1 }, avgPrice: { $avg: "$price" } } }
      ]
    }
  }
])
```

## `$bucket` and `$bucketAuto`

These stages group numeric/range-like values into buckets. Explicit boundaries and output specifications must match the stage's documented grammar.

## `$unionWith`

Combine documents from another collection in an aggregation pipeline. This is not identical in every respect to a relational `UNION`, and stage support may be restricted in some deployments.

## `$graphLookup`

Recursive traversal across a collection's graph-like relationships, such as category trees or reporting structures. Apply depth bounds and access controls; large traversals can be expensive.

## `$merge` and `$out`

These stages write pipeline results to a collection under defined conditions. They are not ordinary read-only stages. Check permissions, replacement/merge semantics, indexes, sharding, transactions, and deployment restrictions before using them.

---

# 25. Window Functions and Set Operators

`$setWindowFields` computes window calculations within a partition.

Illustrative shape:

```javascript
db.sales.aggregate([
  {
    $setWindowFields: {
      partitionBy: "$storeId",
      sortBy: { date: 1 },
      output: {
        runningTotal: {
          $sum: "$amount",
          window: { documents: ["unbounded", "current"] }
        }
      }
    }
  }
])
```

Common window-related expressions/accumulators include ranking, document/window bounds, shift values, and accumulators supported by the selected release. Exact operators and restrictions evolve across MongoDB versions.

Related pipeline stages:
- `$sort`
- `$setWindowFields`
- `$group`
- `$densify`
- `$fill`

Set operations include:
- `$setUnion`
- `$setIntersection`
- `$setDifference`
- `$setEquals`
- `$setIsSubset`
- `$anyElementTrue`
- `$allElementsTrue`

MongoDB set expressions apply set semantics (duplicates/order treatment differs from array-preserving operations). Do not use a set operator when array order or duplicate elements must be preserved.

---

# 26. Aggregation Performance

General practices:
- Put selective `$match` stages early where it preserves semantics.
- Use indexes for supported filters/sorts before expensive transformations.
- Project only needed fields when this actually reduces downstream work.
- Understand `$unwind` fan-out and `$lookup` cardinality.
- Bound recursive traversals.
- Use `$limit` where the task only needs a bounded result.
- Watch memory use and stage limits; some stages have configurable disk spill behavior, subject to server/version/options.
- Avoid unnecessary large `$push` arrays and huge result documents.
- Inspect `explain()` output and measure with representative data.

Example:

```javascript
db.orders.explain("executionStats").aggregate([
  { $match: { status: "PAID" } },
  { $group: { _id: "$customerId", total: { $sum: "$total" } } }
])
```

Explain syntax and available verbosity differ by operation/version. Execution-statistics mode can execute the query, so consider workload impact.

---

# 27. Indexes and Index Types

Indexes help MongoDB locate documents without scanning an entire collection, but use disk and increase write overhead.

## Single-field index

```javascript
db.products.createIndex({ sku: 1 })
```

## Descending index

```javascript
db.products.createIndex({ createdAt: -1 })
```

## Compound index

```javascript
db.products.createIndex({ categoryId: 1, price: -1 })
```

Compound field order matters. Think about equality filters, sort patterns, range conditions, selectivity, and prefix behavior.

## Unique index

```javascript
db.users.createIndex({ email: 1 }, { unique: true })
```

Unique index creation can fail if existing data already violates uniqueness. Null/missing field behavior depends on index options and data model.

## Partial index

```javascript
db.products.createIndex(
  { price: 1 },
  { partialFilterExpression: { isActive: true } }
)
```

Partial indexes only include documents meeting the filter. The query must be compatible with that filter for the index to serve it as expected.

## TTL index

```javascript
db.sessions.createIndex(
  { expiresAt: 1 },
  { expireAfterSeconds: 0 }
)
```

TTL deletion is asynchronous and not an exact real-time scheduler. Store the correct date and do not rely on the precise second for business workflows.

## Text index

```javascript
db.articles.createIndex({ title: "text", body: "text" })
db.articles.find({ $text: { $search: "machine learning" } })
```

Text index limits and behavior depend on the server version and language/tokenization rules. For richer search experiences consider the appropriate search product/feature and its index syntax.

## Geospatial indexes

- `2dsphere`
- `2d` for supported legacy coordinate use cases

```javascript
db.places.createIndex({ location: "2dsphere" })
```

GeoJSON data should follow the supported coordinate ordering and geometry specification.

## Hashed, wildcard, sparse, clustered, and specialized indexes

MongoDB has additional index options/types with particular query limitations and version/deployment requirements. Examples include hashed indexes, wildcard indexes (`$**` patterns), sparse indexes, hidden indexes, and clustered collections where supported. Learn the relevant type for the access pattern; do not index every field.

Drop an index:

```javascript
db.products.dropIndex("sku_1")
```

List indexes:

```javascript
db.products.getIndexes()
```

---

# 28. Query Plans and Explain

`explain()` can describe how MongoDB plans/runs a query.

```javascript
db.products.find({ sku: "A100" }).explain("executionStats")
```

Look for:
- Index scan vs collection scan
- Documents/keys examined
- Returned document count
- Sort stages and memory use
- Fetch stage and index coverage
- Number of examined rows/documents relative to results
- Shard targeting where relevant

An index is not necessarily used just because it exists. The optimizer evaluates selectivity, cardinality, query shape, indexes, and statistics/metadata. Check behavior on representative data, not just an empty dev database.

---

# 29. Data Modeling and Schema Design

Unlike a traditional relational design, MongoDB's data model often embeds related data for common access patterns.

Example embedded document:

```javascript
{
  _id: ObjectId("65f000000000000000000001"),
  fullName: "Asha Kumar",
  address: {
    city: "Chennai",
    postalCode: "600001"
  },
  preferences: {
    theme: "dark",
    language: "en"
  }
}
```

Good schema design considers:
- Main read/write patterns.
- How much related data is usually retrieved together.
- Document growth and document size limits.
- One-to-one, one-to-many, and many-to-many relationships.
- Update frequency and consistency rules.
- Data duplication and synchronization.
- Indexing, sharding, and access patterns.
- Audit/retention needs.

Embedding can make related reads efficient and allows atomic update of the document. Referencing can reduce duplication and support independently growing entities. Neither is always better.

Avoid designing the database solely by translating every normalized SQL table directly into a collection or embedding everything recursively. Design for actual queries and update patterns.

---

# 30. Embedding vs Referencing

## Embed related data

```javascript
{
  _id: 101,
  title: "My Order",
  items: [
    { sku: "A100", quantity: 2, unitPrice: 500 },
    { sku: "B200", quantity: 1, unitPrice: 900 }
  ]
}
```

Advantages:
- Retrieve related data in one read.
- Update a single document atomically.
- Natural representation of bounded child data.

Trade-offs:
- Duplication can become stale.
- Arrays can grow too large.
- Independent updates to embedded elements can be complex.

## Reference related data

```javascript
// orders
{ _id: 101, customerId: ObjectId("65f000000000000000000099") }

// customers
{ _id: ObjectId("65f000000000000000000099"), name: "Asha" }
```

Advantages:
- Shared entities stay in one place.
- Independently growing data is easier to manage.
- Avoids repeated large objects.

Trade-offs:
- May require multiple queries or `$lookup`.
- Multi-document changes may need a transaction or a deliberately designed consistency strategy.

Useful heuristic: embed bounded data that is normally read/updated with its parent; reference large, independently changing, many-to-many, or frequently shared data when it fits the access pattern. Validate the choice with workload measurements.

---

# 31. Atomicity and Transactions

MongoDB guarantees atomicity for a single-document write operation. Multi-document transactions are supported on replica sets and sharded clusters within their documented constraints; standalone deployments have different transaction capabilities.

Conceptual multi-document transaction through `mongosh`:

```javascript
const session = db.getMongo().startSession();

try {
  session.startTransaction();

  const sessionDb = session.getDatabase("store_db");
  sessionDb.accounts.updateOne(
    { _id: "A" },
    { $inc: { balance: -100 } }
  );
  sessionDb.accounts.updateOne(
    { _id: "B" },
    { $inc: { balance: 100 } }
  );

  session.commitTransaction();
} catch (error) {
  session.abortTransaction();
  throw error;
} finally {
  session.endSession();
}
```

The example illustrates the transaction flow; confirm exact `mongosh` session usage and deployment requirements for your version. Production code should validate sufficient balance, handle transient transaction errors, and use supported driver transaction APIs.

Driver APIs often expose:
- Start session
- Start transaction
- Commit transaction
- Abort transaction
- End session
- Retry handling for documented transient error labels

Use transactions when a true multi-document invariant demands them. Often good document modeling reduces the need for transactions. Keep transactions short and do not call slow external APIs inside an open transaction.

---

# 32. Read/Write Concern and Read Preference

These settings affect consistency and durability trade-offs across replica sets/sharded deployments.

- **Read preference:** which replica-set member handles a read.
- **Read concern:** consistency level of read results.
- **Write concern:** acknowledgment/durability level requested for writes.

Conceptual shell examples:

```javascript
db.products.find({ category: "Books" })
```

Driver operations can specify read/write concerns and read preference through supported options. Exact syntax differs among shell, Node.js driver, Java driver, and other clients.

Do not change defaults without understanding the failure model, latency, durability, replication, and transaction implications. For critical writes, pick settings suitable for the application's consistency requirements and test failover behavior.

---

# 33. Validation, Schema Rules, and Data Integrity

Use collection validators to enforce field types/required values; use unique indexes for uniqueness; use application validation for business rules and authorization.

Example validator:

```javascript
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["email", "displayName"],
      properties: {
        email: { bsonType: "string", maxLength: 254 },
        displayName: { bsonType: "string", minLength: 1, maxLength: 100 },
        roles: {
          bsonType: "array",
          items: { bsonType: "string" }
        }
      }
    }
  },
  validationAction: "error"
})
```

Collection validation is not equivalent to a full relational foreign-key system. Where integrity spans collections, application logic, unique indexes, transactions, and data-reconciliation workflows may be needed.

For migrations, plan for existing documents that violate a newly introduced validator.

---

# 34. Geospatial Queries

MongoDB supports geospatial query and index capabilities. GeoJSON coordinates conventionally use longitude then latitude.

Create a `2dsphere` index:

```javascript
db.places.createIndex({ location: "2dsphere" })
```

Sample point:

```javascript
db.places.insertOne({
  name: "Central Point",
  location: {
    type: "Point",
    coordinates: [80.2707, 13.0827]
  }
})
```

Near-query structure (distance units depend on the GeoJSON/spherical query form and options):

```javascript
db.places.find({
  location: {
    $near: {
      $geometry: {
        type: "Point",
        coordinates: [80.2707, 13.0827]
      },
      $maxDistance: 5000
    }
  }
})
```

GeoJSON `$maxDistance` is typically in meters for `2dsphere` queries. Validate coordinate order and geometry. Query operators include `$near`, `$nearSphere`, `$geoWithin`, `$geoIntersects`, and related geometrical specifications, with restrictions depending on index type and query shape.

Do not treat geographic coordinates from untrusted users as valid without validation.

---

# 35. Text Search, Atlas Search, and Vector Search

MongoDB has more than one search feature; they are not interchangeable.

## Classic text index

```javascript
db.articles.createIndex({ title: "text", body: "text" })

db.articles.find({
  $text: { $search: "deep learning" }
})
```

Text index capabilities and language behavior are more limited than a purpose-built search engine in some use cases.

## Atlas Search

Atlas Search provides search functionality with a separate index configuration and an aggregation-stage interface such as `$search` in supported Atlas deployments. Its search operators/analyzers are specific to that product and configuration.

Use its official documentation for:
- Search index mappings
- Analyzers and tokenizers
- Compound queries
- Autocomplete
- Facets
- Highlighting
- Scoring and boosting
- Synonyms and language analyzers

## Vector Search

Vector search retrieves items based on embedding distance/similarity. Availability, index syntax, supported query operators, filtering, and deployment requirements depend on MongoDB/Atlas version and configuration.

Typical conceptual pipeline:
1. Store embedding and metadata.
2. Configure vector index dimensions and similarity metric.
3. Embed the incoming query using the compatible model.
4. Run a vector search query and retrieve top matches.
5. Apply access control/metadata filters and optional reranking.
6. Evaluate relevance and latency with representative tests.

An embedding model's dimensions and normalization must match the index/query configuration. Do not assume vector search automatically makes results semantically correct.

---

# 36. Change Streams and Event-Driven Systems

Change streams let applications observe database changes in supported deployment configurations, such as replica sets and sharded clusters.

Conceptual `mongosh` example:

```javascript
const changeStream = db.orders.watch();

changeStream.next();
```

Production applications should use driver change-stream APIs with correct lifecycle, resume token, error handling, and cancellation. Do not block the shell indefinitely without a clear plan.

Key concepts:
- Change event
- Resume token
- Full document lookup options
- Pipeline filters
- Invalidate events
- Resume after / start after behavior
- Change stream lifetime, permissions, and deployment limits

Change streams are not a replacement for designing durable event delivery. Consumers should consider duplicate handling, resume behavior, idempotency, schema changes, and downstream outages.

---

# 37. Security, Roles, and Access Control

MongoDB security includes:
- Authentication
- Authorization / role-based access control
- TLS
- Network restrictions
- Encryption at rest where supported/configured
- Auditing where available
- Field/document-level encryption features where configured
- Secret management and rotation
- Backups and least privilege

Create specific database users/roles using documented administration commands or managed deployment tooling. Exact command syntax depends on deployment and permissions.

In application design:
- Create a user for each application/service with only the required privileges.
- Never expose privileged credentials to frontend code.
- Keep the database off public networks unless securely required.
- Use TLS when required by the threat model and deployment.
- Rotate exposed secrets and remove old credentials.
- Avoid logging complete connection strings.
- Restrict administrative endpoints and access to backups.
- Review audit requirements and personal-data retention.

Role names and built-in role privileges are documented per MongoDB edition/deployment. Avoid granting broad `root`/admin roles to application accounts.

---

# 38. Backup, Restore, Import, and Export

Tools depend on deployment:
- `mongodump` / `mongorestore` for BSON backups/restores where supported.
- `mongoexport` / `mongoimport` for JSON/CSV data exchange; these are not equivalent to full-fidelity backups.
- Managed cloud backup/snapshot tools for managed deployments.
- Filesystem snapshots only with supported consistency procedures.

Illustrative local commands (adapt options, authentication, and deployment details):

```bash
mongodump --uri="mongodb://localhost:27017/store_db" --out=./backup
mongorestore --uri="mongodb://localhost:27017" ./backup/store_db
```

JSON/CSV examples:

```bash
mongoexport --uri="mongodb://localhost:27017/store_db" \
  --collection=products --out=products.json

mongoimport --uri="mongodb://localhost:27017/store_db" \
  --collection=products --file=products.json --jsonArray
```

Not all import/export options are suitable for every format. Verify the tool version and exact JSON mode. Treat credential-bearing command lines and shell history carefully.

Operational checklist:
- Automate backups and monitor failures.
- Encrypt backups and restrict access.
- Store copies separately from the production deployment.
- Set RPO/RTO targets.
- Test restore procedures regularly.
- Ensure indexes, users/roles, and required metadata are recreated/restored appropriately.
- Understand consistency guarantees of the chosen backup method.
- Never assume that a backup file is valid until a restore test passes.

---

# 39. `mongosh` Methods and Shell Helpers

Common database/collection helpers include:

## Database-level helpers

- `db.getName()`
- `db.getCollectionNames()`
- `db.getCollectionInfos()`
- `db.createCollection()`
- `db.createView()`
- `db.dropDatabase()`
- `db.runCommand()`
- `db.aggregate()`
- `db.adminCommand()` (administrative commands require relevant privilege)
- `db.getMongo()`

## Collection helpers

- `find()`
- `findOne()`
- `findOneAndUpdate()`
- `findOneAndReplace()`
- `findOneAndDelete()`
- `insertOne()`
- `insertMany()`
- `updateOne()`
- `updateMany()`
- `replaceOne()`
- `deleteOne()`
- `deleteMany()`
- `bulkWrite()`
- `countDocuments()`
- `estimatedDocumentCount()`
- `distinct()`
- `aggregate()`
- `createIndex()`
- `createIndexes()`
- `getIndexes()`
- `dropIndex()`
- `dropIndexes()`
- `reIndex()` availability/behavior is version-specific and should be checked before use.
- `stats()`
- `explain()` is commonly invoked from query/cursor contexts.

## Cursor methods

Common methods include:
- `sort()`
- `limit()`
- `skip()`
- `project()` in appropriate cursor/API contexts
- `hasNext()`
- `next()`
- `forEach()`
- `toArray()`
- `count()`/cursor count helpers have been deprecated/changed across driver and shell versions; prefer the documented collection counting methods for your version.

`mongosh` helper methods are JavaScript-shell interfaces, and their return shapes/options may differ from official language drivers. Use `help` in the installed shell and the official methods reference for exact signatures.

---

# 40. Node.js Driver Integration

Install the official Node.js driver:

```bash
npm install mongodb
```

Example ESM setup:

```javascript
import { MongoClient, ObjectId } from "mongodb";

const uri = process.env.MONGODB_URI;
if (!uri) {
  throw new Error("MONGODB_URI environment variable is required");
}

const client = new MongoClient(uri);

async function main() {
  await client.connect();

  const db = client.db("store_db");
  const products = db.collection("products");

  const inserted = await products.insertOne({
    name: "Keyboard",
    price: 2499,
    isActive: true,
    createdAt: new Date()
  });

  const found = await products.findOne({ _id: inserted.insertedId });
  console.log(found);

  await products.updateOne(
    { _id: inserted.insertedId },
    { $set: { price: 2299 } }
  );

  const list = await products
    .find({ isActive: true }, { projection: { name: 1, price: 1 } })
    .sort({ name: 1 })
    .limit(20)
    .toArray();

  console.log(list);
}

main()
  .catch(console.error)
  .finally(async () => {
    await client.close();
  });
```

Use a long-lived `MongoClient` for a running backend rather than creating a new connection pool for each request. In a server API, connect during startup and close during graceful shutdown.

Common collection methods:
- `insertOne`, `insertMany`
- `find`, `findOne`
- `updateOne`, `updateMany`
- `replaceOne`
- `deleteOne`, `deleteMany`
- `findOneAndUpdate`, `findOneAndReplace`, `findOneAndDelete`
- `bulkWrite`
- `aggregate`
- `distinct`
- `countDocuments`, `estimatedDocumentCount`
- `createIndex`, `listIndexes`, `dropIndex`
- `watch` for change streams in supported deployments

Method signatures and return structures can change between major driver versions. Check the official Node.js driver reference.

---

# 41. Mongoose Overview

Mongoose is an ODM for Node.js that adds schemas, models, casting, validation, middleware, and query helpers. It is distinct from the official MongoDB Node.js driver.

Install:

```bash
npm install mongoose
```

Illustrative schema/model:

```javascript
import mongoose from "mongoose";

const productSchema = new mongoose.Schema(
  {
    name: { type: String, required: true, trim: true, maxlength: 120 },
    price: { type: Number, required: true, min: 0 },
    tags: { type: [String], default: [] },
    isActive: { type: Boolean, default: true }
  },
  {
    timestamps: true
  }
);

const Product = mongoose.model("Product", productSchema);
```

CRUD shape:

```javascript
await Product.create({ name: "Keyboard", price: 2499 });

const items = await Product.find({ isActive: true })
  .sort({ name: 1 })
  .limit(20)
  .lean();

await Product.updateOne(
  { _id: productId },
  { $set: { price: 2299 } },
  { runValidators: true }
);

await Product.deleteOne({ _id: productId });
```

Mongoose features:
- `Schema`
- `model`
- Schema types, defaults, required rules, enums, validators
- Index definitions
- Middleware/hooks
- Virtuals
- Instance/static methods
- Populate/reference support
- Query helpers
- Discriminators
- Transactions via sessions
- Lean queries and aggregation

Mongoose validation/middleware behavior is not identical to database validation or direct-driver behavior. Update validators generally need explicit options in common Mongoose update patterns; consult the installed version's documentation.

---

# 42. Python Driver Integration

The official Python driver is PyMongo.

Install:

```bash
python -m pip install pymongo
```

Example:

```python
import os
from pymongo import MongoClient

uri = os.environ["MONGODB_URI"]
client = MongoClient(uri)

db = client["store_db"]
products = db["products"]

insert_result = products.insert_one({
    "name": "Keyboard",
    "price": 2499,
    "isActive": True
})

document = products.find_one({"_id": insert_result.inserted_id})
print(document)

products.update_one(
    {"_id": insert_result.inserted_id},
    {"$set": {"price": 2299}}
)

for product in products.find({"isActive": True}).sort("name", 1).limit(20):
    print(product)

client.close()
```

In a long-running application, keep client lifecycle aligned with application lifecycle and use the driver's documented connection-pooling behavior.

---

# 43. MongoDB with Spring Boot / Java Overview

Spring Data MongoDB maps Java objects to MongoDB documents.

Dependency selection is managed through Spring Initializr or the Spring Boot dependency management used by the project. Avoid guessing dependency versions.

Document model:

```java
@Document("products")
public class Product {
    @Id
    private String id;

    private String name;
    private BigDecimal price;
    private boolean active;

    // constructors, getters/setters omitted
}
```

Repository:

```java
public interface ProductRepository extends MongoRepository<Product, String> {
    List<Product> findByActiveTrue();
    List<Product> findByNameContainingIgnoreCase(String name);
}
```

Typical annotations:
- `@Document`
- `@Id`
- `@Field`
- `@Indexed`
- `@CompoundIndex`
- `@DBRef` (consider carefully; not the same as automatic SQL foreign keys)
- `@Query`
- Auditing annotations when auditing is configured

Spring Data can derive queries from method names, but supported keywords and mappings are version-specific. Use `MongoTemplate` / aggregation framework APIs for more complex operations.

---

# 44. Monitoring, Troubleshooting, and Performance

Common issues:

| Symptom | Investigate |
|---|---|
| Authentication failure | URI, database user, auth source, credentials, roles |
| Connection timeout | DNS, host/port, TLS, firewall, network allowlist |
| Missing documents | Query shape, BSON types, field paths, database selection |
| No match for ID | ObjectId vs string type mismatch |
| Unexpected array matches | Query predicate vs `$elemMatch` semantics |
| Update has no effect | Filter mismatch, update operator shape, validators |
| Duplicate-key error | Unique index and existing data |
| Aggregation error | Stage order, expression vs query operator, incompatible types |
| Slow query | Indexes, selectivity, result size, explain output, lookup fanout |
| Memory/resource errors | Large arrays/results, sort/group resources, unbounded pipeline |
| Transaction failure | Deployment type, session use, write conflicts, retry handling |
| Driver compatibility issue | Server/driver versions and API signature changes |

Performance checklist:
1. Use the right index for important query patterns.
2. Return only necessary fields.
3. Limit and paginate results.
4. Avoid unbounded arrays and ever-growing documents.
5. Use indexes for `$lookup` join fields where suitable.
6. Inspect `explain("executionStats")` on representative data.
7. Reuse the driver client/connection pool.
8. Monitor query latency and resource use.
9. Batch independent writes where appropriate.
10. Use transactions only when required by the data invariant.
11. Design shard keys carefully for sharded deployments.
12. Re-test performance after schema/index/query changes.

---

# 45. Full CRUD Example

This example builds an anime collection. It is intended for a local learning database; adapt validation and indexes to your workload.

## Insert

```javascript
db.anime.insertMany([
  {
    title: "Example Adventure",
    genres: ["Action", "Fantasy"],
    year: 2024,
    rating: 8.4,
    isOngoing: true,
    createdAt: new Date()
  },
  {
    title: "Example Mystery",
    genres: ["Mystery", "Drama"],
    year: 2022,
    rating: 7.9,
    isOngoing: false,
    createdAt: new Date()
  }
])
```

## Read/filter

```javascript
db.anime.find(
  { rating: { $gte: 8 }, isOngoing: true },
  { title: 1, rating: 1, genres: 1 }
).sort({ rating: -1 }).limit(20)
```

## Update

```javascript
db.anime.updateOne(
  { title: "Example Adventure" },
  { $set: { rating: 8.6, updatedAt: new Date() } }
)
```

## Increment

```javascript
db.anime.updateOne(
  { title: "Example Adventure" },
  { $inc: { viewCount: 1 } }
)
```

## Delete

```javascript
db.anime.deleteOne({ title: "Example Mystery" })
```

## Aggregate by genre after unwinding

```javascript
db.anime.aggregate([
  { $unwind: "$genres" },
  {
    $group: {
      _id: "$genres",
      animeCount: { $sum: 1 },
      averageRating: { $avg: "$rating" }
    }
  },
  { $sort: { animeCount: -1 } }
])
```

This intentionally uses sample titles rather than real data; it demonstrates the structure of a CRUD and aggregation workflow.

---

# 46. Common Query Patterns

## Top N items

```javascript
db.products.find({ isActive: true })
  .sort({ score: -1, _id: 1 })
  .limit(10)
```

## Count matching documents

```javascript
db.products.countDocuments({ isActive: true })
```

Use `estimatedDocumentCount()` for a fast estimate of the collection's total document count when its semantics fit the task; exactness/metadata behavior differs from counting a filtered query.

## Find documents with missing fields

```javascript
db.users.find({ phone: { $exists: false } })
```

Find explicit null or missing:

```javascript
db.users.find({ phone: null })
```

This can match null and missing-field cases. For only explicit null:

```javascript
db.users.find({ phone: { $type: 10 } })
```

BSON type code/operator behavior should be confirmed in the versioned documentation; using schema rules to avoid ambiguous missing/null states is often better.

## Search within arrays

```javascript
db.posts.find({ tags: "mongodb" })
db.posts.find({ tags: { $all: ["database", "backend"] } })
db.posts.find({
  comments: {
    $elemMatch: { likes: { $gte: 10 }, approved: true }
  }
})
```

## Latest document per group

```javascript
db.events.aggregate([
  { $sort: { createdAt: -1, _id: -1 } },
  {
    $group: {
      _id: "$userId",
      latestEvent: { $first: "$$ROOT" }
    }
  }
])
```

The initial sort can be expensive; consider indexes and newer window/group approaches supported by the chosen server.

## Count and paginate as separate operations

A typical API might run a `countDocuments(filter)` and a find query with sort/limit. If records are changing concurrently, the count and page might not describe exactly the same snapshot unless using an appropriate consistency/transaction approach.

---

# 47. MongoDB Operator and Method Quick Reference

## Query filter operators

`$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`, `$and`, `$or`, `$nor`, `$not`, `$exists`, `$type`, `$regex`, `$expr`, `$jsonSchema`, `$mod`, `$all`, `$elemMatch`, `$size`, `$text`, `$where` (restricted/avoid as a normal default).

## Update operators

`$set`, `$unset`, `$rename`, `$setOnInsert`, `$currentDate`, `$inc`, `$mul`, `$min`, `$max`, `$push`, `$addToSet`, `$pop`, `$pull`, `$pullAll`, `$each`, `$position`, `$slice`, `$sort`, positional `$`, `$[]`, `$[identifier]`.

## Aggregation stages

`$match`, `$project`, `$set`, `$addFields`, `$unset`, `$group`, `$sort`, `$skip`, `$limit`, `$count`, `$unwind`, `$lookup`, `$facet`, `$bucket`, `$bucketAuto`, `$replaceRoot`, `$replaceWith`, `$sample`, `$sortByCount`, `$unionWith`, `$graphLookup`, `$setWindowFields`, `$densify`, `$fill`, `$merge`, `$out`, and additional stages documented for your release.

## Aggregation expression families

Arithmetic, comparison, boolean/logical, conditional, type conversion, string, array, date/time, set, literal, variable (`$let`), accumulator, window, regex, document/object, and system variables such as `$$ROOT`, `$$CURRENT`, and supported stage-specific variables.

## CRUD methods

`insertOne`, `insertMany`, `find`, `findOne`, `updateOne`, `updateMany`, `replaceOne`, `deleteOne`, `deleteMany`, `findOneAndUpdate`, `findOneAndReplace`, `findOneAndDelete`, `bulkWrite`, `countDocuments`, `estimatedDocumentCount`, `distinct`, `aggregate`.

## Index methods

`createIndex`, `createIndexes`, `getIndexes`, `dropIndex`, `dropIndexes`, and listing/index-statistics commands supported by the selected client/version.

## Cursor helpers

`sort`, `skip`, `limit`, projection options, `toArray`, cursor iteration, and explain methods in the contexts supported by the specific shell/driver.

This shortlist is an orientation map, not every MongoDB method/operator. API signatures, deprecations, and restrictions vary by server, shell, and driver.

---

# 48. Practice Projects and Learning Roadmap

Suggested learning sequence:

1. Database, collection, BSON, documents, `_id`.
2. CRUD and filters.
3. Projection, sorting, pagination.
4. Array and nested-document queries.
5. Update operators and array filters.
6. Aggregation pipeline.
7. Indexes and `explain`.
8. Schema validation and data modeling.
9. Transactions and consistency.
10. Authentication, roles, backups, and operational monitoring.
11. Official Node.js / Python / Java driver integration.
12. Production-ready backend API.

Practice projects:
- User profile database
- Anime catalog
- Inventory and order management
- Blog with embedded comments or referenced comments
- Chat/messages data model
- Search and filter API
- Event log and aggregation dashboard
- RAG document metadata and embedding store
- Multi-tenant application with per-tenant authorization filters

For every project, create sample data, document your schema decisions, create indexes that match real queries, and test authorization and deletion behavior.

---

# 49. Official Documentation

Use the documentation matching the deployed server, shell, driver, and framework versions.

- [MongoDB Manual](https://www.mongodb.com/docs/manual/)
- [MongoDB Query Language Reference](https://www.mongodb.com/docs/manual/reference/mql/)
- [MongoDB CRUD Operations](https://www.mongodb.com/docs/manual/crud/)
- [Query and Projection Operators](https://www.mongodb.com/docs/manual/reference/operator/query/)
- [Update Operators](https://www.mongodb.com/docs/manual/reference/operator/update/)
- [Aggregation Pipeline](https://www.mongodb.com/docs/manual/core/aggregation-pipeline/)
- [Aggregation Pipeline Stages](https://www.mongodb.com/docs/manual/reference/operator/aggregation-pipeline/)
- [Aggregation Operators](https://www.mongodb.com/docs/manual/reference/operator/aggregation/)
- [Indexes](https://www.mongodb.com/docs/manual/indexes/)
- [Index Types](https://www.mongodb.com/docs/manual/core/indexes/index-types/)
- [Transactions](https://www.mongodb.com/docs/manual/core/transactions/)
- [Schema Validation](https://www.mongodb.com/docs/manual/core/schema-validation/)
- [Data Modeling](https://www.mongodb.com/docs/manual/data-modeling/)
- [Security](https://www.mongodb.com/docs/manual/security/)
- [mongosh Documentation](https://www.mongodb.com/docs/mongodb-shell/)
- [mongosh Methods](https://www.mongodb.com/docs/mongodb-shell/reference/methods/)
- [Node.js Driver](https://www.mongodb.com/docs/drivers/node/current/)
- [Node.js Driver CRUD](https://www.mongodb.com/docs/drivers/node/current/crud/)
- [Mongoose Documentation](https://mongoosejs.com/docs/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/en/stable/)
- [Spring Data MongoDB](https://docs.spring.io/spring-data/mongodb/reference/)

---

## Final Note

Use this file as a structured learning reference, then verify exact syntax against your actual MongoDB server, `mongosh`, and application-driver versions. MongoDB's shell methods, language-driver APIs, aggregation operators, Atlas Search/Vector Search features, and server commands are separate but related interfaces. No single Markdown file can guarantee literally every current and future method; the official versioned documentation is the source of truth for exact signatures and compatibility.
