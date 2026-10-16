"""Design-system engine: validates LLM design tokens and renders a complete, accessible token layer locally.

No LLM tokens are spent here and nothing from the model is ever pasted into CSS unchecked. From 5 colours, 2 fonts,
a radius and a spacing unit it derives what a senior product designer would hand over: AA-checked text colours,
surfaces/borders/focus ring, status colours, hover states, a fluid type scale, a spacing + radius scale, shadows,
z-index layers and safe Google-Font loading (curated families + real weights + fallback stacks).
"""
import re
from html import escape

DEFAULT = {"colors": {"bg": "#0b0b14", "fg": "#f5f5ff", "primary": "#7c5cff", "accent": "#00d4ff", "muted": "#9a9ab5"},
           "fonts": {"head": "Poppins", "body": "Inter"}}
HEX = re.compile(r"^#[0-9a-fA-F]{3,8}$")
FONT = re.compile(r"^[A-Za-z0-9 ]{2,30}$")

# ---------------------------------------------------------------------------------------------------------------
# Fonts. A single unknown family or an unsupported weight makes the whole Google Fonts request fail (HTTP 400), so
# only curated families are accepted and only the weights each family really ships are requested.
# ---------------------------------------------------------------------------------------------------------------
FULL = (400, 500, 600, 700)
_CATALOG = {
    "sans": {
        **{n: FULL for n in (
            "Inter", "Poppins", "Manrope", "DM Sans", "Plus Jakarta Sans", "Outfit", "Sora", "Space Grotesk",
            "Montserrat", "Raleway", "Nunito", "Nunito Sans", "Work Sans", "Rubik", "Open Sans", "Source Sans 3",
            "Figtree", "Urbanist", "Lexend", "Albert Sans", "Be Vietnam Pro", "Mulish", "Karla", "Barlow", "Cabin",
            "IBM Plex Sans", "Public Sans", "Red Hat Display", "Syne", "Epilogue", "Jost", "Quicksand", "Archivo",
            "Onest", "Geist", "Bricolage Grotesque", "Unbounded", "Oswald")},
        "Lato": (400, 700), "Roboto": (400, 500, 700),
    },
    "serif": {
        **{n: FULL for n in ("Playfair Display", "Lora", "Cormorant Garamond", "Fraunces", "Source Serif 4",
                              "Crimson Pro", "EB Garamond")},
        "Merriweather": (400, 700), "Libre Baskerville": (400, 700), "PT Serif": (400, 700),
        "DM Serif Display": (400,), "Instrument Serif": (400,),
    },
    "mono": {
        "JetBrains Mono": FULL, "Fira Code": FULL, "IBM Plex Mono": FULL,
        "Space Mono": (400, 700), "DM Mono": (400, 500),
    },
    "display": {n: (400,) for n in ("Bebas Neue", "Anton", "Abril Fatface", "Righteous", "Archivo Black", "Lobster",
                                    "Pacifico")},
}
_LOOKUP = {name.lower(): (name, cat, w) for cat, fonts in _CATALOG.items() for name, w in fonts.items()}
_STACK = {
    "sans": "system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif",
    "display": "system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif",
    "serif": "Georgia,'Times New Roman',Times,serif",
    "mono": "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace",
}


def _font(name, role: str) -> str:
    """Return the canonical catalogue name, or the role default when the family is unknown/unsafe."""
    if isinstance(name, str) and FONT.match(name):
        hit = _LOOKUP.get(" ".join(name.lower().split()))
        if hit:
            return hit[0]
    return DEFAULT["fonts"][role]


def _info(name: str):
    return _LOOKUP.get(name.lower()) or _LOOKUP[DEFAULT["fonts"]["body"].lower()]


# ---------------------------------------------------------------------------------------------------------------
# Colour maths (WCAG 2.x)
# ---------------------------------------------------------------------------------------------------------------
def _num(v, lo, hi, d):
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        return d


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(c) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(x))) for x in c)


def _lum(c) -> float:
    f = lambda v: (v / 255 / 12.92) if v / 255 <= 0.03928 else (((v / 255) + 0.055) / 1.055) ** 2.4    # noqa: E731
    r, g, b = (f(x) for x in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _mix(a, b, t: float) -> tuple:
    """Linear blend: t=0 -> a, t=1 -> b."""
    return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))


