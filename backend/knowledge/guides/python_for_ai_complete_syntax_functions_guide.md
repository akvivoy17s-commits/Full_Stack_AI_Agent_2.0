# Python for AI: Complete Syntax, Functions, Machine Learning, Deep Learning, and LLM Guide
## A Practical Reference for AI Engineering and Full-Stack AI Development

> **Purpose:** Learn Python from fundamentals through the main workflows used in artificial intelligence: data preparation, machine learning, deep learning, natural-language processing, large language models, retrieval-augmented generation (RAG), model evaluation, and serving AI through APIs.
>
> **Scope note:** Python and its AI ecosystem contain thousands of functions, classes, operators, models, and APIs that evolve independently. There is no honest finite list of “100% of every Python/AI function,” and no single guide can cover every current and future library API. This file covers the core Python language and the main concepts/APIs used in common AI engineering workflows. Use the official versioned documentation linked at the end for the exact function signatures of the packages you install.
>
> **Version note:** Python examples use modern Python 3 syntax (generally suitable for Python 3.10+ unless a newer feature is marked). AI libraries have independent release cycles, so install compatible versions and verify any version-specific changes in their official documentation.

---

## Table of Contents

### Part I — Python Language
1. Setup, Interpreter, and Virtual Environments
2. Comments, Indentation, and Statements
3. Variables and Naming
4. Built-in Data Types
5. Strings and Formatting
6. Numbers and Numeric Operations
7. Operators and Expressions
8. Conditions and Pattern Matching
9. Loops and Iteration
10. Collections: Lists, Tuples, Sets, Dictionaries
11. Comprehensions
12. Functions and Parameters
13. Scope, Closures, and Functional Tools
14. Object-Oriented Python
15. Dataclasses, Enums, and Properties
16. Iterators and Generators
17. Exceptions and Error Handling
18. Files, Paths, JSON, CSV, and Pickle
19. Modules, Packages, Imports, and `__main__`
20. Type Hints and Static Checking
21. Decorators and Context Managers
22. Regular Expressions and Common Standard-Library Modules
23. Async Python, Threads, and Processes
24. Testing, Debugging, Logging, and Code Quality

### Part II — Python for Data and AI
25. AI, Machine Learning, and Deep Learning Overview
26. Environment and Dependency Management for AI
27. NumPy Arrays and Vectorized Operations
28. NumPy Indexing, Broadcasting, Linear Algebra, and Randomness
29. pandas Series and DataFrames
30. Data Cleaning and Feature Engineering
31. Data Visualization
32. Math and Statistics for AI
33. Machine Learning with scikit-learn
34. Data Splitting, Preprocessing, and Pipelines
35. Regression, Classification, and Clustering
36. Metrics, Validation, and Hyperparameter Search
37. PyTorch Tensors and Autograd
38. Building Neural Networks with PyTorch
39. Datasets, DataLoaders, Training, and Checkpoints
40. TensorFlow and Keras
41. NLP and Text Processing
42. Hugging Face Transformers
43. Tokenization, Embeddings, and Semantic Search
44. LLM Inference and Prompting
45. RAG: Retrieval-Augmented Generation
46. AI Agent and Tool-Calling Basics
47. Image and Computer Vision
48. Audio and Speech
49. Model Evaluation, Safety, Privacy, and Responsible AI
50. Serving AI with FastAPI
51. Persistence, Model Files, and Reproducibility
52. GPU, CPU, Memory, and Performance
53. Experiment Tracking and MLOps
54. Complete Mini Projects
55. Python Built-in Functions Quick Reference
56. Common NumPy / pandas / ML / Deep Learning API Reference
57. AI Development Roadmap
58. Official Documentation

---

# PART I — PYTHON LANGUAGE

# 1. Setup, Interpreter, and Virtual Environments

Check the installed Python version:

```bash
python --version
python -V
```

Depending on the system, the command can be `python3`.

Run a script:

```bash
python app.py
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**
```bat
.venv\Scripts\activate.bat
```

**macOS/Linux**
```bash
source .venv/bin/activate
```

Upgrade pip and install packages:

```bash
python -m pip install --upgrade pip
python -m pip install numpy pandas scikit-learn matplotlib
```

Deactivate:

```bash
deactivate
```

Use a separate virtual environment per project so dependencies do not conflict. Keep a tested dependency lock or requirements file for reproducibility.

---

# 2. Comments, Indentation, and Statements

Python uses indentation to define blocks.

```python
if True:
    print("Inside the block")
    print("Same indentation level")

print("Outside the block")
```

Comments:

```python
# Single-line comment

"""
This is a string literal often used as a
module, class, or function docstring.
It is not technically a comment.
"""
```

Line continuation is normally clearest inside parentheses, brackets, or braces:

```python
total = (
    first_value
    + second_value
    + third_value
)
```

Use spaces consistently (commonly four spaces per indentation level). Python is case-sensitive: `model`, `Model`, and `MODEL` are different names.

---

# 3. Variables and Naming

Python names refer to objects; variables do not need a separate declaration statement.

```python
name = "Asha"
age = 21
learning_ai = True
score = 98.5
```

Multiple assignment:

```python
x, y = 10, 20
x, y = y, x  # Swap
a = b = 0    # Both names refer to the same assigned object
```

Naming conventions:
- `snake_case` for variables and functions: `training_data`
- `PascalCase` for classes: `ImageClassifier`
- `UPPER_SNAKE_CASE` for module-level constants by convention: `MAX_TOKENS`
- A leading underscore often signals internal/private-by-convention names: `_helper`

Python does not enforce constant variables:

```python
LEARNING_RATE = 0.001  # Convention, not immutable
```

Useful introspection:

```python
value = 42
print(type(value))
print(id(value))  # Identity, useful mostly for diagnostics
print(repr(value))
```

Avoid naming variables after built-ins such as `list`, `str`, `id`, or `sum`, because doing so shadows those names.

---

# 4. Built-in Data Types

Main built-in types include:

| Type | Example |
|---|---|
| `int` | `42` |
| `float` | `3.14` |
| `complex` | `2 + 3j` |
| `bool` | `True` |
| `str` | `"Python"` |
| `list` | `[1, 2, 3]` |
| `tuple` | `(1, 2, 3)` |
| `range` | `range(10)` |
| `dict` | `{"name": "Asha"}` |
| `set` | `{1, 2, 3}` |
| `frozenset` | `frozenset({1, 2})` |
| `bytes` | `b"abc"` |
| `bytearray` | `bytearray(b"abc")` |
| `NoneType` | `None` |

Type conversion:

```python
int("42")
float("3.14")
str(100)
list("cat")             # ['c', 'a', 't']
tuple([1, 2])
set([1, 1, 2])          # {1, 2}
bool(0)                 # False
```

Python truthiness:
- False-like values include `False`, `None`, numeric zero, empty strings, and empty built-in collections.
- Non-empty strings and collections are normally truthy.

```python
if not records:
    print("No records")
```

Check identity with `is` only when identity is intended (especially `x is None`); use `==` for value equality.

---

# 5. Strings and Formatting

```python
text = "Python for AI"
text[0]        # 'P'
text[-1]       # 'I'
text[0:6]      # 'Python'
text.lower()
text.upper()
text.title()
text.strip()
text.replace("AI", "Data Science")
text.startswith("Python")
text.endswith("AI")
text.find("for")
text.count("o")
text.split()
" ".join(["Python", "for", "AI"])
```

Strings are immutable; string operations return new strings.

## f-strings

```python
name = "Asha"
accuracy = 0.93251

message = f"Hello, {name}"
formatted = f"Accuracy: {accuracy:.2%}"  # 93.25%
```

Other formatting:

```python
"Name: {}, score: {:.2f}".format(name, accuracy)
"%s: %d" % ("samples", 12)  # Legacy style; modern code usually prefers f-strings
```

Raw strings are useful for regular expressions and Windows paths:

```python
pattern = r"\d{4}-\d{2}-\d{2}"
path = r"C:\data\train.csv"
```

Unicode matters in NLP. A visible character can comprise multiple code points, and string length is not always the same as the number of user-perceived characters.

---

# 6. Numbers and Numeric Operations

```python
a = 10
b = 3

