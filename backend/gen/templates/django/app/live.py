"""Django: GET cache + write invalidation (no WebSocket: Django needs ASGI + Channels for that). Listed after ApiMiddleware, so cached
responses still get the security headers, CORS and the rate limit."""
import json

from django.http import JsonResponse

from . import cache, live_core


class LiveMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not live_core.entity_for(request.path):
            return self.get_response(request)
        if request.method == "GET":
            key = live_core.read_key(cache.version(), request.headers.get("Authorization", ""), request.get_full_path())
            hit = cache.get(key)
            if hit is not None:
                res = JsonResponse(hit)
                res["X-Cache"] = "HIT"
                return res
            res = self.get_response(request)
            if res.status_code == 200 and "json" in res.get("Content-Type", "") and not res.streaming:
                cache.set(key, json.loads(res.content))
                res["X-Cache"] = "MISS"
            return res
        res = self.get_response(request)
        if request.method in live_core.OPS and res.status_code < 400:
            cache.invalidate()
        return res
