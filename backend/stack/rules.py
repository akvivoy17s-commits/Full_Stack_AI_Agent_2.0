"""Centralised compatibility rules. One function validates a whole stack; everything else (selection, UI option
filtering, API) reuses it, so the rules live in exactly one place."""
from backend.stack import catalog as C

SQL_FREE = ("none", None, "")


def _issue(fields, msg):
    return {"fields": list(fields), "field": fields[0], "msg": msg}


def validate(s: dict) -> tuple[list[dict], list[dict]]:
    """Returns (errors, warnings). An error means the combination cannot be generated; a warning is a caveat."""
    errs, warns = [], []
    E = lambda fields, msg: errs.append(_issue(fields, msg))      # noqa: E731
    W = lambda fields, msg: warns.append(_issue(fields, msg))     # noqa: E731

    for field, table in C.TABLES.items():                         # unknown ids first: nothing else is reliable then
        v = s.get(field)
        if v not in (None, "") and v not in table:
            E([field], f"Unknown {field.replace('_', ' ')} '{v}'.")
    if errs:
        return errs, warns

    fe, fl, be, bl, db = (s.get(k) or "" for k in ("frontend", "frontend_lang", "backend", "backend_lang", "database"))
    orm, auth, cache, store, ai, test, dep = (s.get(k) or "none" for k in ("orm", "auth", "cache", "storage", "ai", "testing", "deploy"))
    be, db = be or "none", db or "none"
    grp = C.db_group(db)

    # ---- languages
    if fe:
        f = C.FRONTEND[fe]
        if fl and fl not in f["langs"]:
            if fe == "html":
                E(["frontend", "frontend_lang"], "TypeScript needs a build step. Plain HTML/CSS/JS cannot use it; pick React, Vue, Svelte or another framework for TypeScript.")
            else:
                E(["frontend", "frontend_lang"], f"{f['label']} does not support {C.FRONTEND_LANG[fl]['label']} (supported: {', '.join(f['langs'])}).")
    if be != "none" and bl and bl not in C.BACKEND[be]["langs"]:
        E(["backend", "backend_lang"], f"{C.BACKEND[be]['label']} is written in {', '.join(C.BACKEND[be]['langs'])}, not '{bl}'.")
    if be == "none" and bl:
        E(["backend", "backend_lang"], "A backend language was chosen but there is no backend.")

    # ---- backend <-> database
    if be == "none":
        if grp in ("sql", "mongodb"):
            E(["backend", "database"], f"{C.DATABASE[db]['label']} cannot be used directly from the browser (credentials would be exposed). Choose a backend, or use Firebase.")
    elif grp and grp not in C.ORMS[be]:
        why = "Django's ORM has no first-party MongoDB support; use PostgreSQL/MySQL, or pick Express/FastAPI for MongoDB." if (be, grp) == ("django", "mongodb") \
            else f"{C.BACKEND[be]['label']} has no supported data layer for {C.DATABASE[db]['label']}."
        E(["backend", "database"], why)
    if be == "django" and db == "mssql":
        W(["backend", "database"], "SQL Server on Django needs the third-party 'mssql-django' package.")
    if grp == "firebase" and be not in ("none",):
        W(["database", "backend"], "Firebase is accessed through the Admin SDK from this backend; relational features (joins, migrations) do not apply.")

    # ---- ORM / data layer
    if orm not in ("none",):
        if db == "none":
            W(["orm", "database"], "A data layer was chosen but there is no database; it will be ignored.")
        elif grp and orm not in C.ORMS.get(be, {}).get(grp, []):
            E(["orm", "backend", "database"], f"{C.ORM[orm]['label']} does not work with {C.BACKEND[be]['label']} + {C.DATABASE[db]['label']}.")

    # ---- authentication
    if auth in ("jwt", "session", "oauth2") and be == "none":
        E(["auth", "backend"], f"{C.AUTH[auth]['label']} needs a backend. Use Firebase Authentication for a backend-free app.")
    # Firestore can be used without a visible sign-in UI. In that case the generated
    # browser data adapter provisions Firebase anonymous auth so owner-scoped rules still apply.
    if auth in ("jwt", "session") and db == "none":
        E(["auth", "database"], f"{C.AUTH[auth]['label']} needs a database to store users.")
    if auth == "oauth2" and db == "none" and be != "none":
        W(["auth", "database"], "OAuth sign-in without a database will not persist user profiles or roles.")
    if auth == "session" and be != "none" and fe and C.FRONTEND[fe]["kind"] == "spa":
        W(["auth", "frontend"], "Cookie sessions with a separately served SPA need same-site hosting or credentialed CORS.")

    # ---- cache / storage
    if cache != "none" and be == "none":
        E(["cache", "backend"], "A cache needs a backend.")
    if store in ("local", "s3") and be == "none":
        E(["storage", "backend"], f"{C.STORAGE[store]['label']} needs a backend to receive and sign uploads. Use Firebase Storage for a backend-free app.")
    if store == "local" and dep in ("vercel", "netlify"):
        W(["storage", "deploy"], "Serverless hosting has an ephemeral disk: local file storage will not persist.")

    # ---- AI
    if ai != "none" and be == "none":
        E(["ai", "backend"], "AI features need a backend so provider keys and models stay server-side.")
    if ai == "python-inprocess" and be != "none" and C.BACKEND[be]["runtime"] != "python":
        E(["ai", "backend"], f"An in-process Python AI module needs a Python backend; with {C.BACKEND[be]['label']} use a separate Python AI service.")
    if ai == "python-service" and be in ("fastapi", "flask", "django"):
        W(["ai", "backend"], "The Python backend can host the AI code itself; a separate service only pays off for heavy dependencies, scaling or isolation.")

    # ---- testing
    if fe and test not in C.TESTING_FOR[fe]:
        E(["testing", "frontend"], f"{C.TESTING[test]['label']} is not offered for {C.FRONTEND[fe]['label']} (options: {', '.join(C.TESTING_FOR[fe])}).")

    # ---- deployment
    if dep in ("static", "vercel", "netlify", "firebase-hosting") and be != "none":
        W(["deploy", "backend"], f"{C.DEPLOY[dep]['label']} hosts the frontend only; deploy the backend separately (Docker or Render).")
    if dep == "static" and fe and C.FRONTEND[fe]["kind"] == "ssr":
        E(["deploy", "frontend"], f"{C.FRONTEND[fe]['label']} renders on a server; plain static hosting cannot run it.")
    if dep in ("vercel", "netlify") and be != "none" and C.BACKEND[be]["runtime"] in ("java", "dotnet", "php", "go", "python"):
        W(["deploy", "backend"], f"{C.DEPLOY[dep]['label']} is not a natural host for {C.BACKEND[be]['label']}; prefer Docker or Render.")
    return errs, warns


def options(stack: dict) -> dict:
    """For every field: each option with allowed/why_not, given everything else already chosen.
    An option is blocked only by an error that involves that field, so one conflict never greys out the whole form."""
    out = {}
    for field, table in C.TABLES.items():
        rows = []
        for key, item in table.items():
            if field == "orm":
                pool = C.ORMS.get(stack.get("backend") or "none", {}).get(C.db_group(stack.get("database")) or "", [])
                if key != "none" and stack.get("database") not in (None, "", "none") and key not in pool:
                    rows.append({"id": key, "label": item["label"], "allowed": False, "why_not": "Not supported by this backend + database.",
                                 "status": C.status(field, key)})
                    continue
            errs, _ = validate({**stack, field: key})
            bad = next((e for e in errs if field in e["fields"]), None)
            rows.append({"id": key, "label": item["label"], "allowed": bad is None, "why_not": bad["msg"] if bad else "",
                         "status": C.status(field, key, {**stack, field: key})})
        out[field] = rows
    return out
