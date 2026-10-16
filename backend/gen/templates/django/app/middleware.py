import logging

from django.core.exceptions import DisallowedHost, PermissionDenied, RequestDataTooBig, SuspiciousOperation
from django.http import Http404, HttpResponse, JsonResponse

from .config import cfg
from .deps import API_LIMIT, client_ip
from .errors import ApiError

log = logging.getLogger("app")
METHODS = "GET, POST, PUT, DELETE"
HEADERS = "Content-Type, Authorization"


def error_response(e: ApiError) -> JsonResponse:
    return JsonResponse(e.body(), status=e.status)


class ApiMiddleware:
    """Host check, CORS allow-list, rate limit, security headers and the error envelope. Replaces CommonMiddleware / CorsMiddleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        api = request.path.startswith("/api")
        origin = request.headers.get("Origin")
        try:
            request.get_host()                       # enforces ALLOWED_HOSTS (normally done by CommonMiddleware)
            if api and request.method == "OPTIONS" and origin and "Access-Control-Request-Method" in request.headers:
                res = HttpResponse(status=204)       # CORS preflight; headers are added below
            else:
                if api:
                    API_LIMIT.enforce(client_ip(request))
                    if int(request.META.get("CONTENT_LENGTH") or 0) > 100 * 1024 and request.path.rstrip("/") != "/api/uploads":
                        raise ApiError(413, "payload_too_large", "Request body is too large")
                res = self.get_response(request)
        except DisallowedHost:
            res = error_response(ApiError(400, "bad_request", "Invalid host header"))
        except ApiError as e:
            res = error_response(e)
        res["X-Content-Type-Options"] = "nosniff"
        res["X-Frame-Options"] = "DENY"
        res["Referrer-Policy"] = "no-referrer"
        if api:
            res["Cache-Control"] = "no-store"
            if origin and origin in cfg.cors_origins:
                res["Access-Control-Allow-Origin"] = origin
                res["Vary"] = "Origin"
                if request.method == "OPTIONS":
                    res["Access-Control-Allow-Methods"] = METHODS
                    res["Access-Control-Allow-Headers"] = HEADERS
                    res["Access-Control-Max-Age"] = "600"
        return res

    def process_exception(self, request, exc):
        if isinstance(exc, ApiError):
            return error_response(exc)
        if isinstance(exc, RequestDataTooBig):
            return error_response(ApiError(413, "payload_too_large", "Request body is too large"))
        if isinstance(exc, (Http404, PermissionDenied, SuspiciousOperation)):
            return None                              # Django maps these itself (handler400 / handler404 in urls.py)
        log.error("%s %s failed: %s", request.method, request.path, exc, exc_info=exc)   # details stay in the log, never in the response
        return error_response(ApiError(500, "internal_error", "Something went wrong"))
