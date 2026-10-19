import re
from backend import config
from backend.agent import intent, prompts, llm, schemas, prompt_context
from backend.memory import task_memory
from backend.engines import design_engine, animation_engine

MAX_SECTIONS = 6  # Keep per-section model calls bounded for local 7B models
# ----------------------------------------------------------------
# LAYOUT CONFIGURATION
# Layout -> (allowed section IDs, fallback plan)
# ----------------------------------------------------------------

LAYOUTS = {

    # Marketing websites and landing pages
    "landing": (
        [
            "hero",
            "logos",
            "features",
            "showcase",
            "how",
            "stats",
            "testimonials",
            "pricing",
            "faq",
            "cta",
        ],
        [
            "hero",
            "features",
            "cta",
        ],
    ),

    # Analytics dashboards and admin panels
    "dashboard": (
        [
            "overview",
            "kpis",
            "charts",
            "table",
            "activity",
        ],
        [
            "overview",
            "kpis",
            "charts",
            "table",
        ],
    ),

    # Personal and professional portfolios
    "portfolio": (
        [
            "hero",
            "work",
            "about",
            "skills",
            "experience",
            "contact",
        ],
        [
            "hero",
            "work",
            "about",
            "contact",
        ],
    ),

    # Complete schema-driven applications.
    # The application shell and pages are generated from the
    # requirements, entities, routes, permissions and API schemas.
    "app": (
        [
            "app",
        ],
        [
            "app",
        ],
    ),

    # SaaS products with authentication and feature pages
    "saas": (
        [
            "hero",
            "features",
            "showcase",
            "pricing",
            "faq",
            "cta",
        ],
        [
            "hero",
            "features",
            "cta",
        ],
    ),

    # E-commerce websites and online stores
    "ecommerce": (
        [
            "hero",
            "categories",
            "products",
            "features",
            "testimonials",
            "faq",
            "cta",
        ],
        [
            "hero",
            "categories",
            "products",
            "cta",
        ],
    ),

    # Blogs, magazines and content platforms
    "blog": (
        [
            "hero",
            "featured_posts",
            "categories",
            "latest_posts",
            "newsletter",
            "cta",
        ],
        [
            "hero",
            "featured_posts",
            "latest_posts",
        ],
    ),

    # Agency and business websites
    "business": (
        [
            "hero",
            "services",
            "about",
            "work",
            "process",
            "testimonials",
            "pricing",
            "faq",
            "contact",
            "cta",
        ],
        [
            "hero",
            "services",
            "about",
            "contact",
        ],
    ),

    # Educational platforms and online courses
    "education": (
        [
            "hero",
            "courses",
            "features",
            "instructors",
            "testimonials",
            "pricing",
            "faq",
            "cta",
        ],
        [
            "hero",
            "courses",
            "features",
            "cta",
        ],
    ),

    # Community and social applications
    "community": (
        [
            "hero",
            "feed",
            "members",
            "groups",
            "events",
            "activity",
        ],
        [
            "hero",
            "feed",
            "members",
        ],
    ),

    # Documentation and developer portals
    "documentation": (
        [
            "hero",
            "getting_started",
            "features",
            "examples",
            "api_reference",
            "faq",
        ],
        [
            "hero",
            "getting_started",
            "api_reference",
        ],
    ),

    # Login, registration and account-access pages
    "authentication": (
        [
            "login",
            "register",
            "forgot_password",
            "reset_password",
        ],
        [
            "login",
        ],
    ),
}


# ----------------------------------------------------------------
# LAYOUT DETECTION RULES
# ----------------------------------------------------------------

LAYOUT_RULES = {
    "landing": [
        "Marketing or product-promotion website",
        "Product introduction and conversion-focused content",
    ],
    "dashboard": [
        "Analytics, administration or data-monitoring interface",
        "Metrics, charts, tables or activity feeds",
    ],
    "portfolio": [
        "Personal portfolio, resume or professional showcase",
        "Projects, skills, experience or contact information",
    ],
    "app": [
        "Interactive application with multiple functional workflows",
        "CRUD operations, authentication, database or API integration",
        "Custom application pages that do not fit a static landing page",
    ],
    "saas": [
        "Software-as-a-Service marketing website",
        "Subscription plans, product features or account-based services",
    ],
    "ecommerce": [
        "Online store or product-selling application",
        "Product catalog, cart, checkout or order management",
    ],
    "blog": [
        "Publishing platform, blog or online magazine",
        "Articles, categories, authors or newsletters",
    ],
    "business": [
        "Company, agency or professional services website",
        "Services, company information, projects or enquiries",
    ],
    "education": [
        "Learning management system or educational platform",
        "Courses, lessons, instructors or student progress",
    ],
    "community": [
        "Community, forum or social networking application",
        "Members, posts, groups, discussions or events",
    ],
    "documentation": [
        "Technical documentation or developer portal",
        "Guides, examples, API references or navigation sidebar",
    ],
    "authentication": [
        "Standalone authentication interface",
        "Login, registration, password recovery or account access",
    ],
}


