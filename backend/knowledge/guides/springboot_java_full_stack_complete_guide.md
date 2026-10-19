# Spring Boot + Java: Complete Full-Stack Backend Development Guide
## Java Syntax, Methods, Spring Boot APIs, REST, Databases, Security, Testing, and Deployment

> **Purpose:** A practical, structured reference for learning Java and Spring Boot for real-world backend development.
>
> **Version note:** This guide uses Spring Boot **4.1.1** and Java 21-style examples. According to the official Spring Boot system requirements, Spring Boot 4.1.1 requires at least Java 17 and supports Java versions through 26. Spring Boot 4 uses `spring-boot-starter-webmvc` for the standard Spring MVC web stack. Spring Boot 3 projects commonly use `spring-boot-starter-web`; check the documentation for the version your project uses.
>
> **Scope note:** Java and the Spring ecosystem are large and continue to evolve. There is no finite, official list that can honestly be called “100% of all syntax, methods, APIs, and future features.” This guide covers core Java syntax, the major Spring Boot development patterns, and the features commonly needed for production-oriented full-stack applications. Always consult the official documentation for version-specific APIs.

---

## Table of Contents

1. Java and Spring Boot Overview
2. Development Tools and Project Setup
3. Maven Project Configuration
4. Java Program Structure
5. Variables, Primitive Types, and Type Conversion
6. Operators and Expressions
7. Conditions and Loops
8. Methods and Function-Like Syntax
9. Arrays and Varargs
10. Strings, Text Blocks, and Formatting
11. Classes, Objects, Constructors, and Records
12. Access Modifiers, Packages, and Imports
13. Inheritance, Interfaces, and Polymorphism
14. Enums, Nested Classes, and Sealed Types
15. Generics
16. Collections Framework
17. Lambdas, Functional Interfaces, and Streams
18. Optional
19. Exceptions and Error Handling
20. Date and Time API
21. File I/O and Resource Management
22. Concurrency and Virtual Threads
23. Annotations and Reflection
24. JDBC and SQL Fundamentals
25. Spring Boot Project Structure
26. Spring Boot Application Startup and Auto-Configuration
27. Spring Core: IoC, Beans, and Dependency Injection
28. Configuration: Properties, YAML, Profiles, and Secrets
29. Building REST APIs with Spring MVC
30. DTOs, Records, and Validation
31. Error Handling and API Response Design
32. Spring Data JPA and Database Mapping
33. Repositories, Queries, Pagination, and Sorting
34. Transactions and Service-Layer Design
35. Database Migrations
36. Calling External APIs
37. Spring Security Fundamentals
38. Password Hashing, Authentication, and Authorization
39. CORS, CSRF, and Other Security Practices
40. File Upload and Download
41. Caching, Scheduling, and Asynchronous Work
42. Logging, Actuator, Metrics, and Health Checks
43. Testing Java and Spring Boot Applications
44. API Documentation
45. WebSockets and Reactive Programming Overview
46. Email and Background Jobs
47. Docker and Deployment
48. Microservices and Messaging Overview
49. Performance and Troubleshooting
50. Complete CRUD Example
51. Common Spring Boot Annotations
52. Common Java and Spring Methods
53. Full-Stack Learning Roadmap
54. Practice Projects
55. Quick Syntax Reference
56. Official Documentation

---

# 1. Java and Spring Boot Overview

**Java** is a programming language. **Spring Framework** provides infrastructure such as dependency injection, web support, transactions, and data access. **Spring Boot** makes Spring applications easier to configure, package, run, and monitor.

Common request flow:

```text
Browser / React / Angular
        |
        | HTTP request (JSON)
        v
Controller  ---> validates input and defines HTTP endpoint
        |
        v
Service     ---> business rules and transaction boundary
        |
        v
Repository  ---> database operations
        |
        v
Database
```

A typical Spring Boot API project uses:

- Java for application code.
- Spring Boot for application setup and auto-configuration.
- Spring MVC for REST endpoints.
- Bean Validation for request validation.
- Spring Data JPA/Hibernate for relational database access.
- Spring Security for authentication and authorization.
- JUnit and Spring test support for testing.
- Actuator for health and operational information.

Spring Boot is not a Java replacement; it is a framework built around the Java and Spring ecosystem.

---

# 2. Development Tools and Project Setup

Install a supported JDK, Git, and an IDE such as IntelliJ IDEA, Eclipse, or VS Code with Java support. Maven is used in the examples below.

Verify Java and Maven:

```bash
java -version
javac -version
mvn -version
```

