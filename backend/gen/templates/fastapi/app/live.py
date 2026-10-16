"""FastAPI: GET cache + write invalidation + WebSocket /ws. Connect, then send {"type":"auth","token":"<access token>"} within 5 s (apps with sign-in).
The server pushes {"type":"change","entity":...,"op":...} after writes; clients refetch over the normal, authorised REST API."""
import asyncio
import json

from fastapi import Request, Response, WebSocket
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.websockets import WebSocketDisconnect

from . import cache, live_core, schema
from .config import cfg
from .errors import ApiError

CLIENTS: set[WebSocket] = set()
I = schema.SCHEMA["integrations"]


async def broadcast(entity: str, op: str) -> None:
    text = json.dumps({"type": "change", "entity": entity, "op": op})
    await asyncio.gather(*(c.send_text(text) for c in list(CLIENTS)), return_exceptions=True)


def install(app) -> None:
    @app.middleware("http")
    async def live(request: Request, call_next):
        ent = live_core.entity_for(request.url.path)
        if not ent:
            return await call_next(request)
        if request.method == "GET" and I["cache"]:
            key = live_core.read_key(await run_in_threadpool(cache.version), request.headers.get("authorization", ""), str(request.url.path) + "?" + request.url.query)
            hit = await run_in_threadpool(cache.get, key)
            if hit is not None:
                return JSONResponse(hit, headers={"X-Cache": "HIT"})
            res = await call_next(request)
            if res.status_code != 200 or "json" not in res.headers.get("content-type", ""):
                return res
            body = b"".join([c async for c in res.body_iterator])
            await run_in_threadpool(cache.set, key, json.loads(body))
            headers = {k: v for k, v in res.headers.items() if k.lower() != "content-length"}
            return Response(body, 200, {**headers, "X-Cache": "MISS"}, media_type="application/json")
        res = await call_next(request)
        if request.method in live_core.OPS and res.status_code < 400:
            if I["cache"]:
                await run_in_threadpool(cache.invalidate)
            if I["ws"]:
                await broadcast(ent, live_core.OPS[request.method])
        return res

    if I["ws"]:
        @app.websocket("/ws")
        async def ws(sock: WebSocket):
            origin = sock.headers.get("origin")
            if (origin and origin not in cfg.cors_origins) or len(CLIENTS) >= cfg.ws_max_clients:
                return await sock.close(code=1008)
            await sock.accept()
            try:
                if schema.SCHEMA["auth"]:
                    from .security import decode_access
                    try:
                        msg = json.loads(await asyncio.wait_for(sock.receive_text(), 5))
                        if msg.get("type") != "auth":
                            raise ValueError
                        decode_access(str(msg.get("token", "")))
                    except (asyncio.TimeoutError, ValueError, AttributeError, ApiError):
                        return await sock.close(code=4401)
                    await sock.send_text('{"type":"ready"}')
                CLIENTS.add(sock)
                while True:
                    if len(await sock.receive_text()) > 2048:
                        return await sock.close(code=1009)
            except WebSocketDisconnect:
                pass
            finally:
                CLIENTS.discard(sock)
