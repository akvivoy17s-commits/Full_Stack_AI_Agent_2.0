from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from .. import schema, uploads_core
from ..config import cfg
from ..deps import user_dep
from ..errors import ApiError

router = APIRouter()
_who = user_dep("user" if schema.SCHEMA["auth"] else "public")


@router.post("", summary="Upload a file (raw body; PNG, JPEG, GIF, WebP or PDF)", status_code=201)
async def upload(request: Request, user=Depends(_who)):
    buf = bytearray()
    async for chunk in request.stream():          # stop reading as soon as the limit is passed
        buf += chunk
        if len(buf) > cfg.upload_max_bytes:
            raise ApiError(413, "payload_too_large", "The file is too large")
    return await run_in_threadpool(uploads_core.save, bytes(buf))


@router.get("/{name}", summary="Download an uploaded file")
def download(name: str, user=Depends(_who)):
    data, mime = uploads_core.read(name)
    return Response(data, media_type=mime, headers=uploads_core.HEADERS)
