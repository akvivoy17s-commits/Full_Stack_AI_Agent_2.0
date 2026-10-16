"""Spec model -> one OpenAPI 3.0 document. Framework-neutral: every generator writes it as backend/openapi.json and serves it
at /api/openapi.json, so all backends describe themselves the same way. Deterministic, no network, no LLM."""
import json

TYPE = {"string": {"type": "string", "maxLength": 255}, "text": {"type": "string"}, "email": {"type": "string", "format": "email"},
        "url": {"type": "string", "format": "uri"}, "int": {"type": "integer"}, "float": {"type": "number"},
        "bool": {"type": "boolean"}, "datetime": {"type": "string", "format": "date-time"}}
ERR = {"400": "Validation failed", "401": "Not signed in or token invalid", "403": "Not allowed", "404": "Not found",
       "409": "Conflict (duplicate or still referenced)", "413": "Payload too large", "415": "Unsupported file type", "429": "Too many requests", "502": "Payment provider error", "503": "Not configured"}


def _prop(f: dict, mongo: bool) -> dict:
    if f["type"] == "ref":
        return {"type": "string" if mongo else "integer", "description": f"id of a {f['ref']}"}
    if f["type"] == "enum":
        return {"type": "string", "enum": list(f.get("values") or f.get("enum") or [])}
    return dict(TYPE.get(f["type"], {"type": "string"}))


def _writable(e: dict, f: dict) -> bool:      # same rule as the runtime validators
    return f["name"] not in e["sensitive"] and f["name"] != e["ownerField"] and f["name"] not in ("id", "created_at", "updated_at")


def _resp(code: str, desc: str, ref: str | None = None, arr: bool = False) -> dict:
    r = {"description": desc}
    if ref:
        r["content"] = {"application/json": {"schema": {"$ref": f"#/components/schemas/{ref}"}}}
    return {code: r}


