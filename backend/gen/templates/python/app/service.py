"""Framework-independent CRUD with server-side access control: public | user | owner | admin.
`user` is None or {"id": str, "role": str}. Every web framework only maps HTTP onto these functions."""
from . import schema, validation as V
from .errors import ApiError, validation_failed

ADMIN = schema.SCHEMA["adminRole"]


def is_admin(user) -> bool:
    return bool(user) and user.get("role") == ADMIN


def _has(e, name) -> bool:
    return any(f["name"] == name for f in e["fields"])


def _scope(db, e, user) -> dict:
    """Owner-scoped entities only expose the caller's own records to non-admins."""
    if e["read"] == "owner" and e["ownerField"] and not is_admin(user):
        return {e["ownerField"]: db.parse_id(user["id"])}
    return {}


def _check_refs(db, e, data) -> None:
    errors = {f["name"]: "refers to a record that does not exist" for f in e["fields"]
              if f["type"] == "ref" and data.get(f["name"]) is not None and not db.get(f["ref"], data[f["name"]])}
    if errors:
        raise validation_failed(details=errors)


def _load(db, e, rid, user, level) -> dict:
    i = db.parse_id(rid)
    rec = None if i is None else db.get(e["name"], i)
    owned = level != "owner" or not e["ownerField"] or is_admin(user) or (rec and str(rec.get(e["ownerField"])) == str(user["id"]))
    if not rec or not owned:
        raise ApiError(404, "not_found", "Record not found")  # 404, not 403: do not reveal other users' records
    return rec


def list_records(db, e, query: dict, user) -> dict:
    o = V.parse_list(e, query)
    r = db.list_page(e["name"], o["page"], o["limit"], o["q"], o["filters"], _scope(db, e, user), o["sort"])
    return {"data": r["rows"], "page": o["page"], "limit": o["limit"], "total": r["total"]}


def get_record(db, e, rid, user) -> dict:
    return _load(db, e, rid, user, e["read"])


def create_record(db, e, body, user) -> dict:
    data = V.validate_body(e, body, False)
    _check_refs(db, e, data)
    if e["ownerField"] and user:
        data[e["ownerField"]] = db.parse_id(user["id"])
    if _has(e, "created_at"):
        data["created_at"] = V.now_iso()
    return db.create(e["name"], data)


def update_record(db, e, rid, body, user) -> dict:
    _load(db, e, rid, user, e["write"])
    data = V.validate_body(e, body, True)
    _check_refs(db, e, data)
    if _has(e, "updated_at"):
        data["updated_at"] = V.now_iso()
    return db.update(e["name"], db.parse_id(rid), data)


def delete_record(db, e, rid, user) -> None:
    _load(db, e, rid, user, e["write"])
    db.remove(e["name"], db.parse_id(rid))