a + b   # 13
a - b   # 7
a * b   # 30
a / b   # 3.333...
a // b  # 3, floor division
a % b   # 1, remainder
a ** b  # 1000
```

Numeric helpers:

```python
abs(-5)
round(3.14159, 2)
divmod(10, 3)  # (3, 1)
pow(2, 5)      # 32
sum([1, 2, 3])
min([4, 1, 9])
max([4, 1, 9])
```

For precise decimal arithmetic, use `decimal.Decimal` where appropriate:

```python
from decimal import Decimal

price = Decimal("19.99")
tax = Decimal("0.18")
total = price * (Decimal("1") + tax)
```

Avoid constructing `Decimal` from a binary float when decimal accuracy matters; pass a string or integer.

---

# 7. Operators and Expressions

Arithmetic operators: `+`, `-`, `*`, `/`, `//`, `%`, `**`.

Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`.

Logical: `and`, `or`, `not`.

Membership: `in`, `not in`.

Identity: `is`, `is not`.

Bitwise: `&`, `|`, `^`, `~`, `<<`, `>>`.

Assignment:
```python
count = 0
count += 1
count -= 1
count *= 2
count /= 2
count //= 2
count %= 3
count **= 2
```

Assignment expression (`:=`):

```python
if (length := len("python")) > 3:
    print(length)
```

Use assignment expressions only when they improve clarity.

Ternary-style conditional expression:

```python
label = "large" if score >= 80 else "small"
```

Chained comparisons:

```python
if 0 <= probability <= 1:
    print("Valid probability")
```

---

# 8. Conditions and Pattern Matching

```python
if score >= 90:
    grade = "A"
elif score >= 75:
    grade = "B"
else:
    grade = "C"
```

`match` / `case` (Python 3.10+):

```python
match status_code:
    case 200:
        message = "OK"
    case 404:
        message = "Not found"
    case 400 | 422:
        message = "Invalid request"
    case _:
        message = "Other"
```

Structural pattern matching also supports sequence, mapping, class, and guarded patterns:

```python
match point:
    case (0, 0):
        location = "origin"
    case (x, y) if x == y:
        location = "diagonal"
    case (x, y):
        location = "other point"
```

---

# 9. Loops and Iteration

## `for`

```python
for item in ["a", "b", "c"]:
    print(item)
```

## `range`

```python
for i in range(5):       # 0 to 4
    print(i)

for i in range(2, 10, 2):
    print(i)
```

## `while`

```python
attempts = 0
while attempts < 3:
    attempts += 1
```

`break` exits the nearest loop, `continue` skips to the next iteration, and `pass` is a no-op placeholder.

Useful iteration tools:

```python
for index, value in enumerate(["a", "b"], start=1):
    print(index, value)

for name, score in zip(["Asha", "Ravi"], [90, 82]):
    print(name, score)

for key, value in {"a": 1, "b": 2}.items():
    print(key, value)
```

Also useful:
- `reversed(iterable)`
- `sorted(iterable)`
- `iter(iterable)`
- `next(iterator, default)`
- `any(iterable)`
- `all(iterable)`

---

# 10. Collections: Lists, Tuples, Sets, Dictionaries

## Lists

```python
values = [10, 20, 30]
values.append(40)
values.extend([50, 60])
values.insert(0, 5)
values.remove(20)
last = values.pop()
values.sort()
values.reverse()
copy_values = values.copy()
```

Indexing/slicing:

```python
values[0]
values[-1]
values[1:4]
values[:3]
values[::2]
values[::-1]
```

List methods include `append`, `extend`, `insert`, `remove`, `pop`, `clear`, `index`, `count`, `sort`, `reverse`, and `copy`.

## Tuples

```python
point = (3, 4)
x, y = point
single_item = (10,)
```

Tuples are immutable containers, but a tuple can contain mutable objects.

## Sets

```python
a = {1, 2, 3}
b = {3, 4, 5}

a.add(4)
a.discard(99)  # Does not raise if absent
a.remove(2)    # Raises KeyError if absent

a | b  # Union
a & b  # Intersection
a - b  # Difference
a ^ b  # Symmetric difference
```

## Dictionaries

```python
user = {"name": "Asha", "age": 22}
user["name"]
user.get("email", "unknown")
user["city"] = "Chennai"
user.update({"age": 23})
user.setdefault("role", "user")

for key in user:
    print(key)

for key, value in user.items():
    print(key, value)
```

Dictionary methods: `get`, `keys`, `values`, `items`, `update`, `pop`, `popitem`, `setdefault`, `clear`, and `copy`.

---

# 11. Comprehensions

List comprehension:

```python
squares = [x * x for x in range(10)]
even_squares = [x * x for x in range(10) if x % 2 == 0]
```

Set comprehension:

```python
lengths = {len(word) for word in ["AI", "Python", "ML"]}
```

Dictionary comprehension:

```python
square_by_number = {x: x * x for x in range(5)}
```

Generator expression:

```python
total = sum(x * x for x in range(1000))
```

Nested comprehensions are valid but can become hard to read. Prefer ordinary loops when the transformation has several steps or complex conditions.

---

# 12. Functions and Parameters

```python
def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b
```

Return `None` implicitly if no return statement is executed.

Default parameters:

```python
def greet(name: str, prefix: str = "Hello") -> str:
    return f"{prefix}, {name}"
```

Keyword arguments:

```python
greet(name="Asha", prefix="Welcome")
```

Avoid mutable default arguments:

```python
# Bad:
# def add_item(item, items=[]): ...

# Good:
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

Variable-length positional arguments:

```python
def total(*numbers: float) -> float:
    return sum(numbers)
```

Variable-length keyword arguments:

```python
def describe(**attributes):
    for key, value in attributes.items():
        print(key, value)
```

Keyword-only parameters:

```python
def train(model, *, epochs: int, learning_rate: float):
    ...
```

Positional-only parameters use `/` in function definitions:

```python
def divide(a, b, /):
    return a / b
```

Python functions support higher-order patterns, recursion, nested definitions, annotations, closures, generators, and async declarations.

---

# 13. Scope, Closures, and Functional Tools

Python name resolution is commonly described with LEGB:
- Local
- Enclosing
- Global
- Built-in

```python
count = 10

def show():
    local_value = 5
    print(local_value, count)
```

Use `global` or `nonlocal` only when necessary:

```python
def make_counter():
    count = 0

    def increment():
        nonlocal count
        count += 1
        return count

    return increment
```

Lambda:

```python
square = lambda x: x * x
```

Common helpers from `functools`:
- `partial`
- `reduce`
- `lru_cache`
- `cache` (where supported)
- `wraps`
- `singledispatch`

```python
from functools import lru_cache

@lru_cache(maxsize=256)
def expensive_calculation(n: int) -> int:
    return n * n
```

Cache only functions whose results are safe to reuse for the same arguments and whose external state does not invalidate the result.

---

# 14. Object-Oriented Python

```python
class ModelConfig:
    def __init__(self, model_name: str, max_tokens: int = 512):
        self.model_name = model_name
        self.max_tokens = max_tokens

    def describe(self) -> str:
        return f"{self.model_name}: {self.max_tokens}"

config = ModelConfig("demo-model")
print(config.describe())
```

Important concepts:
- `self`: reference to the instance by convention.
- `__init__`: initializer called during instance creation.
- Instance vs class attributes.
- Inheritance and method overriding.
- Composition and dependency injection.
- Public/protected/private naming conventions (Python does not enforce Java-style member access).
- `super()` to access inherited behavior.

Class method and static method:

```python
class Example:
    count = 0

    @classmethod
    def from_name(cls, name: str):
        instance = cls()
        instance.name = name
        return instance

    @staticmethod
    def normalize(text: str) -> str:
        return text.strip().lower()
```

