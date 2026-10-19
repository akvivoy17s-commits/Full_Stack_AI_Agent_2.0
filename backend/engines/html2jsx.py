"""Deterministic HTML -> JSX conversion (zero LLM tokens). Generated section HTML stays the model's output format;
React components are derived from it, so repairs/edits keep working on small HTML patches."""
import json
import re
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
# The section generator returns HTML fragments, not arbitrary React components. Keep an explicit
# allow-list so a hallucinated tag such as <ProductCardList> cannot become an invalid JSX intrinsic.
HTML_TAGS = set((
    "a abbr address area article aside audio b base bdi bdo blockquote body br button canvas caption cite code col colgroup data datalist dd del details dfn dialog div dl dt em embed fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 head header hgroup hr html i iframe img input ins kbd label legend li link main map mark menu meta meter nav noscript object ol optgroup option output p picture pre progress q rp rt ruby s samp script search section select slot small source span strong style sub summary sup table tbody td template textarea tfoot th thead time title tr track u ul var video wbr svg math"
).split())
SVG_TAGS = {t.lower(): t for t in ("linearGradient", "radialGradient", "clipPath", "feGaussianBlur", "feColorMatrix", "feOffset", "feBlend",
                                   "feMerge", "feMergeNode", "feFlood", "feComposite", "textPath", "foreignObject", "animateTransform", "animateMotion")}
SVG_ELEMENTS = set((
    "svg g defs symbol use path rect circle ellipse line polyline polygon text tspan title desc metadata clippath mask pattern marker lineargradient radialgradient stop filter feblend fecolormatrix fecomponenttransfer fecomposite feconvolvematrix fediffuselighting fedisplacementmap fedistantlight fedropshadow feflood fefunca fefuncb fefuncg fefuncr fegaussianblur feimage femerge femergenode femorphology feoffset fepointlight fespecularlighting fespotlight fetile feturbulence foreignobject textpath animatemotion animatetransform animate set view"
).split())
SAFE_UNKNOWN_ATTRS = {"id", "class", "style", "title", "role", "lang", "dir", "hidden", "tabindex", "slot"}
ATTR = {"class": "className", "classname": "className", "for": "htmlFor", "htmlfor": "htmlFor", "tabindex": "tabIndex", "colspan": "colSpan", "rowspan": "rowSpan", "readonly": "readOnly",
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
        self.out: list[str] = []
        # (source tag, rendered tag) pairs let unsupported components be rendered safely as divs
        # while still matching the original closing tag from the fragment.
        self.stack: list[tuple[str, str]] = []
        self.raw = None

    def _is_known_tag(self, tag: str) -> bool:
        return tag.lower() in HTML_TAGS or tag.lower() in SVG_ELEMENTS

    def _tag(self, t: str) -> str:
        low = t.lower()
        if low in HTML_TAGS:
            return low
        if low in SVG_ELEMENTS:
            return SVG_TAGS.get(low, low)
        # Unknown React component names/custom tags are not valid in generated HTML fragments.
        return "div"

    def _safe_attrs(self, tag: str, attrs):
        if self._is_known_tag(tag):
            return attrs
        safe = [(k, v) for k, v in attrs if k.lower() in SAFE_UNKNOWN_ATTRS or
                k.lower().startswith(("aria-", "data-"))]
        if not any(k.lower() == "data-generated-tag" for k, _ in safe):
            safe.append(("data-generated-tag", tag.lower()[:64]))
        return safe

    def handle_starttag(self, tag, attrs):
        out_tag = self._tag(tag)
        safe_attrs = self._safe_attrs(tag, attrs)
        if tag.lower() == "style":
            self.raw = []
        self.out.append(f"<{out_tag}{_attrs(safe_attrs, out_tag)}" + (" />" if out_tag in VOID else ">"))
        if out_tag not in VOID:
            self.stack.append((tag, out_tag))

    def handle_startendtag(self, tag, attrs):
        out_tag = self._tag(tag)
        safe_attrs = self._safe_attrs(tag, attrs)
        self.out.append(f"<{out_tag}{_attrs(safe_attrs, out_tag)} />")

    def handle_endtag(self, tag):
        if tag.lower() in VOID:
            return
        if tag.lower() == "style" and self.raw is not None:
            css = "".join(self.raw).replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
            self.out.append("{`" + css + "`}")
            self.raw = None
        if any(source_tag == tag for source_tag, _ in self.stack):
            # Close intervening malformed elements before closing the requested source element.
            while self.stack and self.stack[-1][0] != tag:
                _source_tag, rendered_tag = self.stack.pop()
                self.out.append(f"</{rendered_tag}>")
            _source_tag, rendered_tag = self.stack.pop()
            self.out.append(f"</{rendered_tag}>")

    def handle_data(self, data):
        if self.raw is not None:
            self.raw.append(data)
        elif data.strip():
            self.out.append(_text(data.strip("\n")) if "\n" in data else _text(data))
        elif data and "\n" not in data:
            self.out.append("{' '}")

    def result(self) -> str:
        while self.stack:
            _source_tag, rendered_tag = self.stack.pop()
            self.out.append(f"</{rendered_tag}>")
        return "".join(self.out)


def convert(html: str) -> str:
    p = _J()
    p.feed(re.sub(r"<!--.*?-->", "", html, flags=re.S))
    p.close()
    return p.result()
