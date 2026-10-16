from flask import Blueprint, request

from .. import schema, service
from ..deps import PUBLIC_LIMIT, get_db, json_body, rate_limit, user_for


def _doc(e: dict) -> str:
    fields = ", ".join(f"{f['name']} ({f['type']}{'' if not f['required'] else ', required'})" for f in e["fields"]
                       if f["name"] not in e["sensitive"] and f["name"] != e["ownerField"] and f["name"] not in ("id", "created_at", "updated_at"))
    return f"Accepted fields: {fields or 'none'}. Read access: {e['read']}. Write access: {e['write']}."


def _register(bp: Blueprint, e: dict) -> None:
    base, ops, name, doc = "/" + e["path"], e["ops"], e["name"], _doc(e)
    read_user, write_user = user_for(e["read"]), user_for(e["write"])
    limit = rate_limit(PUBLIC_LIMIT) if e["write"] == "public" else (lambda fn: fn)

    def add(rule, method, endpoint, summary, fn):
        fn.__name__, fn.__doc__ = endpoint, summary
        bp.add_url_rule(rule, endpoint, fn, methods=[method])

    if "list" in ops:
        add(base, "GET", f"{name}_list", f"List {name} records. {doc}",
            lambda: service.list_records(get_db(), e, {k: v for k, v in request.args.lists()}, read_user()))
    if "get" in ops:
        add(base + "/<rid>", "GET", f"{name}_get", f"Get one {name} record",
            lambda rid: service.get_record(get_db(), e, rid, read_user()))
    if "create" in ops:
        add(base, "POST", f"{name}_create", f"Create a {name} record. {doc}",
            limit(lambda: (service.create_record(get_db(), e, json_body(), write_user()), 201)))
    if "update" in ops:
        add(base + "/<rid>", "PUT", f"{name}_update", f"Update a {name} record. {doc}",
            limit(lambda rid: service.update_record(get_db(), e, rid, json_body(), write_user())))
    if "delete" in ops:
        def delete(rid):
            service.delete_record(get_db(), e, rid, write_user())
            return "", 204
        add(base + "/<rid>", "DELETE", f"{name}_delete", f"Delete a {name} record", limit(delete))


def make_blueprint() -> Blueprint:
    bp = Blueprint("crud", __name__)
    for e in schema.SCHEMA["entities"].values():
        if not e["internal"] and e["ops"]:
            _register(bp, e)
    return bp
