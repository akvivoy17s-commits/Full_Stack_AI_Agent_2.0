# Django Complete Guide for Full-Stack Development
## Python Syntax, Django APIs, Models, ORM, Views, Templates, Forms, Security, Testing, and Deployment

> **Purpose:** A comprehensive learning reference for building full-stack websites and APIs with Django.
>
> **Version note:** This guide targets modern Django patterns and references the Django 6.1 documentation line. The official Django downloads page lists Django 6.1.2 as the latest official release as of the date this guide was prepared. Django 6.1 supports Python 3.12–3.14; check the installation documentation for the exact patch release and Python version you install.
>
> **Scope note:** Django is a large framework, and its ecosystem includes many optional packages. There is no finite, stable list of “100% of every syntax and function,” especially across all Django versions and third-party packages. This guide covers core Python syntax commonly used with Django, major built-in Django APIs, ORM/queryset methods, request/response patterns, forms, security, testing, and deployment. Use the official versioned documentation linked at the end for exact signatures and version-specific details.

---

## Table of Contents

### Part I — Python and Web Foundations
1. Django Overview
2. Python Environment and Project Setup
3. Project and App Structure
4. HTTP, URLs, Requests, and Responses
5. Python Syntax Essentials for Django
6. Configuration and Environment Variables

### Part II — Django Core
7. Creating a Django Project
8. Settings and Installed Apps
9. URL Routing
10. Function-Based Views
11. Request Object
12. Response Types
13. Templates and Template Language
14. Static Files
15. Models and Fields
16. Migrations
17. Django ORM: Create, Read, Update, Delete
18. QuerySet Methods
19. Query Expressions and F Objects
20. Relationships: ForeignKey, OneToOneField, ManyToManyField
21. Aggregation, Annotation, and Grouping
22. Transactions and Concurrency
23. Forms and ModelForms
24. Validation
25. Class-Based Views
26. Generic Views and Mixins
27. Admin Site
28. Authentication and Authorization
29. Sessions and Cookies
30. Messages Framework
31. Middleware
32. Signals
33. File Uploads and Storage
34. Email
35. Caching
36. Async Views and Async ORM Considerations
37. Pagination
38. Internationalization and Time Zones
39. Logging and Error Handling
40. Security Checklist

### Part III — APIs and Advanced Development
41. Django REST API Patterns
42. Django REST Framework Overview
43. Database Configuration and Raw SQL
44. Custom Management Commands
45. Testing Django Applications
46. Performance and Query Optimization
47. Channels, WebSockets, and Real-Time Features
48. Deployment
49. Common Errors and Troubleshooting
50. Common Django Functions, Methods, and Decorators
51. Complete Mini CRUD Application
52. Full-Stack Learning Roadmap
53. Practice Projects
54. Official Documentation

---

# PART I — PYTHON AND WEB FOUNDATIONS

# 1. Django Overview

Django is a high-level Python web framework. It includes URL routing, request/response handling, templates, an ORM, forms, authentication, sessions, an admin interface, security features, and testing utilities.

A common request flow:

```text
Browser / React / Angular
        |
        | HTTP request
        v
URL configuration (urls.py)
        |
        v
View function/class (views.py)
        |
        +---- Form / Serializer / Validation
        |
        +---- Service or business logic
        |
        +---- Model / ORM / Database
        |
        v
HTTP response (HTML / JSON / redirect / file)
```

Django follows a Model–Template–View (MTV) pattern:
- **Model:** represents stored data and database operations.
- **Template:** renders HTML or other presentation output.
- **View:** decides how to process a request and what response to return.
- **URLconf:** maps a URL path to a view.

Django does not require React or a separate API. It can render pages using templates, expose APIs for a separate frontend, or combine approaches.

---

# 2. Python Environment and Project Setup

Check Python and pip:

```bash
python --version
python -m pip --version
```

Create and activate a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install Django:

```bash
python -m pip install --upgrade pip
python -m pip install Django==6.1.2
python -m django --version
```

The precise latest patch version may change; consult the official downloads page before starting a new project. To install the latest compatible release instead, use the documented current installation command.

Project commands:

```bash
django-admin startproject config .
python manage.py startapp products
python manage.py runserver
python manage.py check
python manage.py test
```

The development server is not intended for production deployment. Use the deployment guidance for a supported WSGI/ASGI server and hosting environment.

---

# 3. Project and App Structure

A project coordinates settings and installed applications; an app groups a set of related functionality.

```text
myproject/
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── products/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
├── templates/
├── static/
└── media/
```

Typical file roles:
- `manage.py`: project management command entry point.
- `settings.py`: installed apps, middleware, database, templates, security, and other settings.
- `urls.py`: URL patterns.
- `views.py`: request handlers.
- `models.py`: data models.
- `forms.py`: input forms and validation.
- `admin.py`: admin registrations and configuration.
- `tests.py` or `tests/`: automated tests.
- `migrations/`: versioned database schema changes.
- `asgi.py` / `wsgi.py`: deployment application entry points.

Keep business logic organized. In a larger project, separate apps by domain or feature and consider service/query modules instead of making a view responsible for everything.

---

# 4. HTTP, URLs, Requests, and Responses

HTTP request components:
- Method: GET, POST, PUT, PATCH, DELETE, etc.
- Path: `/products/12/`
- Query string: `?page=2&search=keyboard`
- Headers: `Content-Type`, `Authorization`, `Accept`, etc.
- Body: HTML form, JSON, file, or other payload.

Common status codes:

| Code | Meaning |
|---:|---|
| 200 | OK |
| 201 | Created |
| 202 | Accepted |
| 204 | No Content |
| 301 / 302 | Redirect variants |
| 400 | Bad Request |
| 401 | Unauthorized / authentication challenge semantics depend on API |
| 403 | Forbidden |
| 404 | Not Found |
| 405 | Method Not Allowed |
| 409 | Conflict |
| 413 | Request too large |
| 415 | Unsupported Media Type |
| 422 | Unprocessable Content (API convention) |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 502 / 503 / 504 | Upstream / availability / timeout issues |

Django views return response objects, not arbitrary raw Python objects. For HTML use `render()` or `HttpResponse`; for JSON use `JsonResponse`; for redirects use `redirect()` or an appropriate redirect response.

---

# 5. Python Syntax Essentials for Django

Variables and common values:

```python
name = "Asha"
price = 2499.00
is_active = True
items = ["Keyboard", "Mouse"]
user = {"id": 1, "name": "Asha"}
```

Conditions and loops:

```python
if price > 1000:
    label = "premium"
else:
    label = "budget"

for item in items:
    print(item)
```

Functions:

```python
def calculate_total(price: float, quantity: int = 1) -> float:
    return price * quantity
```

