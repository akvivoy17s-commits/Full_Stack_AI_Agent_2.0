"""Deterministic accessibility audit executed inside the page (no network, no extra dependency).
Covers a useful SUBSET of WCAG 2.x: it does not replace manual / screen-reader testing, and it is NOT axe-core."""

A11Y_JS = r"""() => {
  const out = [];
  const sidOf = (e) => { const s = e.closest('main > [id]'); return s ? s.id : ''; };
  const add = (rule, el, msg) => out.push({ rule, sid: el ? sidOf(el) : '', msg });
  const shown = (e) => e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
  const txt = (e) => (e.textContent || '').trim();
  const nameOf = (e) => (e.getAttribute('aria-label') || '').trim()
    || (e.getAttribute('aria-labelledby') || '').split(/\s+/).map((i) => { const n = document.getElementById(i); return n ? txt(n) : ''; }).join('').trim()
    || txt(e) || (e.getAttribute('title') || '').trim()
    || (e.querySelector('img[alt]:not([alt=""])') ? 'img' : '') || (e.querySelector('svg title') ? 'svg' : '');

  const root = document.documentElement;
  if (!(root.getAttribute('lang') || '').trim()) add('lang', null, 'html element has no lang attribute');
  if (!txt(document.querySelector('title') || document.createElement('i'))) add('title', null, 'page has no <title>');
  if (!document.querySelector('main')) add('landmark', null, 'page has no <main> landmark');

  document.querySelectorAll('img').forEach((i) => {
    if (!i.hasAttribute('alt') && i.getAttribute('role') !== 'presentation' && i.getAttribute('aria-hidden') !== 'true') add('img-alt', i, 'image without alt text');
  });
  document.querySelectorAll('a[href],button,[role=button]').forEach((e) => {
    if (shown(e) && !nameOf(e)) add('name', e, `${e.tagName.toLowerCase()} without an accessible name`);
  });
  document.querySelectorAll('input,select,textarea').forEach((e) => {
    const t = (e.getAttribute('type') || '').toLowerCase();
    if (['hidden', 'submit', 'button', 'reset', 'image'].includes(t) || !shown(e)) return;
    const labelled = (e.id && document.querySelector(`label[for="${CSS.escape(e.id)}"]`)) || e.closest('label') || e.getAttribute('aria-label') || e.getAttribute('aria-labelledby');
    if (!labelled) add('label', e, `${e.tagName.toLowerCase()} field has no label`);
  });
  const ids = {};
  document.querySelectorAll('[id]').forEach((e) => { ids[e.id] = (ids[e.id] || 0) + 1; });
  Object.entries(ids).filter(([, n]) => n > 1).slice(0, 3).forEach(([id]) => add('dup-id', document.getElementById(id), `duplicate id "${id}"`));
  document.querySelectorAll('[tabindex]').forEach((e) => { if (parseInt(e.getAttribute('tabindex'), 10) > 0) add('tabindex', e, 'positive tabindex disturbs keyboard order'); });

  const hs = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(shown);
  const h1 = hs.filter((h) => h.tagName === 'H1').length;
  if (h1 !== 1) add('h1', h1 ? hs.find((h) => h.tagName === 'H1') : null, h1 ? `page has ${h1} <h1> elements (expected 1)` : 'page has no <h1>');
  for (let k = 1, prev = hs.length ? +hs[0].tagName[1] : 0; k < hs.length; k++) {
    const l = +hs[k].tagName[1];
    if (l > prev + 1) { add('heading-order', hs[k], `heading level jumps from h${prev} to h${l}`); break; }
    prev = l;
  }

  // ---- colour contrast (WCAG AA) where the background is a flat colour; gradients/images are skipped, not guessed
  const parse = (c) => {
    if (!c || c === 'transparent') return [0, 0, 0, 0];
    let m = c.match(/^rgba?\(([^)]+)\)/);
    if (m) { const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(parseFloat); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; }
    m = c.match(/^color\(srgb ([^)]+)\)/);
    if (m) { const p = m[1].split(/[\s\/]+/).filter(Boolean).map(parseFloat); return [p[0] * 255, p[1] * 255, p[2] * 255, p.length > 3 ? p[3] : 1]; }
    return null;
  };
  const lum = ([r, g, b]) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const over = (top, base) => [0, 1, 2].map((i) => top[i] * top[3] + base[i] * (1 - top[3]));
  const bgOf = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (cs.backgroundImage !== 'none') return null;
      const c = parse(cs.backgroundColor);
      if (!c) return null;
      if (c[3] > 0) layers.push(c);
      if (c[3] >= 1) break;
    }
    let base = [255, 255, 255];
    for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return base;
  };
  const opacityOf = (el) => { let o = 1; for (let e = el; e; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity); return o; };
  const bad = {}; let checked = 0, skipped = 0;
  document.querySelectorAll('main *, header *, footer *, nav *').forEach((el) => {
    if (checked > 400 || !shown(el)) return;
    if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) return;
    const cs = getComputedStyle(el);
    if (cs.webkitTextFillColor === 'rgba(0, 0, 0, 0)' || opacityOf(el) < 0.99) { skipped++; return; }
    const fg = parse(cs.color), bg = bgOf(el);
    if (!fg || !bg) { skipped++; return; }
    checked++;
    const f = fg[3] < 1 ? over(fg, bg) : fg;
    const a = lum(f), b = lum(bg), ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    const px = parseFloat(cs.fontSize), large = px >= 24 || (px >= 18.66 && parseInt(cs.fontWeight, 10) >= 700);
    const need = large ? 3 : 4.5;
    if (ratio < need) { const k = sidOf(el); (bad[k] = bad[k] || []).push({ ratio, need, t: txt(el).slice(0, 24) }); }
  });
  Object.entries(bad).forEach(([sid, l]) => {
    l.sort((x, y) => x.ratio - y.ratio);
    out.push({ rule: 'contrast', sid, msg: `${l.length} text element(s) below WCAG AA contrast (worst "${l[0].t}" ${l[0].ratio.toFixed(1)}:1, needs ${l[0].need}:1)` });
  });
  return out;
}"""


def audit(page) -> list[dict]:
    """[{rule, sid, msg}] — empty list means no problem found by these rules."""
    return page.evaluate(A11Y_JS)
