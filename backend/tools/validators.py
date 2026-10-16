"""Free (zero-token) static checks run before any LLM repair."""
import json
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class _Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []
        self.ids, self.duplicate_ids = set(), set()

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        value = attr_map.get("id")
        if value:
            if value in self.ids:
                self.duplicate_ids.add(value)
            self.ids.add(value)
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unexpected </{tag}>")
        else:
            self.stack.pop()


def _balanced(text: str, pairs: str = "{}()[]") -> bool:
    st, m = [], dict(zip(pairs[1::2], pairs[::2]))
    for ch in text:
        if ch in pairs[::2]:
            st.append(ch)
        elif ch in m:
            if not st or st.pop() != m[ch]:
                return False
    return not st


def validate_html(t: str) -> list[str]:
    p = _Tags()
    p.feed(t)
    errs = p.errors[:3] + ([f"unclosed <{p.stack[-1]}>"] if p.stack else [])
    errs += [f"duplicate id {value!r}" for value in sorted(p.duplicate_ids)[:3]]
    if "<html" in t.lower() and 'name="viewport"' not in t:
        errs.append("missing viewport meta")
    return errs


def validate_css(t: str) -> list[str]:
    errs = [] if _balanced(t, "{}") else ["unbalanced braces in CSS"]
    if ("animation" in t or "transition" in t) and "prefers-reduced-motion" not in t:
        errs.append("animations without prefers-reduced-motion")
    return errs


def validate_js(t: str) -> list[str]:
    return [] if _balanced(t) else ["unbalanced brackets in JS/TS"]


def validate_json(t: str) -> list[str]:
    try:
        json.loads(t)
        return []
    except ValueError as e:
        return [f"invalid JSON: {e}"]


def validate_file(path: str, text: str) -> list[str]:
    ext = path.rsplit(".", 1)[-1].lower()
    fn = {"html": validate_html, "css": validate_css, "json": validate_json,
          "js": validate_js, "jsx": validate_js, "ts": validate_js, "tsx": validate_js}.get(ext)
    return [f"{path}: {e}" for e in fn(text)] if fn else []
