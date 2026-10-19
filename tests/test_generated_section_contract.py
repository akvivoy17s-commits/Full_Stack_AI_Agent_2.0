from pathlib import Path
from types import SimpleNamespace

from backend.agent import prompt_context
from backend.engines import html2jsx, react_engine


class FakeProjectFiles:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def write(self, rel: str, content: str):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")


def _state():
    return SimpleNamespace(
        plan={
            "brand": "Shop Admin",
            "layout": "dashboard",
            "stack": "react",
            "sections": ["kpis", "charts", "table", "activity"],
            "features": ["Order tracking", "Inventory summary"],
            "components": [],
            "page_blueprint": [],
        },
        design={"colors": {}, "fonts": {}},
        motion={},
        stack_config={"frontend": "React + TypeScript"},
        brief="Build an ecommerce admin dashboard for orders and inventory.",
        sections_done=["overview"],
    )


def test_html2jsx_maps_unregistered_component_tags_to_safe_html_elements():
    source = (
        '<section><HeroBanner title="Shop" />'
        '<ProductCardList products="{featuredProducts}"><b>Products</b></ProductCardList>'
        '<CategoryList categories="{categories}"></CategoryList></section>'
    )
    result = html2jsx.convert(source)
    assert "<HeroBanner" not in result
    assert "<ProductCardList" not in result
    assert "<CategoryList" not in result
    assert 'data-generated-tag="herobanner"' in result
    assert 'data-generated-tag="productcardlist"' in result
    assert "ProductCardList" not in result


def test_kpi_section_with_react_component_syntax_uses_deterministic_html_fallback(tmp_path):
    pf = FakeProjectFiles(tmp_path)
    state = _state()
    broken_fragment = (
        '<section id="kpis"><HeroBanner />'
        '<ProductCardList products={featuredProducts} />'
        '<CategoryList categories={categories} />'
        '</section>'
    )

    react_engine.insert(pf, state, "kpis", broken_fragment, ".stale{color:red}")

    saved_html = pf.read(".agent/parts/kpis.html")
    saved_tsx = pf.read("src/sections/Kpis.tsx")
    assert "Key performance indicators" in saved_html
    assert "Total sales" in saved_html and "Awaiting live data" in saved_html
    assert "HeroBanner" not in saved_html
    assert "ProductCardList" not in saved_html
    assert "featuredProducts" not in saved_tsx
    assert "CategoryList" not in saved_tsx
    assert "productcardlist" not in saved_tsx
    assert "safe-kpi-grid" in saved_tsx


def test_prompt_context_requires_html_not_raw_react_jsx():
    context = prompt_context.section_user_context(_state(), "kpis", "KPI metric cards")
    assert "STRICT FRAGMENT CONTRACT" in context
    assert "KPI-ONLY SCOPE" in context
    assert "Do not emit HeroBanner" in context


def test_html_only_component_contract_detection():
    assert react_engine._looks_like_raw_jsx('<section><ProductCardList /></section>')
    assert react_engine._looks_like_raw_jsx('<div>{featuredProducts}</div>')
    assert not react_engine._looks_like_raw_jsx('<section><article><h2>Orders</h2></article></section>')