def _toward(c, target, need, against) -> tuple:
    """Move colour c toward target in small steps until it reaches `need` contrast against `against`."""
    for i in range(1, 21):
        t = i / 20
        n = tuple(c[k] + (target[k] - c[k]) * t for k in range(3))
        if contrast(n, against) >= need:
            return n
    return target


SAFE_PRIMARY = "#4f46e5"       # 6.3:1 with the white button label, still visible on light and dark backgrounds
WHITE, BLACK = (255, 255, 255), (0, 0, 0)


def _readable(colors: dict) -> dict:
    """The app shell draws button/brand-mark labels in white and uses accent/muted as text, so LLM palettes that are
    too pale (white button on a white page, invisible borders) are corrected instead of shipped.
    Targets: fg 4.5:1, muted 4.5:1 (AA body text), accent 3:1 (large text / graphics), primary 4:1 with white."""
    bg = _rgb(colors["bg"])
    out = dict(colors)
    fg = _rgb(colors["fg"])
    if contrast(fg, bg) < 4.5:
        fg = WHITE if contrast(WHITE, bg) >= contrast(BLACK, bg) else BLACK
        out["fg"] = _hex(fg)
    pr = _rgb(colors["primary"])
    if contrast(pr, WHITE) < 4.0:
        pr = _toward(pr, BLACK, 4.0, WHITE)
    if contrast(pr, bg) < 1.5:
        pr = _rgb(SAFE_PRIMARY)
    out["primary"] = _hex(pr)
    away = BLACK if _lum(bg) > 0.5 else WHITE                        # direction that increases contrast with the page
    for k, need in (("accent", 3.0), ("muted", 4.5)):
        c = _rgb(colors[k])
        if contrast(c, bg) < need:
            c = _toward(c, away, need, bg)
        out[k] = _hex(c)
    return out


def normalize(d) -> dict:
    d = d if isinstance(d, dict) else {}
    out = {"colors": {}, "fonts": {}}
    for k, dv in DEFAULT["colors"].items():
        v = (d.get("colors") or {}).get(k)
        out["colors"][k] = v if isinstance(v, str) and HEX.match(v) and len(v) in (4, 5, 7, 9) else dv
    out["colors"] = _readable(out["colors"])
    for k in DEFAULT["fonts"]:
        out["fonts"][k] = _font((d.get("fonts") or {}).get(k), k)
    out["radius"] = _num(d.get("radius"), 0, 40, 16)
    out["spacing"] = _num(d.get("spacing"), 4, 12, 8)
    out["style"] = re.sub(r"[^\w\s,.&/+-]", "", str(d.get("style", "")))[:60].strip()
    out["mode"] = "dark" if _lum(_rgb(out["colors"]["bg"])) < 0.179 else "light"
    return out


# ---------------------------------------------------------------------------------------------------------------
# Token rendering
# ---------------------------------------------------------------------------------------------------------------
def _derived(d: dict) -> dict:
    """Every colour the generated UI needs beyond the 5 base colours, all contrast-checked against the page."""
    c = {k: _rgb(v) for k, v in d["colors"].items()}
    bg, fg, pr, ac = c["bg"], c["fg"], c["primary"], c["accent"]
    dark = d["mode"] == "dark"
    away = WHITE if dark else BLACK
    on_pr = WHITE if contrast(WHITE, pr) >= 4.0 or contrast(WHITE, pr) >= contrast(BLACK, pr) else BLACK
    # darken a white-labelled button on hover (keeps the label readable), lighten a black-labelled one
    hover = _mix(pr, BLACK if on_pr == WHITE else WHITE, 0.14)
    status = ({"success": (52, 211, 153), "warning": (251, 191, 36), "danger": (248, 113, 113)} if dark else
              {"success": (21, 128, 61), "warning": (180, 83, 9), "danger": (185, 28, 28)})
    out = {
        "surface": _mix(bg, fg, 0.05), "surface-2": _mix(bg, fg, 0.09),
        "border": _mix(bg, fg, 0.14), "border-strong": _mix(bg, fg, 0.28),
        "primary-hover": hover, "on-primary": on_pr,
        "primary-soft": _mix(bg, pr, 0.14), "accent-soft": _mix(bg, ac, 0.14),
        "accent-text": _toward(ac, away, 4.5, bg) if contrast(ac, bg) < 4.5 else ac,     # accent used as small text
        "link": _toward(pr, away, 4.5, bg) if contrast(pr, bg) < 4.5 else pr,
        "ring": _toward(pr, away, 3.0, bg) if contrast(pr, bg) < 3.0 else pr,           # focus ring, WCAG 1.4.11
    }
    for k, v in status.items():
        out[k] = _toward(v, away, 4.5, bg) if contrast(v, bg) < 4.5 else v
    return out