Special methods (“dunder” methods) include `__init__`, `__repr__`, `__str__`, `__eq__`, `__lt__`, `__len__`, `__iter__`, `__next__`, `__enter__`, and `__exit__`.

---

# 15. Dataclasses, Enums, and Properties

Dataclasses reduce boilerplate:

```python
from dataclasses import dataclass

@dataclass
class TrainingConfig:
    model_name: str
    epochs: int = 10
    learning_rate: float = 0.001
```

Useful dataclass options include `frozen`, `order`, `slots`, `kw_only`, `repr`, `eq`, and `init` (check Python version support).

Enums:

```python
from enum import Enum

class TaskType(Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
```

Properties:

```python
class Temperature:
    def __init__(self, celsius: float):
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("Below absolute zero")
        self._celsius = value
```

---

# 16. Iterators and Generators

An iterator implements `__iter__()` and `__next__()`.

```python
iterator = iter([10, 20, 30])
next(iterator)
next(iterator)
```

Generator function:

```python
def batches(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]
```

Generator expressions:

```python
squares = (x * x for x in range(100))
```

Generators are useful for streaming large datasets without loading everything into memory. Deep learning data pipelines frequently rely on lazy iteration or dataset abstractions.

---

# 17. Exceptions and Error Handling

```python
try:
    value = int("123")
except ValueError as error:
    print(f"Invalid number: {error}")
else:
    print("Conversion succeeded")
finally:
    print("Cleanup")
```

Raise an exception:

```python
def validate_probability(value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError("Probability must be between zero and one")
```

Custom exception:

```python
class ModelLoadError(RuntimeError):
    pass
```

Best practices:
- Catch the specific exception you expect.
- Do not silently swallow failures.
- Preserve exception causes when re-raising.
- Do not expose credentials, access tokens, file paths, or sensitive payloads in error responses.
- Use exceptions for exceptional conditions, not routine branching.

---

# 18. Files, Paths, JSON, CSV, and Pickle

## Text files

```python
from pathlib import Path

path = Path("data.txt")
path.write_text("hello", encoding="utf-8")
text = path.read_text(encoding="utf-8")
```

## CSV

```python
import csv

with open("records.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["name", "score"])
    writer.writeheader()
    writer.writerow({"name": "Asha", "score": 90})
```

## JSON

```python
import json

data = {"name": "Asha", "active": True}
serialized = json.dumps(data, ensure_ascii=False)
restored = json.loads(serialized)
```

File JSON:

```python
with open("data.json", encoding="utf-8") as file:
    data = json.load(file)

with open("output.json", "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)
```

## Pickle caution

`pickle` can serialize Python objects, but **never unpickle untrusted files**: deserialization can execute code. For interchange use JSON, Parquet, formats designed for the model/library, or another constrained format as appropriate. Model checkpoint files also require provenance and trust checks.

---

# 19. Modules, Packages, Imports, and `__main__`

```python
import math
from pathlib import Path
import json as json_module
```

Common project structure:

```text
my_ai_project/
├── pyproject.toml
├── README.md
├── src/
│   └── my_ai_project/
│       ├── __init__.py
│       ├── data.py
│       ├── model.py
│       └── app.py
└── tests/
```

Entry point:

```python
def main() -> None:
    print("Application started")

if __name__ == "__main__":
    main()
```

The `__main__` guard prevents the script's main action from running when the module is imported.

Install a package:

```bash
python -m pip install package_name
```

Use project packaging and lock files appropriate to your team. Avoid ambiguous file names such as `json.py`, `typing.py`, `random.py`, or `torch.py` because they can shadow standard/third-party modules.

---

# 20. Type Hints and Static Checking

Type annotations help tools, editors, maintainers, and static analyzers. Python does not generally enforce them automatically at runtime.

```python
def normalize(values: list[float]) -> list[float]:
    minimum = min(values)
    maximum = max(values)
    if maximum == minimum:
        return [0.0 for _ in values]
    return [(value - minimum) / (maximum - minimum) for value in values]
```

Common type syntax:

```python
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence
from collections.abc import Awaitable
```

- `list[str]`
- `dict[str, float]`
- `tuple[int, str]`
- `str | None` (modern union syntax)
- `Any`
- `Literal["train", "test"]`
- `TypedDict`
- `Protocol`
- `TypeVar`
- `Generic`
- `Callable[[int], str]`
- `Iterable[T]`, `Iterator[T]`, `Sequence[T]`, `Mapping[K, V]`

Type aliases:

```python
Vector = list[float]
```

Typed dictionary:

```python
from typing import TypedDict

class UserRecord(TypedDict):
    id: int
    name: str
```

Run a configured type checker (e.g., mypy or Pyright) in CI. Libraries may offer stubs or annotations with different completeness.

---

# 21. Decorators and Context Managers

Decorator:

```python
from functools import wraps
from time import perf_counter

def timed(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            print(f"Elapsed: {perf_counter() - start:.4f}s")
    return wrapper
```

```python
@timed
def calculate():
    return sum(range(100_000))
```

Context managers manage setup and cleanup:

```python
with open("data.txt", encoding="utf-8") as file:
    content = file.read()
```

Create one with a class implementing `__enter__` / `__exit__`, or with `contextlib.contextmanager`.

```python
from contextlib import contextmanager

@contextmanager
def managed_resource():
    print("Open")
    try:
        yield "resource"
    finally:
        print("Close")
```

In AI/data pipelines, context managers are useful for files, temporary directories, database connections, and controlled resources.

---

# 22. Regular Expressions and Common Standard-Library Modules

Regex basics:

```python
import re

pattern = re.compile(r"\b[A-Z][a-z]+\b")
matches = pattern.findall("Asha studies Python")
```

Useful regex functions:
- `re.compile`
- `re.search`
- `re.match`
- `re.fullmatch`
- `re.findall`
- `re.finditer`
- `re.sub`
- `re.split`
- `re.escape`

Common standard-library modules for AI/data work:
- `pathlib`, `os`, `sys`
- `json`, `csv`, `sqlite3`
- `datetime`, `time`, `zoneinfo`
- `math`, `statistics`, `decimal`
- `collections`, `itertools`, `functools`
- `logging`, `argparse`, `configparser`
- `re`, `string`, `textwrap`
- `hashlib`, `secrets`
- `concurrent.futures`, `threading`, `multiprocessing`
- `asyncio`, `subprocess`
- `unittest`, `unittest.mock`, `doctest`
- `tempfile`, `shutil`, `glob`
- `dataclasses`, `enum`, `typing`
- `urllib`, `http`, `email`

The standard library is broad. The official library reference is the authoritative inventory.

---

# 23. Async Python, Threads, and Processes

Asynchronous I/O:

```python
import asyncio

async def fetch_data():
    await asyncio.sleep(0.1)
    return {"status": "ok"}

async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

- `async def` defines a coroutine function.
- `await` suspends a coroutine until an awaitable completes.
- `asyncio.gather` can await multiple tasks; error/cancellation behavior depends on the call and version.
- Use async libraries for the I/O operations being awaited; blocking calls still block the event loop.

Threads are often useful for concurrent I/O. Processes are often useful for CPU-bound Python code when process overhead is justified. Numerical/AI libraries may use their own native thread pools or GPU work, so benchmark the combined configuration.

---

# 24. Testing, Debugging, Logging, and Code Quality

Simple test:

```python
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
```

Standard library `unittest`:

```python
import unittest

class AddTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

if __name__ == "__main__":
    unittest.main()
```

Logging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting model training")
logger.exception("Operation failed")
```

Common tools:
- `pytest` for testing
- `ruff` for linting/formatting workflows
- `mypy` or `pyright` for static type checks
- `coverage` for coverage reporting
- `debugpy` or IDE debugger for step-through debugging

Never log passwords, API keys, authorization headers, or sensitive training samples.

---

# PART II — PYTHON FOR DATA AND AI

# 25. AI, Machine Learning, and Deep Learning Overview

