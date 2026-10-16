"""Requirement analysis from a natural-language brief: keyword rules only, so it costs zero LLM tokens.

Returns kind, complexity, needs (backend/db/auth/...) and explicit technology mentions ("using Angular and Spring Boot").
Mentions are treated as user preferences by the selector. Negations ("no backend", "frontend only") are honoured."""
import re

_STYLE_TAG = re.compile(r"\n*design style:\s*([^.\n]+)\.?\s*animation intensity:[^\n]*\s*$", re.I)
STYLE_KIND = {"analytics dashboard": "dashboard", "interactive portfolio": "portfolio", "e-commerce storefront": "ecommerce",
              "anime streaming platform": "social"}          # "Premium SaaS" etc. carry no technical meaning

KINDS = {   # kind -> keywords (regex fragments)
    "portfolio": r"portfolio|personal (?:web)?site|resume site|\bcv site|freelancer showcase",
    "landing": r"landing page|marketing (?:web)?site|coming soon|product page|startup (?:web)?site",
    "site": r"(?:college|school|university|business|restaurant|hotel|company|church|ngo|clinic|agency|wedding) (?:web)?site|informational site",
    "dashboard": r"dashboard|analytics|admin panel|kpi|saas|back ?office",
    "ecommerce": r"e-?commerce|online (?:store|shop)|storefront|shopping cart|\bcart\b|checkout|marketplace|\bshop\b",
    "chat": r"chat (?:app|application|platform|room)|messaging|real-?time chat|instant messag",
    "chatbot": r"chat ?bot|ai assistant|ai chat|\bllm\b|\brag\b|ai agent|copilot",
    "management": r"management system|\berp\b|\bhrms?\b|\bcrm\b|hospital|library (?:management|system)|attendance|inventory|booking system|student portal|admission|\bcollege\b.*(?:system|portal)|school (?:system|portal)|payroll|\blms\b",
    "cms": r"\bcms\b|content management|blog platform|publishing platform|headless",
    "social": r"social (?:network|media|platform)|community platform|\bforum\b|news ?feed|streaming platform",
    "local": r"local (?:app|application|only)|offline|single[- ]user|personal (?:tracker|tool)|to-?do app|note[- ]taking",
}
NEEDS = {
    "auth": r"log ?in|sign ?in|sign ?up|register|authenticat|user accounts?|user roles?|role-based|rbac|admin (?:panel|login)|\bjwt\b|oauth|\bsso\b",
    "db": r"database|\bdb\b|store (?:data|records)|persist|\bcrud\b|orders|inventory|patients|bookings|product catalog",
    "realtime": r"real-?time|websocket|live (?:updates|chat|collab)|presence|socket\.io|push notification",
    "payments": r"payments?|stripe|razorpay|paypal|checkout|billing|subscriptions?",
    "email": r"send (?:an )?emails?|email notification|newsletter|smtp|verification email|password reset|sendgrid|mailgun",
    "uploads": r"upload|file storage|attachments?|image gallery uploads|profile (?:photo|picture)",
    "cache": r"\bcach(?:e|ing)\b|redis|leaderboard|job queue|rate limit",
    "firebase": r"firebase|firestore",
    "rtdb": r"realtime database|rtdb|presence",
    "documents": r"flexible schema|document (?:store|database)|schemaless|nested data|activity feed|event logs?|json documents",
    "ml": r"computer vision|image (?:classif|recogn)|classif\w*\s+(?:\w+\s+)?images?|(?:face|speech) recognition|object detection|machine learning|\bml\b|\bnlp\b|sentiment|recommendation engine|pandas|forecasting|train(?:ing)? a model|embeddings?|vector (?:db|search)|\brag\b|data analysis|\bocr\b",
    "llm": r"chat ?bot|\bllm\b|gpt|openai|claude|gemini|ai (?:assistant|chat|helper|bot|agent|feature)s?|summariz|generative|ai[- ]powered|copilot",
    "seo": r"\bseo\b|search engine|blog|articles|product pages",
    "enterprise": r"enterprise|\berp\b|\bhrms?\b|hospital|college|university|bank|insurance|multi-?tenant|microservice|scalab|millions|compliance",
    "microsoft": r"microsoft|azure|windows server|\biis\b|office 365|active directory",
    "hosting_mysql": r"shared hosting|cpanel|wordpress|woocommerce",
    "s3": r"\bs3\b|minio|object storage|cloudflare r2",
}
NEGATIONS = {
    "backend": r"(?:no|without|skip)\s+(?:a\s+|any\s+)?(?:backend|back-end|server)|front-?end only|static (?:site|website|only)|no server",
    "db": r"(?:no|without)\s+(?:a\s+|any\s+)?database",
    "auth": r"(?:no|without)\s+(?:a\s+|any\s+)?(?:login|auth\w*)",
}
# explicit technology mentions -> (field, value). Order matters inside a field (first match wins).
MENTIONS = [
    ("frontend", "nuxt", r"\bnuxt(?:\.?js)?\b"), ("frontend", "next", r"\bnext\.?js\b"),
    ("frontend", "sveltekit", r"\bsvelte ?kit\b"), ("frontend", "svelte", r"\bsvelte\b"),
    ("frontend", "solid", r"\bsolid\.?js\b|\bsolid-js\b"), ("frontend", "angular", r"\bangular\b"),
    ("frontend", "vue", r"\bvue(?:\.?js)?\b"), ("frontend", "react", r"\breact(?:\.?js)?\b"),
    ("frontend", "html", r"\bvanilla (?:js|javascript)\b|\bhtml,? css,? (?:and |&)?(?:js|javascript)\b|\bhtml/css/js\b|\bplain html\b"),
    ("backend", "nestjs", r"\bnest\.?js\b"), ("backend", "fastapi", r"\bfast ?api\b"), ("backend", "flask", r"\bflask\b"),
    ("backend", "django", r"\bdjango\b"), ("backend", "spring", r"\bspring ?boot\b|\bspring (?:framework|backend)\b"),
    ("backend", "aspnet", r"\basp\.?net\b|\.net core|\bdotnet\b|\bc# (?:backend|api)\b"), ("backend", "laravel", r"\blaravel\b"),
    ("backend", "go", r"\bgolang\b|\bgo (?:backend|api|server)\b"),
    ("backend", "express", r"\bexpress(?:\.?js)\b|\bexpress (?:api|server|backend|app)\b|\bnode(?:\.?js)? (?:with |\+ ?|and )?express\b"
                           r"|(?:\bmern\b|\b(?:with|using|and|plus)\b|[,+])\s*express\b(?!\s+(?:checkout|delivery|shipping|interest|yourself|lane))"),
    ("database", "firebase-rtdb", r"firebase realtime(?: database)?|\brtdb\b"), ("database", "firestore", r"\bfirestore\b"),
    ("database", "mssql", r"\bsql server\b|\bmssql\b|\bms sql\b"), ("database", "postgresql", r"\bpostgres(?:ql)?\b"),
    ("database", "mysql", r"\bmy ?sql\b"), ("database", "sqlite", r"\bsqlite\b"), ("database", "mongodb", r"\bmongo(?:db)?\b"),
    ("auth", "firebase-auth", r"firebase auth(?:entication)?"), ("auth", "jwt", r"\bjwt\b"),
    ("auth", "oauth2", r"\boauth2?\b|google login|sign in with google"),
    ("cache", "redis", r"\bredis\b"), ("storage", "s3", r"\bs3\b|\bminio\b"), ("storage", "firebase-storage", r"firebase storage"),
    ("ai", "python-service", r"python (?:ai |ml )?(?:service|microservice)|separate python"),
    ("testing", "vitest", r"\bvitest\b"), ("testing", "jest", r"\bjest\b"), ("testing", "playwright", r"\bplaywright\b"),
    ("testing", "cypress", r"\bcypress\b"), ("testing", "karma", r"\bkarma\b"),
    ("deploy", "docker", r"\bdocker\b"), ("deploy", "vercel", r"\bvercel\b"), ("deploy", "netlify", r"\bnetlify\b"),
    ("deploy", "render", r"\brender\.com\b|\bon render\b"), ("deploy", "firebase-hosting", r"firebase hosting"),
    ("deploy", "static", r"github pages"),
]
IMPLIED_AUTH_KINDS = {"management", "social", "chat", "dashboard", "ecommerce"}
IMPLIED_DB_KINDS = {"management", "social", "chat", "dashboard", "ecommerce", "cms"}
BACKEND_NEED_KEYS = ("auth", "db", "realtime", "payments", "email", "uploads", "cache", "ml", "llm")


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.I) is not None