Exceptions:

```python
try:
    quantity = int("5")
except ValueError:
    quantity = 0
```

Imports:

```python
from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
```

Python type annotations help editors/static tools but do not enforce runtime validity automatically. Django form/model validation and explicit application logic are used to validate untrusted data.

---

# 6. Configuration and Environment Variables

`settings.py` contains the project configuration.

Important settings include:
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `INSTALLED_APPS`
- `MIDDLEWARE`
- `ROOT_URLCONF`
- `TEMPLATES`
- `DATABASES`
- `AUTH_PASSWORD_VALIDATORS`
- `LANGUAGE_CODE`
- `TIME_ZONE`
- `STATIC_URL`
- `STATIC_ROOT`
- `MEDIA_URL`
- `MEDIA_ROOT`
- `DEFAULT_AUTO_FIELD`
- Security cookie/HTTPS settings and deployment-specific settings.

Use environment variables or a secret manager for confidential configuration:

```python
import os

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
```

This example raises an error if `DJANGO_SECRET_KEY` is absent; define the setting in your environment. Do not fall back to a known public production secret.

Never use `DEBUG=True` in production. Configure `ALLOWED_HOSTS` to match actual hostnames. Review Django's deployment checklist and run `python manage.py check --deploy` with the production settings.

---

# PART II — DJANGO CORE

# 7. Creating a Django Project

Create a project:

```bash
django-admin startproject config myproject
cd myproject
python manage.py runserver
```

Create an application:

```bash
python manage.py startapp products
```

Add the application to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # Django apps...
    "products",
]
```

Typical URL inclusion:

`config/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("products/", include("products.urls")),
]
```

`products/urls.py`:

```python
from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="list"),
]
```

The `app_name` provides an application namespace for URL reversing.

---

# 8. Settings and Installed Apps

Common settings shape:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "products",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

Do not remove security/session/CSRF middleware without understanding the consequences. Required middleware and ordering depend on the apps/features being used.

Default database configuration often uses SQLite for a starter project. For a deployment, choose a database supported by the Django version and configure credentials through environment variables/secrets.

---

# 9. URL Routing

Django URL patterns use `path()` or `re_path()`.

```python
from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    re_path(r"^legacy/(?P<code>[A-Z0-9]+)/$", views.legacy_lookup, name="legacy_lookup"),
]
```

Common path converters:
- `str`
- `int`
- `slug`
- `uuid`
- `path`

Examples:

```python
path("users/<int:user_id>/", views.user_detail, name="user_detail")
path("posts/<slug:slug>/", views.post_detail, name="post_detail")
path("jobs/<uuid:job_id>/", views.job_detail, name="job_detail")
```

Reverse URLs:

```python
from django.urls import reverse

url = reverse("products:product_detail", kwargs={"product_id": 10})
```

In templates:

```django
<a href="{% url 'products:product_detail' product.id %}">View product</a>
```

Use stable URL names instead of hard-coded links throughout templates. URL patterns are matched in order.

---

# 10. Function-Based Views

A Django view takes a request and returns a response.

```python
from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    return HttpResponse("Hello, Django!")

def dashboard(request):
    context = {"title": "Dashboard"}
    return render(request, "dashboard.html", context)
```

JSON response:

```python
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok"})
```

`JsonResponse` accepts dictionaries by default. For other top-level JSON shapes, explicitly review the `safe` argument and serialization behavior.

Check the HTTP method:

```python
from django.views.decorators.http import require_GET, require_POST

@require_GET
def status_view(request):
    return JsonResponse({"status": "ok"})

@require_POST
def submit_view(request):
    return JsonResponse({"accepted": True}, status=202)
```

A view should generally:
- Validate input.
- Enforce authentication/authorization.
- Call business/data logic.
- Return an appropriate response.
- Avoid exposing internal exception messages or sensitive fields.

---

# 11. Request Object

The `HttpRequest` object exposes request data.

Common attributes:
- `request.method`
- `request.path`
- `request.path_info`
- `request.GET`: query parameters
- `request.POST`: form fields for supported encoded form submissions
- `request.FILES`: uploaded files
- `request.body`: raw request bytes
- `request.headers`
- `request.COOKIES`
- `request.user` when authentication middleware is installed
- `request.session` when session middleware is installed
- `request.content_type`
- `request.content_params`
- `request.META`: server/request metadata

Query parameters:

```python
def search(request):
    query = request.GET.get("q", "")
    page = request.GET.get("page", "1")
    return JsonResponse({"q": query, "page": page})