Artificial intelligence (AI) is the broad field. Machine learning (ML) trains systems from data. Deep learning uses neural networks with multiple learned layers. Generative AI includes systems that generate text, images, audio, code, and other content.

Common workflow:

```text
Problem definition
    ↓
Collect / label data
    ↓
Explore and clean data
    ↓
Split data correctly
    ↓
Build baseline
    ↓
Train model
    ↓
Validate / tune
    ↓
Evaluate on held-out test data
    ↓
Package model
    ↓
Serve model behind an API
    ↓
Monitor quality, latency, drift, and errors
```

AI is not a single library. A typical ecosystem includes:
- NumPy: arrays and numerical computation
- pandas: tabular data manipulation
- Matplotlib/Seaborn: visualization
- scikit-learn: classic machine learning
- PyTorch or TensorFlow/Keras: deep learning
- Hugging Face Transformers: pretrained transformer models
- Tokenizers/embedding libraries: text processing and vector representations
- FastAPI: model API serving
- Experiment and monitoring tools: reproducibility and operations

Choose the toolset based on the problem and hardware instead of installing every library into one environment.

---

# 26. Environment and Dependency Management for AI

Use a dedicated virtual environment:

```bash
python -m venv .venv
```

Activate it (see Chapter 1), then install only the packages your project needs.

Example starter data/ML environment:

```bash
python -m pip install numpy pandas matplotlib scikit-learn jupyter
```

For deep learning, select the correct PyTorch or TensorFlow build for your operating system and hardware using its official installation instructions. GPU support depends on hardware, drivers, runtime, and library build. Do not assume a package installed from a generic command automatically enables a supported GPU.

For transformers / NLP, typical package names include:

```bash
python -m pip install transformers datasets tokenizers
```

Some models require framework-specific dependencies, tokenizers, a trust decision, and additional packages. Review each model card and repository license before using weights.

Reproducible environments:
- Pin tested package versions.
- Keep a dependency lock or frozen environment file.
- Record Python and CUDA/runtime versions where relevant.
- Separate CPU and GPU environments if their dependency needs differ.
- Rebuild the environment in CI to check reproducibility.

---

# 27. NumPy Arrays and Vectorized Operations

NumPy provides the `ndarray` multidimensional array and numerical operations.

```python
import numpy as np

a = np.array([1, 2, 3])
matrix = np.array([[1, 2], [3, 4]])

print(a.shape)       # (3,)
print(matrix.shape)  # (2, 2)
print(matrix.ndim)   # 2
print(matrix.size)   # 4
print(matrix.dtype)
```

Array creation:

```python
np.zeros((2, 3))
np.ones((3, 3))
np.full((2, 2), 7)
np.empty((2, 2))
np.arange(0, 10, 2)
np.linspace(0, 1, 5)
np.eye(3)
np.zeros_like(matrix)
np.ones_like(matrix)
```

Vectorized arithmetic:

```python
x = np.array([1, 2, 3])
y = np.array([10, 20, 30])

x + y
x * y
x ** 2
np.sqrt(y)
np.exp(x)
np.log(y)
```

Vectorization applies operations over arrays without writing a Python loop for each element in many cases, improving speed and enabling native optimized kernels.

Do not assume all operations are in-place. `x + y` creates a result; `x += y` generally updates `x` where allowed.

---

# 28. NumPy Indexing, Broadcasting, Linear Algebra, and Randomness

## Indexing and slicing

```python
a = np.arange(12).reshape(3, 4)

a[0, 0]
a[1]
a[:, 1]
a[0:2, 1:3]
a[a > 5]
```

Boolean indexing selects elements matching a mask. Advanced indexing can return copies; basic slicing often returns views. Understand copy/view behavior when updating arrays.

## Reshape and transpose

```python
a.reshape(4, 3)
a.T
a.flatten()
a.ravel()
np.concatenate([a, a], axis=0)
np.stack([a, a], axis=0)
np.expand_dims(a, axis=0)
np.squeeze(a)
```

Shape compatibility is required. `reshape` normally needs the same total number of elements.

## Broadcasting

Broadcasting lets compatible shapes operate together:

```python
features = np.array([[1., 2.], [3., 4.], [5., 6.]])
offset = np.array([10., 20.])
features + offset
```

Leading dimensions can be broadcast when equal or one of the sizes is `1`. Incompatible shapes raise a broadcasting error.

## Aggregation and statistics

```python
a.sum()
a.mean()
a.std()
a.var()
a.min()
a.max()
a.argmax()
a.argmin()
np.median(a)
np.percentile(a, 90)
np.mean(a, axis=0)
```

`axis` determines which dimension is reduced. Confirm result shapes during ML preprocessing.

## Linear algebra

```python
A = np.array([[1., 2.], [3., 4.]])
b = np.array([5., 6.])

np.dot(A, b)
A @ b
np.linalg.norm(b)
np.linalg.solve(A, b)
np.linalg.det(A)
np.linalg.inv(A)  # Often avoid explicitly computing an inverse when a solve is possible
np.linalg.svd(A)
np.linalg.eig(A)
```

Functions have mathematical and numerical assumptions. For singular or ill-conditioned systems, interpret results carefully.

## Reproducible randomness

```python
rng = np.random.default_rng(seed=42)
rng.random(5)
rng.integers(0, 10, size=5)
rng.normal(loc=0, scale=1, size=(3, 2))
rng.choice([0, 1], size=10)
```

Use an explicit random generator/seed where reproducibility matters. Exact results can still depend on library versions, algorithms, hardware, and parallel execution.

---

# 29. pandas Series and DataFrames

pandas is widely used for tabular data. `Series` is a labeled 1D structure; `DataFrame` is a labeled 2D table.

```python
import pandas as pd

df = pd.DataFrame({
    "age": [20, 25, 30],
    "score": [80, 92, 88],
    "city": ["Chennai", "Madurai", "Chennai"],
})
```

Inspect:

```python
df.head()
df.tail()
df.sample(2)
df.shape
df.columns
df.dtypes
df.info()
df.describe()
df.isna().sum()
df.nunique()
```

Selection:

```python
df["age"]
df[["age", "score"]]
df.loc[0, "age"]    # Label-based
df.iloc[0, 0]       # Position-based
df.loc[df["age"] >= 25]
```

Create/change columns:

```python
df["passed"] = df["score"] >= 85
df["age_next_year"] = df["age"] + 1
df = df.rename(columns={"score": "exam_score"})
df = df.drop(columns=["city"])
```

Be mindful of view/copy semantics, alignment by index labels, and the evolving pandas API. Prefer explicit `.loc[...]` assignments and consult current warnings rather than ignoring them.

---

# 30. Data Cleaning and Feature Engineering

Read common data sources:

```python
df = pd.read_csv("data.csv")
df = pd.read_json("data.json")
df = pd.read_parquet("data.parquet")
```

Excel support may require an engine package:

```python
df = pd.read_excel("data.xlsx")
```

Missing values:

```python
df.isna().sum()
df.dropna()
df.fillna(0)
df["age"] = df["age"].fillna(df["age"].median())
```

Duplicate handling:

```python
df.duplicated().sum()
df = df.drop_duplicates()
```

Types and text cleanup:

```python
df["age"] = pd.to_numeric(df["age"], errors="coerce")
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
df["email"] = df["email"].astype("string").str.strip().str.lower()
```

Filtering and transformation:

```python
df = df[df["score"] >= 50].copy()
df["log_price"] = np.log1p(df["price"])
df["age_band"] = pd.cut(df["age"], bins=[0, 18, 35, 60, 120])
```

Avoid leakage:
- Fit preprocessing only on the training split.
- Do not let validation/test information influence imputation, scaling, feature selection, or target encoding.
- Avoid splitting randomly when time/order/group structure matters.
- Understand missingness and outliers instead of replacing them blindly.

---

# 31. Data Visualization

