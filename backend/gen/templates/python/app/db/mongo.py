"""PyMongo adapter. Same interface as sql.py. Ids are 24-character hex strings (ObjectId) in every response."""
import re

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, DuplicateKeyError

from .. import schema
from ..config import cfg
from ..errors import ApiError
from ..validation import iso, parse_dt

E = schema.SCHEMA["entities"]
_HEX = re.compile(r"^[a-f0-9]{24}$", re.I)


def _oid(v):
    if isinstance(v, ObjectId):
        return v
    return ObjectId(v) if isinstance(v, str) and _HEX.match(v) else None


def _out(e, doc, raw=False):
    if doc is None:
        return None
    o = {"id": str(doc["_id"])}
    for f in e["fields"]:
        n = f["name"]
        if (not raw and n in e["sensitive"]) or n not in doc:
            continue
        v = doc[n]
        if v is not None:
            v = str(v) if f["type"] == "ref" else iso(v) if f["type"] == "datetime" else v
        o[n] = v
    return o


def _val(f, v):
    if v is None:
        return None
    if f["type"] == "ref":
        return _oid(v)
    if f["type"] == "datetime":
        return parse_dt(v) if isinstance(v, str) else v
    return v


def _where(e, where):
    fmap = {f["name"]: f for f in e["fields"]}
    return {("_id" if k == "id" else k): (_oid(v) if k == "id" else _val(fmap[k], v)) for k, v in where.items()}


def _split(e, data):
    """(fields to set, fields to unset). A missing value is unset, not stored as null, so sparse unique indexes keep working."""
    fmap = {f["name"]: f for f in e["fields"]}
    sets, unsets = {}, {}
    for k, v in data.items():
        if v is None and fmap[k]["unique"]:
            unsets[k] = ""
        else:
            sets[k] = _val(fmap[k], v)
    return sets, unsets


def _order(sort):
    f, d = (sort or {}).get("field", "id"), (sort or {}).get("dir", "desc")
    direction = 1 if d == "asc" else -1
    return [("_id", direction)] if f == "id" else [(f, direction), ("_id", -1)]


class MongoDb:
    def __init__(self, client, database):
        self.client, self.db = client, database

    parse_id = staticmethod(_oid)

    def clean(self, name, rec):
        """Drops sensitive fields from a record that was read with raw=True."""
        return {k: v for k, v in rec.items() if k not in E[name]["sensitive"]}

    def ping(self):
        self.client.admin.command("ping")

    def migrate(self):
        """Creates indexes (idempotent). Collections are created on first write."""
        for e in E.values():
            for f in e["fields"]:
                if f["unique"]:
                    self.db[e["table"]].create_index(f["name"], unique=True, sparse=not f["required"])
                elif f.get("index"):
                    self.db[e["table"]].create_index(f["name"])

    def close(self):
        self.client.close()

    def get(self, name, rid):
        i = _oid(rid)
        return None if i is None else _out(E[name], self.db[E[name]["table"]].find_one({"_id": i}))

    def find_one(self, name, where, raw=False):
        e = E[name]
        return _out(e, self.db[e["table"]].find_one(_where(e, where)), raw)

    def list_page(self, name, page, limit, q, filters, where, sort=None):
        e = E[name]
        flt = _where(e, {**filters, **where})
        if q and e["searchable"]:
            flt["$or"] = [{n: {"$regex": re.escape(q), "$options": "i"}} for n in e["searchable"]]
        coll = self.db[e["table"]]
        docs = coll.find(flt).sort(_order(sort)).skip((page - 1) * limit).limit(limit)
        return {"rows": [_out(e, d) for d in docs], "total": coll.count_documents(flt)}

    def create(self, name, data):
        e = E[name]
        sets, _ = _split(e, data)
        try:
            res = self.db[e["table"]].insert_one(sets)
        except DuplicateKeyError as exc:
            raise ApiError(409, "conflict", "A record with the same unique value already exists") from exc
        return self.get(name, res.inserted_id)

    def update(self, name, rid, data):
        e = E[name]
        sets, unsets = _split(e, data)
        ops = {**({"$set": sets} if sets else {}), **({"$unset": unsets} if unsets else {})}
        if ops:
            try:
                self.db[e["table"]].update_one({"_id": _oid(rid)}, ops)
            except DuplicateKeyError as exc:
                raise ApiError(409, "conflict", "A record with the same unique value already exists") from exc
        return self.get(name, rid)

    def remove(self, name, rid):
        self.db[E[name]["table"]].delete_one({"_id": _oid(rid)})

    def remove_where(self, name, where):
        e = E[name]
        return self.db[e["table"]].delete_many(_where(e, where)).deleted_count


def connect():
    client = MongoClient(cfg.database_url, tz_aware=True, serverSelectionTimeoutMS=5000)
    try:
        database = client.get_default_database()
    except ConfigurationError as exc:
        raise RuntimeError("The MongoDB connection string must include a database name, e.g. mongodb://localhost:27017/appdb") from exc
    return MongoDb(client, database)