# ----------------------------------------------------------------
# LAYOUT SELECTION POLICY
# ----------------------------------------------------------------

LAYOUT_SELECTION = {
    "mode": "automatic",
    "allow_user_override": True,
    "preserve_explicit_user_choice": True,
    "fallback_layout": "app",
    "unknown_layout_behavior": "validate_then_fallback",
    "allow_custom_layout": True,
    "require_schema_for_app": True,
    "require_real_interactions": True,
    "require_responsive_design": True,
    "require_accessibility_checks": True,
}


# ----------------------------------------------------------------
# APPLICATION SHELL CONFIGURATION
# ----------------------------------------------------------------

APP_SHELL = {
    "navigation": [
        "sidebar",
        "topbar",
        "mobile_navigation",
    ],
    "common_components": [
        "Button",
        "Input",
        "Select",
        "Dialog",
        "Modal",
        "Dropdown",
        "Toast",
        "LoadingState",
        "EmptyState",
        "ErrorState",
        "Pagination",
        "ConfirmDialog",
    ],
    "required_states": [
        "loading",
        "success",
        "empty",
        "error",
    ],
    "features": [
        "responsive_navigation",
        "route_handling",
        "form_validation",
        "api_integration",
        "authentication_when_required",
        "authorization_when_required",
        "database_integration_when_required",
    ],
    "rules": [
        "Generate pages from validated project requirements.",
        "Use shared components instead of duplicating UI code.",
        "Generate real CRUD operations when requested.",
        "Connect forms to actual application actions.",
        "Keep frontend routes consistent with backend capabilities.",
        "Enforce authorization on the server.",
        "Never create fake buttons or placeholder navigation.",
        "Do not add authentication when the requirements do not need it.",
        "Do not invent database records or external API credentials.",
        "Validate generated files before writing them.",
    ],
}


KIND_LAYOUT = {
    "dashboard": "dashboard", "management": "app", "cms": "app", "portfolio": "portfolio",
    "ecommerce": "ecommerce", "chat": "community", "social": "community",
    "chatbot": "saas", "site": "business", "landing": "landing",
}
APP_INTENT = re.compile(r"\b(app|application|web app|todo|to-do|task manager|notes? app|note[- ]taking|tracker|planner|record manager|crud|admin panel|management system|crm|inventory|booking system|student portal|attendance|budget app|expense tracker|content management|calculator)\b", re.I)


def layout_for(brief: str, kind: str | None = None) -> str:
    """Choose a real app shell for data-management apps; use section layouts for marketing pages.
    Intent rules are shared with Autopilot (backend.agent.intent) so both paths agree."""
    from backend.stack.analyze import split_style
    user_text, style = split_style(brief)
    s = user_text.lower()
    # Explicit landing-page language wins over the richer multi-page layout; otherwise
    # honor the rule-based domain classifier instead of silently falling back to landing.
    if intent.MARKETING_PROMPT.search(s):
        return "portfolio" if "portfolio" in s else "landing"
    if kind == "portfolio" or style == "interactive portfolio":
        return "portfolio"
    if re.search(r"\b(?:login|log[ -]?in|sign[ -]?in|sign[ -]?up|registration|register|forgot password|reset password)\s+(?:page|screen|form|ui|interface)\b", s):
        return "authentication"
    if "portfolio" in s and not intent.is_app_prompt(s, allow_dashboard=False):
        return "portfolio"
    if kind in ("management", "cms"):
        return "app"
    if kind == "dashboard" or "analytics" in s or style == "analytics dashboard":
        return "dashboard"
    if kind in KIND_LAYOUT and kind not in ("generic", "local"):
        return KIND_LAYOUT[kind]
    if style == "e-commerce storefront" or re.search(r"\b(storefront|online store|online shop|e-?commerce)\b", s):
        return "ecommerce"
    if re.search(r"\b(api documentation|developer documentation|documentation site|docs portal|api reference)\b", s):
        return "documentation"
    if re.search(r"\b(blog|magazine|news site|article publishing)\b", s):
        return "blog"
    if re.search(r"\b(online course|course platform|learning platform|e-learning)\b", s):
        return "education"
    if re.search(r"\b(community site|forum|member community|social network)\b", s):
        return "community"
    if kind in ("local", "generic") and intent.is_app_prompt(s, allow_dashboard=False):
        return "app"
    return "landing"


