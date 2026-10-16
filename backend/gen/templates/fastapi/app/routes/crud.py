from typing import Any

from fastapi import APIRouter, Body, Depends, Request, Response

from .. import schema, service
from ..deps import PUBLIC_LIMIT, get_db, rate_limit, user_dep

router = APIRouter()


def _doc(e: dict) -> str:
    fields = ", ".join(f"{f['name']} ({f['type']}{'' if not f['required'] else ', required'})" for f in e["fields"]
                       if f["name"] not in e["sensitive"] and f["name"] != e["ownerField"] and f["name"] not in ("id", "created_at", "updated_at"))
    return f"Accepted fields: {fields or 'none'}. Read access: {e['read']}. Write access: {e['write']}."


def _register(e: dict) -> None:
    base, ops, name, doc = "/" + e["path"], e["ops"], e["name"], _doc(e)
    read_user, write_user = user_dep(e["read"]), user_dep(e["write"])
    write_deps = [Depends(rate_limit(PUBLIC_LIMIT))] if e["write"] == "public" else []

    if "list" in ops:
        @router.get(base, tags=[name], summary=f"List {name} records", description=doc)
        def list_records(request: Request, db=Depends(get_db), user=Depends(read_user)):
            query: dict[str, list[str]] = {}
            for k, v in request.query_params.multi_items():
                query.setdefault(k, []).append(v)
            return service.list_records(db, e, query, user)

    if "get" in ops:
        @router.get(base + "/{rid}", tags=[name], summary=f"Get one {name} record")
        def get_record(rid: str, db=Depends(get_db), user=Depends(read_user)):
            return service.get_record(db, e, rid, user)

    if "create" in ops:
        @router.post(base, status_code=201, tags=[name], summary=f"Create a {name} record", description=doc, dependencies=write_deps)
        def create_record(body: Any = Body(None), db=Depends(get_db), user=Depends(write_user)):
            return service.create_record(db, e, body, user)

    if "update" in ops:
        @router.put(base + "/{rid}", tags=[name], summary=f"Update a {name} record", description=doc, dependencies=write_deps)
        def update_record(rid: str, body: Any = Body(None), db=Depends(get_db), user=Depends(write_user)):
            return service.update_record(db, e, rid, body, user)

    if "delete" in ops:
        @router.delete(base + "/{rid}", status_code=204, response_class=Response, tags=[name], summary=f"Delete a {name} record", dependencies=write_deps)
        def delete_record(rid: str, db=Depends(get_db), user=Depends(write_user)):
            service.delete_record(db, e, rid, user)
            return Response(status_code=204)


for _e in schema.SCHEMA["entities"].values():
    if not _e["internal"] and _e["ops"]:
        _register(_e)