def _errors(codes) -> dict:
    return {c: {"description": ERR[c], "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}} for c in codes}


def build(m: dict, spec: dict) -> dict:
    mongo = m["db"] == "mongodb"
    title = (spec.get("purpose") or "API").split(".")[0][:80]
    schemas = {"Error": {"type": "object", "required": ["error"], "properties": {"error": {"type": "object", "required": ["code", "message"],
               "properties": {"code": {"type": "string"}, "message": {"type": "string"}, "details": {"type": "object"}}}}}}
    paths = {"/api/health": {"get": {"summary": "Health check", "tags": ["system"], "responses": {"200": {"description": "ok"}, "503": {"description": "degraded"}}}}}
    sec = [{"bearerAuth": []}]
    if m["auth"]:
        schemas["User"] = {"type": "object", "properties": {"id": {"type": "integer"}, "email": {"type": "string", "format": "email"}, "name": {"type": "string"},
                                                           "role": {"type": "string", "enum": list(m["roles"])}}}
        auth_out = {"type": "object", "properties": {"user": {"$ref": "#/components/schemas/User"}, "accessToken": {"type": "string"},
                    "tokenType": {"type": "string"}, "expiresIn": {"type": "integer"}, **({"refreshToken": {"type": "string"}} if m["refresh"] else {})}}
        schemas["AuthResult"] = auth_out
        body = lambda props, req: {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": req, "additionalProperties": False, "properties": props}}}}
        pw = {"type": "string", "minLength": 8, "maxLength": 72}
        em = {"type": "string", "format": "email"}
        paths["/api/auth/register"] = {"post": {"summary": f"Sign up (always role {m['defaultRole']})", "tags": ["auth"], "requestBody": body({"email": em, "name": {"type": "string"}, "password": pw}, ["email", "name", "password"]),
                                                "responses": {**_resp("201", "Created", "AuthResult"), **_errors(["400", "409", "429"])}}}
        paths["/api/auth/login"] = {"post": {"summary": "Sign in", "tags": ["auth"], "requestBody": body({"email": em, "password": pw}, ["email", "password"]),
                                             "responses": {**_resp("200", "Signed in", "AuthResult"), **_errors(["400", "401", "429"])}}}
        if m.get("firebaseAuth"):
            paths["/api/auth/firebase"] = {"post": {"summary": "Sign in with a Firebase ID token (verified server side; role is never taken from the token)", "tags": ["auth"], "requestBody": body({"idToken": {"type": "string"}}, ["idToken"]),
                                                    "responses": {**_resp("200", "Signed in", "AuthResult"), **_errors(["400", "401", "429", "503"])}}}
        if m["refresh"]:
            paths["/api/auth/refresh"] = {"post": {"summary": "Exchange a refresh token (single use, rotates)", "tags": ["auth"], "requestBody": body({"refreshToken": {"type": "string"}}, ["refreshToken"]),
                                                   "responses": {**_resp("200", "New token pair", "AuthResult"), **_errors(["401", "429"])}}}
        paths["/api/auth/logout"] = {"post": {"summary": "Sign out (revokes the refresh token, or all of them if none is sent)", "tags": ["auth"], "security": sec, "responses": {"204": {"description": "Signed out"}, **_errors(["401"])}}}
        paths["/api/auth/me"] = {"get": {"summary": "Current user", "tags": ["auth"], "security": sec, "responses": {**_resp("200", "User", "User"), **_errors(["401"])}}}
    for e in m["entities"]:
        if e["internal"] or not e["ops"]:
            continue
        n, base = e["name"], "/api/" + e["path"]
        props = {"id": {"type": "integer"} if not mongo else {"type": "string"}}
        props.update({f["name"]: _prop(f, mongo) for f in e["fields"] if f["name"] not in e["sensitive"]})
        schemas[n] = {"type": "object", "properties": props}
        inp = {f["name"]: _prop(f, mongo) for f in e["fields"] if _writable(e, f)}
        req = [f["name"] for f in e["fields"] if _writable(e, f) and f["required"]]
        schemas[n + "Input"] = {"type": "object", "additionalProperties": False, "properties": inp, **({"required": req} if req else {})}
        schemas[n + "List"] = {"type": "object", "properties": {"data": {"type": "array", "items": {"$ref": f"#/components/schemas/{n}"}},
                               "page": {"type": "integer"}, "limit": {"type": "integer"}, "total": {"type": "integer"}}}
        sortable = ["id"] + [f["name"] for f in e["fields"] if f["type"] != "text" and f["name"] not in e["sensitive"]]
        qp = [{"name": "page", "in": "query", "schema": {"type": "integer", "minimum": 1, "default": 1}},
              {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20}},
              {"name": "sort", "in": "query", "description": "Field name; prefix with - for descending. Default -id.", "schema": {"type": "string", "enum": sortable + ["-" + s for s in sortable]}}]
        if e["searchable"]:
            qp.append({"name": "q", "in": "query", "description": "Search in: " + ", ".join(e["searchable"]), "schema": {"type": "string", "maxLength": 100}})
        qp += [{"name": f["name"], "in": "query", "description": "Exact match", "schema": _prop(f, mongo)} for f in e["fields"] if f["type"] in ("ref", "enum", "bool")]
        idp = [{"name": "id", "in": "path", "required": True, "schema": {"type": "string" if mongo else "integer"}}]
        ref, jbody = f"#/components/schemas/{n}", {"required": True, "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{n}Input"}}}}

        def access(level):
            return ({"security": sec, "x-access": level} if level != "public" else {"x-access": "public"})

        def codes(level, extra):
            return (["401", "403"] if level == "admin" else ["401"] if level in ("user", "owner") else []) + extra + ["429"]
        ops = {}
        if "list" in e["ops"]:
            ops["get"] = {"summary": f"List {n} records", "parameters": qp, **access(e["read"]), "responses": {**_resp("200", "Page of records", n + "List"), **_errors(["400"] + codes(e["read"], []))}}
        if "create" in e["ops"]:
            ops["post"] = {"summary": f"Create a {n}", "requestBody": jbody, **access(e["write"]), "responses": {**_resp("201", "Created", n), **_errors(["400"] + codes(e["write"], ["409"]))}}
        if ops:
            paths[base] = {k: {**v, "tags": [n]} for k, v in ops.items()}
        one = {}
        if "get" in e["ops"]:
            one["get"] = {"summary": f"Get a {n}", "parameters": idp, **access(e["read"]), "responses": {**_resp("200", "Record", n), **_errors(["400"] + codes(e["read"], ["404"]))}}
        if "update" in e["ops"]:
            one["put"] = {"summary": f"Update a {n}", "parameters": idp, "requestBody": jbody, **access(e["write"]), "responses": {**_resp("200", "Updated", n), **_errors(["400"] + codes(e["write"], ["404", "409"]))}}
        if "delete" in e["ops"]:
            one["delete"] = {"summary": f"Delete a {n}", "parameters": idp, **access(e["write"]), "responses": {"204": {"description": "Deleted"}, **_errors(codes(e["write"], ["404", "409"]))}}
        if one:
            paths[base + "/{id}"] = {k: {**v, "tags": [n]} for k, v in one.items()}
    if m.get("checkout"):
        paths["/api/checkout"] = {"post": {"summary": "Place an order (prices and stock are read server-side)", "tags": ["checkout"], "security": sec,
                                           "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["items"], "properties": {"items": {"type": "array", "minItems": 1, "maxItems": 50, "items": {"type": "object"}}}}}}},
                                           "responses": {"201": {"description": "Order created"}, **_errors(["400", "401", "409", "429"])}}}
    I = m.get("integrations") or {}
    if I.get("uploads"):
        paths["/api/uploads"] = {"post": {"summary": "Upload a file (raw body; PNG, JPEG, GIF, WebP or PDF)", "tags": ["uploads"], "security": sec, "requestBody": {"required": True, "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}},
                                          "responses": {"201": {"description": "Stored"}, **_errors(["400", "401", "413", "415", "429"])}}}
        paths["/api/uploads/{name}"] = {"get": {"summary": "Download an uploaded file", "tags": ["uploads"], "security": sec, "parameters": [{"name": "name", "in": "path", "required": True, "schema": {"type": "string"}}],
                                                "responses": {"200": {"description": "The file"}, **_errors(["401", "404"])}}}
    if I.get("payments"):
        paths["/api/payments/intent"] = {"post": {"summary": "Start a payment for one of your pending orders (amount read from the order)", "tags": ["payments"], "security": sec,
                                                  "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["orderId"], "properties": {"orderId": {"type": "integer"}}}}}},
                                                  "responses": {"201": {"description": {"stripe": "clientSecret for the payment form", "razorpay": "razorpayOrderId and public keyId for the Razorpay checkout", "paypal": "paypalOrderId and approveUrl for the buyer"}[m.get("paymentProvider") or "stripe"]}, **_errors(["400", "401", "404", "409", "429", "502", "503"])}}}
        paths["/api/payments/webhook"] = {"post": {"summary": f"{ {'stripe': 'Stripe', 'razorpay': 'Razorpay', 'paypal': 'PayPal'}[m.get('paymentProvider') or 'stripe'] } webhook (signature verified)", "tags": ["payments"], "responses": {"200": {"description": "Received"}, **_errors(["400", "503"])}}}
    return {"openapi": "3.0.3", "info": {"title": title + " - API", "version": "1.0.0"}, "paths": dict(sorted(paths.items())),
            "components": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}}, "schemas": schemas}}


def dumps(m: dict, spec: dict) -> str:
    return json.dumps(build(m, spec), indent=1, ensure_ascii=False) + "\n"
