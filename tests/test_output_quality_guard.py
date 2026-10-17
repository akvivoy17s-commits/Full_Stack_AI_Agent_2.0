from types import SimpleNamespace

from backend.engines import animation_engine, quality_engine


class FakeProjectFiles:
    def __init__(self, root):
        self.root = root

    def tree(self):
        return [
            str(p.relative_to(self.root)).replace("\\\\", "/")
            for p in self.root.rglob("*")
            if p.is_file()
        ]


def test_three_d_detection_is_explicit():
    assert animation_engine.wants_3d("Build an interactive 3D portfolio")
    assert animation_engine.wants_3d("Use Three.js and WebGL")
    assert not animation_engine.wants_3d("Build a clean portfolio with smooth animations")
    assert not animation_engine.wants_3d("Build a 3 day planner")


def test_quality_guard_detects_missing_assets_placeholders_and_dead_form(tmp_path):
    (tmp_path / "index.html").write_text(
        """<!doctype html><html><body>
        <!--SECTION:hero--><section id="hero"><h1>Developer Portfolio</h1></section><!--/SECTION:hero-->
        <!--SECTION:work--><section id="work"><img src="project1.svg"><p>Project 1</p></section><!--/SECTION:work-->
        <!--SECTION:contact--><section id="contact"><form><input name="email"><button>Send</button></form></section><!--/SECTION:contact-->
        </body></html>""",
        encoding="utf-8",
    )
    (tmp_path / "css").mkdir()
    (tmp_path / "css" / "style.css").write_text("body{color:#fff}", encoding="utf-8")
    state = SimpleNamespace(
        brief="Build a portfolio website",
        plan={"sections": ["hero", "work", "contact"], "stack": "html"},
    )
    issues = quality_engine.inspect(FakeProjectFiles(tmp_path), state)
    messages = [i["msg"] for i in issues]
    assert any("missing local asset" in m for m in messages)
    assert any("generic project placeholder" in m for m in messages)
    assert any("form has no real submission" in m for m in messages)
    assert any(i["sid"] == "work" for i in issues)


def test_three_d_quality_guard_requires_runtime_and_mount(tmp_path):
    (tmp_path / "index.html").write_text(
        '<!--SECTION:hero--><section id="hero"><h1>Portfolio</h1></section><!--/SECTION:hero-->',
        encoding="utf-8",
    )
    state = SimpleNamespace(
        brief="Build an interactive 3D portfolio",
        plan={"sections": ["hero"], "stack": "html"},
    )
    issues = quality_engine.inspect(FakeProjectFiles(tmp_path), state)
    messages = [i["msg"] for i in issues]
    assert any("three-hero.js runtime is missing" in m for m in messages)
    assert any("no Three.js mount point" in m for m in messages)


def test_react_public_assets_are_resolved_from_vite_public_directory(tmp_path):
    (tmp_path / "index.html").write_text(
        '<html><body><div id="root"></div><script type="module" src="/src/main.tsx"></script>'
        '<script type="module" src="/js/three-hero.js"></script></body></html>',
        encoding="utf-8",
    )
    (tmp_path / "src" / "sections").mkdir(parents=True)
    (tmp_path / "src" / "main.tsx").write_text("export {}", encoding="utf-8")
    (tmp_path / "src" / "sections" / "Hero.tsx").write_text(
        '<section id="hero" data-three-hero></section>', encoding="utf-8"
    )
    (tmp_path / "public" / "js").mkdir(parents=True)
    (tmp_path / "public" / "js" / "three-hero.js").write_text("export {}", encoding="utf-8")
    state = SimpleNamespace(
        brief="Build a 3D portfolio",
        plan={"sections": ["hero"], "stack": "react"},
    )
    issues = quality_engine.inspect(FakeProjectFiles(tmp_path), state)
    assert not any("missing local asset" in i["msg"] for i in issues)
    assert not any("Three.js mount point" in i["msg"] for i in issues)


def test_quality_guard_detects_real_portfolio_generation_mistakes(tmp_path):
    (tmp_path / "index.html").write_text(
        '''<!doctype html><html><body>
        <!--SECTION:hero--><section id="hero"><h1 data-three-hero>Developer Portfolio</h1></section><!--/SECTION:hero-->
        <!--SECTION:work--><section id="work"><div style="background-image:url('path/to/project1-cover.jpg')"></div>
        <h3>Project 1</h3><p>Outcome of Project 1</p><span>Tech 1</span></section><!--/SECTION:work-->
        <!--SECTION:contact--><section id="contact"><form action="https://formspree.io/your-email" method="POST"><button>Send</button></form>
        <a href="https://www.linkedin.com/in/yourname/" target="_blank">LinkedIn</a></section><!--/SECTION:contact-->
        </body></html>''',
        encoding="utf-8",
    )
    (tmp_path / "css").mkdir()
    (tmp_path / "css" / "sections.css").write_text(
        "#hero { padding: var(--space) * 2; margin: calc(var(--space) * 2); }",
        encoding="utf-8",
    )
    (tmp_path / "js").mkdir()
    (tmp_path / "js" / "three-hero.js").write_text("// runtime exists", encoding="utf-8")
    state = SimpleNamespace(
        brief="Build an interactive 3D portfolio website",
        plan={"sections": ["hero", "work", "contact"], "stack": "html"},
    )
    issues = quality_engine.inspect(FakeProjectFiles(tmp_path), state)
    messages = [issue["msg"] for issue in issues]
    assert any("missing local CSS asset" in message and "path/to/project1-cover.jpg" in message for message in messages)
    assert any("invalid CSS arithmetic" in message for message in messages)
    assert any("3D mount point is attached" in message for message in messages)
    assert any("placeholder endpoint" in message for message in messages)
    assert any("generic project placeholder" in message for message in messages)
    assert any("generic technology placeholder" in message for message in messages)
    assert any("external link opens a new tab" in message for message in messages)


def test_quality_guard_accepts_calc_and_safe_external_links(tmp_path):
    (tmp_path / "index.html").write_text(
        '<html><body><section id="hero"><h1>Build better software</h1>'
        '<a href="https://example.org/docs" target="_blank" rel="noopener noreferrer">Docs</a>'
        '<a href="#contact">Contact</a></section><section id="contact"></section></body></html>',
        encoding="utf-8",
    )
    (tmp_path / "css").mkdir()
    (tmp_path / "css" / "style.css").write_text(
        "#hero { padding: calc(var(--space) * 2); }", encoding="utf-8"
    )
    state = SimpleNamespace(brief="Build a landing page", plan={"sections": ["hero", "contact"], "stack": "html"})
    issues = quality_engine.inspect(FakeProjectFiles(tmp_path), state)
    messages = [issue["msg"] for issue in issues]
    assert not any("invalid CSS arithmetic" in message for message in messages)
    assert not any("external link opens a new tab" in message for message in messages)
    assert not any("internal link points to missing" in message for message in messages)