_STYLE_LABELS = {"premium saas", "cinematic dark", "anime streaming platform", "e-commerce storefront", "interactive portfolio",
                 "analytics dashboard", "editorial", "creative agency", "futuristic interface", "glassmorphism", "product landing page"}
_BRAND_JUNK = {"", "brand", "your brand", "brand name", "company", "app", "workspace", "my app", "untitled"}
_FILLER = {"build", "create", "make", "design", "generate", "me", "a", "an", "the", "my", "our", "simple", "modern", "new", "and", "for", "with",
           "app", "application", "website", "site", "web", "page", "please", "i", "want", "need", "to", "that", "of", "in", "using"}


def brand_for(raw, brief: str) -> str:
    """Brand shown in the generated app. Small models often echo the design-style label ("Premium SaaS") or a placeholder;
    in that case derive a name from the user's own words."""
    from backend.stack.analyze import split_style
    name = re.sub(r"\s+", " ", str(raw or "")).strip().strip("\"'")[:30]
    if name.lower() not in _STYLE_LABELS and name.lower() not in _BRAND_JUNK and "style" not in name.lower():
        return name
    user_text, _ = split_style(brief or "")
    words = [w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9&'-]*", user_text) if w.lower() not in _FILLER][:3]
    return (" ".join(w.capitalize() for w in words) or "Workspace")[:30]


def _ids(raw, layout: str = "landing") -> list[str]:
    allowed, fallback = LAYOUTS[layout]
    out = []
    for s in raw if isinstance(raw, list) else []:
        s = re.sub(r"[^a-z0-9-]", "", str(s).lower())[:20]
        if s in allowed and s not in out:
            out.append(s)
    out.sort(key=allowed.index)                        # keep canonical page order
    return out[:MAX_SECTIONS] if len(out) >= 2 else fallback


def blueprint(state) -> dict:
    """1 cheap call -> plan + design + motion. Returns token usage."""
    kind = (state.spec_digest.split(" | ")[0].removeprefix("kind=") if state.spec_digest else None)
    autopilot = (state.stack_config or {}).get("autopilot") or {}
    state.layout = "app" if autopilot.get("app_shell") else layout_for(state.brief, kind)
    allowed = LAYOUTS[state.layout][0]
    # Blueprint is the single prompt-analysis call: pass the whole accepted brief so
    # late-listed constraints are considered before section generation starts.
    user = (f"ORIGINAL USER PROMPT (read all of it; maximum 6000 characters):\n{state.brief[:6000]}"
            f"\nLAYOUT: {state.layout}\nALLOWED SECTIONS (choose only from this list): {','.join(allowed)}"
            f"\nSELECTED STACK / TOOLS: UI={state.stack}; config={str(state.stack_config or {})[:650]}")
    if state.spec_digest:
        user += f"\nRULE-BASED APP SPEC SUMMARY: {state.spec_digest[:350]}"
    ctx = task_memory.context(state.project_id, 350)       # small repo map for continuing projects
    if ctx:
        user += f"\nEXISTING PROJECT CONTEXT (preserve compatible conventions):\n{ctx}"
    data, usage = llm.call_json("blueprint", prompts.BLUEPRINT, user,
                                None, 900 if state.layout == "app" else 1350, schema=schemas.BlueprintOut)
    chosen_sections = _ids(data.get("sections"), state.layout)
    page_blueprint = data.get("pages") if isinstance(data.get("pages"), list) else []
    components = [str(x).strip()[:80] for x in data.get("components", [])
                  if isinstance(x, str) and x.strip()][:16]
    features = [str(x).strip()[:140] for x in data.get("features", [])
                if isinstance(x, str) and x.strip()][:20]
    architecture = data.get("architecture") if isinstance(data.get("architecture"), dict) else {}
    state.plan = {"stack": state.stack, "layout": state.layout, "brand": brand_for(data.get("brand"), state.brief),
                  "sections": chosen_sections, "pages": ["index"], "page_blueprint": page_blueprint[:8],
                  "components": components, "features": features, "architecture": architecture,
                  "blueprint_notes": str(data.get("notes", ""))[:500],
                  "model_stack": str(data.get("stack", ""))[:100]}
    state.design = design_engine.normalize(data.get("design"))
    state.motion = animation_engine.normalize(data.get("motion"))
    return usage