Create a project through [Spring Initializr](https://start.spring.io/). For this guide's examples, select:

- Project: Maven
- Language: Java
- Spring Boot: 4.1.1 (or the latest compatible stable release shown by Initializr)
- Java: 21
- Packaging: Jar
- Dependencies: Spring Web MVC, Validation, Spring Data JPA, PostgreSQL Driver, Spring Boot Actuator, Spring Boot Test

For Boot 4, the standard MVC starter is `spring-boot-starter-webmvc`. Older Boot 3 tutorials often use `spring-boot-starter-web`.

Typical commands:

```bash
mvn clean
mvn test
mvn package
mvn spring-boot:run
java -jar target/app-0.0.1-SNAPSHOT.jar
```

---

# 3. Maven Project Configuration

Maven describes dependencies, build settings, tests, and plugins in `pom.xml`.

A minimal Spring Boot 4.1.1 project with REST, validation, JPA, PostgreSQL, and tests:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>4.1.1</version>
        <relativePath/>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>catalog-api</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <name>catalog-api</name>
    <description>Learning Spring Boot REST API</description>

    <properties>
        <java.version>21</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webmvc</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>

        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

Useful Maven commands:

```bash
mvn dependency:tree
mvn help:effective-pom
mvn -DskipTests package
mvn -Dtest=CatalogServiceTest test
mvn clean verify
```

Do not add versions to Spring-managed dependencies unless you have a clear reason. Spring Boot's dependency management selects compatible versions.

---

# 4. Java Program Structure

```java
package com.example.demo;

import java.util.List;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, Spring Boot!");
    }
}
```

- `package` declares the package.
- `import` lets the source file refer to types by simple name.
- `public class Main` declares a class.
- `main` is the conventional Java application entry point.
- Statements usually end with semicolons.
- Blocks use `{` and `}`.
- Java is statically typed and case-sensitive.

Comments:

```java
// Single-line comment

/*
 * Multi-line comment
 */

/**
 * Javadoc comment for classes and methods.
 * @author Example
 */
```

---

# 5. Variables, Primitive Types, and Type Conversion

## Primitive types

| Type | Example | Notes |
|---|---|---|
| `byte` | `byte n = 10;` | 8-bit signed integer |
| `short` | `short n = 1000;` | 16-bit signed integer |
| `int` | `int age = 20;` | 32-bit signed integer |
| `long` | `long population = 8_000_000_000L;` | 64-bit signed integer |
| `float` | `float rate = 1.5F;` | 32-bit floating point |
| `double` | `double price = 19.99;` | 64-bit floating point |
| `char` | `char grade = 'A';` | UTF-16 code unit |
| `boolean` | `boolean active = true;` | `true` or `false` |

Reference types include `String`, arrays, records, classes, interfaces, and collections.

```java
int age = 20;
final double taxRate = 0.18;
String name = "Ajmal";
var city = "Chennai"; // Local variable type inference

// taxRate = 0.2; // Does not compile
```

`var` works only for local variables with an initializer; it is not a way to declare fields without a type.

Numeric conversions:

```java
int count = 10;
long larger = count;          // widening conversion
double decimal = larger;
int truncated = (int) 9.8;    // explicit narrowing: becomes 9

String text = "123";
int parsed = Integer.parseInt(text);
double amount = Double.parseDouble("12.50");
String rendered = String.valueOf(parsed);
```

Avoid using floating-point types for exact financial calculations. Use `BigDecimal` with a defined rounding policy for money.

Default values apply to fields, not ordinary local variables. Local variables must be initialized before they are read.

---

# 6. Operators and Expressions

Arithmetic:

```java
int a = 10, b = 3;
int sum = a + b;
int difference = a - b;
int product = a * b;
int quotient = a / b;  // integer division: 3
int remainder = a % b;
double exactQuotient = (double) a / b;
```

Comparison:

```java
a == b;
a != b;
a < b;
a <= b;
a > b;
a >= b;
```

Logical:

```java
boolean valid = age >= 18 && age <= 120;
boolean allowed = isAdmin || isOwner;
boolean notEmpty = !name.isEmpty();
```

Assignment and increment:

```java
int x = 5;
x += 2;
x -= 1;
x *= 3;
x /= 2;
x++;
++x;
x--;
--x;
```

Conditional expression:

```java
String category = age >= 18 ? "adult" : "minor";
```

Bitwise operators: `&`, `|`, `^`, `~`, `<<`, `>>`, `>>>`. These are useful for bit manipulation; `&&` and `||` are the usual short-circuit logical operators.

Operator precedence can be subtle. Add parentheses when they make the intended evaluation clearer.

---

# 7. Conditions and Loops

## `if`, `else if`, `else`

```java
if (score >= 90) {
    System.out.println("A");
} else if (score >= 75) {
    System.out.println("B");
} else {
    System.out.println("Keep practicing");
}
```

## Traditional `switch`

```java
switch (day) {
    case "MONDAY":
        System.out.println("Start");
        break;
    case "FRIDAY":
        System.out.println("Finish");
        break;
    default:
        System.out.println("Regular day");
}
```

## Switch expression (modern Java)

```java
int dayNumber = switch (day) {
    case "MONDAY" -> 1;
    case "TUESDAY" -> 2;
    case "WEDNESDAY" -> 3;
    default -> 0;
};
```

## Loops

```java
for (int i = 0; i < 5; i++) {
    System.out.println(i);
}

int count = 0;
while (count < 3) {
    count++;
}

do {
    System.out.println("Runs at least once");
} while (false);

String[] names = {"Ada", "Grace"};
for (String item : names) {
    System.out.println(item);
}
```

`break` exits a loop or switch. `continue` skips to the next loop iteration. Labeled `break` and `continue` exist but should be used sparingly.

---

# 8. Methods and Function-Like Syntax

Java calls reusable operations **methods**. A method must be declared inside a class, record, enum, or interface (with applicable rules).

```java
public int add(int a, int b) {
    return a + b;
}

public void printMessage(String message) {
    System.out.println(message);
}

public static double area(double width, double height) {
    return width * height;
}
```

A method signature includes the method name and parameter types; return type alone cannot overload a method.

## Parameters, return values, and overloads

```java
public int multiply(int a, int b) {
    return a * b;
}

public double multiply(double a, double b) {
    return a * b;
}
```

## Static versus instance methods

```java
class Calculator {
    public static int square(int n) {
        return n * n;
    }

    public int add(int a, int b) {
        return a + b;
    }
}

int squared = Calculator.square(4);
int total = new Calculator().add(2, 3);
```

## Varargs

```java
public int sum(int... values) {
    int total = 0;
    for (int value : values) {
        total += value;
    }
    return total;
}

// sum(1, 2, 3, 4);
```

Only one varargs parameter can appear in a method, and it must be last.

## Recursion

```java
public long factorial(int n) {
    if (n < 0) {
        throw new IllegalArgumentException("n must be non-negative");
    }
    return n <= 1 ? 1 : n * factorial(n - 1);
}
```

Very deep recursion can cause stack overflow. An iterative solution is often safer for large input.

## Pass-by-value

Java always passes arguments by value. For object arguments, the value copied is the object reference; a method can mutate the referenced object but cannot replace the caller's variable.

---

# 9. Arrays and Varargs

```java
int[] values = {10, 20, 30};
int[] empty = new int[5];

System.out.println(values.length);
System.out.println(values[0]);
values[1] = 25;

for (int value : values) {
    System.out.println(value);
}
```

Arrays have fixed length. Valid indexes range from `0` through `length - 1`.

Multidimensional arrays:

```java
int[][] matrix = {
    {1, 2},
    {3, 4}
};

System.out.println(matrix[1][0]); // 3
```

Helpful utilities:

```java
import java.util.Arrays;

int[] numbers = {3, 1, 2};
Arrays.sort(numbers);
System.out.println(Arrays.toString(numbers));
int[] copy = Arrays.copyOf(numbers, numbers.length);
```

Use `List` when the collection needs to grow or shrink dynamically.

---

# 10. Strings, Text Blocks, and Formatting

`String` is immutable: operations produce new strings rather than changing the existing instance.

```java
String first = "Spring";
String second = "Boot";
String full = first + " " + second;

full.length();
full.isEmpty();
full.isBlank();
full.toUpperCase();
full.toLowerCase();
full.contains("Boot");
full.startsWith("Spring");
full.endsWith("Boot");
full.substring(0, 6);
full.replace("Boot", "Framework");
full.split(" ");
full.trim();
full.strip(); // Unicode-aware whitespace trimming
```

Use `.equals()` to compare text content:

```java
String expected = "admin";
if (expected.equals(userRole)) {
    // ...
}
```

`==` compares object references for strings, not content.

Text blocks (Java 15+):

```java
String json = """
        {
          "name": "Notebook",
          "price": 499.99
        }
        """;
```

Formatting:

```java
String message = String.format("User %s has %d points", name, points);
System.out.printf("Price: %.2f%n", price);
```

For repeated concatenation in loops, use `StringBuilder`:

```java
StringBuilder builder = new StringBuilder();
builder.append("Spring");
builder.append(' ');
builder.append("Boot");
String result = builder.toString();
```

---

# 11. Classes, Objects, Constructors, and Records

## Class and object

```java
public class User {
    private final String name;
    private int age;

    public User(String name, int age) {
        this.name = name;
        setAge(age);
    }

    public String getName() {
        return name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        if (age < 0) {
            throw new IllegalArgumentException("Age cannot be negative");
        }
        this.age = age;
    }
}
```

```java
User user = new User("Asha", 24);
System.out.println(user.getName());
```

- Fields store state.
- Constructors initialize objects and have no return type.
- `this` refers to the current instance.
- Encapsulation keeps implementation details behind a public API.

## Constructor overloading and chaining

```java
class Product {
    private final String name;
    private final double price;

    Product(String name) {
        this(name, 0.0);
    }

    Product(String name, double price) {
        this.name = name;
        this.price = price;
    }
}
```

Calling another constructor with `this(...)` must follow the applicable constructor invocation rules. Java 25+ has additional flexible constructor-body capabilities; check the selected JDK documentation before using newer syntax.

## Records

Records provide concise data-carrier classes:

```java
public record ProductDto(Long id, String name, double price) {}
```

A record automatically provides component accessors (`id()`, `name()`, `price()`), a canonical constructor, `equals`, `hashCode`, and `toString`. Records are shallowly immutable; mutable objects held inside a record are not automatically deep-copied.

## `equals` and `hashCode`

When defining value equality for a regular class, keep `equals` and `hashCode` consistent. Records generate them from record components.

---

# 12. Access Modifiers, Packages, and Imports

| Modifier | Typical meaning |
|---|---|
| `public` | Accessible wherever the enclosing type is accessible |
| `protected` | Same package and subclasses, subject to Java's access rules |
| no modifier | Package-private access |
| `private` | Enclosing top-level type's members are limited to the enclosing class; nested types have additional rules |

```java
package com.example.catalog;

import java.util.List;
import java.util.Optional;
```

A public top-level class typically resides in a file with the matching class name. Organize packages by feature or layer; keep the main `@SpringBootApplication` class in a root package above application components.

Common package layout:

```text
com.example.catalog
├── CatalogApplication.java
├── product
│   ├── Product.java
│   ├── ProductController.java
│   ├── ProductService.java
│   ├── ProductRepository.java
│   ├── ProductRequest.java
│   └── ProductResponse.java
└── common
    └── ApiExceptionHandler.java
```

---

# 13. Inheritance, Interfaces, and Polymorphism

## Inheritance

```java
class Animal {
    public void speak() {
        System.out.println("Sound");
    }
}

class Dog extends Animal {
    @Override
    public void speak() {
        System.out.println("Woof");
    }
}
```

## Interface

```java
interface Notifier {
    void send(String message);

    default boolean isAvailable() {
        return true;
    }

    static Notifier noop() {
        return message -> {};
    }
}
```

Classes can implement multiple interfaces but extend only one class. Prefer composition over deep inheritance hierarchies in many application designs.

## Polymorphism

```java
Notifier notifier = message -> System.out.println(message);
notifier.send("Hello");
```

The runtime implementation determines which overridden instance method runs.

## Abstract classes

```java
abstract class PaymentMethod {
    public abstract void pay(double amount);

    public void logAttempt() {
        System.out.println("Payment attempt");
    }
}
```

An abstract class cannot be instantiated directly.

---

# 14. Enums, Nested Classes, and Sealed Types

## Enums

```java
public enum OrderStatus {
    PENDING,
    PAID,
    SHIPPED,
    CANCELLED
}
```

```java
OrderStatus status = OrderStatus.PAID;

switch (status) {
    case PAID -> System.out.println("Paid");
    case PENDING -> System.out.println("Waiting");
    default -> System.out.println("Other");
}
```

Avoid relying on enum ordinal values for database persistence; use stable names or a deliberately designed mapping.

## Nested classes

Java supports static nested classes, inner classes, local classes, and anonymous classes.

```java
class Outer {
    static class Nested {
        void run() {
            System.out.println("Nested");
        }
    }
}
```

## Sealed classes (Java 17+)

```java
sealed interface ApiResult permits Success, Failure {}

record Success(String value) implements ApiResult {}
record Failure(String message) implements ApiResult {}
```

A sealed type restricts which classes may directly extend or implement it. `permits`, `non-sealed`, and `final` are used to describe the allowed hierarchy.

---

# 15. Generics

Generics provide compile-time type safety.

```java
List<String> names = new ArrayList<>();
names.add("Ada");
// names.add(10); // Compile error
```

Generic class:

```java
class Box<T> {
    private T value;

    public Box(T value) {
        this.value = value;
    }

    public T getValue() {
        return value;
    }
}
```

Generic method:

```java
public static <T> T first(List<T> items) {
    if (items.isEmpty()) {
        throw new IllegalArgumentException("List is empty");
    }
    return items.get(0);
}
```

Bounded type parameter:

```java
public static <T extends Number> double asDouble(T value) {
    return value.doubleValue();
}
```

Wildcards:

```java
List<? extends Number> source; // Read as Number; cannot safely add an arbitrary Number
List<? super Integer> target;  // Can add Integer values
```

Rule of thumb: **PECS** — Producer Extends, Consumer Super. Java generics use type erasure in most runtime contexts; parameterized types are not all preserved as distinct runtime classes.

---

# 16. Collections Framework

Main interfaces:

- `List`: ordered sequence, permits duplicates.
- `Set`: unique elements.
- `Queue` and `Deque`: queue and double-ended queue behavior.
- `Map`: key-value mappings; `Map` is not a subtype of `Collection`.

```java
import java.util.*;

List<String> names = new ArrayList<>();
names.add("Ada");
names.add("Grace");
names.get(0);
names.set(0, "Katherine");
names.remove("Grace");

Set<String> uniqueNames = new HashSet<>();
uniqueNames.add("Ada");
uniqueNames.add("Ada"); // Duplicate is not stored as another element

Map<Long, String> users = new HashMap<>();
users.put(1L, "Asha");
String userName = users.get(1L);
boolean exists = users.containsKey(1L);
users.remove(1L);
```

Common implementations:

| Interface | Implementations |
|---|---|
| `List` | `ArrayList`, `LinkedList` |
| `Set` | `HashSet`, `LinkedHashSet`, `TreeSet` |
| `Map` | `HashMap`, `LinkedHashMap`, `TreeMap`, `ConcurrentHashMap` |
| `Queue` | `ArrayDeque`, `PriorityQueue`, concurrent queues |

Immutable or unmodifiable factories:

```java
List<String> names = List.of("Ada", "Grace");
Set<Integer> ids = Set.of(1, 2, 3);
Map<String, Integer> scores = Map.of("Ada", 10, "Grace", 20);
```

These factories reject null elements/keys/values and return unmodifiable collections.

Sorting:

```java
names.sort(Comparator.naturalOrder());

List<Product> sorted = products.stream()
        .sorted(Comparator.comparing(Product::getName))
        .toList();
```

Choose collection implementations based on required ordering, lookup behavior, concurrency, and memory needs.

---

# 17. Lambdas, Functional Interfaces, and Streams

## Lambda expressions

```java
Runnable task = () -> System.out.println("Running");

Comparator<String> byLength =
        (left, right) -> Integer.compare(left.length(), right.length());
```

## Method references

```java
names.forEach(System.out::println);
names.stream().map(String::toUpperCase);
```

Common functional interfaces from `java.util.function`:

- `Predicate<T>`: `boolean test(T value)`
- `Function<T, R>`: `R apply(T value)`
- `Consumer<T>`: `void accept(T value)`
- `Supplier<T>`: `T get()`
- `UnaryOperator<T>`: transforms `T` into `T`
- `BiFunction<T, U, R>`: takes two values and returns one

```java
Predicate<String> nonBlank = value -> !value.isBlank();
Function<String, Integer> length = String::length;
Consumer<String> printer = System.out::println;
Supplier<UUID> idGenerator = UUID::randomUUID;
```

## Streams

```java
List<String> result = names.stream()
        .filter(name -> name.length() >= 4)
        .map(String::toUpperCase)
        .sorted()
        .toList();
```

Frequently used methods:

- Intermediate: `filter`, `map`, `flatMap`, `distinct`, `sorted`, `peek`, `limit`, `skip`, `takeWhile`, `dropWhile`.
- Terminal: `toList`, `collect`, `forEach`, `count`, `min`, `max`, `anyMatch`, `allMatch`, `noneMatch`, `findFirst`, `findAny`, `reduce`.
- Creation: `stream`, `Stream.of`, `Arrays.stream`, `IntStream.range`.

Grouping:

```java
Map<String, List<Product>> byCategory = products.stream()
        .collect(Collectors.groupingBy(Product::getCategory));
```

Summing:

```java
double total = products.stream()
        .mapToDouble(Product::getPrice)
        .sum();
```

Streams are lazy until a terminal operation runs. Avoid side effects inside stream pipelines. A stream should normally be consumed only once. Parallel streams are not an automatic performance win; measure before using them.

---

# 18. Optional

`Optional<T>` represents a value that may be absent.

```java
Optional<User> found = repository.findById(id);

String name = found
        .map(User::getName)
        .orElse("Unknown");
```

Methods include `empty`, `of`, `ofNullable`, `isPresent`, `isEmpty`, `ifPresent`, `ifPresentOrElse`, `map`, `flatMap`, `filter`, `orElse`, `orElseGet`, `orElseThrow`, and `stream`.

```java
User user = repository.findById(id)
        .orElseThrow(() -> new UserNotFoundException(id));
```

Use `orElseGet` when computing the fallback is expensive or has side effects; `orElse` evaluates its argument eagerly. Optional is most commonly useful as a return type, not as a replacement for every nullable field or method parameter.

---

# 19. Exceptions and Error Handling

Hierarchy overview:

- `Throwable`
  - `Error`: serious conditions generally not handled by application code.
  - `Exception`
    - Checked exceptions, which must be caught or declared.
    - `RuntimeException` and subclasses, which are unchecked.

```java
try {
    int number = Integer.parseInt("123");
    System.out.println(number);
} catch (NumberFormatException exception) {
    System.err.println("Invalid number: " + exception.getMessage());
} finally {
    System.out.println("Cleanup can go here");
}
```

Throwing:

```java
if (amount <= 0) {
    throw new IllegalArgumentException("Amount must be positive");
}
```

Declaring checked exceptions:

```java
public String readConfig(Path path) throws IOException {
    return Files.readString(path);
}
```

Try-with-resources:

```java
try (BufferedReader reader = Files.newBufferedReader(path)) {
    return reader.readLine();
}
```

Custom exception:

```java
public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(Long id) {
        super("Product not found: " + id);
    }
}
```

Good practices:
- Catch the most specific exception you can handle.
- Do not silently swallow exceptions.
- Do not return internal stack traces to API clients.
- Preserve causes when wrapping exceptions.
- Use `try-with-resources` for `AutoCloseable` resources.
- Avoid using exceptions as ordinary control flow.

---

# 20. Date and Time API

Use `java.time` rather than old `Date`/`Calendar` APIs for most new code.

```java
LocalDate today = LocalDate.now();
LocalTime nowTime = LocalTime.now();
LocalDateTime localDateTime = LocalDateTime.now();
Instant timestamp = Instant.now();
OffsetDateTime offsetTime = OffsetDateTime.now();
ZonedDateTime zoned = ZonedDateTime.now(ZoneId.of("Asia/Kolkata"));

LocalDate dueDate = today.plusDays(7);
Period period = Period.between(today, dueDate);
Duration duration = Duration.ofMinutes(30);
```

Important types:
- `LocalDate`: date without time zone.
- `LocalTime`: time without date or zone.
- `LocalDateTime`: date-time without zone.
- `Instant`: point on the UTC timeline.
- `OffsetDateTime` / `ZonedDateTime`: date-time with offset/zone information.
- `Duration`: time-based amount.
- `Period`: date-based amount.

Formatting:

```java
DateTimeFormatter formatter = DateTimeFormatter.ISO_LOCAL_DATE;
String value = today.format(formatter);
LocalDate parsedDate = LocalDate.parse(value, formatter);
```

Store timestamps using an intentional time-zone policy. For cross-region applications, persist a suitable instant and retain a zone separately when business rules depend on a user's named time zone.

---

# 21. File I/O and Resource Management

```java
Path path = Path.of("data", "notes.txt");

Files.writeString(path, "Hello");
String text = Files.readString(path);
List<String> lines = Files.readAllLines(path);
boolean exists = Files.exists(path);
```

Directory listing:

```java
try (Stream<Path> entries = Files.list(Path.of("data"))) {
    entries.forEach(System.out::println);
}
```

Imports commonly needed:

```java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.stream.Stream;
```

Always check path permissions, maximum file sizes, allowed file types, and whether user-controlled paths could escape an intended directory. Do not trust a client-supplied filename or content type.

---

# 22. Concurrency and Virtual Threads

Java concurrency APIs include `Thread`, `Runnable`, `Callable`, `ExecutorService`, `Future`, `CompletableFuture`, synchronization utilities, locks, and concurrent collections.

```java
ExecutorService executor = Executors.newFixedThreadPool(4);

try {
    Future<Integer> future = executor.submit(() -> 20 + 22);
    System.out.println(future.get());
} finally {
    executor.shutdown();
}
```

`CompletableFuture`:

```java
CompletableFuture<String> future =
        CompletableFuture.supplyAsync(() -> "hello")
                .thenApply(String::toUpperCase)
                .exceptionally(error -> "FALLBACK");

String result = future.join();
```

Virtual threads (Java 21+):

```java
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<String> future = executor.submit(() -> callRemoteService());
    System.out.println(future.get());
}
```

Use concurrency deliberately. Shared mutable state can lead to race conditions. Use thread-safe structures, locks, immutability, and clear ownership rules where appropriate. Virtual threads help many blocking-I/O workloads but do not make CPU-heavy work infinitely scalable.

In Spring, `@Async` and task executors can help with background work, but configure them and handle failures deliberately. Never assume that placing `@Async` on a method makes every invocation asynchronous; proxying and call paths matter.

---

# 23. Annotations and Reflection

Annotations add metadata to program elements.

Common Java annotations:

```java
@Override
@Deprecated
@SuppressWarnings("unchecked")
@FunctionalInterface
```

Custom annotation:

```java
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Audited {
    String value() default "";
}
```

Reflection can inspect classes and methods at runtime:

```java
Class<?> type = User.class;

for (Method method : type.getDeclaredMethods()) {
    System.out.println(method.getName());
}
```

Reflection imports:

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;
```

Reflection is powerful but can reduce compile-time safety and complicate maintenance. Use it when framework integration or metadata-driven behavior warrants it.

---

# 24. JDBC and SQL Fundamentals

JDBC is Java's low-level API for relational databases. In normal Spring Boot applications, Spring Data JPA or `JdbcTemplate` may remove much of the repetitive JDBC code.

Parameterized JDBC example:

```java
String sql = "SELECT id, name FROM products WHERE id = ?";

try (Connection connection = dataSource.getConnection();
     PreparedStatement statement = connection.prepareStatement(sql)) {
    statement.setLong(1, id);

    try (ResultSet result = statement.executeQuery()) {
        if (result.next()) {
            String name = result.getString("name");
        }
    }
}
```

Important JDBC types include `DataSource`, `Connection`, `PreparedStatement`, `ResultSet`, and `SQLException`.

Never build SQL by concatenating untrusted user input. Use parameters or safe query APIs to prevent SQL injection. Table names and column names generally cannot be passed as ordinary value parameters; any dynamic identifiers must come from a strict allowlist.

---

# 25. Spring Boot Project Structure

A typical feature-oriented structure:

```text
src/
├── main/
│   ├── java/com/example/catalog/
│   │   ├── CatalogApplication.java
│   │   ├── product/
│   │   │   ├── Product.java
│   │   │   ├── ProductRequest.java
│   │   │   ├── ProductResponse.java
│   │   │   ├── ProductRepository.java
│   │   │   ├── ProductService.java
│   │   │   └── ProductController.java
│   │   └── common/
│   │       └── ApiExceptionHandler.java
│   └── resources/
│       ├── application.yml
│       └── db/migration/
└── test/
    └── java/com/example/catalog/
```

Keep the main application class at a parent package so component scanning can discover child packages.

---

# 26. Spring Boot Application Startup and Auto-Configuration

Entry point:

```java
package com.example.catalog;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class CatalogApplication {
    public static void main(String[] args) {
        SpringApplication.run(CatalogApplication.class, args);
    }
}
```

`@SpringBootApplication` combines the key configuration behavior of:
- `@SpringBootConfiguration`
- `@EnableAutoConfiguration`
- `@ComponentScan`

Auto-configuration registers infrastructure based on dependencies and application configuration. You can override defaults by providing your own beans or properties.

Run with Maven:

```bash
mvn spring-boot:run
```

Or package and run:

```bash
mvn clean package
java -jar target/catalog-api-0.0.1-SNAPSHOT.jar
```

Startup lifecycle callbacks include `ApplicationRunner` and `CommandLineRunner`. Use them for controlled startup tasks, not long-running loops that block application startup.

---

# 27. Spring Core: IoC, Beans, and Dependency Injection

**Inversion of Control (IoC)** means the container manages object creation and wiring. **Dependency Injection (DI)** lets a class receive collaborators instead of constructing them itself.

Recommended constructor injection:

```java
@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

With a single constructor, `@Autowired` is generally unnecessary.

Important stereotype/configuration annotations:

- `@Component`: generic managed component.
- `@Service`: service-layer component.
- `@Repository`: persistence-oriented component.
- `@Controller`: MVC controller for views.
- `@RestController`: REST controller; response bodies are written directly.
- `@Configuration`: configuration class.
- `@Bean`: method declares an object managed by Spring.
- `@Primary`: preferred bean when multiple candidates match.
- `@Qualifier`: selects a specific bean.
- `@Profile`: bean/configuration active only for specified profiles.
- `@Scope`: bean scope configuration.
- `@Lazy`: delay initialization under supported circumstances.

Configuration example:

```java
@Configuration
public class AppConfiguration {
    @Bean
    Clock applicationClock() {
        return Clock.systemUTC();
    }
}
```

Inject it through a constructor:

```java
@Service
public class AuditService {
    private final Clock clock;

    public AuditService(Clock clock) {
        this.clock = clock;
    }
}
```

Common bean scopes include singleton (default), prototype, and web-aware request/session scopes when the relevant environment is present. Singleton does not mean that every method is thread-safe; avoid storing per-request mutable state in singleton services.

---

# 28. Configuration: Properties, YAML, Profiles, and Secrets

`src/main/resources/application.yml`:

```yaml
server:
  port: 8080

spring:
  application:
    name: catalog-api
  datasource:
    url: ${DB_URL:jdbc:postgresql://localhost:5432/catalog}
    username: ${DB_USERNAME:catalog}
    password: ${DB_PASSWORD:}
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate

management:
  endpoints:
    web:
      exposure:
        include: health,info
```

Equivalent properties are written as `key=value`.

Profiles:

```yaml
spring:
  config:
    activate:
      on-profile: dev
```

Alternatively use `application-dev.yml`, `application-test.yml`, and `application-prod.yml`. Activate a profile with:

```bash
SPRING_PROFILES_ACTIVE=dev
```

Use environment variables or a secrets manager for credentials. Never commit passwords, API keys, signing keys, or production connection strings to source control.

Bind grouped properties with `@ConfigurationProperties`:

```java
@ConfigurationProperties(prefix = "catalog")
public record CatalogProperties(String defaultCategory, int maxPageSize) {}
```

Register it using `@ConfigurationPropertiesScan` on the application class or `@EnableConfigurationProperties(CatalogProperties.class)` in configuration.

---

# 29. Building REST APIs with Spring MVC

REST APIs expose resources through HTTP methods and status codes.

| HTTP method | Common purpose |
|---|---|
| `GET` | Read a resource |
| `POST` | Create or trigger an operation |
| `PUT` | Replace a resource |
| `PATCH` | Partially update a resource |
| `DELETE` | Remove a resource |

Controller example:

```java
@RestController
@RequestMapping("/api/greetings")
public class GreetingController {

    @GetMapping
    public Map<String, String> greet() {
        return Map.of("message", "Hello!");
    }

    @GetMapping("/{name}")
    public Map<String, String> greetName(@PathVariable String name) {
        return Map.of("message", "Hello, " + name);
    }

    @GetMapping("/search")
    public Map<String, String> search(
            @RequestParam(defaultValue = "guest") String name) {
        return Map.of("message", "Hello, " + name);
    }
}
```

Request body:

```java
@PostMapping
public ResponseEntity<Map<String, String>> create(
        @RequestBody Map<String, String> payload) {
    return ResponseEntity.status(HttpStatus.CREATED).body(payload);
}
```

Prefer request DTOs over arbitrary maps for real APIs.

Parameter annotations:

- `@PathVariable`: value from URL path.
- `@RequestParam`: query/form parameter.
- `@RequestHeader`: HTTP header.
- `@CookieValue`: cookie.
- `@RequestBody`: body converted to a Java object.
- `@ModelAttribute`: bind request parameters to an object, typically for MVC forms.
- `@RequestPart`: part of a multipart request.
- `@ResponseStatus`: declare a response status.
- `@CrossOrigin`: configure endpoint-level CORS where appropriate.

Response entity:

```java
return ResponseEntity.ok(response);
return ResponseEntity.created(location).body(response);
return ResponseEntity.noContent().build();
return ResponseEntity.notFound().build();
```

Common HTTP statuses:
- `200 OK`: successful read/update with response.
- `201 Created`: resource created.
- `204 No Content`: successful operation with no response body.
- `400 Bad Request`: invalid client input.
- `401 Unauthorized`: authentication is missing/invalid.
- `403 Forbidden`: authenticated client is not allowed.
- `404 Not Found`: resource does not exist or is not exposed.
- `409 Conflict`: state conflict.
- `422 Unprocessable Content`: sometimes used for semantic validation failures.
- `500 Internal Server Error`: unexpected server failure.

Use consistent status semantics and document your endpoints.

---

# 30. DTOs, Records, and Validation

DTOs (Data Transfer Objects) define the input/output shape of an API separately from database entities.

```java
public record ProductRequest(
        @NotBlank(message = "Name is required")
        @Size(max = 120)
        String name,

        @NotNull
        @PositiveOrZero
        BigDecimal price
) {}
```

Response DTO:

```java
public record ProductResponse(
        Long id,
        String name,
        BigDecimal price
) {}
```

Controller validation:

```java
@PostMapping
public ResponseEntity<ProductResponse> create(
        @Valid @RequestBody ProductRequest request) {
    ProductResponse created = service.create(request);
    return ResponseEntity.status(HttpStatus.CREATED).body(created);
}
```

Common Bean Validation constraints (with `spring-boot-starter-validation`):
- `@NotNull`
- `@NotBlank`
- `@NotEmpty`
- `@Size`
- `@Min`, `@Max`
- `@Positive`, `@PositiveOrZero`, `@Negative`
- `@DecimalMin`, `@DecimalMax`
- `@Email`
- `@Pattern`
- `@Past`, `@PastOrPresent`, `@Future`, `@FutureOrPresent`
- `@Valid` for nested validation
- `@AssertTrue`, `@AssertFalse`

Validation is not authorization. A valid request can still be forbidden by business rules.

---

# 31. Error Handling and API Response Design

Define a stable error response:

```java
public record ApiError(
        Instant timestamp,
        int status,
        String error,
        String message,
        String path
) {}
```

A global handler using Spring MVC:

```java
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<ApiError> handleNotFound(
            ProductNotFoundException exception,
            HttpServletRequest request) {

        ApiError body = new ApiError(
                Instant.now(),
                404,
                "Not Found",
                exception.getMessage(),
                request.getRequestURI()
        );

        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(body);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidation(
            MethodArgumentNotValidException exception,
            HttpServletRequest request) {

        String message = exception.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .findFirst()
                .orElse("Invalid request");

        ApiError body = new ApiError(
                Instant.now(), 400, "Bad Request", message,
                request.getRequestURI()
        );

        return ResponseEntity.badRequest().body(body);
    }
}
```

Required imports include `HttpServletRequest`, validation exception classes, `Instant`, and Spring web/HTTP types.

For a complete production handler, also consider malformed JSON, constraint violations, missing parameters, conflicts, access-denied errors, and safe fallback handling. Avoid exposing SQL, file paths, stack traces, credentials, and internal implementation details to clients.

Spring Boot and Spring Framework versions may provide Problem Details support using `ProblemDetail`; check the documentation for the selected version and standardize the API error format.

---

# 32. Spring Data JPA and Database Mapping

Entity example:

```java
@Entity
@Table(name = "products")
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 120)
    private String name;

    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal price;

    protected Product() {
        // Required by common JPA entity construction rules
    }

    public Product(String name, BigDecimal price) {
        this.name = name;
        this.price = price;
    }

    public Long getId() { return id; }
    public String getName() { return name; }
    public BigDecimal getPrice() { return price; }

    public void rename(String name) {
        this.name = name;
    }

    public void changePrice(BigDecimal price) {
        this.price = price;
    }
}
```

Common annotations:
- `@Entity`, `@Table`
- `@Id`, `@GeneratedValue`
- `@Column`
- `@Enumerated`
- `@Embedded`, `@Embeddable`
- `@Version` for optimistic locking
- `@OneToOne`, `@OneToMany`, `@ManyToOne`, `@ManyToMany`
- `@JoinColumn`, `@JoinTable`
- `@MappedSuperclass`

Store enum names rather than ordinals when that is the intended stable mapping:

```java
@Enumerated(EnumType.STRING)
private OrderStatus status;
```

Avoid returning JPA entities directly from controllers. Entity graphs and bidirectional relationships can expose fields unexpectedly, trigger lazy-loading issues, or create JSON cycles. Map entities to DTOs.

Relationship example:

```java
@ManyToOne(fetch = FetchType.LAZY, optional = false)
@JoinColumn(name = "category_id", nullable = false)
private Category category;
```

Be explicit about cascading, fetch strategy, ownership, and delete behavior. `CascadeType.ALL` is not appropriate for every relationship.

For schema creation, development environments may use `ddl-auto: update`, but production should normally use reviewed database migrations and a validation-oriented schema setting.

---

# 33. Repositories, Queries, Pagination, and Sorting

Repository interface:

```java
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByNameContainingIgnoreCase(String name);
    Optional<Product> findByNameIgnoreCase(String name);
    boolean existsByNameIgnoreCase(String name);
    long countByPriceGreaterThanEqual(BigDecimal minimum);
}
```

Spring Data derives queries from method names. Examples include `findBy`, `existsBy`, `countBy`, `deleteBy`, `And`, `Or`, `Between`, `LessThan`, `GreaterThanEqual`, `Containing`, `IgnoreCase`, `OrderBy`, and `In`.

JPQL query:

```java
@Query("select p from Product p where p.price >= :minimum")
List<Product> findAffordable(@Param("minimum") BigDecimal minimum);
```

Native SQL may be used when needed, but it ties queries to a database dialect:

```java
@Query(value = "SELECT * FROM products WHERE price >= :minimum",
       nativeQuery = true)
List<Product> findNativeAffordable(@Param("minimum") BigDecimal minimum);
```

Pagination and sorting:

```java
Page<Product> page = repository.findAll(
        PageRequest.of(0, 20, Sort.by("name").ascending())
);
```

Controller query parameters:

```java
@GetMapping
public Page<ProductResponse> list(
        @PageableDefault(size = 20, sort = "name") Pageable pageable) {
    return service.list(pageable);
}
```

Put a sensible maximum on page size. Validate allowed sort fields so clients cannot request unsupported or sensitive fields. For read-heavy endpoints, DTO projections can reduce unnecessary entity loading.

---

# 34. Transactions and Service-Layer Design

Service layer example:

```java
@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public ProductResponse findById(Long id) {
        Product product = repository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException(id));

        return toResponse(product);
    }

    @Transactional
    public ProductResponse create(ProductRequest request) {
        Product product = new Product(request.name(), request.price());
        Product saved = repository.save(product);
        return toResponse(saved);
    }

    private ProductResponse toResponse(Product product) {
        return new ProductResponse(product.getId(), product.getName(), product.getPrice());
    }
}
```

`@Transactional` controls transaction boundaries when called through the Spring transaction infrastructure. Common attributes include `readOnly`, `timeout`, `rollbackFor`, `noRollbackFor`, and transaction propagation settings.

Important behavior:
- By default, Spring commonly rolls back on unchecked exceptions and `Error`, but not every checked exception. Configure rollback rules if needed.
- Proxy-based transaction advice has self-invocation limitations: calling another `@Transactional` method within the same object may bypass proxy advice.
- Do not hold a database transaction open while waiting on slow external network services without a strong reason.
- Use optimistic locking (`@Version`) or other concurrency controls for conflicting updates.

Use the service layer for multi-step business operations instead of putting all logic in controller methods.

---

# 35. Database Migrations

Use a migration tool such as Flyway or Liquibase to version schema changes. Example Flyway filename:

```text
src/main/resources/db/migration/V1__create_products.sql
```

Example SQL:

```sql
CREATE TABLE products (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0)
);
```

A migration is generally append-only after it has been applied to shared environments. Write a new migration for changes rather than editing an old migration already applied elsewhere. Test upgrades from realistic schema versions and back up important data before risky migrations.

---

# 36. Calling External APIs

For synchronous HTTP calls in current Spring applications, consider Spring's `RestClient`; for reactive/non-blocking work, `WebClient` may be appropriate. Use the client and starter versions supported by the selected Spring Boot release.

Illustrative `RestClient` example:

```java
@Service
public class CatalogClient {
    private final RestClient restClient;

    public CatalogClient(RestClient.Builder builder) {
        this.restClient = builder
                .baseUrl("https://api.example.com")
                .build();
    }

    public RemoteProduct getProduct(String id) {
        return restClient.get()
                .uri("/products/{id}", id)
                .retrieve()
                .body(RemoteProduct.class);
    }
}
```

Create a configuration bean or inject a configured builder according to the current Boot version and the exact APIs available. Define connection/read timeouts, authentication, retry rules, and error mapping appropriate to the service. Retry only operations where retrying is safe; repeated `POST` calls may create duplicate effects unless an idempotency strategy exists.

Never hard-code credentials or trust response bodies without validation.

---

# 37. Spring Security Fundamentals

Adding Spring Security changes the default access behavior of a web application. Configure an explicit security policy instead of assuming endpoints remain public or protected automatically.

Security responsibilities:
- Authentication: who is the caller?
- Authorization: what is the caller allowed to do?
- Password storage: use a slow, purpose-built password hashing function.
- Session/cookie policy: protect session identifiers and account for CSRF.
- Token policy: validate issuer, audience, signature, expiry, and claims when using JWTs.
- Endpoint policy: define public routes, user routes, and admin routes deliberately.

Minimal configuration shape for a stateless API (illustrative; adapt to your authentication mechanism and Boot version):

```java
@Configuration
@EnableWebSecurity
public class SecurityConfiguration {

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
                .csrf(csrf -> csrf.disable()) // Only appropriate for a deliberately stateless API
                .sessionManagement(session -> session
                        .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/api/public/**", "/actuator/health").permitAll()
                        .requestMatchers("/api/admin/**").hasRole("ADMIN")
                        .anyRequest().authenticated())
                .build();
    }
}
```

**Security caveat:** Disabling CSRF is not a universal recommendation. It can be appropriate for APIs that do not use browser cookies for authentication, but cookie-based session authentication usually needs CSRF protection. Choose the policy based on how clients authenticate.

This configuration alone does not implement authentication. Add a supported authentication mechanism such as OAuth 2.0 Resource Server for validated bearer tokens, or configure secure login/session handling. Do not hand-roll cryptographic token verification.

---

# 38. Password Hashing, Authentication, and Authorization

Use a password encoder rather than storing raw or reversibly encrypted passwords.

```java
@Bean
PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}
```

Where appropriate, choose a supported adaptive password hash (for example BCrypt or Argon2) and tune its parameters to the deployment environment.

Encode a password before storage:

```java
String storedHash = passwordEncoder.encode(rawPassword);
boolean matches = passwordEncoder.matches(candidatePassword, storedHash);
```

Never log raw passwords or return hashes in API responses.

Method authorization can be enabled in configuration:

```java
@EnableMethodSecurity
@Configuration
public class MethodSecurityConfiguration {}
```

Then:

```java
@PreAuthorize("hasRole('ADMIN')")
public void deleteProduct(Long id) {
    // ...
}
```

Check the exact role/authority naming convention used by your authentication setup. `hasRole("ADMIN")` commonly checks for an authority prefixed with `ROLE_`; `hasAuthority(...)` checks an exact authority string.

Never rely only on a frontend hiding a button. Enforce access rules on the server for every sensitive operation.

---

# 39. CORS, CSRF, and Other Security Practices

CORS controls whether browser JavaScript from one origin can read responses from another origin. It is not authentication and does not stop non-browser clients from making requests.

Controller-level CORS:

```java
@CrossOrigin(origins = "https://app.example.com")
@RestController
@RequestMapping("/api")
class ExampleController {}
```

Prefer centralized, explicit CORS policy for larger applications. Avoid allowing every origin together with credentials.

Security checklist:
- Use HTTPS in production.
- Validate input on the server.
- Use parameterized SQL / ORM APIs.
- Keep dependencies patched.
- Enforce authorization in server-side services/endpoints.
- Protect cookies with appropriate `Secure`, `HttpOnly`, and `SameSite` settings.
- Keep secrets out of Git and logs.
- Limit request size and upload size.
- Rate-limit high-risk endpoints where appropriate.
- Avoid leaking stack traces, tokens, or sensitive data.
- Set appropriate security headers.
- Use least-privilege database credentials.
- Add audit logging for sensitive actions.
- Do not invent your own cryptographic algorithms.
- Avoid mass assignment by binding requests to dedicated DTOs rather than unrestricted entities.

---

# 40. File Upload and Download

Controller example:

```java
@PostMapping("/files")
public ResponseEntity<Map<String, String>> upload(
        @RequestParam("file") MultipartFile file) throws IOException {

    if (file.isEmpty()) {
        throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "File is empty");
    }

    // Store using a server-generated identifier and a configured storage service.
    // Validate size, allowed types, content, and access policy before persistence.
    String storedName = storageService.store(file);

    return ResponseEntity.status(HttpStatus.CREATED)
            .body(Map.of("fileId", storedName));
}
```

The `storageService` is application-specific and must be implemented. Do not use a user-supplied filename as a filesystem path. Store outside the public web root or use object storage; check extension, MIME type, file signature where possible, maximum size, and malware scanning needs. Authorization should protect both upload and download endpoints.

Set upload limits through the multipart configuration supported by the selected Boot version, for example:

```yaml
spring:
  servlet:
    multipart:
      max-file-size: 10MB
      max-request-size: 12MB
```

For production, define retention, private access, backups, quotas, and cleanup policies.

---

# 41. Caching, Scheduling, and Asynchronous Work

## Caching

Enable caching:

```java
@EnableCaching
@Configuration
public class CacheConfiguration {}
```

Example:

```java
@Cacheable(cacheNames = "products", key = "#id")
public ProductResponse findById(Long id) {
    // ...
}

@CacheEvict(cacheNames = "products", key = "#id")
public void deleteById(Long id) {
    // ...
}
```

Caching requires an actual cache provider/configuration suitable for the environment. Consider invalidation, TTL, consistency, memory limits, and whether the result is safe to share between users.

## Scheduling

```java
@EnableScheduling
@Configuration
class SchedulingConfiguration {}
```

```java
@Component
public class CleanupJob {

    @Scheduled(cron = "0 0 2 * * *")
    public void runCleanup() {
        // Keep work bounded and observable.
    }
}
```

Cron expressions and time-zone behavior should be checked against Spring's supported syntax. In multi-instance deployments, a scheduled job may run on every instance unless you coordinate it with a distributed lock or another scheduling design.

## Async execution

`@Async` can run work on a configured task executor:

```java
@Async
public CompletableFuture<Void> sendNotification() {
    // ...
    return CompletableFuture.completedFuture(null);
}
```

Enable asynchronous execution when needed using `@EnableAsync`. Configure thread pool size and queue capacity. Handle exceptions, cancellation, retry, and shutdown behavior instead of ignoring task failures.

---

# 42. Logging, Actuator, Metrics, and Health Checks

Use a logger rather than `System.out.println` in application code:

```java
private static final Logger log =
        LoggerFactory.getLogger(ProductService.class);

log.info("Creating product");
log.warn("Unexpected request state");
log.error("Operation failed", exception);
```

Avoid logging credentials, access tokens, sensitive personal information, or raw secret-bearing payloads.

Add `spring-boot-starter-actuator` to expose operational endpoints. A conservative setting is:

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info
  endpoint:
    health:
      show-details: never
```

Health endpoint commonly:

```text
GET /actuator/health
```

Actuator endpoints can disclose system information or perform management operations. Expose only what is needed and protect the endpoints at the network and application layers. Metrics may be exported using Micrometer integrations when configured.

---

# 43. Testing Java and Spring Boot Applications

## Unit test with JUnit

```java
class CalculatorTest {
    @Test
    void addsTwoNumbers() {
        assertEquals(5, 2 + 3);
    }
}
```

## Service unit tests

Test business rules directly; inject fake or mocked dependencies where useful. Avoid using mocks for every object when a simple real object would be clearer.

## Spring Boot integration test

```java
@SpringBootTest
class CatalogApplicationTest {
    @Test
    void contextLoads() {
    }
}
```

## MVC slice test (illustrative)

Depending on the current Spring Boot release, use its MVC test starter and supported test annotations. `@WebMvcTest` is common in Spring Boot 3 projects and remains a familiar testing pattern; verify the matching Boot 4 testing module if using Boot 4.

Example shape:

```java
@WebMvcTest(ProductController.class)
class ProductControllerTest {
    @Autowired
    MockMvc mockMvc;

    @Test
    void healthLikeEndpointReturnsOk() throws Exception {
        // Configure/mocked controller dependencies as needed.
        // mockMvc.perform(get("/api/products"))
        //        .andExpect(status().isOk());
    }
}
```

Useful test styles:
- Unit tests: one class or method with dependencies controlled.
- Slice tests: MVC, JSON, repository, or JDBC subset.
- Integration tests: Spring context plus multiple layers.
- End-to-end tests: app started and exercised through HTTP.
- Contract tests: ensure API consumers/providers agree.
- Load tests: validate throughput and latency under expected workloads.

Test validation failures, access controls, missing records, pagination boundaries, transaction behavior, and unexpected dependencies. Avoid making tests depend on live third-party services unless the test is explicitly an external integration check.

---

# 44. API Documentation

OpenAPI describes API endpoints, parameters, schemas, and responses. Integrate an OpenAPI generator/library that is compatible with your Spring Boot version, then document:
- Endpoint purpose.
- Query/path parameters.
- Request and response schemas.
- Authentication requirements.
- Status codes and error format.
- Pagination and filtering.
- Rate limits and idempotency requirements where relevant.

Treat API schema as a maintained contract, not merely a generated UI. Do not publish secrets or internal administration details in public API documentation.

---

# 45. WebSockets and Reactive Programming Overview

## WebSockets

WebSockets support long-lived, bidirectional communication. Common uses include live chat, notifications, and dashboards. Spring supports WebSocket integrations; choose the starter/protocol appropriate to the app (raw WebSocket, STOMP, or another messaging protocol).

Consider authentication, authorization per destination, message validation, payload limits, reconnect behavior, and horizontal scaling.

## Spring WebFlux and Reactor

WebFlux provides a reactive web stack. A basic shape:

```java
@RestController
@RequestMapping("/reactive")
class ReactiveController {

    @GetMapping
    Mono<String> hello() {
        return Mono.just("Hello");
    }

    @GetMapping("/items")
    Flux<String> items() {
        return Flux.just("one", "two", "three");
    }
}
```

This example assumes the WebFlux starter and Reactor types are on the classpath.

Learn:
- `Mono<T>`: zero or one item.
- `Flux<T>`: zero to many items.
- `map`, `flatMap`, `filter`, `zip`, `onErrorResume`, `timeout`, `retry`.
- Backpressure and cancellation.
- Non-blocking I/O requirements.

Do not block event-loop threads with blocking database drivers or long-running CPU work. Use MVC for many conventional applications; reactive programming is most valuable when the whole request path benefits from non-blocking I/O.

---

# 46. Email and Background Jobs

Email typically needs a mail starter and SMTP or provider configuration. Externalize SMTP credentials and use provider-specific authentication guidance. For reliability, send important email through a queued/background workflow and track delivery failures rather than blocking the main API request indefinitely.

Background jobs should consider retries, deduplication, idempotency, observability, timeouts, and application shutdown behavior. For durable workflows, use a persistent queue/job system rather than relying only on an in-memory task.

---

# 47. Docker and Deployment

Example Dockerfile (adjust the JAR path/name to your actual Maven artifact):

```dockerfile
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY target/catalog-api-0.0.1-SNAPSHOT.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

Build and run:

```bash
mvn clean package
docker build -t catalog-api:local .
docker run --rm -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=prod \
  -e DB_URL="jdbc:postgresql://host.docker.internal:5432/catalog" \
  -e DB_USERNAME="catalog" \
  -e DB_PASSWORD="set-through-a-secret-store" \
  catalog-api:local
```

The exact host name depends on the environment; `host.docker.internal` is not universally available in all Linux/container setups. Use a container network or managed database address in real deployments.

Production checklist:
- Use a supported JDK and patched base image.
- Run as a non-root user where possible.
- Externalize secrets.
- Configure connection pools and timeouts.
- Apply database migrations safely.
- Configure health checks, logs, metrics, and alerts.
- Use HTTPS and secure network rules.
- Test graceful shutdown.
- Define backup/restore and rollback procedures.
- Pin and review dependencies and container images.
- Do not expose management endpoints publicly without protection.

---

# 48. Microservices and Messaging Overview

A monolith can be the right choice. Split services only when independent deployment, scaling, ownership, or boundaries justify the operational cost.

Common ecosystem options include:
- Spring Cloud Config for externalized distributed configuration patterns.
- Spring Cloud Gateway for API gateway patterns.
- Messaging using Kafka, RabbitMQ/AMQP, or other brokers.
- Resilience patterns such as timeouts, bounded retries, circuit breakers, and bulkheads.
- Distributed tracing and metrics.
- OAuth 2.0 / OpenID Connect for identity across services.

Design for message idempotency, schema evolution, duplicate delivery, ordering requirements, and dead-letter handling. A distributed transaction across services usually needs a saga/outbox-style design or compensating actions rather than a single local database transaction.

---

# 49. Performance and Troubleshooting

Start with measurement:
- Profile CPU and allocation.
- Review SQL queries and indexes.
- Watch connection-pool wait times.
- Find N+1 database queries.
- Use pagination rather than returning unbounded lists.
- Cache only where consistency and invalidation are understood.
- Tune thread pools and timeouts based on workload measurements.
- Monitor latency percentiles, failure rate, traffic, saturation, and resource usage.

Common issues:

| Problem | Likely place to investigate |
|---|---|
| Application fails to start | Startup logs, missing bean, invalid configuration, dependency mismatch |
| Database connection refused | URL, port, network, database status, credentials |
| 404 | Route mapping, HTTP method, context path |
| 400 | JSON shape, input conversion, validation |
| 401 | Authentication setup, missing/invalid credentials |
| 403 | Authorization rules, CSRF, role/authority mapping |
| 415 | Content-Type mismatch |
| 500 | Exception logs, SQL error, null handling, external dependency |
| Lazy-loading exception | Transaction boundaries, DTO mapping, fetch strategy |
| Duplicate records | Missing uniqueness rule, concurrency, retry behavior |
| Slow requests | Query plans, network calls, pool/thread saturation, serialization |

Use `mvn dependency:tree` to find unexpected dependency versions. Avoid fixing dependency conflicts by randomly overriding transitive versions; use the Spring Boot dependency management and official compatibility information.

---

# 50. Complete CRUD Example

The following snippets form the core of a small Product CRUD API. Place each public Java type in its own matching `.java` file. They assume the dependencies in Section 3 and package root `com.example.catalog`.

## 50.1 Entity

`product/Product.java`

```java
package com.example.catalog.product;

import jakarta.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "products")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 120)
    private String name;

    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal price;

    protected Product() {}

    public Product(String name, BigDecimal price) {
        this.name = name;
        this.price = price;
    }

    public Long getId() { return id; }
    public String getName() { return name; }
    public BigDecimal getPrice() { return price; }

    public void update(String name, BigDecimal price) {
        this.name = name;
        this.price = price;
    }
}
```

## 50.2 Request and response DTOs

`product/ProductRequest.java`

```java
package com.example.catalog.product;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;

public record ProductRequest(
        @NotBlank @Size(max = 120) String name,
        @NotNull @PositiveOrZero BigDecimal price
) {}
```

`product/ProductResponse.java`

```java
package com.example.catalog.product;

import java.math.BigDecimal;

public record ProductResponse(Long id, String name, BigDecimal price) {}
```

## 50.3 Repository

`product/ProductRepository.java`

```java
package com.example.catalog.product;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductRepository extends JpaRepository<Product, Long> {}
```

## 50.4 Not-found exception

`product/ProductNotFoundException.java`

```java
package com.example.catalog.product;

public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(Long id) {
        super("Product not found: " + id);
    }
}
```

## 50.5 Service

`product/ProductService.java`

```java
package com.example.catalog.product;

import java.util.List;

import org.springframework.data.domain.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public Page<ProductResponse> list(Pageable pageable) {
        return repository.findAll(pageable).map(this::toResponse);
    }

    @Transactional(readOnly = true)
    public ProductResponse get(Long id) {
        return toResponse(findEntity(id));
    }

    @Transactional
    public ProductResponse create(ProductRequest request) {
        Product saved = repository.save(new Product(request.name(), request.price()));
        return toResponse(saved);
    }

    @Transactional
    public ProductResponse update(Long id, ProductRequest request) {
        Product product = findEntity(id);
        product.update(request.name(), request.price());
        return toResponse(product);
    }

    @Transactional
    public void delete(Long id) {
        Product product = findEntity(id);
        repository.delete(product);
    }

    private Product findEntity(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException(id));
    }

    private ProductResponse toResponse(Product product) {
        return new ProductResponse(product.getId(), product.getName(), product.getPrice());
    }
}
```

The unused `List` import may be removed by your IDE; it is not required by this service.

## 50.6 Controller

`product/ProductController.java`

```java
package com.example.catalog.product;

import jakarta.validation.Valid;
import org.springframework.data.domain.*;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public Page<ProductResponse> list(
            @PageableDefault(size = 20, sort = "name") Pageable pageable) {
        return service.list(pageable);
    }

    @GetMapping("/{id}")
    public ProductResponse get(@PathVariable Long id) {
        return service.get(id);
    }

    @PostMapping
    public ResponseEntity<ProductResponse> create(
            @Valid @RequestBody ProductRequest request) {
        ProductResponse created = service.create(request);
        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
                .path("/{id}")
                .buildAndExpand(created.id())
                .toUri();
        return ResponseEntity.created(location).body(created);
    }

    @PutMapping("/{id}")
    public ProductResponse update(
            @PathVariable Long id,
            @Valid @RequestBody ProductRequest request) {
        return service.update(id, request);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

## 50.7 Local configuration

For a local PostgreSQL database, configure `spring.datasource.url`, username and password using environment variables. Set `spring.jpa.hibernate.ddl-auto=update` only for a disposable learning database if you need Hibernate to create the table for the first run. For a production-like workflow, use Flyway or Liquibase migrations and `validate`.

## 50.8 Try the API

Create:

```bash
curl -X POST http://localhost:8080/api/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Keyboard","price":1499.00}'
```

Read:

```bash
curl http://localhost:8080/api/products
curl http://localhost:8080/api/products/1
```

Update:

```bash
curl -X PUT http://localhost:8080/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Mechanical Keyboard","price":2499.00}'
```

Delete:

```bash
curl -X DELETE http://localhost:8080/api/products/1
```

This is a learning example, not a complete production service. Add a suitable security policy, centralized error handling, database migrations, tests, and deployment configuration before exposing real data.

---

# 51. Common Spring Boot Annotations

## Application and configuration

- `@SpringBootApplication`
- `@Configuration`
- `@Bean`
- `@ConfigurationProperties`
- `@ConfigurationPropertiesScan`
- `@Import`
- `@Profile`
- `@ConditionalOnProperty` and other conditional annotations

## Dependency injection and components

- `@Component`
- `@Service`
- `@Repository`
- `@Controller`
- `@RestController`
- `@Autowired` (constructor injection is normally preferred)
- `@Qualifier`
- `@Primary`
- `@Value`
- `@Lazy`
- `@Scope`

## Web

- `@RequestMapping`
- `@GetMapping`, `@PostMapping`, `@PutMapping`, `@PatchMapping`, `@DeleteMapping`
- `@PathVariable`
- `@RequestParam`
- `@RequestBody`
- `@RequestPart`
- `@RequestHeader`
- `@ResponseStatus`
- `@RestControllerAdvice`
- `@ExceptionHandler`
- `@CrossOrigin`

## Validation

- `@Valid`
- `@Validated`
- `@NotNull`
- `@NotBlank`
- `@NotEmpty`
- `@Size`
- `@Email`
- `@Pattern`
- `@Positive`, `@PositiveOrZero`
- `@Min`, `@Max`

## Persistence and transactions

- `@Entity`
- `@Table`
- `@Id`
- `@GeneratedValue`
- `@Column`
- `@Enumerated`
- Relationship annotations (`@ManyToOne`, `@OneToMany`, and others)
- `@Query`
- `@Param`
- `@Transactional`
- `@Version`
- `@CreatedDate`, `@LastModifiedDate` when auditing is configured

## Security, caching, and scheduling

- `@EnableWebSecurity`
- `@EnableMethodSecurity`
- `@PreAuthorize`
- `@PostAuthorize`
- `@EnableCaching`
- `@Cacheable`
- `@CachePut`
- `@CacheEvict`
- `@EnableScheduling`
- `@Scheduled`
- `@EnableAsync`
- `@Async`

## Testing

- `@SpringBootTest`
- `@Test`
- `@BeforeEach`
- `@AfterEach`
- Test-slice annotations supported by the chosen Boot version
- `@Mock` / `@InjectMocks` when using Mockito directly
- `@ActiveProfiles`
- `@TestConfiguration`

Annotations work only when the relevant framework features/dependencies are available and configured. Check official docs for exact version-specific behavior.

---

# 52. Common Java and Spring Methods

## Frequently used Java methods

| Type | Methods / patterns |
|---|---|
| `String` | `length`, `isBlank`, `contains`, `substring`, `replace`, `split`, `strip`, `equals` |
| `List` | `add`, `get`, `set`, `remove`, `contains`, `size`, `isEmpty`, `sort` |
| `Set` | `add`, `remove`, `contains`, `size` |
| `Map` | `put`, `get`, `getOrDefault`, `containsKey`, `computeIfAbsent`, `merge`, `entrySet` |
| `Optional` | `map`, `flatMap`, `filter`, `orElse`, `orElseGet`, `orElseThrow`, `ifPresent` |
| `Stream` | `filter`, `map`, `flatMap`, `sorted`, `distinct`, `collect`, `toList`, `reduce`, `count` |
| `Files` | `readString`, `writeString`, `readAllLines`, `copy`, `move`, `deleteIfExists`, `exists` |
| `Objects` | `requireNonNull`, `equals`, `hash`, `toString` |
| `Collections` | `sort`, `reverse`, `unmodifiableList`, `frequency`, `emptyList` |
| `Arrays` | `sort`, `toString`, `equals`, `copyOf`, `stream` |

## Common Spring API patterns

| API | Typical role |
|---|---|
| `SpringApplication.run(...)` | Starts the app |
| `repository.save(...)` | Insert/update entity |
| `repository.findById(...)` | Look up entity by ID |
| `repository.findAll(...)` | Query entities |
| `repository.delete(...)` | Delete entity |
| `ResponseEntity.ok(...)` | Build HTTP 200 response |
| `ResponseEntity.created(...)` | Build HTTP 201 response |
| `ResponseEntity.noContent()` | Build HTTP 204 response |
| `PageRequest.of(...)` | Create pagination request |
| `Sort.by(...)` | Define sorting |
| `PasswordEncoder.encode(...)` | Hash a password |
| `PasswordEncoder.matches(...)` | Compare raw password with stored hash |
| `RestClient.get()/post()` | Build HTTP client request |
| `ApplicationRunner.run(...)` | Startup callback |

This is a practical shortlist, not an exhaustive listing of every method in the Java or Spring class libraries.

---

# 53. Full-Stack Learning Roadmap

Learn in this sequence:

1. **Java basics:** types, control flow, methods, classes, collections, exceptions.
2. **Modern Java:** generics, records, lambdas, streams, `Optional`, `java.time`.
3. **Build tooling:** Maven, dependencies, tests, Git.
4. **Spring Core:** IoC, beans, constructor injection, configuration.
5. **Spring Boot:** startup, properties, profiles, auto-configuration.
6. **REST APIs:** controllers, HTTP methods, DTOs, status codes.
7. **Validation and errors:** Bean Validation, centralized handlers.
8. **Databases:** SQL, PostgreSQL/MySQL, JPA, repositories, transactions.
9. **Security:** authentication, authorization, password hashing, CORS/CSRF.
10. **Testing:** JUnit, mocks, MVC tests, integration tests.
11. **Production readiness:** logging, Actuator, metrics, migrations, Docker.
12. **Advanced systems:** caching, async work, messaging, reactive stack, microservices where justified.

For React or Angular frontend integration, learn JSON, HTTP status codes, CORS, API error handling, authentication flows, pagination, and environment-specific API URLs.

---

# 54. Practice Projects

Build these progressively:

1. **CLI student manager:** Java classes, lists, methods, validation.
2. **Task REST API:** CRUD endpoints and DTOs.
3. **Product catalog:** JPA, PostgreSQL, pagination, sorting.
4. **User registration API:** validation, safe password hashing, login/session or token-based auth.
5. **Expense tracker:** transactions, filtering, date ranges, reports.
6. **Anime catalog API:** shows, seasons, episodes, categories, search and pagination.
7. **File metadata service:** upload controls, external file storage, authorization.
8. **Realtime discussion service:** WebSocket updates, access control, message persistence.
9. **Full-stack dashboard:** React/Angular + Spring Boot + SQL database.
10. **Deployment-ready service:** migrations, Docker, CI, tests, health checks, structured logs, metrics.

For every project, include input validation, secure configuration, tests, error handling, README setup steps, and realistic sample data.

---

# 55. Quick Syntax Reference

```java
// Variable
int count = 1;
final String name = "Spring";
var inferred = "Java";

// Condition
if (count > 0) { } else { }

// Loop
for (int i = 0; i < 10; i++) { }
for (String item : items) { }

// Method
public int add(int a, int b) {
    return a + b;
}

// Lambda
Predicate<String> valid = value -> !value.isBlank();

// Stream
List<String> results = names.stream()
        .filter(valid)
        .map(String::toUpperCase)
        .toList();

// Optional
String value = optionalValue.orElse("fallback");

// Class
public class Example {
    private final String name;

    public Example(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }
}

// Record
public record UserDto(Long id, String name) {}

// Spring Boot entry
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// Controller
@RestController
@RequestMapping("/api/items")
class ItemController {
    @GetMapping("/{id}")
    public Map<String, Object> get(@PathVariable Long id) {
        return Map.of("id", id);
    }
}

// Service
@Service
class ItemService {
    private final ItemRepository repository;

    ItemService(ItemRepository repository) {
        this.repository = repository;
    }
}

// Repository
interface ItemRepository extends JpaRepository<Item, Long> {}

// Transaction
@Transactional
public void performBusinessOperation() {
    // multiple database operations
}
```

---

# 56. Official Documentation

Use documentation that matches the exact version of your project.

- [Spring Boot project page](https://spring.io/projects/spring-boot)
- [Spring Boot Reference Documentation](https://docs.spring.io/spring-boot/reference/)
- [Spring Boot System Requirements](https://docs.spring.io/spring-boot/system-requirements.html)
- [Spring Boot Web documentation](https://docs.spring.io/spring-boot/reference/web/)
- [Spring Boot SQL / JPA documentation](https://docs.spring.io/spring-boot/reference/data/sql.html)
- [Spring Boot Security documentation](https://docs.spring.io/spring-boot/reference/web/spring-security.html)
- [Spring Boot Testing documentation](https://docs.spring.io/spring-boot/reference/testing/)
- [Spring Boot Actuator documentation](https://docs.spring.io/spring-boot/reference/actuator/)
- [Spring Framework Reference](https://docs.spring.io/spring-framework/reference/)
- [Spring Data JPA Reference](https://docs.spring.io/spring-data/jpa/reference/)
- [Spring Security Reference](https://docs.spring.io/spring-security/reference/)
- [Java Documentation](https://docs.oracle.com/en/java/)
- [Java Language Specification](https://docs.oracle.com/javase/specs/)
- [Maven Documentation](https://maven.apache.org/guides/)
- [Spring Initializr](https://start.spring.io/)

---

## Final Note

Use this file as a roadmap and a reference, not as a substitute for running the examples. Java and Spring Boot expose many more APIs than can reasonably fit into one Markdown guide. Some examples intentionally show the important shape of an integration and need application-specific configuration, imports, tests, or dependencies before they can run unchanged. Always check the current official documentation for version-specific API changes and test security-sensitive behavior before deployment.