def split_style(brief: str) -> tuple[str, str]:
    """The UI appends 'Design style: X. Animation intensity: Y.' to the brief; analyse the user's words and the style apart."""
    m = _STYLE_TAG.search(brief or "")
    return ((brief or "")[:m.start()], m.group(1).strip().lower()) if m else ((brief or ""), "")


def analyze(brief: str) -> dict:
    text, style = split_style(brief)
    t = text.lower()
    signals: list[str] = []

    scores = {k: len(re.findall(p, t, re.I)) for k, p in KINDS.items()}
    if STYLE_KIND.get(style):
        scores[STYLE_KIND[style]] += 1
    order = list(KINDS)                                              # ties resolve by this priority
    kind = max(order, key=lambda k: (scores[k], -order.index(k))) if any(scores.values()) else "generic"
    if kind != "generic":
        signals.append(f"kind={kind}")

    flags = {k: _has(p, t) for k, p in NEEDS.items()}
    neg = {k: _has(p, t) for k, p in NEGATIONS.items()}

    auth = flags["auth"] or (kind in IMPLIED_AUTH_KINDS and kind != "dashboard") or (kind == "dashboard" and _has(r"saas|admin|users|team", t))
    db = flags["db"] or kind in IMPLIED_DB_KINDS or auth
    ai = "ml" if flags["ml"] else ("llm" if flags["llm"] or kind == "chatbot" else "none")
    firebase = flags["firebase"]
    needs = {"auth": auth and not neg["auth"], "db": db and not neg["db"], "realtime": flags["realtime"] or kind == "chat",
             "payments": flags["payments"], "email": flags["email"], "uploads": flags["uploads"], "cache": flags["cache"],
             "ai": ai, "firebase": firebase, "rtdb": flags["rtdb"], "documents": flags["documents"], "seo": flags["seo"] or kind in ("landing", "site", "ecommerce", "cms"),
             "enterprise": flags["enterprise"], "microsoft": flags["microsoft"], "mysql_hosting": flags["hosting_mysql"], "s3": flags["s3"],
             "local": kind == "local"}
    server_side = any(needs[k] for k in ("realtime", "payments", "email", "uploads", "cache")) or ai != "none"
    backend = (needs["db"] or needs["auth"] or server_side) and not neg["backend"]
    if firebase and not server_side and not neg["backend"]:
        backend = False                                              # Firebase covers auth + data without a custom server
    if neg["backend"] and not firebase:
        needs["db"] = needs["auth"] = False
    needs["backend"] = backend
    signals += [k for k in ("auth", "db", "realtime", "payments", "email", "uploads", "cache", "firebase") if needs[k]]
    if ai != "none":
        signals.append(f"ai={ai}")

    points = sum(bool(needs[k]) for k in ("auth", "db", "realtime", "payments", "email", "uploads", "cache")) + (ai != "none") \
        + (kind in ("management", "ecommerce", "social", "cms")) + 2 * bool(needs["enterprise"]) + (len(text) > 600)
    complexity = "simple" if points <= 1 else ("medium" if points <= 4 else "complex")
    if kind in ("portfolio", "landing", "site") and not backend:
        complexity = "simple"

    mentions: dict[str, str] = {}
    for field, value, pat in MENTIONS:
        if field not in mentions and _has(pat, t):
            mentions[field] = value
    if re.search(r"\btypescript\b|\bts\b", t) and not re.search(r"\bjavascript\b|\bvanilla js\b", t):
        mentions["frontend_lang"] = "ts"
    elif re.search(r"\bjavascript\b|\bvanilla js\b", t) and not re.search(r"\btypescript\b", t):
        mentions["frontend_lang"] = "js"
    if neg["backend"]:
        mentions.setdefault("backend", "none")
    if firebase and "database" not in mentions:
        mentions["database"] = "firebase-rtdb" if needs["rtdb"] and not _has(r"firestore", t) else "firestore"
    return {"kind": kind, "complexity": complexity, "needs": needs, "mentions": mentions, "signals": signals, "style": style}