```

Values are generally strings; parse and validate integers/booleans carefully.

Form body:

```python
def submit_form(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    name = request.POST.get("name", "").strip()
    return JsonResponse({"name": name})
```

JSON body:

```python
import json
from json import JSONDecodeError
from django.http import JsonResponse

def create_json(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Expected a JSON object"}, status=400)

    return JsonResponse({"received": True}, status=201)
```

For larger APIs use forms, model forms, serializers (for example Django REST Framework), or explicit schema validation rather than hand-validating every field.

---

# 12. Response Types

## HttpResponse

```python
from django.http import HttpResponse

def text_page(request):
    return HttpResponse("Hello", content_type="text/plain", status=200)
```

## JsonResponse

```python
from django.http import JsonResponse

def api_page(request):
    return JsonResponse({"message": "ok", "count": 3})
```

## Redirect

```python
from django.shortcuts import redirect

def after_save(request):
    return redirect("products:product_list")
```

## Response headers

```python
def response_with_header(request):
    response = JsonResponse({"status": "ok"})
    response["X-App-Version"] = "1"
    return response
```

## File responses

Django includes file response support for controlled downloads. Use safe file paths/storage references, authorization, and correct content headers. Do not expose arbitrary filesystem paths supplied by a client.

Avoid returning sensitive fields merely because they exist on the model.

---

# 13. Templates and Template Language

Django Template Language (DTL) supports variable output, tags, filters, inheritance, and context.

Render:

```python
return render(request, "products/list.html", {"products": products})
```

Variables:

```django
<h1>{{ title }}</h1>
<p>{{ user.username }}</p>
```

Filters:

```django
{{ name|lower }}
{{ description|truncatewords:20 }}
{{ created_at|date:"Y-m-d" }}
{{ price|floatformat:2 }}
{{ items|length }}
{{ value|default:"Not provided" }}
```

Control flow:

```django
{% if products %}
  {% for product in products %}
    <p>{{ product.name }}</p>
  {% empty %}
    <p>No products found.</p>
  {% endfor %}
{% else %}
  <p>Nothing to show.</p>
{% endif %}
```

Template inheritance:

`base.html`:

```django
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{% block title %}My Site{% endblock %}</title>
</head>
<body>
  <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

`products/list.html`:

```django
{% extends "base.html" %}
{% block title %}Products{% endblock %}
{% block content %}
  <h1>Products</h1>
  {% for product in products %}
    <p>{{ product.name }}</p>
  {% endfor %}
{% endblock %}
```

Template tags include `{% url %}`, `{% csrf_token %}`, `{% static %}`, `{% include %}`, `{% with %}`, `{% load %}`, `{% comment %}`, and conditional/loop tags.

Do not disable autoescaping or use `safe` for untrusted input. Use Django's template escaping protections, but understand context-sensitive output safety.

---

# 14. Static Files

In templates:

```django
{% load static %}
<link rel="stylesheet" href="{% static 'css/site.css' %}">
<script src="{% static 'js/site.js' %}" defer></script>
<img src="{% static 'images/logo.svg' %}" alt="Logo">
```

Common settings:

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

Development and production static serving differ. Production typically uses `collectstatic` and a compatible static-file server/CDN/storage backend.

Command:

```bash
python manage.py collectstatic
```

Configure storage and cache headers according to your deployment. Do not place secret files in a publicly served static directory.

---

# 15. Models and Fields

A Django model maps Python attributes to database fields.

```python
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
```

Common field classes:
- `AutoField`, `BigAutoField`, `UUIDField`
- `CharField`, `TextField`, `SlugField`
- `IntegerField`, `BigIntegerField`, `PositiveIntegerField`
- `FloatField`, `DecimalField`
- `BooleanField`
- `DateField`, `TimeField`, `DateTimeField`, `DurationField`
- `EmailField`, `URLField`
- `FileField`, `ImageField`
- `BinaryField`
- `JSONField`
- `ForeignKey`, `OneToOneField`, `ManyToManyField`
- `GenericIPAddressField`
- `IPAddressField` has historical/version-specific behavior; consult the versioned docs.

Common field options:
- `null`
- `blank`
- `default`
- `choices`
- `unique`
- `db_index`
- `primary_key`
- `editable`
- `help_text`
- `verbose_name`
- `validators`
- `db_column`
- `related_name`
- `on_delete` for relationship fields

`null=True` is a database-nullability option; `blank=True` controls form/model validation blank behavior. They are not identical. For text fields, the usual recommendation is to avoid storing two meanings for emptiness without a clear reason.

---

# 16. Migrations

Create migration files after model changes:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
python manage.py sqlmigrate products 0001
```

Migrations version database schema changes. Keep migrations in version control, review generated SQL where important, and test upgrades with realistic data.

Common migration patterns:
- Create/delete model
- Add/remove/alter field
- Add indexes and constraints
- Data migration with `RunPython`
- Raw SQL migration with `RunSQL`

Data migration shape:

```python
from django.db import migrations

def forwards(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    # Update data using the historical model.

def backwards(apps, schema_editor):
    # Reverse the operation if practical and meaningful.
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
```

Use `apps.get_model()` within data migrations rather than directly importing a model that may change in the future. Do not assume every schema operation is cheap or lock-free on a large production table.

---

# 17. Django ORM: Create, Read, Update, Delete

Assume `Product` is the model shown above.

## Create

```python
product = Product.objects.create(
    name="Keyboard",
    price="2499.00",
    is_active=True,
)
```

Or:

```python
product = Product(name="Mouse", price="799.00")
product.save()
```

Use strings for exact decimal input when creating `DecimalField` values, or pass a `Decimal`.

## Read

```python
Product.objects.all()
Product.objects.get(pk=1)
Product.objects.filter(is_active=True)
Product.objects.exclude(price__lt=100)
```

`get()` raises `DoesNotExist` if no row matches and `MultipleObjectsReturned` if multiple rows match.

## Update one instance

```python
product = Product.objects.get(pk=1)
product.price = "2299.00"
product.save(update_fields=["price", "updated_at"])
```

`auto_now`/`auto_now_add` and `update_fields` behavior should be understood; if `updated_at` is intended to change, include it or use a suitable update path.

## Bulk update

```python
Product.objects.filter(is_active=False).update(is_active=True)
```

`QuerySet.update()` runs a database-level update and does not call each model instance's `save()` or emit the normal `pre_save`/`post_save` signals for each instance.

## Delete

```python
product = Product.objects.get(pk=1)
product.delete()
```

Bulk delete:

```python
Product.objects.filter(is_active=False).delete()
```

Django's ORM deletion collector handles related objects according to relationship rules, although database-level behavior and signals require attention.

---

# 18. QuerySet Methods

QuerySets are lazy until evaluated in common situations. They represent database queries, not a list immediately fetched in every case.

Common methods:

- `all()`
- `filter(**lookups)`
- `exclude(**lookups)`
- `get(**lookups)`
- `create(**kwargs)`
- `get_or_create(defaults=..., **kwargs)`
- `update_or_create(defaults=..., **kwargs)`
- `bulk_create(objs, ...)`
- `bulk_update(objs, fields, ...)`
- `update(**kwargs)`
- `delete()`
- `count()`
- `exists()`
- `first()`
- `last()`
- `earliest()`
- `latest()`
- `in_bulk()`
- `values(*fields)`
- `values_list(*fields, flat=False)`
- `distinct()`
- `order_by(*fields)`
- `reverse()`
- `only(*fields)`
- `defer(*fields)`
- `select_related(*fields)`
- `prefetch_related(*lookups)`
- `annotate(**expressions)`
- `aggregate(**expressions)`
- `dates()`, `datetimes()` where suitable
- `none()`
- `union()`, `intersection()`, `difference()` subject to backend limitations
- `select_for_update()` under supported transaction/database rules
- `explain()`
- `iterator()` to manage iteration memory behavior

Examples:

```python
Product.objects.filter(price__gte=1000).order_by("-price", "name")

Product.objects.values("id", "name", "price")

Product.objects.values_list("name", flat=True)

Product.objects.filter(is_active=True).exists()

Product.objects.count()
```

Do not call `len(queryset)` or convert huge querysets to lists just to test whether they contain rows. Use `.exists()` for an existence check and paginate large outputs.

Some methods differ in available keyword parameters across Django versions. The documented queryset reference is the complete API reference.

---

# 19. Query Expressions and F Objects

Field lookup syntax uses double underscores:

```python
Product.objects.filter(price__gt=1000)
Product.objects.filter(name__icontains="key")
Product.objects.filter(created_at__year=2026)
Product.objects.filter(name__startswith="Pro")
```

Common lookup suffixes:
- `exact`
- `iexact`
- `contains`, `icontains`
- `in`
- `gt`, `gte`, `lt`, `lte`
- `startswith`, `istartswith`
- `endswith`, `iendswith`
- `range`
- `isnull`
- `regex`, `iregex` where supported

`F()` references a database field rather than a Python value:

```python
from django.db.models import F

Product.objects.filter(stock__lt=F("reorder_level"))
Product.objects.update(stock=F("stock") - 1)
```

Using `F()` allows a calculation to be performed in the database and can avoid some read-modify-write races. It does not by itself implement every business invariant; use a filter, constraint, and/or transaction as needed.

`Q()` builds complex logic:

```python
from django.db.models import Q

Product.objects.filter(
    Q(price__lt=1000) | Q(name__icontains="basic")
)
```

Other expression tools include `Value`, `ExpressionWrapper`, `Case`, `When`, `Func`, `Subquery`, `OuterRef`, `Exists`, and backend-supported database functions.

---

# 20. Relationships: ForeignKey, OneToOneField, ManyToManyField

## Many-to-one

```python
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products"
    )
    name = models.CharField(max_length=120)
```

Access:

```python
product.category
category.products.all()
```

## One-to-one

```python
class UserProfile(models.Model):
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="profile"
    )
    display_name = models.CharField(max_length=100)
```

For a custom user model, use `settings.AUTH_USER_MODEL` in relationship definitions rather than hard-coding the default model.

## Many-to-many

```python
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

class Article(models.Model):
    title = models.CharField(max_length=200)
    tags = models.ManyToManyField(Tag, related_name="articles")
```

Use `.add()`, `.remove()`, `.clear()`, `.set()`, and `.all()` on the related manager.

When a many-to-many relationship needs fields like role, ordering, or creation time, define a through model explicitly.

---

# 21. Aggregation, Annotation, and Grouping

Aggregates summarize a queryset:

```python
from django.db.models import Avg, Count, Max, Min, Sum

Product.objects.aggregate(
    total=Count("id"),
    average_price=Avg("price"),
    highest_price=Max("price"),
    lowest_price=Min("price"),
    inventory_value=Sum("price"),
)
```

Annotations add values to each result:

```python
Category.objects.annotate(product_count=Count("products"))
```

Conditional aggregation:

```python
from django.db.models import Count, Q

Category.objects.annotate(
    active_products=Count("products", filter=Q(products__is_active=True))
)
```

Aggregations, null behavior, join duplication, and filter/order interactions can be subtle. Inspect generated SQL with `str(queryset.query)` for debugging, while avoiding reliance on internal query representation as an application contract.

---

# 22. Transactions and Concurrency

`transaction.atomic()` defines a transaction boundary:

```python
from django.db import transaction

@transaction.atomic
def place_order():
    # Create an order and related rows atomically.
    ...
```

Or:

```python
with transaction.atomic():
    ...
```

Useful tools:
- `transaction.atomic`
- `transaction.on_commit`
- `transaction.set_rollback` in appropriate contexts
- `select_for_update()` in supported transactional/database scenarios
- Database constraints and unique indexes

Example of post-commit work:

```python
from django.db import transaction

transaction.on_commit(lambda: enqueue_order_email(order_id))
```

`enqueue_order_email` must be implemented, and the callback should not be treated as a durable queue by itself. If a process can exit after commit but before queued work is persisted, consider an outbox or durable worker system.

Transactions should be short. Understand database isolation, locking, and backend limitations. An `atomic()` block does not make external network APIs transactional.

---

# 23. Forms and ModelForms

Django forms validate and clean user input.

```python
from django import forms

class ProductForm(forms.Form):
    name = forms.CharField(max_length=120)
    price = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    is_active = forms.BooleanField(required=False)
```

View:

```python
def create_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            Product.objects.create(**cleaned)
            return redirect("products:list")
    else:
        form = ProductForm()

    return render(request, "products/form.html", {"form": form})
```

A `ModelForm` maps form fields to a model:

```python
class ProductModelForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", "is_active"]
```

Use an explicit allowlist for `ModelForm.Meta.fields`; avoid `fields = "__all__"` for forms that allow users to modify sensitive fields.

Form concepts:
- `is_valid()`
- `cleaned_data`
- `errors`
- `add_error()`
- `clean_<fieldname>()`
- `clean()`
- `initial`
- `prefix`
- `ModelForm.save(commit=False)`
- `formset_factory`, `modelformset_factory`, and inline formsets

---

# 24. Validation

Field validation:

```python
from django.core.exceptions import ValidationError
from django import forms

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=50)

    def clean_username(self):
        value = self.cleaned_data["username"].strip()
        if " " in value:
            raise ValidationError("Username cannot contain spaces.")
        return value
