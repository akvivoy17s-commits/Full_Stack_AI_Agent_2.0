"""Django ORM adapter for SQLite / PostgreSQL / MySQL. Models and the first migration are generated from schema.py (see app/models.py)."""
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import reduce
from operator import or_

from django.core.management import call_command
from django.db import IntegrityError, connection, connections, transaction
from django.db.models import ProtectedError, Q, RestrictedError

from .. import models, schema
from ..errors import ApiError
from ..validation import INT32, iso, parse_dt

E = schema.SCHEMA["entities"]
FK_MSG = "The record is referenced by, or references, another record"
UNIQUE_MSG = "A record with the same unique value already exists"


def _model(name):
    return getattr(models, name)


def _kw(name: str, where: dict) -> dict:
    keys = models.KEYS[name]
    return {keys.get(k, k): v for k, v in where.items()}


def _out(e, row, raw=False):
    if row is None:
        return None
    keys = models.KEYS[e["name"]]
    o = {"id": row["id"]}
    for f in e["fields"]:
        if not raw and f["name"] in e["sensitive"]:
            continue
        v = row[keys[f["name"]]]
        if v is not None:
            if f["type"] == "bool":
                v = bool(v)
            elif f["type"] == "datetime":
                v = iso(v.replace(tzinfo=timezone.utc))
        o[f["name"]] = v
    return o


def _in(e, data):
    fmap, keys, row = {f["name"]: f for f in e["fields"]}, models.KEYS[e["name"]], {}
    for k, v in data.items():
        if v is not None and fmap[k]["type"] == "datetime":
            v = (v if isinstance(v, datetime) else parse_dt(v)).astimezone(timezone.utc).replace(tzinfo=None)
        row[keys[k]] = v
    return row


@contextmanager
def _mapped():
    try:
        with transaction.atomic():
            yield
    except (ProtectedError, RestrictedError) as exc:
        raise ApiError(409, "conflict", FK_MSG) from exc
    except IntegrityError as exc:
        raise ApiError(409, "conflict", FK_MSG if "foreign key" in str(exc).lower() else UNIQUE_MSG) from exc


def _order(keys, sort):
    f, d = (sort or {}).get("field", "id"), (sort or {}).get("dir", "desc")
    col = "id" if f == "id" else keys.get(f, f)
    first = ("" if d == "asc" else "-") + col
    return [first] if f == "id" else [first, "-id"]


class DjangoDb:
    @staticmethod
    def parse_id(v):
        if isinstance(v, bool):
            return None
        if isinstance(v, str) and v.isascii() and v.isdigit():
            v = int(v)
        return v if isinstance(v, int) and 0 < v <= INT32 else None

    def clean(self, name, row):
        """Drops sensitive fields from a record that was read with raw=True."""
        return {k: v for k, v in row.items() if k not in E[name]["sensitive"]}

    def ping(self):
        connection.ensure_connection()
        with connection.cursor() as c:
            c.execute("SELECT 1")

    def migrate(self):
        """Applies the Django migrations (app/migrations). For later schema changes run `python manage.py makemigrations`."""
        call_command("migrate", interactive=False, verbosity=0)

    def close(self):
        connections.close_all()

    def get(self, name, rid):
        i = self.parse_id(rid)
        return None if i is None else _out(E[name], _model(name).objects.filter(pk=i).values().first())

    def find_one(self, name, where, raw=False):
        return _out(E[name], _model(name).objects.filter(**_kw(name, where)).values().first(), raw)

    def list_page(self, name, page, limit, q, filters, where, sort=None):
        e, keys = E[name], models.KEYS[name]
        qs = _model(name).objects.filter(**_kw(name, {**filters, **where}))
        if q and e["searchable"]:
            qs = qs.filter(reduce(or_, (Q(**{keys[n] + "__icontains": q}) for n in e["searchable"])))   # Django escapes % and _ itself
        rows = qs.order_by(*_order(keys, sort)).values()[(page - 1) * limit:page * limit]
        return {"rows": [_out(e, r) for r in rows], "total": qs.count()}

    def create(self, name, data):
        with _mapped():
            obj = _model(name).objects.create(**_in(E[name], data))
        return self.get(name, obj.pk)

    def update(self, name, rid, data):
        if data:
            with _mapped():
                _model(name).objects.filter(pk=rid).update(**_in(E[name], data))
        return self.get(name, rid)

    def remove(self, name, rid):
        with _mapped():
            _model(name).objects.filter(pk=rid).delete()

    def remove_where(self, name, where):
        M = _model(name)
        with _mapped():
            return M.objects.filter(**_kw(name, where)).delete()[1].get(M._meta.label, 0)