def render_tokens(d) -> str:
    d = normalize(d)
    dark = d["mode"] == "dark"
    sp, r = d["spacing"], d["radius"]
    pr = _rgb(d["colors"]["primary"])
    fh, fb = _info(d["fonts"]["head"]), _info(d["fonts"]["body"])
    v = {f"--{k}": val for k, val in d["colors"].items()}
    v.update({f"--{k}": _hex(val) for k, val in _derived(d).items()})
    v["--grad"] = "linear-gradient(135deg,var(--primary),var(--accent))"
    v["--font-head"] = f"'{fh[0]}',{_STACK[fh[1]]}"
    v["--font-body"] = f"'{fb[0]}',{_STACK[fb[1]]}"
    v["--font-mono"] = _STACK["mono"]
    # fluid type scale: readable on a 320px phone, expressive on a 1440px desktop, no breakpoints needed
    v.update({
        "--fs-xs": "clamp(.75rem,.73rem + .1vw,.8125rem)", "--fs-sm": ".875rem", "--fs-base": "1rem",
        "--fs-md": "clamp(1.0625rem,1rem + .3vw,1.1875rem)", "--fs-lg": "clamp(1.25rem,1.1rem + .7vw,1.5rem)",
        "--fs-xl": "clamp(1.5rem,1.2rem + 1.4vw,2rem)", "--fs-2xl": "clamp(1.875rem,1.4rem + 2.2vw,2.75rem)",
        "--fs-3xl": "clamp(2.25rem,1.5rem + 3.6vw,3.75rem)", "--fs-4xl": "clamp(2.75rem,1.6rem + 5.4vw,5rem)",
        "--lh-tight": "1.15", "--lh-snug": "1.3", "--lh-body": "1.6",
        "--tracking-tight": "-.02em", "--tracking-wide": ".08em",
    })
    # spacing + radius share one base unit so every component stays on the same grid
    v["--space"] = f"{sp}px"
    for i, m in enumerate((.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 16), 1):
        v[f"--space-{i}"] = f"{round(sp * m, 2):g}px"
    v["--radius"] = f"{r}px"
    v["--radius-sm"] = f"{max(2, round(r * .5)) if r else 0}px"
    v["--radius-lg"] = f"{min(48, round(r * 1.5))}px"
    v["--radius-xl"] = f"{min(64, round(r * 2))}px"
    v["--radius-pill"] = "999px"
    if dark:
        v.update({"--shadow-sm": "0 1px 2px rgba(0,0,0,.4)", "--shadow-md": "0 8px 24px rgba(0,0,0,.45)",
                  "--shadow-lg": "0 24px 64px rgba(0,0,0,.55)", "--overlay": "rgba(0,0,0,.6)"})
    else:
        v.update({"--shadow-sm": "0 1px 2px rgba(15,23,42,.08)", "--shadow-md": "0 8px 24px rgba(15,23,42,.10)",
                  "--shadow-lg": "0 24px 64px rgba(15,23,42,.16)", "--overlay": "rgba(15,23,42,.5)"})
    v["--shadow-glow"] = f"0 12px 40px rgba({pr[0]},{pr[1]},{pr[2]},.28)"
    v.update({"--container": "1200px", "--header-h": "64px", "--touch": "44px",
              "--z-nav": "50", "--z-overlay": "100", "--z-modal": "110", "--z-toast": "120",
              "--t-fast": ".15s ease", "--t-base": ".25s ease"})
    body = "".join(f"{k}:{val};" for k, val in v.items())
    return f":root{{color-scheme:{d['mode']};{body}}}\n"


def fonts_link(d) -> str:
    d = normalize(d)
    fams: dict[str, tuple] = {}
    for role in ("head", "body"):
        name, _cat, weights = _info(d["fonts"][role])
        fams[name] = tuple(sorted(set(fams.get(name, ())) | set(weights)))
    q = "&".join(f"family={n.replace(' ', '+')}:wght@{';'.join(map(str, w))}" for n, w in fams.items())
    return ('<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            f'<link rel="stylesheet" href="{escape("https://fonts.googleapis.com/css2?" + q + "&display=swap")}">')
