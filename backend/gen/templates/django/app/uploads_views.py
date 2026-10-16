from django.http import HttpResponse

from . import schema, uploads_core
from .deps import user_for
from .views import only, respond

_who = user_for("user" if schema.SCHEMA["auth"] else "public")


@only("POST")
def upload(request):
    """Upload a file (raw body; PNG, JPEG, GIF, WebP or PDF)"""
    _who(request)
    return respond(uploads_core.save(request.body), 201)


@only("GET")
def download(request, name):
    """Download an uploaded file"""
    _who(request)
    data, mime = uploads_core.read(name)
    res = HttpResponse(data, content_type=mime)
    for k, v in uploads_core.HEADERS.items():
        res[k] = v
    return res
