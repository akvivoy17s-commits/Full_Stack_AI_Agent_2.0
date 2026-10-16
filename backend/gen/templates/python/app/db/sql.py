"""SQLAlchemy Core adapter for SQLite / PostgreSQL / MySQL. Tables are built from schema.py (one source of truth)."""
from contextlib import contextmanager
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects import mssql, mysql
from sqlalchemy.pool import StaticPool

from .. import schema
from ..config import cfg
from ..errors import ApiError
from ..validation import INT32, iso, parse_dt

E = schema.SCHEMA["entities"]
metadata = sa.MetaData()
TABLES = {}


def _type(f):
    t = f["type"]
    if t == "ref" or t == "int":
        return sa.Integer()
    if t in ("string", "enum"):
        return sa.String(64 if t == "enum" else 255)
    if t == "email":
        return sa.String(255)
    if t == "url":
        return sa.String(2048)
    if t == "text":
        return sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql").with_variant(mssql.NVARCHAR("max"), "mssql")   # SQL Server: NVARCHAR(max), not the deprecated TEXT/NTEXT
    if t == "float":
        return sa.Float(53)
    if t == "bool":
        return sa.Boolean()
    return sa.DateTime().with_variant(mssql.DATETIME2(), "mssql")  # stored as naive UTC in every database


MSSQL = schema.SCHEMA["db"] == "mssql"

for _n, _e in E.items():
    _cols, _extra = [sa.Column("id", sa.Integer, primary_key=True, autoincrement=True)], []
    for _f in _e["fields"]:
        _args = [_type(_f)]
        if _f["type"] == "ref" and _f.get("fk"):
            _args.append(sa.ForeignKey(E[_f["ref"]]["table"] + ".id", ondelete=_f["onDelete"]))
        # SQL Server allows one NULL per unique index, so an optional unique column gets a filtered index instead (several NULLs allowed, like the other databases)
        _filtered = MSSQL and _f["unique"] and not _f["required"]
        _col = sa.Column(_f["name"], *_args, nullable=not _f["required"], unique=bool(_f["unique"]) and not _filtered, index=bool(_f.get("index")))
        _cols.append(_col)
        if _filtered:
            _extra.append(sa.Index(f"uq_{_e['table']}_{_f['name']}", _col, unique=True, mssql_where=_col.isnot(None)))
    TABLES[_n] = sa.Table(_e["table"], metadata, *_cols, *_extra)


def _out(e, row, raw=False):
    if row is None:
        return None
    m = row._mapping
    o = {"id": m["id"]}
    for f in e["fields"]:
        if not raw and f["name"] in e["sensitive"]:
            continue
        v = m[f["name"]]
        if v is not None:
            if f["type"] == "bool":
                v = bool(v)
            elif f["type"] == "datetime":
                v = iso(v.replace(tzinfo=timezone.utc))
        o[f["name"]] = v
    return o


def _in(e, data):
    fmap = {f["name"]: f for f in e["fields"]}
    row = {}
    for k, v in data.items():
        if v is not None and fmap[k]["type"] == "datetime":
            v = (v if isinstance(v, datetime) else parse_dt(v)).astimezone(timezone.utc).replace(tzinfo=None)
        row[k] = v
    return row


@contextmanager
def _mapped():
    try:
        yield
    except sa.exc.IntegrityError as exc:
        if any(k in str(exc.orig).lower() for k in ("foreign key", "reference constraint")):
            raise ApiError(409, "conflict", "The record is referenced by, or references, another record") from exc
        raise ApiError(409, "conflict", "A record with the same unique value already exists") from exc


def _esc(s: str) -> str:
    return s.replace("!", "!!").replace("%", "!%").replace("_", "!_")


def _order(t, sort):
    """ORDER BY for ?sort (validated against the schema before it gets here); id is always the tie-breaker so pages are stable."""
    f, d = (sort or {}).get("field", "id"), (sort or {}).get("dir", "desc")
    col = t.c[f]
    first = col.asc() if d == "asc" else col.desc()
    return [first] if f == "id" else [first, t.c.id.desc()]


class SqlDb:
    def __init__(self, engine):
        self.engine = engine

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
        with self.engine.connect() as c:
            c.execute(sa.text("SELECT 1"))

    def migrate(self):
        """Applies the Alembic migrations (migrations/versions) to this database."""
        from pathlib import Path

        from alembic import command
        from alembic.config import Config

        root = Path(__file__).resolve().parents[2]
        conf = Config(str(root / "alembic.ini"))
        conf.set_main_option("script_location", str(root / "migrations"))
        with self.engine.connect() as conn:
            conf.attributes["connection"] = conn
            command.upgrade(conf, "head")
            conn.commit()

    def close(self):
        self.engine.dispose()

    def get(self, name, rid):
        i, t = self.parse_id(rid), TABLES[name]
        if i is None:
            return None
        with self.engine.connect() as c:
            return _out(E[name], c.execute(sa.select(t).where(t.c.id == i)).first())

    def find_one(self, name, where, raw=False):
        t = TABLES[name]
        with self.engine.connect() as c:
            row = c.execute(sa.select(t).where(*[t.c[k] == v for k, v in where.items()]).limit(1)).first()
        return _out(E[name], row, raw)

    def list_page(self, name, page, limit, q, filters, where, sort=None):
        e, t = E[name], TABLES[name]
        conds = [t.c[k] == v for k, v in {**filters, **where}.items()]
        if q and e["searchable"]:
            conds.append(sa.or_(*[t.c[n].ilike(f"%{_esc(q)}%", escape="!") for n in e["searchable"]]))
        with self.engine.connect() as c:
            total = c.execute(sa.select(sa.func.count()).select_from(t).where(*conds)).scalar_one()
            rows = c.execute(sa.select(t).where(*conds).order_by(*_order(t, sort)).limit(limit).offset((page - 1) * limit)).all()
        return {"rows": [_out(e, r) for r in rows], "total": total}

    def create(self, name, data):
        e, t = E[name], TABLES[name]
        with _mapped(), self.engine.begin() as c:
            pk = c.execute(sa.insert(t).values(**_in(e, data))).inserted_primary_key[0]
            row = c.execute(sa.select(t).where(t.c.id == pk)).first()
        return _out(e, row)

    def update(self, name, rid, data):
        e, t = E[name], TABLES[name]
        if data:
            with _mapped(), self.engine.begin() as c:
                c.execute(sa.update(t).where(t.c.id == rid).values(**_in(e, data)))
        return self.get(name, rid)

    def remove(self, name, rid):
        t = TABLES[name]
        with _mapped(), self.engine.begin() as c:
            c.execute(sa.delete(t).where(t.c.id == rid))

    def remove_where(self, name, where):
        t = TABLES[name]
        with _mapped(), self.engine.begin() as c:
            return c.execute(sa.delete(t).where(*[t.c[k] == v for k, v in where.items()])).rowcount


def connect():
    url = cfg.sql_url
    kw = {"pool_pre_ping": True}
    sqlite = url.startswith("sqlite")
    if sqlite:
        kw["connect_args"] = {"check_same_thread": False}  # request handlers run in a thread pool
        if url in ("sqlite://", "sqlite:///") or ":memory:" in url:
            kw["poolclass"] = StaticPool  # one shared connection, otherwise every connection would be a new empty database
    elif cfg.database_ssl and url.startswith("postgresql"):
        kw["connect_args"] = {"sslmode": "require"}
    engine = sa.create_engine(url, **kw)
    if sqlite:
        @sa.event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _record):  # SQLite ignores foreign keys unless asked
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()
    return SqlDb(engine)
