import re

from django.urls import re_path

from . import schema, views

S = schema.SCHEMA
handler400, handler404, handler500 = "app.views.bad_request", "app.views.not_found", "app.views.server_error"

urlpatterns = [re_path(r"^api/health/?$", views.health), re_path(r"^api/docs/?$", views.docs), re_path(r"^api/openapi\.json$", views.openapi)]
if S["integrations"]["uploads"]:
    from . import uploads_views
    urlpatterns += [re_path(r"^api/uploads/?$", uploads_views.upload), re_path(r"^api/uploads/(?P<name>[^/]+)$", uploads_views.download)]
if S.get("checkout"):
    from . import checkout_views
    urlpatterns.append(re_path(r"^api/checkout/?$", checkout_views.checkout))
if S["integrations"]["payments"]:
    from . import payments_views
    urlpatterns += [re_path(r"^api/payments/intent/?$", payments_views.intent), re_path(r"^api/payments/webhook/?$", payments_views.webhook)]
if S["auth"]:
    for _name in ("register", "login", "logout", "me") + (("refresh",) if S["refresh"] else ()):
        urlpatterns.append(re_path(rf"^api/auth/{_name}/?$", getattr(views, f"auth_{_name}")))
if S["db"]:
    for _e in S["entities"].values():
        if _e["internal"] or not _e["ops"]:
            continue
        _p, _kw = re.escape(_e["path"]), {"name": _e["name"]}
        if {"list", "create"} & set(_e["ops"]):
            urlpatterns.append(re_path(rf"^api/{_p}/?$", views.collection, _kw))
        if {"get", "update", "delete"} & set(_e["ops"]):
            urlpatterns.append(re_path(rf"^api/{_p}/(?P<rid>[^/]+?)/?$", views.item, _kw))
