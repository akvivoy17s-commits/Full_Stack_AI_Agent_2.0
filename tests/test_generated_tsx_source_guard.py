from pathlib import Path
from types import SimpleNamespace

from backend.agent import selfrepair
from backend.engines import react_engine


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
        plan={"brand": "Shop Admin", "layout": "dashboard", "stack": "react", "sections": ["kpis"]},
        design={"colors": {}, "fonts": {}}, motion={}, sections_done=["kpis"],
    )


def test_unknown_lowercase_component_and_unknown_variables_are_rejected():
    broken = '<section><productcardlist products={featuredProducts}></productcardlist>{categories}</section>'
    assert react_engine._looks_like_raw_jsx(broken)


def test_plain_prose_curly_braces_are_not_treated_as_raw_jsx():
    assert not react_engine._looks_like_raw_jsx('<section><p>Braces are { text } in this explanation.</p></section>')


def test_generated_section_tsx_is_restored_from_canonical_html_css(tmp_path):
    pf = FakeProjectFiles(tmp_path)
    state = _state()
    good = '<section id="kpis"><h2>Key performance indicators</h2><article><strong>—</strong><span>Awaiting live data</span></article></section>'
    react_engine.insert(pf, state, "kpis", good, ".kpis{display:grid}")
    corrupted = (
        "import React from 'react';\n"
        "export default function Kpis(){ return <section><HeroBanner />"
        "<productcardlist>{featuredProducts}</productcardlist>{categories}</section> }\n"
    )
    pf.write("src/sections/Kpis.tsx", corrupted)

    restored = react_engine.restore_generated_sections_from_diagnostics(
        pf, state,
        "src/sections/Kpis.tsx(6,50): error TS2304: Cannot find name 'HeroBanner'.\n"
        "src/sections/Kpis.tsx(6,125): error TS2304: Cannot find name 'featuredProducts'.",
    )

    assert restored == ["src/sections/Kpis.tsx"]
    output = pf.read("src/sections/Kpis.tsx")
    assert "HeroBanner" not in output
    assert "featuredProducts" not in output
    assert "categories" not in output
    assert "Key performance indicators" in output


def test_file_selfrepair_protects_generated_section_components():
    assert selfrepair.PROTECTED.search("src/sections/Kpis.tsx")
    assert not selfrepair.PROTECTED.search("src/pages/Checkout.tsx")


def test_uppercase_standard_html_tags_are_not_mistaken_for_react_components():
    assert not react_engine._looks_like_raw_jsx('<SECTION><H2>Orders</H2><DIV>Summary</DIV></SECTION>')


def test_reconcile_restores_llm_corrupted_derived_tsx_from_canonical_html(tmp_path):
    pf = FakeProjectFiles(tmp_path)
    state = _state()
    canonical = (
        '<section id="kpis" class="metrics"><h2>Store metrics</h2>'
        '<article><span>Orders</span><strong>—</strong></article></section>'
    )
    react_engine.insert(pf, state, "kpis", canonical, ".metrics{display:grid}")
    pf.write(
        "src/sections/Kpis.tsx",
        "export default function Kpis(){ return <section><HeroBanner />"
        "<productcardlist products={featuredProducts} />{categories}</section> }",
    )

    changed = react_engine.reconcile_derived_outputs(pf, state)
    result = pf.read("src/sections/Kpis.tsx")

    assert "src/sections/Kpis.tsx" in changed
    assert "HeroBanner" not in result
    assert "featuredProducts" not in result
    assert "categories" not in result
    assert "Store metrics" in result


def test_reconcile_persists_safe_fallback_when_canonical_html_contains_react_expressions(tmp_path):
    pf = FakeProjectFiles(tmp_path)
    state = _state()
    pf.write(".agent/parts/kpis.html", (
        '<section id="kpis"><HeroBanner />'
        '<ProductCardList products={featuredProducts} />'
        '<CategoryList categories={categories} /></section>'
    ))
    pf.write(".agent/parts/kpis.css", ".bad{color:red}")
    pf.write("src/sections/Kpis.tsx", "// stale/invalid output")
    pf.write("src/sections/kpis.css", "// stale CSS")

    changed = react_engine.reconcile_derived_outputs(pf, state)

    saved_html = pf.read(".agent/parts/kpis.html")
    saved_tsx = pf.read("src/sections/Kpis.tsx")
    assert "HeroBanner" not in saved_html
    assert "ProductCardList" not in saved_html
    assert "featuredProducts" not in saved_tsx
    assert "categories" not in saved_tsx
    assert "safe-kpi-grid" in saved_html
    assert "src/sections/Kpis.tsx" in changed
    assert "src/sections/kpis.css" in changed


def test_reconcile_is_idempotent_for_valid_canonical_section(tmp_path):
    pf = FakeProjectFiles(tmp_path)
    state = _state()
    react_engine.insert(
        pf, state, "kpis",
        '<section id="kpis"><h2>Orders</h2><article><strong>—</strong></article></section>',
        ".kpis{display:grid}",
    )

    assert react_engine.reconcile_derived_outputs(pf, state) == []


def test_react_build_reconciles_derived_tsx_before_invoking_typescript(monkeypatch, tmp_path):
    pf = FakeProjectFiles(tmp_path)
    state = _state()
    react_engine.insert(
        pf, state, "kpis",
        '<section id="kpis"><h2>Orders</h2><article><strong>—</strong></article></section>',
        ".kpis{display:grid}",
    )
    pf.write(
        "src/sections/Kpis.tsx",
        "export default function Kpis(){ return <section><HeroBanner />{featuredProducts}</section> }",
    )
    (tmp_path / "node_modules" / "vite").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(react_engine.shutil, "which", lambda name: "/fake/node" if name in {"node", "npm"} else None)
    observed = []

    def fake_run(args, cwd, timeout=0, max_out=0):
        observed.append((list(args), pf.read("src/sections/Kpis.tsx")))
        return {"code": 0, "out": "vite build succeeded"}

    monkeypatch.setattr(react_engine.terminal, "run", fake_run)
    result = react_engine.build(pf, state)

    assert result["built"] is True
    assert observed and observed[0][0] == ["npm", "run", "build"]
    assert "HeroBanner" not in observed[0][1]
    assert "featuredProducts" not in observed[0][1]


def test_section_source_fingerprint_is_stable_and_changes_with_canonical_source(tmp_path):
    from backend.agent.orchestrator import _section_source_fingerprint

    pf = FakeProjectFiles(tmp_path)
    state = _state()
    react_engine.insert(pf, state, "kpis", '<section id="kpis"><h2>Orders</h2></section>', ".kpis{display:grid}")
    first = _section_source_fingerprint(pf, state, "kpis")
    assert first == _section_source_fingerprint(pf, state, "kpis")
    pf.write(".agent/parts/kpis.html", '<section id="kpis"><h2>Revenue</h2></section>')
    assert first != _section_source_fingerprint(pf, state, "kpis")