Matplotlib basics:

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 4))
plt.plot([1, 2, 3], [2, 4, 3], marker="o")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training Curve")
plt.tight_layout()
plt.show()
```

Other common plots:
- Histogram: `plt.hist(...)`
- Scatter: `plt.scatter(x, y)`
- Bar: `plt.bar(labels, values)`
- Box plot: `plt.boxplot(...)`
- Heatmap often uses a visualization library such as Seaborn or Matplotlib's `imshow`.

pandas plotting:

```python
df["score"].hist()
plt.show()
```

Visualize:
- Class balance
- Missingness
- Distributions and outliers
- Feature relationships
- Training/validation curves
- Prediction errors
- Calibration and threshold trade-offs

Charts should reflect sample sizes and uncertainty; a plot is not proof of causation.

---

# 32. Math and Statistics for AI

Common concepts:
- Scalars, vectors, matrices, tensors
- Dot products and matrix multiplication
- Norms and distances
- Mean, median, variance, standard deviation
- Probability, conditional probability, Bayes' rule
- Distributions, sampling, confidence intervals
- Derivatives, gradients, chain rule
- Loss functions and optimization
- Overfitting, bias/variance trade-off
- Regularization

Example computations:

```python
import numpy as np

values = np.array([1, 2, 3, 4, 5])
mean = values.mean()
variance = values.var()
std_dev = values.std()
```

A simplified linear model:

```python
prediction = weight * feature + bias
error = prediction - target
squared_error = error ** 2
```

These scalar examples show the shapes of calculations; real training requires coherent batches, losses, gradients, parameter updates, validation, and safeguards against numerical instability.

---

# 33. Machine Learning with scikit-learn

scikit-learn provides many classical ML algorithms and common preprocessing/evaluation tools.

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
```

Typical workflow:

```python
X = df[["age", "income"]]
y = df["purchased"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

predictions = model.predict(X_test)
print(accuracy_score(y_test, predictions))
print(classification_report(y_test, predictions))
```

`X` is usually a feature matrix and `y` is the target. The correct split options depend on classification balance, time series, group structure, and data size.

Main estimator API:
- `fit(X, y)`: learn model parameters
- `predict(X)`: produce predictions
- `predict_proba(X)`: class probabilities for compatible estimators
- `decision_function(X)`: decision scores for compatible estimators
- `transform(X)`: transform features for transformers
- `fit_transform(X)`: fit and transform in one step
- `score(X, y)`: estimator-specific score (check its definition)

---

# 34. Data Splitting, Preprocessing, and Pipelines

Common split patterns:
- Training set: fit models.
- Validation set / cross-validation folds: selection and tuning.
- Test set: final unbiased evaluation after decisions are complete.

Scaling:

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

Important: do not call `fit_transform` on the test set. Fit preprocessing on the training data, then transform validation/test data using the learned parameters.

Pipeline:

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

pipeline = make_pipeline(
    StandardScaler(),
    LogisticRegression(max_iter=1000)
)
pipeline.fit(X_train, y_train)
predictions = pipeline.predict(X_test)
```

For mixed numeric/categorical columns, use a `ColumnTransformer` and suitable imputers/encoders. For a full workflow, preprocessing should be fitted within cross-validation using an integrated `Pipeline`, not separately on all data.

---

# 35. Regression, Classification, and Clustering

## Regression

Predict a numeric target, such as price.

```python
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

Other choices include Ridge, Lasso, ElasticNet, tree models, random forests, gradient boosting, and support-vector regression.

Metrics:
- MAE
- MSE
- RMSE
- R²

## Classification

Predict a category, such as spam/not spam.

```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

Other algorithms include decision trees, random forests, gradient boosting, support vector machines, k-nearest neighbors, Naive Bayes, and neural networks.

Metrics:
- Accuracy
- Precision
- Recall
- F1 score
- ROC-AUC
- PR-AUC / average precision
- Confusion matrix
- Log loss and calibration metrics

Accuracy can be misleading on imbalanced data. Choose metrics that match the practical costs of false positives and false negatives.

## Clustering

```python
from sklearn.cluster import KMeans

clusterer = KMeans(n_clusters=3, random_state=42, n_init="auto")
labels = clusterer.fit_predict(X)
```

Other methods include DBSCAN, hierarchical clustering, and Gaussian mixture models. Cluster labels do not automatically have semantic meaning; validate stability and usefulness.

---

# 36. Metrics, Validation, and Hyperparameter Search

Common metrics:

```python
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
```

Cross-validation:

```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy")
print(scores.mean())
```

Grid search:

```python
from sklearn.model_selection import GridSearchCV

search = GridSearchCV(
    estimator=pipeline,
    param_grid={"logisticregression__C": [0.1, 1.0, 10.0]},
    cv=5,
    scoring="accuracy",
)
search.fit(X_train, y_train)
best_model = search.best_estimator_
```

The estimator parameter name in a pipeline depends on the pipeline's step names. Check `pipeline.get_params()`.

Avoid repeatedly using the test set for model selection. For time-series data use time-aware splitting. For grouped data, keep samples from the same entity in the same split when required to prevent leakage.

---

# 37. PyTorch Tensors and Autograd

PyTorch is a tensor/deep-learning library. Install the correct build according to the official selector for your operating system and hardware.

```python
import torch

x = torch.tensor([1.0, 2.0, 3.0])
zeros = torch.zeros((2, 3))
ones = torch.ones((2, 3))
random_values = torch.rand((2, 3))

x.shape
x.dtype
x.device
x.to("cpu")
```

Tensor operations:

```python
a = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
b = torch.tensor([[2.0, 0.0], [0.0, 2.0]])

a + b
a * b        # elementwise multiplication
a @ b        # matrix multiplication
a.mean()
a.sum()
a.reshape(4)
a.transpose(0, 1)
```

Device selection:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
```

This is a basic CUDA check; other devices/backends have separate support rules. Ensure model and tensors are on compatible devices.

Autograd:

```python
x = torch.tensor(2.0, requires_grad=True)
y = x ** 2 + 3 * x
y.backward()
print(x.grad)
```

Gradients accumulate in many training patterns; clear them appropriately before a new update.

---

# 38. Building Neural Networks with PyTorch

```python
import torch
from torch import nn

class SimpleClassifier(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_classes: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, num_classes),
        )

    def forward(self, x):
        return self.network(x)
```

Create model, loss, optimizer:

```python
model = SimpleClassifier(input_size=10, hidden_size=32, num_classes=2)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
```

Training-loop pattern:

```python
model.train()

for features, labels in train_loader:
    features = features.to(device)
    labels = labels.to(device)

    optimizer.zero_grad()
    logits = model(features)
    loss = loss_fn(logits, labels)
    loss.backward()
    optimizer.step()
```

Notes:
- `CrossEntropyLoss` for ordinary class-index classification targets normally expects raw logits rather than softmax probabilities.
- Targets and tensor shapes/dtypes must match the selected loss function.
- `model.train()` enables training behavior for layers such as dropout and batch normalization.
- Use `model.eval()` for evaluation/inference behavior.
- Use `torch.no_grad()` or appropriate inference mode during evaluation/inference to avoid recording gradients when not needed.
- Monitor validation metrics, checkpoint the best model, and handle reproducibility.

---

# 39. Datasets, DataLoaders, Training, and Checkpoints

Custom dataset:

```python
from torch.utils.data import Dataset, DataLoader

class ArrayDataset(Dataset):
    def __init__(self, features, labels):
        self.features = features
        self.labels = labels

    def __len__(self):
        return len(self.features)

    def __getitem__(self, index):
        return self.features[index], self.labels[index]

dataset = ArrayDataset(features_tensor, labels_tensor)
train_loader = DataLoader(dataset, batch_size=32, shuffle=True)
```

Saving state:

```python
torch.save(model.state_dict(), "model_state.pt")
```

Loading state:

```python
model = SimpleClassifier(input_size=10, hidden_size=32, num_classes=2)
state = torch.load("model_state.pt", map_location="cpu", weights_only=True)
model.load_state_dict(state)
model.eval()
```

Checkpoint behavior and `weights_only` availability/security semantics are library-version-specific; verify documentation for the installed PyTorch release. Treat unknown model/checkpoint files as untrusted. Save optimizer state and training metadata too when resume-training is required.