```

Model validation:
- Field validators
- `clean_fields()`
- `clean()`
- `validate_unique()`
- `full_clean()`

`Model.save()` does not automatically call `full_clean()` in the general case. If model validation is required, ensure the application invokes it or uses the appropriate form/serializer/service rules. The database's constraints remain important for correctness under concurrent requests.

Validation does not replace authorization: check that a user may update a given record.

---

# 25. Class-Based Views

Django supports both function-based views and class-based views.

```python
from django.views import View
from django.http import JsonResponse

class StatusView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "ok"})

    def post(self, request, *args, **kwargs):
        return JsonResponse({"accepted": True}, status=202)
```

URL:

```python
from django.urls import path

urlpatterns = [
    path("status/", StatusView.as_view(), name="status"),
]
```

Important methods/hooks include:
- `dispatch()`
- `setup()`
- `http_method_not_allowed()`
- `get()`, `post()`, `put()`, `patch()`, `delete()`, `head()`, `options()`
- `get_context_data()` in suitable generic views
- `get_queryset()` in list/detail views
- `get_object()` in detail views
- `form_valid()` and `form_invalid()` in form views

Method availability depends on the base class. Override the documented hook that fits the task rather than copying an unrelated method into every view.

---

# 26. Generic Views and Mixins

Common generic views:
- `TemplateView`
- `RedirectView`
- `ListView`
- `DetailView`
- `CreateView`
- `UpdateView`
- `DeleteView`
- `FormView`
- `ArchiveIndexView` / `YearArchiveView` and related date-based views where appropriate

Example:

```python
from django.views.generic import ListView
from .models import Product

class ProductListView(ListView):
    model = Product
    template_name = "products/list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        return Product.objects.filter(is_active=True).order_by("name")
