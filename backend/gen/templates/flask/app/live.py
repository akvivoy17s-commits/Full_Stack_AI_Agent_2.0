"""Flask: GET cache + write invalidation (no WebSocket: Flask has no built-in support)."""
import json

from flask import Response, g, request

from . import cache, live_core


def install(app) -> None:
    @app.before_request
    def _cache_read():
        g.cache_key = None
        if request.method == "GET" and live_core.entity_for(request.path):
            key = live_core.read_key(cache.version(), request.headers.get("Authorization", ""), request.full_path)
            hit = cache.get(key)
            if hit is not None:
                return Response(json.dumps(hit), 200, {"X-Cache": "HIT"}, mimetype="application/json")
            g.cache_key = key
        return None

    @app.after_request
    def _cache_write(res):
        key = getattr(g, "cache_key", None)
        if key and res.status_code == 200 and res.mimetype == "application/json" and not res.direct_passthrough:
            cache.set(key, json.loads(res.get_data()))
            res.headers["X-Cache"] = "MISS"
        elif request.method in live_core.OPS and res.status_code < 400 and live_core.entity_for(request.path):
            cache.invalidate()
        return res
