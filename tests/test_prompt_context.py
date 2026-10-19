"""Regression tests for complete-prompt preservation across website planning and generation."""

from backend.agent import planner, prompts, schemas
from backend.agent.prompt_context import compact_requirements, section_user_context
from backend.agent.state import AgentState


def test_compact_requirements_keeps_late_explicit_constraints():
    prompt = (
        "Build a polished website for a creative studio. Audience: small businesses. "
        + "General background details about the business and its goals. " * 32
        + "Non-negotiable: use the exact colors #101820 and #FEE715, include a working contact form, "
        "make the layout mobile-first, and do not add a pricing section."
    )
    assert len(prompt) > 1900
    compacted = compact_requirements(prompt, 900)
    assert "#101820" in compacted
    assert "working contact form" in compacted
    assert "do not add a pricing section" in compacted


def test_section_context_includes_brief_plan_design_and_late_requirements():
    prompt = (
        "Build a website for an independent bookstore. "
        + "Background information that is less important to the final layout. " * 20
        + "Required: search books by title and author, show stock status, use forest green and cream, "
        "and the cart button must open a real cart panel."
    )
    state = AgentState(project_id="prompt-context-test", brief=prompt, stack="react", layout="ecommerce")
    state.plan = {
        "brand": "Leaf & Letter", "layout": "ecommerce", "stack": "react",
        "sections": ["hero", "categories", "products", "cta"],
        "components": ["BookSearch", "BookCard", "CartPanel"],
        "features": ["Search by title and author", "Show stock status", "Functional cart panel"],
        "page_blueprint": [{"name": "Shop", "sections": ["categories", "products"]}],
    }
    state.design = {"colors": {"bg": "#f5f0e6", "primary": "#18553a"}, "fonts": {"head": "DM Sans"}, "style": "editorial bookstore"}
    state.motion = {"hero": "fade-up", "scroll": "reveal", "hover": "lift", "lib": "css"}
    context = section_user_context(state, "products", "Product grid and search controls")
    assert "bookstore" in context.lower()
    assert "search books by title and author" in context.lower()
    assert "CartPanel" in context
    assert "#18553a" in context
    assert "CURRENT SECTION: products" in context


def test_blueprint_schema_keeps_prompt_analysis_and_motion_fields():
    data = schemas.BlueprintOut.model_validate({
        "brand": "Leaf & Letter", "stack": "react",
        "sections": ["hero", "products"],
        "pages": [{"name": "Shop", "sections": ["hero", "products"]}],
        "components": ["BookCard"], "features": ["Book search"],
        "architecture": {"frontend": "React", "backend": "none", "database": "none"},
        "design": {"style": "editorial"},
        "motion": {"hero": "fade-up", "scroll": "reveal", "hover": "lift", "lib": "css"},
    }).model_dump()
    assert data["features"] == ["Book search"]
    assert data["pages"][0]["name"] == "Shop"
    assert data["motion"]["hero"] == "fade-up"
    assert '"sections"' in prompts.BLUEPRINT


def test_blueprint_passes_entire_brief_and_persists_analysis(monkeypatch):
    prompt = "Create an online store. " + ("Use clean, concise product copy. " * 60) + "Late requirement: prioritize accessible filters and no autoplay video."
    captured = {}

    def fake_call_json(kind, system, user, model=None, max_tokens=None, schema=None, images=None):
        captured["kind"] = kind
        captured["user"] = user
        return ({
            "brand": "Store Studio", "stack": "react",
            "sections": ["hero", "categories", "products", "cta"],
            "pages": [{"name": "Store", "sections": ["hero", "products"]}],
            "components": ["ProductCard", "FilterBar"],
            "features": ["Accessible filters", "No autoplay video"],
            "architecture": {"frontend": "react", "backend": "none", "database": "none"},
            "design": {"colors": {"bg": "#111111", "fg": "#ffffff", "primary": "#116644", "accent": "#eedd99", "muted": "#aaaaaa"},
                       "fonts": {"head": "Inter", "body": "Inter"}, "style": "modern store"},
            "motion": {"hero": "fade-up", "scroll": "reveal", "hover": "lift", "lib": "css",
                       "duration_ms": [250, 700], "easing": "cubic-bezier(.22,1,.36,1)"},
            "notes": "Preserve accessible filters and no autoplay video.",
        }, {"in": 1, "out": 2})

    monkeypatch.setattr(planner.llm, "call_json", fake_call_json)
    monkeypatch.setattr(planner.task_memory, "context", lambda *_args, **_kwargs: "")
    state = AgentState(project_id="blueprint-prompt-test", brief=prompt, stack="react", spec_digest="kind=ecommerce")
    usage = planner.blueprint(state)
    assert captured["kind"] == "blueprint"
    assert "Late requirement: prioritize accessible filters and no autoplay video." in captured["user"]
    assert state.plan["layout"] == "ecommerce"
    assert state.plan["components"] == ["ProductCard", "FilterBar"]
    assert state.plan["features"] == ["Accessible filters", "No autoplay video"]
    assert state.motion["hero"] == "fade-up"
    assert usage == {"in": 1, "out": 2}


def test_prompt_type_selects_domain_specific_layouts():
    assert planner.layout_for("Build a responsive storefront for a candle brand", "ecommerce") == "ecommerce"
    assert planner.layout_for("Build a developer API documentation portal", "generic") == "documentation"
    assert planner.layout_for("Create a blog about indie games", "generic") == "blog"
    assert planner.layout_for("Create a landing page for a fitness app", "landing") == "landing"


def test_login_page_prompt_selects_standalone_auth_layout():
    assert planner.layout_for("Create a responsive login page with email, password and a forgot password link", "generic") == "authentication"


def test_authentication_scaffold_uses_standalone_layout():
    from backend.engines import code_engine, design_engine, animation_engine
    from backend.tools.project_files import ProjectFiles
    import shutil

    pid = "prompt-auth-layout-test"
    pf = ProjectFiles(pid)
    state = AgentState(project_id=pid, brief="Create a login page", stack="html", layout="authentication")
    state.plan = {"layout": "authentication", "stack": "html", "brand": "Sign In", "sections": ["login"]}
    state.design = design_engine.normalize({})
    state.motion = animation_engine.normalize({})
    try:
        code_engine.scaffold(pf, state)
        html = pf.read("index.html")
        css = pf.read("css/base.css")
        assert 'class="auth-layout"' in html
        assert "auth-layout" in css
        assert "<header class=\"nav\"" not in html
    finally:
        shutil.rmtree(pf.root, ignore_errors=True)


def test_authentication_react_app_omits_marketing_navigation():
    from backend.engines import react_engine, design_engine, animation_engine
    from backend.tools.project_files import ProjectFiles
    import shutil

    pid = "prompt-auth-react-layout-test"
    pf = ProjectFiles(pid)
    state = AgentState(project_id=pid, brief="Create a login page", stack="react", layout="authentication")
    state.plan = {"layout": "authentication", "stack": "react", "brand": "Sign In", "sections": ["login"]}
    state.design = design_engine.normalize({})
    state.motion = animation_engine.normalize({})
    try:
        react_engine.scaffold(pf, state)
        source = pf.read("src/App.tsx")
        assert 'className="auth-layout"' in source
        assert "import Nav from './components/Nav'" not in source
        assert "import Footer from './components/Footer'" not in source
    finally:
        shutil.rmtree(pf.root, ignore_errors=True)