```

URL:

```python
path("products/", ProductListView.as_view(), name="list")
```

Generic views can reduce boilerplate, but authorization still needs to be explicit. Override `get_queryset()` so private records cannot be retrieved just by changing an ID/URL.

Common mixins include login/permission mixins, form mixins, context mixins, and single/multiple-object mixins; consult the versioned class-based views reference for inheritance and method resolution details.

---

# 27. Admin Site

Register a model:

```python
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 50
```

Other useful `ModelAdmin` options/methods:
- `fields`
- `fieldsets`
- `readonly_fields`
- `exclude`
- `list_display`
- `list_display_links`
- `list_editable`
- `list_filter`
- `search_fields`
- `ordering`
- `date_hierarchy`
- `autocomplete_fields`
- `raw_id_fields`
- `filter_horizontal` / `filter_vertical`
- `inlines`
- `actions`
- `get_queryset()`
- `get_readonly_fields()`
- `save_model()`
- `delete_model()`
- `has_view_permission()`, `has_add_permission()`, `has_change_permission()`, `has_delete_permission()`

Register the admin URLs and create an administrator account:

```bash
python manage.py createsuperuser
```

Keep admin access restricted. Admin site visibility and permissions do not automatically secure unrelated API endpoints.

---

# 28. Authentication and Authorization

Django includes users, groups, permissions, password hashing, sessions, and authentication middleware.

Important APIs:
- `django.contrib.auth.authenticate()`
- `login()`
- `logout()`
- `get_user_model()`
- `PermissionRequiredMixin`
- `LoginRequiredMixin`
- `@login_required`
- `@permission_required`
- `request.user`
- `request.user.is_authenticated`
- `request.user.has_perm(...)`

Function-based view:

```python
from django.contrib.auth.decorators import login_required

@login_required
def account(request):
    return render(request, "account.html")
```

Create a user through supported APIs:

```python
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.create_user(
    username="asha",
    email="asha@example.com",
    password="choose-a-strong-password-in-real-use",
)
```

Never save a raw password directly to a model field. Use Django's user/password APIs, password validators, and secure session/authentication workflows.

Prefer defining a custom user model at the beginning of a project if the application needs custom identity fields. Changing user models after migrations have been applied can be complicated.

Authorization must be enforced on the server for every sensitive record and action. Checking whether a user is logged in is not enough; also verify role, permission, ownership, and tenant scope as required.

---

# 29. Sessions and Cookies

Django sessions are typically accessed via `request.session` if session middleware is enabled.

```python
def set_preference(request):
    request.session["theme"] = "dark"
    return JsonResponse({"saved": True})

def get_preference(request):
    return JsonResponse({"theme": request.session.get("theme", "light")})