---

# 40. TensorFlow and Keras

TensorFlow and Keras provide another deep-learning ecosystem. Install using the official instructions for the operating system/hardware.

Simple Keras model:

```python
import keras
from keras import layers

model = keras.Sequential([
    layers.Input(shape=(10,)),
    layers.Dense(32, activation="relu"),
    layers.Dense(1),
])

model.compile(
    optimizer="adam",
    loss="mean_squared_error",
    metrics=["mae"],
)
```

Train and evaluate:

```python
history = model.fit(
    X_train,
    y_train,
    validation_split=0.2,
    epochs=20,
    batch_size=32,
)

metrics = model.evaluate(X_test, y_test)
predictions = model.predict(X_test)
```

Classification requires an output/loss setup appropriate for binary or multi-class tasks. Normalize/encode inputs correctly. Avoid using a test set as a repeatedly tuned validation set.

TensorFlow essentials:
- Tensors and shape/dtype
- `tf.data.Dataset`
- `tf.GradientTape`
- Keras layers, models, losses, optimizers, metrics
- Callbacks and checkpoints
- SavedModel / Keras model formats (format support may evolve)
- Device placement and distributed training APIs

Do not mix PyTorch and TensorFlow examples without being deliberate about conversion and framework boundaries.

---

# 41. NLP and Text Processing

Natural-language-processing tasks include classification, entity extraction, sentiment analysis, summarization, question answering, translation, semantic search, and text generation.

Basic preprocessing:

```python
text = "Python helps build AI applications."
words = text.lower().split()
```

This is only a simple baseline; real tokenization must handle punctuation, multilingual scripts, contractions, Unicode normalization, and the model's tokenizer conventions.

Common techniques:
- Unicode normalization
- Text cleaning where justified
- Tokenization
- Stop-word handling (task-dependent; often harmful in modern transformer workflows if done indiscriminately)
- Stemming and lemmatization
- Bag-of-words and TF-IDF
- N-grams
- Named-entity recognition
- Text embeddings
- Transformer tokenizers
- Padding, truncation, attention masks

scikit-learn text vectorizer example:

```python
from sklearn.feature_extraction.text import TfidfVectorizer

texts = [
    "I like machine learning",
    "Python is useful for data science",
    "I am learning AI",
]

vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
X_text = vectorizer.fit_transform(texts)
```

Fit text vectorizers on training data only when evaluating predictive performance, then apply the fitted vectorizer to validation/test data.

---

# 42. Hugging Face Transformers

The Transformers library provides pretrained model architectures, tokenizers, pipelines, trainers, and integration with supported deep-learning backends. Model support and APIs vary by library/model release.

A high-level inference pattern:

```python
from transformers import pipeline

classifier = pipeline("sentiment-analysis")
result = classifier("The documentation was clear and helpful.")
print(result)
```

This first use may download model files. Read the model card, check license and supported tasks, and understand the memory/compute requirement before loading a large model.

Text generation pattern (model and task must be supported by the chosen checkpoint):

```python
from transformers import pipeline

generator = pipeline("text-generation", model="gpt2")
outputs = generator(
    "Artificial intelligence can",
    max_new_tokens=40,
    do_sample=True,
)
```

Common concepts:
- Model checkpoint
- Tokenizer
- `AutoTokenizer`
- `AutoModel`
- `AutoModelForSequenceClassification`
- `AutoModelForCausalLM`
- `pipeline`
- `generate`
- Attention mask
- Padding and truncation
- Model config
- Training/inference mode
- Device and dtype
- Hub cache and offline mode

The exact supported classes depend on the checkpoint architecture. Don't assume one `AutoModel...` class supports every model/task.

---

# 43. Tokenization, Embeddings, and Semantic Search

An embedding maps an item (often text, image, or audio) into a vector space. Similarity search retrieves vectors that are close under a chosen metric, such as cosine similarity or dot product.

Generic embedding workflow:
1. Clean/normalize input consistently with the model.
2. Use the embedding model's tokenizer/processor.
3. Run inference.
4. Store the returned vector along with the original ID and metadata.
5. Normalize vectors if required by the selected similarity method.
6. Search using a vector index/database.
7. Retrieve the associated content and apply authorization filters.

Cosine similarity concept:

```python
import numpy as np

def cosine_similarity(a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
```

For large datasets, use a vector database or nearest-neighbor index rather than comparing a query against every vector in Python. Index libraries differ in exact search guarantees, distance metrics, filtering, persistence, and deployment requirements.

Keep chunk IDs, source metadata, access-control labels, model version, and content hashes where they matter to retrieval quality and security.

---

# 44. LLM Inference and Prompting

An LLM workflow usually includes:
- Choosing a model suitable for the task and deployment.
- Formatting system/developer/user instructions using the model's expected format.
- Managing the context window.
- Calling inference using a local runtime or provider API.
- Handling latency, errors, retries, rate limits, and token usage.
- Validating output shape and content.
- Evaluating task quality against representative examples.

Example using a provider SDK is provider-specific. For an OpenAI API client, current examples use the official Python SDK and the Responses API; consult current documentation to match the installed SDK version:

```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

response = client.responses.create(
    model=os.environ["OPENAI_MODEL"],
    input="Explain a database index in three sentences.",
)

print(response.output_text)
```

Set `OPENAI_API_KEY` and `OPENAI_MODEL` in your environment. Do not commit secrets. Model names and endpoint options change; use the current provider docs for exact parameters, structured outputs, streaming, tools, and error handling.

For a local model, use that runtime's documented HTTP/API interface. Keep provider-specific code behind a small adapter so the rest of your application is not tied to one provider.

Prompt practices:
- State the task and relevant context clearly.
- Specify output schema when your application needs structured output.
- Distinguish untrusted quoted/user-supplied text from instructions.
- Limit input and output tokens based on the task.
- Evaluate prompts with a fixed test set instead of judging by one demonstration.
- Never treat model output as inherently trusted executable code or SQL.

---

# 45. RAG: Retrieval-Augmented Generation

RAG combines retrieval from an external knowledge source with an LLM response.

Pipeline:

```text
Documents
  ↓
Parse / normalize
  ↓
Split into chunks
  ↓
Embed chunks
  ↓
Store vectors + metadata
  ↓
User query → query embedding
  ↓
Retrieve relevant chunks (+ ACL filters)
  ↓
Build context with source references
  ↓
LLM generates response
  ↓
Validate / cite / return
```

Important decisions:
- Chunk size and overlap
- Source metadata and document identifiers
- Embedding model and dimensionality
- Similarity metric
- Vector index and database
- Keyword + vector hybrid retrieval
- Reranking
- Context budget
- Source citations
- Access-control filtering
- Freshness and deletion propagation
- Prompt-injection handling for retrieved documents
- Retrieval and answer evaluation separately

Pseudocode:

```python
def answer_question(question: str) -> str:
    query_vector = embed(question)
    passages = vector_store.search(
        vector=query_vector,
        top_k=5,
        filters={"is_public": True},
    )
    context = "\n\n".join(passage.text for passage in passages)
    prompt = build_prompt(question=question, context=context)
    return llm.generate(prompt)
```

`embed`, `vector_store.search`, `build_prompt`, and `llm.generate` are placeholders representing your chosen packages/services, not built-in Python functions. Implement authorization and filtering before returning retrieved private data to the model.

---

# 46. AI Agent and Tool-Calling Basics

An agent typically combines an LLM with tool descriptions, execution logic, state, and guardrails. The model may request a tool call, but application code must validate and execute it.

Common architecture:
1. Receive and authenticate request.
2. Build model input with policies and relevant context.
3. Get a model response.
4. If a tool call is requested, validate tool name and typed arguments.
5. Authorize the action and execute with a narrow permission boundary.
6. Return tool output to the model if the protocol requires it.
7. Limit total steps/time/cost.
8. Validate the final response and record safe logs.

Example schema concept:

```python
from typing import TypedDict

class SearchArgs(TypedDict):
    query: str
    limit: int
```

Never allow an LLM to execute arbitrary SQL, shell commands, file operations, or deployments directly without explicit validation, least privilege, isolation, confirmation for sensitive changes, and robust logging. Treat model output and retrieved document text as untrusted.

---

# 47. Image and Computer Vision

Core concepts:
- Images represented as arrays/tensors with channels, height, and width.
- Color spaces (RGB, grayscale, etc.).
- Normalization and resizing.
- Train/validation/test splits.
- Data augmentation.
- Classification, detection, segmentation, OCR, and vision-language models.
- Label quality, class imbalance, and domain shift.

OpenCV example (requires installation):

```python
import cv2

image = cv2.imread("image.jpg")
if image is None:
    raise FileNotFoundError("Could not load image.jpg")

resized = cv2.resize(image, (224, 224))
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
```

OpenCV commonly loads color images as BGR, not RGB. Conversion rules matter before passing images to models.

Using a pretrained image processor/model is framework and checkpoint-specific. Verify its expected resolution, color order, normalization, and output labels.

---

# 48. Audio and Speech

Common workflows:
- Load/resample audio
- Convert waveform to model-required format
- Speech recognition / transcription
- Text-to-speech generation
- Audio classification
- Speaker diarization (model-dependent)
- Noise reduction or separation
- Chunking long audio and aligning timestamps

Python libraries often used include `soundfile`, `librosa`, `torchaudio`, and transformer-based pipelines. Install compatible versions and check supported codecs/system libraries.

Important considerations:
- Sample rate and channel count
- Duration and file size
- Consent and privacy for recordings
- Language/accent variation
- Word error rate and task-specific evaluation
- Latency, streaming, and partial transcripts
- Secure storage/retention of audio data

Audio APIs and preprocessing depend on the chosen model; do not assume a model accepts arbitrary raw audio without a processor.

---

# 49. Model Evaluation, Safety, Privacy, and Responsible AI

Evaluation should be designed before deployment.

For traditional ML:
- Keep train/validation/test roles separate.
- Avoid data leakage.
- Evaluate on representative data.
- Analyze subgroup performance where appropriate.
- Check calibration and decision thresholds.
- Record the model, features, dataset, and code versions.

For LLMs:
- Build a representative set of tasks and difficult cases.
- Measure correctness, completeness, groundedness, refusal behavior where appropriate, tool-call accuracy, and latency/cost.
- Test prompt injection and untrusted inputs.
- Verify claims that require source evidence.
- Monitor regressions when models/prompts/retrievers change.

Privacy/security:
- Minimize collected data.
- Remove sensitive fields when not needed.
- Restrict model access to appropriate documents.
- Follow licenses and usage policies for datasets/models.
- Avoid logging secrets or private prompts by default.
- Protect backups, embeddings, indexes, and model artifacts.
- Set retention/deletion rules.
- Be transparent about generated outputs and known limitations.

A high benchmark score does not guarantee the model is safe or reliable in every real-world context.

---

# 50. Serving AI with FastAPI

Install FastAPI and an ASGI server according to their current documentation:

```bash
python -m pip install fastapi uvicorn
```

Minimal API:

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="AI Inference API")

class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)

class PredictResponse(BaseModel):
    label: str
    confidence: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    # Replace this placeholder with a loaded, evaluated model.
    return PredictResponse(label="example", confidence=0.75)
```

Run for local development:

```bash
uvicorn app:app --reload
```

Production considerations:
- Load expensive models once in application lifespan/startup handling.
- Avoid loading model weights for each request.
- Validate inputs and file size.
- Set request and inference timeouts.
- Add authentication/authorization and rate limiting.
- Limit concurrency based on memory/GPU budget.
- Avoid blocking async endpoints with long blocking work unless moved to an appropriate worker/thread/process.
- Monitor latency, errors, memory, GPU use, and model quality.
- Do not expose interactive development reload mode in production.

---

# 51. Persistence, Model Files, and Reproducibility

Common persistence formats:
- JSON for simple interoperable metadata.
- CSV / Parquet for tabular data.
- NumPy `.npy` / `.npz` for arrays.
- Framework-specific model/checkpoint formats.
- Database tables for metadata and job state.
- Object storage for larger files/model artifacts.

Record:
- Code revision
- Python/library versions
- Model identifier/version or artifact hash
- Training data version/checksum where permissible
- Random seeds and configuration
- Evaluation report
- Timestamp and environment/hardware details

Be cautious when loading serialized objects from untrusted sources. Python pickle-based serialization can execute code during deserialization. Check the official security guidance of your framework and prefer safer/limited-weight formats where available.

---

# 52. GPU, CPU, Memory, and Performance

Before optimizing, measure:
- Batch latency and throughput
- CPU/GPU utilization
- RAM/VRAM usage
- Data-loading bottlenecks
- Tokenization and preprocessing time
- Network/API latency
- Model initialization time
- Peak memory during training/inference

Helpful strategies:
- Use vectorized NumPy/pandas operations.
- Avoid duplicating full datasets in memory unnecessarily.
- Stream/chunk large input files.
- Batch inference when latency constraints permit.
- Use inference/no-gradient contexts where applicable.
- Use mixed precision only when supported and numerically suitable.
- Pin compatible framework/runtime versions.
- Profile before changing thread counts or concurrency.
- Use caching only when correctness/freshness allows it.

A GPU is not automatically faster for tiny tasks or workloads with heavy CPU/data-transfer overhead. Hardware support depends on the library build, drivers, runtime, and device.

---

# 53. Experiment Tracking and MLOps

MLOps brings machine-learning workflows into controlled production practice.

Concepts:
- Data and feature versioning
- Experiment configurations and metrics
- Model registry and approval
- Reproducible pipelines
- Automated tests
- Artifact storage
- Deployment and rollback
- Online monitoring and drift detection
- Scheduled/retraining workflows
- Audit and access controls

Libraries/services vary (for example, MLflow, experiment trackers, model registries, workflow schedulers, and container/orchestration platforms). Evaluate their current documentation and deployment compatibility rather than copying a one-size-fits-all setup.

Example configuration object:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TrainConfig:
    random_seed: int = 42
    batch_size: int = 32
    epochs: int = 10
    learning_rate: float = 1e-3
```

Save configuration with metrics and model artifacts, but do not include secrets.

---

# 54. Complete Mini Projects

Build progressively:

1. **Data exploration notebook:** CSV read, summary stats, missing values, distributions.
2. **Customer churn classifier:** train/test split, preprocessing pipeline, meaningful metrics.
3. **Price prediction model:** regression, residual analysis, baseline comparison.
4. **Image classifier:** pretrained model or small CNN, transforms, training/evaluation.
5. **Text classifier:** TF-IDF baseline versus a transformer.
6. **Semantic search:** embedding model + vector index + document metadata.
7. **RAG assistant:** retrieval, grounded responses, source references, evaluation set.
8. **AI REST service:** FastAPI request schemas, model loading, authentication, timeouts.
9. **AI coding helper:** tool schemas, restricted file scope, diff review, test execution with safeguards.
10. **Production-ready AI application:** reproducible environment, CI tests, monitoring, data privacy, safe rollout.

For each project, track metrics and test edge cases, invalid input, model failures, and resource limits.

---

# 55. Python Built-in Functions Quick Reference

Common built-ins useful for AI/data development:

