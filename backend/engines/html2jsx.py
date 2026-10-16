"""Deterministic HTML -> JSX conversion (zero LLM tokens). Generated section HTML stays the model's output format;
React components are derived from it, so repairs/edits keep working on small HTML patches."""
import json
import re
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SVG_TAGS = {t.lower(): t for t in ("linearGradient", "radialGradient", "clipPath", "feGaussianBlur", "feColorMatrix", "feOffset", "feBlend",
                                   "feMerge", "feMergeNode", "feFlood", "feComposite", "textPath", "foreignObject", "animateTransform", "animateMotion")}
ATTR = {"class": "className", "for": "htmlFor", "tabindex": "tabIndex", "colspan": "colSpan", "rowspan": "rowSpan", "readonly": "readOnly",
        "maxlength": "maxLength", "minlength": "minLength", "autocomplete": "autoComplete", "autofocus": "autoFocus", "crossorigin": "crossOrigin",
        "srcset": "srcSet", "playsinline": "playsInline", "contenteditable": "contentEditable", "spellcheck": "spellCheck",
        "enctype": "encType", "novalidate": "noValidate", "datetime": "dateTime", "frameborder": "frameBorder", "xlink:href": "href"}
CAMEL = ("viewBox preserveAspectRatio gradientUnits gradientTransform stdDeviation patternUnits patternTransform clipPathUnits maskUnits "
         "maskContentUnits markerWidth markerHeight refX refY startOffset spreadMethod filterUnits primitiveUnits baseFrequency numOctaves "
         "tableValues keyTimes keySplines repeatCount calcMode attributeName textLength lengthAdjust pathLength").split()
ATTR.update({a.lower(): a for a in CAMEL})
NUMERIC = {"tabIndex", "colSpan", "rowSpan", "maxLength", "minLength", "cols", "rows", "size", "span"}
BOOL = set("allowfullscreen async autofocus autoplay checked controls default defer disabled formnovalidate hidden loop multiple muted nomodule novalidate open playsinline readonly required reversed selected itemscope inert".split())
DROP = {"xmlns:xlink", "xml:space", "xmlns:svg"}


def _text(s: str) -> str:
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"[{}]", lambda m: "{'" + m.group() + "'}", s)


def _attr_name(n: str) -> str:
    if n in ATTR:
        return ATTR[n]
    if n.startswith(("data-", "aria-")):
        return n
    if "-" in n:                                          # stroke-width -> strokeWidth
        h, *r = n.split("-")
        return h + "".join(w.capitalize() for w in r)
    if ":" in n:
        h, r = n.split(":", 1)
        return h + r.capitalize()
    return n


def _style(v: str) -> str:
    items = []
    for decl in v.split(";"):
        if ":" not in decl:
            continue
        k, val = decl.split(":", 1)
        k, val = k.strip(), val.strip()
        if not k:
            continue
        key = k if k.startswith("--") else re.sub(r"-([a-z])", lambda m: m.group(1).upper(), k.lower())
        items.append(f"{json.dumps(key)}: {json.dumps(val)}")
    return "{{ " + ", ".join(items) + " } as React.CSSProperties}"


def _attrs(attrs, tag: str) -> str:
    out, extra = [], []
    for k, v in attrs:
        k = k.lower()
        if k in DROP or k.startswith("on"):
            continue
        if v is None and k not in BOOL and not k.startswith(("data-", "aria-")) and re.fullmatch(r"[a-z0-9_:\-]+", k):
            extra.append(k)                               # bare token like `lift` / `md:grid-cols-3` is a stray class, not a prop
            continue
        name = _attr_name(k)
        if tag in ("input", "textarea", "select") and name in ("value", "checked"):
            name = "default" + name.capitalize()
        if tag == "option" and name == "selected":
            continue
        if v is None:
            out.append(name)
        elif name == "style":
            out.append(f"style={_style(v)}")
        elif name in NUMERIC and v.strip().lstrip("-").isdigit():
            out.append(f"{name}={{{int(v)}}}")
        elif re.search(r'["&\\\n{}<>]', v):
            out.append(f"{name}={{{json.dumps(v)}}}")
        else:
            out.append(f'{name}="{v}"')
    if extra:
        i = next((n for n, o in enumerate(out) if o.startswith("className=")), None)
        if i is None:
            out.append(f'className="{" ".join(extra)}"')
        else:
            o = out[i]
            out[i] = (o[:-1] + " " + " ".join(extra) + '"') if o.endswith('"') and not o.startswith("className={") else \
                "className={" + json.dumps(json.loads(o[11:-1]) + " " + " ".join(extra)) + "}"
    return (" " + " ".join(out)) if out else ""


class _J(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.stack, self.raw = [], [], None

    def _tag(self, t: str) -> str:
        return SVG_TAGS.get(t, t)

    def handle_starttag(self, tag, attrs):
        if tag == "style":
            self.raw = []
        self.out.append(f"<{self._tag(tag)}{_attrs(attrs, tag)}" + (" />" if tag in VOID else ">"))
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.out.append(f"<{self._tag(tag)}{_attrs(attrs, tag)} />")

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "style" and self.raw is not None:
            css = "".join(self.raw).replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
            self.out.append("{`" + css + "`}")
            self.raw = None
        if tag in self.stack:
            while self.stack and self.stack[-1] != tag:     # close anything left open (model markup is not always clean)
                self.out.append(f"</{self._tag(self.stack.pop())}>")
            self.stack.pop()
            self.out.append(f"</{self._tag(tag)}>")

    def handle_data(self, data):
        if self.raw is not None:
            self.raw.append(data)
        elif data.strip():
            self.out.append(_text(data.strip("\n")) if "\n" in data else _text(data))
        elif data and "\n" not in data:
            self.out.append("{' '}")

    def result(self) -> str:
        while self.stack:
            self.out.append(f"</{self._tag(self.stack.pop())}>")
        return "".join(self.out)


def convert(html: str) -> str:
    p = _J()
    p.feed(re.sub(r"<!--.*?-->", "", html, flags=re.S))
    p.close()
    return p.result()
