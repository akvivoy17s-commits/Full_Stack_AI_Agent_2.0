from backend.engines import html2jsx, react_engine


def test_known_html_tags_work_when_legacy_converter_has_no_tag_exports(monkeypatch):
    monkeypatch.delattr(html2jsx, "HTML_TAGS", raising=False)
    monkeypatch.delattr(html2jsx, "SVG_ELEMENTS", raising=False)
    assert not react_engine._looks_like_raw_jsx(
        '<SECTION><H2>Orders</H2><div class="grid"><article><svg viewBox="0 0 10 10"><path d="M0 0" /></svg></article></div></SECTION>'
    )


def test_unknown_react_components_are_rejected_without_tag_exports(monkeypatch):
    monkeypatch.delattr(html2jsx, "HTML_TAGS", raising=False)
    monkeypatch.delattr(html2jsx, "SVG_ELEMENTS", raising=False)
    assert react_engine._looks_like_raw_jsx("<section><HeroBanner /><ProductCardList /></section>")


def test_custom_elements_remain_allowed_without_tag_exports(monkeypatch):
    monkeypatch.delattr(html2jsx, "HTML_TAGS", raising=False)
    monkeypatch.delattr(html2jsx, "SVG_ELEMENTS", raising=False)
    assert not react_engine._looks_like_raw_jsx('<section><my-product data-id="1"></my-product></section>')


def test_svg_tags_are_recognized_from_fallback_registry(monkeypatch):
    monkeypatch.delattr(html2jsx, "HTML_TAGS", raising=False)
    monkeypatch.delattr(html2jsx, "SVG_ELEMENTS", raising=False)
    assert not react_engine._looks_like_raw_jsx('<svg><linearGradient id="g"><stop offset="0%" /></linearGradient></svg>')


def test_known_tags_union_with_partial_legacy_exports(monkeypatch):
    monkeypatch.setattr(html2jsx, "HTML_TAGS", {"div", "section"}, raising=False)
    monkeypatch.setattr(html2jsx, "SVG_ELEMENTS", {"svg", "path"}, raising=False)
    assert not react_engine._looks_like_raw_jsx("<main><section><p>works</p></section></main>")
    assert react_engine._looks_like_raw_jsx("<main><SomeWidget /></main>")
