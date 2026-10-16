from flask import Blueprint, Response, request

from .. import schema, uploads_core
from ..deps import user_for

_who = user_for("user" if schema.SCHEMA["auth"] else "public")


def make_blueprint() -> Blueprint:
    bp = Blueprint("uploads", __name__)

    @bp.post("")
    def upload():
        """Upload a file (raw body; PNG, JPEG, GIF, WebP or PDF)"""
        _who()
        return uploads_core.save(request.get_data()), 201

    @bp.get("/<name>")
    def download(name: str):
        """Download an uploaded file"""
        _who()
        data, mime = uploads_core.read(name)
        res = Response(data, mimetype=mime)
        res.headers.update(uploads_core.HEADERS)
        return res

    return bp