```

Session operations commonly include setting a value, reading with `.get()`, deleting with `.pop()`/`del`, `.flush()`, `.cycle_key()`, and `.set_expiry()`.

Cookie response:

```python
def set_cookie(request):
    response = JsonResponse({"ok": True})
    response.set_cookie(
        "preference",
        "dark",
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response
```

`secure=True` assumes HTTPS. Cookie names/value policy, expiration, signing, session backend and cookie configuration must reflect the actual deployment. Do not store secrets in client-side readable cookie values.

---

# 30. Messages Framework

The messages framework can display one-time notices after redirects.

```python
from django.contrib import messages
from django.shortcuts import redirect

def save_product(request):
    # Save a valid form here.
    messages.success(request, "Product saved.")
    return redirect("products:list")
```

Common levels:
- `debug`
- `info`
- `success`
- `warning`
- `error`

Templates typically iterate over `messages`:

```django
{% if messages %}
  {% for message in messages %}
    <div class="message {{ message.tags }}">{{ message }}</div>
  {% endfor %}
{% endif %}
```

Ensure the messages app and middleware/context processor are configured as required by the project setup. Do not place confidential information in messages.

---

# 31. Middleware

Middleware wraps request/response processing. It can add headers, identify requests, apply cross-cutting rules, or process responses.

A simplified middleware example:

```python
class AddVersionHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-App-Version"] = "1"
        return response
```

Register it in `MIDDLEWARE` with the correct dotted Python path.

Async middleware has additional rules. Django's middleware stack must respect sync/async capabilities and ordering. Middleware is not the place to hide all business logic, and it must not bypass CSRF/security/auth middleware requirements.

---

# 32. Signals

Django signals notify interested receivers when certain events occur. Common model signals include:
- `pre_save`
- `post_save`
- `pre_delete`
- `post_delete`
- `m2m_changed`
- `class_prepared` (special registration timing considerations)

Example:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product

@receiver(post_save, sender=Product)
def product_saved(sender, instance, created, **kwargs):
    if created:
        # Perform a small side effect or schedule durable work.
        pass
```

Prefer explicit service-layer operations for core business workflows when clarity matters. Signals can create hidden side effects and can behave differently for bulk updates/deletes; bulk `QuerySet.update()` does not call ordinary per-instance save signals.

Register signal handlers in a deliberate location such as an app configuration's `ready()` method when required by your project design. Avoid duplicate registration.

---

# 33. File Uploads and Storage

For form uploads:
- Use `request.FILES` in the view.
- Bind files to a form/model form when suitable.
- Configure `MEDIA_ROOT` / `MEDIA_URL` or a storage backend.
- Validate type, size, and content.
- Use server-generated names or storage keys.
- Do not trust client filenames or MIME types.
- Do not expose private files as public static assets.

Model example:

```python
class Document(models.Model):
    title = models.CharField(max_length=150)
    file = models.FileField(upload_to="documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
```

Image uploads may use `ImageField`, which typically requires Pillow. Production media serving should use a suitable storage service/web server and enforce authorization. Set maximum request/upload sizes at multiple layers.

---

# 34. Email

Django provides email helpers under `django.core.mail`.

```python
from django.core.mail import send_mail

send_mail(
    subject="Welcome",
    message="Thanks for registering.",
    from_email=None,
    recipient_list=["user@example.com"],
    fail_silently=False,
)
```

Use an SMTP/provider configuration appropriate to the deployment, and keep credentials in secrets. For important notification flows, send asynchronously through a durable task system and track failures. Do not put private user data in email subject/body unless needed and protected appropriately.

Other email APIs include `EmailMessage`, `EmailMultiAlternatives`, connection objects, and template-based message composition. Exact arguments are documented in Django's email reference.

---

# 35. Caching

Django cache framework APIs include:
- `cache.get()`
- `cache.set()`
- `cache.add()`
- `cache.get_or_set()`
- `cache.delete()`
- `cache.delete_many()`
- `cache.clear()`
- `cache.incr()`
- `cache.decr()`
- Per-view cache decorators and template-fragment cache tags

Example:

```python
from django.core.cache import cache

cache.set("greeting", "hello", timeout=60)
greeting = cache.get("greeting", "default")
cache.delete("greeting")
```

Use a production-appropriate cache backend. Understand stale data, invalidation, key namespaces, TTL, concurrency, and privacy. Never share user-specific cached responses with other users accidentally.

---

# 36. Async Views and Async ORM Considerations

Django supports asynchronous views and asynchronous request handling under an ASGI deployment. Some components or database operations may still have sync-only constraints depending on the backend/version.

Async view:

```python
import asyncio
from django.http import JsonResponse

async def async_status(request):
    await asyncio.sleep(0)
    return JsonResponse({"status": "ok"})
```

Use `async def` when the operations you await are genuinely asynchronous. Blocking CPU work or synchronous network/database operations still blocks the event loop unless handled appropriately.

Django's ORM has async variants for many operations, often with an `a` prefix (for example, `aget`, `acreate`, and async iteration) in supported contexts. Check the exact queryset/model API for your Django version. Transaction management and some ORM workflows may require synchronous code wrapped appropriately; do not assume every database operation becomes non-blocking just because the view is async.

---

# 37. Pagination

QuerySet slicing:

```python
page_size = 20
page_number = 2
start = (page_number - 1) * page_size
products = Product.objects.all()[start:start + page_size]
```

For robust page handling, use `Paginator`:

```python
from django.core.paginator import Paginator

paginator = Paginator(Product.objects.order_by("id"), 20)
page_obj = paginator.get_page(request.GET.get("page"))
```

`get_page()` handles invalid page inputs using documented fallback behavior; validate the user-facing pagination policy. Use stable ordering and consider the cost of large offsets on large datasets.

API pagination typically returns a structured body with `results`, `count`, `next`, and `previous` or uses cursor pagination depending on the API framework/design.

---

# 38. Internationalization and Time Zones

Common settings:

```python
LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
```

Translation functions:

```python
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

message = _("Welcome")
```

Date formatting tools include template filters such as `date`, utilities in `django.utils.timezone`, and locale-aware formatting functions.

Prefer timezone-aware datetimes when time zones matter. Decide whether stored timestamps represent UTC instants or user-local wall times, and convert at display/input boundaries.

---

# 39. Logging and Error Handling

Use Python's logging configuration and Django error handlers.

```python
import logging

logger = logging.getLogger(__name__)

def operation():
    try:
        do_work()
    except ExpectedError:
        logger.exception("Operation failed")
        raise
```

`do_work` and `ExpectedError` are application-specific.

Django custom error views conventionally use functions such as `handler400`, `handler403`, `handler404`, and `handler500` in the root URLconf, subject to the documented conditions/settings. Error behavior differs between `DEBUG=True` and production. Do not expose stack traces or secret settings in client-facing errors.

---

# 40. Security Checklist

- `DEBUG = False` in production.
- Set exact `ALLOWED_HOSTS`.
- Use HTTPS and carefully configured secure cookies.
- Keep `SECRET_KEY` secret.
- Preserve CSRF protection for cookie-authenticated form requests.
- Use template autoescaping and avoid untrusted `safe` output.
- Validate user input and uploaded files.
- Use Django's built-in password/auth system or a trusted identity integration.
- Apply authorization to every protected operation.
- Use ORM parameterization; avoid building raw SQL with untrusted string concatenation.
- Limit request sizes and rates where appropriate.
- Keep dependencies patched.
- Restrict admin access.
- Protect database credentials, backups, logs, and media files.
- Configure proxy/host/security settings intentionally.
- Run `python manage.py check --deploy` with production settings.
- Test authorization, CSRF, and object ownership, not just login success.

Django's default security features help, but they do not automatically make an incorrectly configured deployment secure.

---

# PART III — APIS AND ADVANCED DEVELOPMENT

# 41. Django REST API Patterns

Django's core can return JSON responses, but it does not automatically provide all the features of a dedicated REST framework.

Simple JSON endpoint:

```python
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok"})
```

For real APIs, decide:
- Request validation
- Response schema
- HTTP methods/status codes
- Authentication and permissions
- Pagination/filtering
- Error format
- Rate limiting
- Versioning
- API documentation
- Serialization and query optimization

Django REST Framework (DRF) is a widely used third-party framework for API serializers, viewsets, routers, permissions, authentication, pagination, and browsable APIs. It is not a built-in Django module; installation and version compatibility must be checked separately.

---

# 42. Django REST Framework Overview

Install:

```bash
python -m pip install djangorestframework
```

Add `"rest_framework"` to `INSTALLED_APPS`.

Serializer:

```python
from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price", "is_active"]
```

Generic list/create API view:

```python
from rest_framework.generics import ListCreateAPIView
from .models import Product
from .serializers import ProductSerializer

class ProductListCreateView(ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
```

Router/viewset pattern:

```python
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
urlpatterns = router.urls
```

These snippets assume `ProductViewSet` is implemented. DRF provides serializers, generic views, viewsets, routers, permission classes, authentication classes, pagination classes, filters, throttles, parsers, renderers, and exception handling. Their exact APIs are documented at the official DRF site.

Use explicit serializer fields. Configure authentication/permissions deliberately, and do not assume a serializer automatically protects a record based on its owner.

---

# 43. Database Configuration and Raw SQL

Django supports multiple relational databases subject to version/backend compatibility. Common configuration uses `DATABASES`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

PostgreSQL/MySQL configurations require appropriate drivers and connection settings. Keep passwords in environment variables/secrets, not source-controlled settings.

Django ORM is often preferred, but parameterized raw SQL is available:

```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(
        "SELECT id, name FROM products WHERE is_active = %s",
        [True],
    )
    rows = cursor.fetchall()
```

The `%s` parameter style shown is Django's placeholder convention for supported database backends; don't interpolate untrusted values into the SQL text. Table/column names cannot normally be bound as ordinary value parameters and must be validated/quoted safely if dynamic identifiers are required.

`cursor.execute`, `fetchone`, `fetchmany`, `fetchall`, and context-managed cursor usage are common DB-API operations. Raw SQL ties code more closely to the selected database dialect and requires careful mapping/validation.

---

# 44. Custom Management Commands

Create a module at:

```text
products/
└── management/
    └── commands/
        └── seed_products.py
```

Example:

```python
from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = "Create demo products"

    def handle(self, *args, **options):
        Product.objects.get_or_create(
            name="Keyboard",
            defaults={"price": "2499.00"},
        )
        self.stdout.write(self.style.SUCCESS("Demo data ready"))
```

Run:

```bash
python manage.py seed_products
```

Management command methods commonly include `add_arguments()` and `handle()`. Commands can support options, standard output/error helpers, and styled messages. Make commands idempotent where repeated execution is expected; protect destructive commands with clear safeguards.

---

# 45. Testing Django Applications

Run tests:

```bash
python manage.py test
```

Simple test:

```python
from django.test import TestCase
from django.urls import reverse

class HomeTests(TestCase):
    def test_home(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
```

Common tools:
- `TestCase`
- `TransactionTestCase`
- `SimpleTestCase`
- `Client`
- `RequestFactory`
- `override_settings`
- `override_config` availability depends on Django version
- `captureOnCommitCallbacks` where supported
- Test database setup and fixture utilities

Test client operations:
- `client.get(...)`
- `client.post(...)`
- `client.put(...)`
- `client.patch(...)`
- `client.delete(...)`
- `client.login(...)`
- `client.force_login(...)`

JSON request example:

```python
response = self.client.post(
    reverse("api:products"),
    data={"name": "Keyboard", "price": "100.00"},
    content_type="application/json",
)
```

Django's `TestCase.client` request encoding conventions depend on content type and version. Use test requests that faithfully match what real clients send.

Test:
- Status codes and response content
- Validation and malformed requests
- Permissions/ownership
- Forms and CSRF behavior as relevant
- Query behavior and performance-sensitive paths
- Database constraints
- Transactions/on-commit work
- File uploads
- Error handlers
- Migrations and key data transformations

Do not run destructive tests against production.

---

# 46. Performance and Query Optimization

Key ORM tools:
- `select_related()` for foreign-key/one-to-one relationships
- `prefetch_related()` for many-to-many/reverse relationships
- `only()` / `defer()` for selected model fields where justified
- `values()` / `values_list()` for smaller data representations
- `annotate()` / `aggregate()`
- `exists()` and `count()`
- `iterator()` for controlled iteration
- `bulk_create()` / `bulk_update()` for supported bulk workflows
- `QuerySet.explain()` where supported by the database/backend

Example:

```python
products = Product.objects.select_related("category").filter(is_active=True)
```

This can reduce repeated queries when accessing `product.category`. `prefetch_related()` is commonly useful for many-to-many and reverse relationships.

Query-count problems (N+1) often arise when a loop triggers one database query per row. Profile with representative data. Check generated SQL and the database's query plan.

---

# 47. Channels, WebSockets, and Real-Time Features

Django's core request handling is traditionally HTTP request/response. WebSockets and channel-layer features commonly use Django Channels or another ASGI-compatible system.

Consider:
- ASGI server and application setup
- WebSocket routing
- Authentication middleware and permission checks
- Channel layer / Redis or other supported backend
- Message schema validation
- Connection lifecycle, reconnects, backpressure, and limits
- Multiple workers and shared state
- Durable persistence for important messages
- Privacy and retention rules

Do not assume in-memory state works across server workers or survives restarts. For chat/events, store durable records where needed and design for duplicate/reconnect events.

---

# 48. Deployment

Before deploying:
1. Use a supported production server configuration.
2. Set `DEBUG=False`.
3. Configure `ALLOWED_HOSTS`.
4. Set a secure `SECRET_KEY`.
5. Use environment-managed database credentials.
6. Configure HTTPS and secure cookies.
7. Configure database and static/media storage.
8. Run migrations in a controlled deployment step.
9. Collect static files where the deployment requires it.
10. Run `python manage.py check --deploy`.
11. Configure logs, health checks, and alerts.
12. Test backup restoration and rollback/forward-fix workflows.
13. Configure timeouts, worker count, resource limits, and graceful shutdown.
14. Patch dependencies and the operating system/runtime.
15. Keep administrative interfaces and internal endpoints appropriately restricted.

Example checks/commands:

```bash
python manage.py check
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic
```

Use the official deployment docs for the chosen WSGI/ASGI host. Django's development server is not a production server.

---

# 49. Common Errors and Troubleshooting

| Error or symptom | Likely cause |
|---|---|
| `ModuleNotFoundError` | Wrong virtual environment, missing dependency, import path |
| `ImproperlyConfigured` | Settings missing/wrong, app not installed |
| `NoReverseMatch` | URL name/namespace/parameters incorrect |
| 404 | URL pattern mismatch, wrong prefix, object not found |
| 405 | Unsupported HTTP method |
| CSRF verification failed | Missing/mismatched token, origin/cookie/proxy configuration |
| `IntegrityError` | Unique, foreign-key, check, or not-null constraint |
| `OperationalError` | Database unavailable, schema/migration issue, invalid SQL |
| `FieldError` | Unknown ORM field/lookup or ambiguous join logic |
| `MultipleObjectsReturned` | `get()` matched more than one record |
| `DoesNotExist` | `get()` matched no record |
| Static files missing | Static settings/collection/deployment configuration |
| Upload fails | Request field name, size limit, storage permissions |
| Permission leak | Missing object-level authorization or unrestricted queryset |
| Slow page/API | N+1 queries, missing index, expensive serialization, external latency |
| Production-only failure | Environment variable, `ALLOWED_HOSTS`, TLS/proxy, worker or permission configuration |

Use `python manage.py check`, review the traceback/logs, reproduce the error in a test, check the migration state, and compare development/production configuration without sharing secrets publicly.

---

# 50. Common Django Functions, Methods, and Decorators

## Shortcuts

- `render(request, template_name, context=None, ...)`
- `redirect(to, *args, permanent=False, ...)`
- `get_object_or_404(klass, *args, **kwargs)`
- `get_list_or_404(klass, *args, **kwargs)`

## HTTP response classes

- `HttpResponse`
- `JsonResponse`
- `StreamingHttpResponse`
- `FileResponse`
- `HttpResponseRedirect`
- `HttpResponsePermanentRedirect`
- `HttpResponseNotFound`
- `HttpResponseBadRequest`
- `HttpResponseForbidden`
- `HttpResponseNotAllowed`
- `HttpResponseServerError`

## URL and view tools

- `path`
- `re_path`
- `include`
- `reverse`
- `resolve`
- `redirect`
- `render`
- `require_GET`
- `require_POST`
- `require_http_methods`
- `login_required`
- `permission_required`
- `csrf_protect`
- `csrf_exempt` (avoid disabling CSRF without a clear, safe design)
- `transaction.atomic`

## ORM / QuerySet

- `all`, `filter`, `exclude`, `get`, `create`
- `get_or_create`, `update_or_create`
- `update`, `delete`, `bulk_create`, `bulk_update`
- `count`, `exists`, `first`, `last`, `latest`, `earliest`
- `values`, `values_list`, `distinct`, `order_by`
- `select_related`, `prefetch_related`
- `aggregate`, `annotate`, `select_for_update`, `explain`
- `F`, `Q`, `Value`, `Case`, `When`, `Count`, `Sum`, `Avg`, `Min`, `Max`
- `Subquery`, `OuterRef`, `Exists`, and supported database functions

## Forms

- `is_valid`
- `cleaned_data`
- `errors`
- `add_error`
- `clean`
- `clean_<fieldname>`
- `save`
- Formset and inline formset APIs

## Authentication

- `authenticate`
- `login`
- `logout`
- `get_user_model`
- Permission/login decorators and mixins
- User/group/permission management APIs

## Management commands

- `BaseCommand`
- `add_arguments`
- `handle`
- `self.stdout.write`
- `self.stderr.write`
- `self.style.SUCCESS`, `WARNING`, `ERROR`

This is a practical shortlist, not a complete inventory of every Django function/class.

---

# 51. Complete Mini CRUD Application

Assume the application is named `products` and has been added to `INSTALLED_APPS`.

## Model

`products/models.py`:

```python
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
```

Create/apply migrations:

```bash
python manage.py makemigrations products
python manage.py migrate
```

## Views

`products/views.py`:

```python
import json
from decimal import Decimal, InvalidOperation
from json import JSONDecodeError

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Product

@require_http_methods(["GET", "POST"])
def products_api(request):
    if request.method == "GET":
        items = list(
            Product.objects.filter(is_active=True)
            .values("id", "name", "price", "is_active")
        )
        # Decimal values are not JSON-native; convert them to strings.
        for item in items:
            item["price"] = str(item["price"])
        return JsonResponse({"results": items})

    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Expected a JSON object"}, status=400)

    name = data.get("name")
    price_value = data.get("price")

    if not isinstance(name, str) or not name.strip():
        return JsonResponse({"error": "name is required"}, status=400)

    try:
        price = Decimal(str(price_value))
    except (InvalidOperation, TypeError, ValueError):
        return JsonResponse({"error": "price must be a decimal number"}, status=400)

    if not price.is_finite() or price < 0:
        return JsonResponse({"error": "price must be non-negative and finite"}, status=400)

    product = Product.objects.create(name=name.strip(), price=price)
    return JsonResponse({
        "id": product.id,
        "name": product.name,
        "price": str(product.price),
        "is_active": product.is_active,
    }, status=201)

@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def product_detail_api(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    if request.method == "GET":
        return JsonResponse({
            "id": product.id,
            "name": product.name,
            "price": str(product.price),
            "is_active": product.is_active,
        })

    if request.method == "DELETE":
        product.delete()
        return JsonResponse({}, status=204)

    try:
        data = json.loads(request.body)
    except (JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "Expected a JSON object"}, status=400)

    if request.method == "PUT" and ("name" not in data or "price" not in data):
        return JsonResponse({"error": "PUT requires name and price"}, status=400)

    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            return JsonResponse({"error": "name cannot be empty"}, status=400)
        product.name = data["name"].strip()

    if "price" in data:
        try:
            price = Decimal(str(data["price"]))
        except (InvalidOperation, TypeError, ValueError):
            return JsonResponse({"error": "price must be a decimal number"}, status=400)
        if not price.is_finite() or price < 0:
            return JsonResponse({"error": "price must be non-negative and finite"}, status=400)
        product.price = price

    product.save()
    return JsonResponse({
        "id": product.id,
        "name": product.name,
        "price": str(product.price),
        "is_active": product.is_active,
    })
```

This deliberately small tutorial API does **not** add authentication/authorization and is not production-ready. For cookie-authenticated clients, preserve CSRF protection. Add permissions, rate limiting, centralized validation/serializers, API versioning, and database constraints before exposing real data. For production APIs, Django REST Framework or another schema-validated API layer may be preferable.

## URLs

`products/urls.py`:

```python
from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("api/products/", views.products_api, name="api-list"),
    path("api/products/<int:product_id>/", views.product_detail_api, name="api-detail"),
]
```

Include in the project `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("", include("products.urls")),
]
```

## Test with curl

Create:

```bash
curl -X POST http://127.0.0.1:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Keyboard\",\"price\":\"2499.00\"}"
```

List:

```bash
curl http://127.0.0.1:8000/api/products/
```

Read one:

```bash
curl http://127.0.0.1:8000/api/products/1/
```

Update:

```bash
curl -X PATCH http://127.0.0.1:8000/api/products/1/ \
  -H "Content-Type: application/json" \
  -d "{\"price\":\"2299.00\"}"
```

Delete:

```bash
curl -X DELETE http://127.0.0.1:8000/api/products/1/
```

Note: A `204 No Content` response should have no response body. If your Django/backend/proxy/test contract requires strict HTTP behavior, return `HttpResponse(status=204)` rather than a JSON response body for delete.

---

# 52. Full-Stack Learning Roadmap

Recommended sequence:

1. Python syntax, collections, functions, exceptions.
2. HTTP requests, URLs, methods, headers, JSON, status codes.
3. Choose one framework first: Flask for minimal flexibility, or FastAPI for typed API-first workflows.
4. Learn routing, query/path/body parameters, and validation.
5. Structure code into routes, schemas/forms, service logic, and repositories.
6. Integrate a relational database or MongoDB.
7. Authentication and object-level authorization.
8. Error handling and response contracts.
9. Unit/integration tests.
10. Logging, configuration, CORS, file handling, and production deployment.
11. Add background jobs or WebSockets where the product needs them.
12. Serve AI models through validated request/response schemas and monitor latency/cost/quality.

---

# 53. Practice Projects

Build these progressively:
1. Health-check API.
2. Product CRUD service.
3. User profile API with access controls.
4. Anime catalog API with search, filters, and pagination.
5. File upload service with private storage and file limits.
6. Authentication and role-based administration.
7. Discussion/chat backend with messages and moderation.
8. AI classification endpoint.
9. RAG question-answer API with source references.
10. Production-ready service with tests, migrations, CI, deployment, health checks, and monitoring.

For every project, include validation, tests, security, clear API contracts, README setup instructions, configuration examples without secrets, and sensible error handling.

---

# 54. Official Documentation

## Flask
- [Flask Documentation](https://flask.palletsprojects.com/en/stable/)
- [Quickstart](https://flask.palletsprojects.com/en/stable/quickstart/)
- [API Reference](https://flask.palletsprojects.com/en/stable/api/)
- [Application Factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/)
- [Blueprints](https://flask.palletsprojects.com/en/stable/blueprints/)
- [Testing](https://flask.palletsprojects.com/en/stable/testing/)
- [Deployment](https://flask.palletsprojects.com/en/stable/deploying/)

## FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Deployment Concepts](https://fastapi.tiangolo.com/deployment/)

## Related tools
- [Starlette](https://www.starlette.io/)
- [Pydantic](https://docs.pydantic.dev/)
- [HTTPX](https://www.python-httpx.org/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Django REST Framework](https://www.django-rest-framework.org/)

---

## Final Note

Use this guide as a structured learning reference, then verify exact APIs against the version you installed. Flask, FastAPI, Starlette, Pydantic, database drivers, and extensions have separate release cycles. No single Markdown file can list literally every current and future API, but the major patterns, functions, integration approaches, security considerations, and project structures needed for practical full-stack backend development are covered here.