| Function | Typical purpose |
|---|---|
| `abs(x)` | Absolute value |
| `all(iterable)` / `any(iterable)` | Boolean reductions |
| `bool(x)` | Boolean conversion |
| `dict(...)`, `list(...)`, `set(...)`, `tuple(...)` | Collection constructors |
| `bytes(...)`, `bytearray(...)` | Binary values |
| `enumerate(iterable)` | Indexed iteration |
| `filter(function, iterable)` | Filter iterator |
| `map(function, iterable)` | Transform iterator |
| `zip(*iterables)` | Pair elements |
| `iter(x)` / `next(it)` | Iterator operations |
| `len(x)` | Number of elements |
| `max(...)` / `min(...)` | Extremes |
| `sum(iterable)` | Sum |
| `sorted(iterable)` | Sorted list |
| `reversed(sequence)` | Reverse iterator |
| `range(...)` | Integer range |
| `round(x, ndigits)` | Round |
| `pow(a, b)` | Power |
| `divmod(a, b)` | Quotient and remainder |
| `isinstance(obj, type)` | Type check |
| `issubclass(cls, base)` | Inheritance check |
| `type(obj)` | Runtime type |
| `getattr`, `setattr`, `hasattr`, `delattr` | Attribute access |
| `callable(obj)` | Check callability |
| `repr(x)` / `str(x)` | Representations |
| `format(value, spec)` | Formatting |
| `print(...)` / `input(...)` | Console I/O |
| `open(...)` | File I/O |
| `help(x)` / `dir(x)` | Introspection |
| `id(x)` | Object identity |
| `hash(x)` | Hash value where supported |
| `ord(char)` / `chr(codepoint)` | Unicode conversion |
| `bin`, `oct`, `hex` | Integer representations |
| `ascii(x)` | Escaped representation |
| `compile`, `eval`, `exec` | Dynamic code facilities; dangerous with untrusted input |
| `globals`, `locals`, `vars` | Namespace/attribute inspection |
| `memoryview` | Memory view |
| `property`, `classmethod`, `staticmethod`, `super` | Class behavior |
| `object` | Root object type |
| `slice` | Slice object |
| `aiter`, `anext` | Async iteration (Python 3.10+) |
| `breakpoint()` | Debugger hook |

This list is not every built-in or every standard-library function. See the official built-ins reference.

---

# 56. Common NumPy / pandas / ML / Deep Learning API Reference

This section is an orientation list, not a guarantee that every API in each library is covered.

## NumPy
Array creation and shape: `array`, `asarray`, `zeros`, `ones`, `empty`, `full`, `arange`, `linspace`, `eye`, `reshape`, `ravel`, `flatten`, `transpose`, `concatenate`, `stack`, `expand_dims`, `squeeze`.

Math/statistics: `sum`, `mean`, `median`, `std`, `var`, `min`, `max`, `argmin`, `argmax`, `percentile`, `quantile`, `sqrt`, `exp`, `log`, `sin`, `cos`, `dot`, `matmul`, `linalg.norm`, `linalg.solve`, `linalg.svd`, `isnan`, `where`, `clip`, `unique`, `sort`, `argsort`.

Random: `default_rng`, generator methods `random`, `integers`, `normal`, `choice`, `permutation`, `shuffle`.

## pandas
Creation/loading: `DataFrame`, `Series`, `read_csv`, `read_json`, `read_parquet`, `read_excel`.

Inspection: `head`, `tail`, `sample`, `info`, `describe`, `value_counts`, `nunique`, `isna`, `duplicated`.

Transform: `loc`, `iloc`, `query`, `assign`, `rename`, `drop`, `dropna`, `fillna`, `astype`, `sort_values`, `sort_index`, `groupby`, `agg`, `transform`, `apply`, `map`, `merge`, `join`, `concat`, `pivot_table`, `melt`, `explode`, `to_datetime`, `to_numeric`, `rolling`, `resample`, `to_csv`, `to_parquet`.

## scikit-learn
Splitting/validation: `train_test_split`, cross-validation utilities, `cross_val_score`, `GridSearchCV`, `RandomizedSearchCV`.

Preprocessing: `StandardScaler`, `MinMaxScaler`, `RobustScaler`, `OneHotEncoder`, `OrdinalEncoder`, `SimpleImputer`, `ColumnTransformer`, `Pipeline`, `make_pipeline`.

Model families: `LinearRegression`, `Ridge`, `Lasso`, `LogisticRegression`, `DecisionTreeClassifier`, `RandomForestClassifier`, gradient boosting estimators, `SVC`, `KNeighborsClassifier`, `KMeans`, `DBSCAN`, `PCA`.

Metrics: `accuracy_score`, `precision_score`, `recall_score`, `f1_score`, `classification_report`, `confusion_matrix`, `roc_auc_score`, `mean_absolute_error`, `mean_squared_error`, `r2_score`.

## PyTorch
Tensors: `tensor`, `as_tensor`, `zeros`, `ones`, `rand`, `randn`, `arange`, `stack`, `cat`, `reshape`, `transpose`, `matmul`, `mean`, `sum`, `no_grad`.

Training: `nn.Module`, `nn.Linear`, activation/loss modules, `torch.optim.Adam`, `DataLoader`, `Dataset`, `state_dict`, `load_state_dict`, `save`, `load`, `autograd`.

## TensorFlow/Keras
Common APIs: `tf.constant`, tensor operations, `tf.data.Dataset`, `keras.Sequential`, `keras.Model`, `keras.layers.Dense`, convolution/recurrent/attention layers, `model.compile`, `model.fit`, `model.evaluate`, `model.predict`, callbacks, optimizers, losses, metrics, model save/load APIs. Exact serialization APIs and compatibility differ by version.

## Hugging Face Transformers
Common concepts/APIs: `pipeline`, `AutoTokenizer`, task-specific `AutoModel...` classes, tokenization outputs, attention masks, `generate`, model config, `Trainer` where suitable, `TrainingArguments` where supported. The supported model classes and argument names depend on the current library and checkpoint.

---

# 57. AI Development Roadmap

Suggested order:
1. Python syntax, built-ins, functions, modules, exceptions.
2. Collections, file I/O, type hints, testing, environments.
3. NumPy arrays, broadcasting, vectorization, linear algebra.
4. pandas data cleaning, feature engineering, data visualization.
5. Probability, statistics, vectors, matrices, derivatives.
6. scikit-learn preprocessing, baselines, evaluation, cross-validation.
7. PyTorch or TensorFlow/Keras fundamentals.
8. Train/validate neural models and save/load checkpoints.
9. Learn NLP, tokenization, embeddings, and transformers.
10. Build inference pipelines, RAG systems, and controlled tool-calling.
11. Serve models through FastAPI.
12. Add tests, monitoring, privacy controls, cost/latency budgets, and deployment automation.

Do not jump directly to fine-tuning large models before understanding dataset quality, evaluation, baselines, and inference resource requirements.

---

# 58. Official Documentation

Use documentation that matches the exact library release you install.

## Python
- [Python Tutorial](https://docs.python.org/3/tutorial/)
- [Python Language Reference](https://docs.python.org/3/reference/)
- [Built-in Functions](https://docs.python.org/3/library/functions.html)
- [Python Standard Library](https://docs.python.org/3/library/)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)

## Data libraries
- [NumPy User Guide](https://numpy.org/doc/stable/user/)
- [NumPy API Reference](https://numpy.org/doc/stable/reference/)
- [pandas User Guide](https://pandas.pydata.org/docs/user_guide/)
- [pandas API Reference](https://pandas.pydata.org/docs/reference/)
- [Matplotlib documentation](https://matplotlib.org/stable/contents.html)

## Machine learning and deep learning
- [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [PyTorch documentation](https://docs.pytorch.org/docs/stable/)
- [PyTorch tutorials](https://docs.pytorch.org/tutorials/)
- [TensorFlow tutorials](https://www.tensorflow.org/tutorials)
- [Keras documentation](https://keras.io/)

## NLP and LLMs
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/en/index)
- [Hugging Face Datasets](https://huggingface.co/docs/datasets/)
- [OpenAI Python SDK reference](https://developers.openai.com/api/reference/python)
- [OpenAI API quickstart](https://developers.openai.com/api/docs/quickstart)

---

## Final Note

Use this guide as a structured entry point, then look up specific signatures in each library's API reference. Python's language syntax, built-in functions, and AI libraries are separate bodies of functionality. No one file can enumerate every current and future API. The reliable way to achieve practical completeness for a project is to pin the versions you use, test your examples in that environment, and consult the matching official documentation.
