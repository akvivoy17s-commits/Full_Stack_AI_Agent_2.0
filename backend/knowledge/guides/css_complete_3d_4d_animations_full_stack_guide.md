# Complete CSS Guide for Full-Stack Web Development
## Syntax, Selectors, Properties, Functions, Responsive UI, 2D/3D and Time-Based Animation

> **Purpose:** A comprehensive CSS learning and reference guide for building responsive, accessible, polished frontend interfaces, including modern layouts, visual effects, 3D scenes, and advanced animations.
>
> **Accuracy note:** CSS is a large, evolving standards platform. There is no fixed, finite official list of “100% of CSS syntax, properties, and functions.” This guide covers the major CSS language features, common property families, modern layout/animation features, and practical patterns. Browser support can vary by feature, so check the linked references before relying on newer APIs. CSS has 2D and 3D transforms, plus animation through time and scroll progress; it does **not** define a native fourth spatial dimension or a standard feature called “4D CSS.” You can create a “4D-like” experience by combining 3D depth with time, scroll, pointer, and state changes.

---

## Contents

1. CSS Fundamentals and Rule Syntax
2. Adding CSS to a Website
3. Selectors: Element, Class, ID, Attribute, Combinators
4. Pseudo-Classes and Pseudo-Elements
5. Cascade, Specificity, Inheritance, and Layers
6. Values, Units, and Data Types
7. CSS Custom Properties and Design Tokens
8. Colors, Transparency, and Color Functions
9. Box Model, Sizing, Overflow, and Display
10. Positioning, Stacking, and Containing Blocks
11. Typography and Text Styling
12. Backgrounds, Borders, Shadows, and Effects
13. Flexbox Layout
14. CSS Grid Layout
15. Responsive Design and Media Queries
16. Container Queries and Modern Responsive Patterns
17. Images, Video, Object Fit, and Aspect Ratio
18. Forms, Buttons, Tables, and UI States
19. Transforms: 2D and 3D
20. Transitions and Keyframe Animations
21. Scroll-Driven Animations and Timelines
22. “4D-Like” UI: Time + 3D + Scroll + Interaction
23. Filters, Masks, Clipping, Shapes, and Blending
24. Gradients and Background Effects
25. CSS Functions Reference
26. At-Rules Reference
27. Modern CSS Features
28. Accessibility, Motion Sensitivity, and Inclusive UI
29. Performance and Maintainable CSS
30. CSS Architecture and Naming
31. Debugging and Troubleshooting
32. Practical Patterns and Complete Examples
33. Common Properties by Category — Quick Reference
34. Practice Projects and Learning Roadmap
35. Official Documentation

---

# 1. CSS Fundamentals and Rule Syntax

CSS (Cascading Style Sheets) controls the presentation and layout of HTML/SVG documents. A style rule contains a selector and a declaration block.

```css
/* selector { property: value; } */
h1 {
  color: rebeccapurple;
  font-size: 2rem;
  margin-block: 0 1rem;
}
```

- **Selector:** identifies the element(s) to style.
- **Declaration:** a property and its value.
- **Declaration block:** declarations inside `{ }`.
- **Comment:** `/* comment */`.
- Property names are generally written in kebab-case, such as `background-color`.
- Declarations are separated by semicolons. A trailing semicolon is recommended.
- Invalid declarations are usually discarded without stopping the rest of the stylesheet from parsing.

### CSS variables are not ordinary programming variables
CSS is declarative. It describes presentation constraints, states, and effects. It does not provide general-purpose functions and loops in the same way JavaScript does. CSS supports custom properties, calculations, selectors, conditions, and animation; JavaScript is used for application logic.

# 2. Adding CSS to a Website

### External stylesheet (recommended for most sites)

```html
<link rel="stylesheet" href="styles.css">
```

```css
/* styles.css */
body { font-family: system-ui, sans-serif; }
```

### Internal stylesheet

```html
<style>
  .notice { padding: 1rem; }
</style>
```

### Inline style

```html
<p style="color: teal">A paragraph</p>
```

Use inline styles sparingly. They are harder to maintain, repeat, and override. For interactive style changes, class toggling is often cleaner than adding many inline declarations.

### Importing a stylesheet

```css
@import url("theme.css");
```

`@import` must appear before ordinary rules (except permitted charset/layer statements). For predictable loading and performance, HTML `<link>` stylesheets are often preferable.

### CSS reset / baseline

```css
*,
*::before,
*::after { box-sizing: border-box; }

html { color-scheme: light dark; }

body {
  margin: 0;
  min-height: 100vh;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  line-height: 1.5;
}

img, picture, video, canvas, svg { display: block; max-width: 100%; }
button, input, select, textarea { font: inherit; }
```

Choose a reset intentionally: `color-scheme: light dark` makes native controls follow the browser's light/dark preference and may not be suitable if your design only supports one theme.

# 3. Selectors

## 3.1 Basic selectors

```css
* { box-sizing: border-box; }      /* universal */
p { line-height: 1.6; }            /* type / element */
.card { padding: 1rem; }            /* class */
#main { max-width: 70rem; }         /* ID */
```

Use classes for reusable styling. IDs are unique identifiers in HTML and usually should not be the default styling hook because ID selectors have high specificity.

## 3.2 Selector lists and combinators

```css
h1, h2, h3 { line-height: 1.1; } /* selector list */
nav a { text-decoration: none; }  /* descendant */
.menu > li { list-style: none; }  /* direct child */
label + input { margin-top: .25rem; } /* adjacent sibling */
h2 ~ p { color: #555; }          /* following siblings */
```

## 3.3 Attribute selectors

```css
input[type="email"] { width: 100%; }
a[target] { border-bottom: 1px dotted; }
a[href^="https"] { color: seagreen; } /* starts with */
a[href$=".pdf"] { font-weight: 700; } /* ends with */
a[href*="docs"] { text-decoration: underline; } /* contains */
[lang|="en"] { hyphens: auto; }
[data-state="open" i] { /* i = case-insensitive */ }
```

Common attribute selector operators: `=`, `~=`, `|=`, `^=`, `$=`, `*=`. Optional flags include `i` (case-insensitive) and `s` (case-sensitive where supported by syntax).

## 3.4 Logical and relational selector functions

```css
:is(h1, h2, h3) { font-family: Georgia, serif; }
:where(.site-header, .site-footer) a { color: inherit; }
.card:not(.card--disabled) { cursor: pointer; }
.form:has(input:invalid) { border-color: crimson; }
```

- `:is()` groups alternatives and takes the specificity of its most specific argument.
- `:where()` groups alternatives but contributes zero specificity.
- `:not()` excludes matching elements.
- `:has()` selects an element based on matching descendants or related elements. Support is modern but check older browser needs.

## 3.5 Useful structural selectors

```css
li:first-child { font-weight: 700; }
li:last-child { margin-bottom: 0; }
li:nth-child(odd) { background: #f5f5f5; }
li:nth-child(3n) { color: tomato; }
article:only-child { max-width: 50rem; }
:empty { display: none; }
:root { --brand: #635bff; }
```

`nth-child()` supports formulas such as `2n`, `2n + 1`, `3n`, and more complex expressions. `:nth-of-type()` counts siblings of the same element type; `:nth-child()` counts all element siblings.

# 4. Pseudo-Classes and Pseudo-Elements

## 4.1 Interaction/state pseudo-classes

```css
button:hover { filter: brightness(1.08); }
button:active { transform: translateY(1px); }
button:focus { outline: 2px solid currentColor; }
button:focus-visible { outline: 3px solid #635bff; outline-offset: 3px; }
input:checked { accent-color: #635bff; }
input:disabled { opacity: .55; cursor: not-allowed; }
input:required { border-inline-start: 3px solid orange; }
input:valid { border-color: seagreen; }
input:invalid { border-color: crimson; }
```

Other common states: `:link`, `:visited`, `:target`, `:enabled`, `:optional`, `:read-only`, `:read-write`, `:placeholder-shown`, `:indeterminate`, `:default`, `:autofill`, `:user-valid`, `:user-invalid`, `:open`, `:popover-open`, `:modal`, `:fullscreen`, and `:defined`. Availability and semantics vary by element and browser support; check the selector reference.

## 4.2 Pseudo-elements

```css
.callout::before { content: "★ "; }
.callout::after { content: ""; display: block; height: 2px; background: currentColor; }
::selection { background: #d8d3ff; color: #17142b; }
input::placeholder { color: #777; }
li::marker { color: #635bff; }
summary::marker { color: currentColor; }
```

Other pseudo-elements include `::first-letter`, `::first-line`, `::file-selector-button`, `::backdrop`, `::cue`, `::part()`, `::slotted()`, and the `::before`/`::after` generated-content pseudo-elements. Some are specific to media, Shadow DOM, or browser APIs.

**Important:** generated content should not carry essential information that is absent from the HTML content or accessible name.

# 5. Cascade, Specificity, Inheritance, and Layers

The final style is determined by the cascade: origin and importance, cascade layer, specificity, scoping proximity where applicable, and source order. Inheritance supplies values from ancestors for properties that inherit by default.

### Specificity examples

```css
p { color: black; }              /* low */
.note { color: blue; }            /* class */
#warning { color: crimson; }      /* ID */
```

Do not solve every cascade issue with `!important`. Prefer clear component ownership, low-specificity selectors, and well-defined layers.

### Cascade layers

```css
@layer reset, vendor, base, components, utilities;

@layer reset {
  *, *::before, *::after { box-sizing: border-box; }
}

@layer components {
  .button { border-radius: .75rem; }
}

@layer utilities {
  .u-hidden { display: none !important; }
}
```

Layer order matters. For normal declarations, later layers generally outrank earlier layers; important declarations have reversed layer-order behavior. Use `!important` only when justified, and document exceptions.

### Global keywords

`inherit`, `initial`, `unset`, `revert`, and `revert-layer` have different cascade/reset meanings. Use them intentionally rather than as generic fixes.

# 6. Values, Units, and Data Types

## 6.1 Lengths

- Absolute: `px`, `cm`, `mm`, `Q`, `in`, `pt`, `pc`.
- Font-relative: `em`, `rem`, `ex`, `ch`, `cap`, `ic`, `lh`, `rlh`.
- Viewport-relative: `vw`, `vh`, `vi`, `vb`, `vmin`, `vmax` and dynamic/small/large variants such as `dvh`, `svh`, `lvh` where supported.
- Container-relative: `cqw`, `cqh`, `cqi`, `cqb`, `cqmin`, `cqmax` for container query units.
- Percentages: `%`, interpreted relative to the particular property's reference dimension or value.

```css
.page { width: min(100% - 2rem, 75rem); }
.title { font-size: clamp(2rem, 5vw, 4.5rem); }
.panel { min-height: 100dvh; }
```

## 6.2 Other value types

CSS values include keywords, numbers, integers, dimensions, percentages, strings, URLs, colors, images, gradients, positions, angles (`deg`, `rad`, `turn`, `grad`), times (`s`, `ms`), frequencies, resolution, custom identifiers, and functional notations.

### CSS-wide keywords

```css
color: inherit;
margin: initial;
font: unset;
all: revert;
```

### Shorthands and longhands

```css
/* shorthand */
margin: 1rem 2rem;

/* longhands */
margin-block: 1rem;
margin-inline: 2rem;
```

A shorthand can reset associated longhand properties. Do not assume it only changes the values you explicitly see in the declaration.

# 7. CSS Custom Properties and Design Tokens

```css
:root {
  --color-brand: #625cff;
  --color-text: #191923;
  --surface: #fff;
  --space-1: .25rem;
  --space-2: .5rem;
  --space-3: .75rem;
  --space-4: 1rem;
  --radius-card: 1rem;
  --shadow-card: 0 1rem 3rem rgb(0 0 0 / .12);
}

.card {
  color: var(--color-text, #222);
  padding: var(--space-4);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
}
```

Custom properties cascade and inherit. They are text-like token streams until substituted; they are not general-purpose variables in the same way as JavaScript variables.

### Registering a custom property

```css
@property --progress {
  syntax: "<number>";
  inherits: false;
  initial-value: 0;
}

.meter {
  --progress: 0;
  background: conic-gradient(rebeccapurple calc(var(--progress) * 1%), #ddd 0);
  transition: --progress 400ms ease;
}
```

`@property` enables typed custom properties where supported. Syntax names and registration rules must follow the specification. Check compatibility before depending on it.

# 8. Colors, Transparency, and Color Functions

```css
.example {
  color: red;
  background: #635bff;
  border-color: rgb(99 91 255 / 70%);
  outline-color: hsl(245 100% 70%);
  box-shadow: 0 0 0 4px oklch(70% .2 280 / .25);
}
```

Common formats: named colors, hexadecimal (`#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA`), `rgb()`, `hsl()`, `hwb()`, `lab()`, `lch()`, `oklab()`, `oklch()`, and device-oriented color spaces such as `color()`, subject to supported profiles and browsers.

```css
background: color-mix(in oklab, rebeccapurple 65%, white);
color: rgb(from rebeccapurple r g b / .9); /* relative color syntax; check support */
```

Useful color-related properties: `color`, `background-color`, `opacity`, `accent-color`, `caret-color`, `fill`, `stroke`, `color-scheme`, `forced-color-adjust`, `print-color-adjust`, and `color-interpolation` for applicable SVG contexts.

# 9. Box Model, Sizing, Overflow, and Display

```css
* { box-sizing: border-box; }
.card {
  display: block;
  width: min(100%, 32rem);
  min-width: 0;
  max-width: 100%;
  padding: 1.25rem;
  border: 1px solid #ddd;
  margin: 0 auto;
  overflow: auto;
}
```

### Display values

Common values include `none`, `block`, `inline`, `inline-block`, `flex`, `inline-flex`, `grid`, `inline-grid`, `flow-root`, `table`, table-role values, `list-item`, and multi-keyword forms such as `inline flow` or `block flex` in modern CSS syntax.

`display: none` removes the element from layout and typically the accessibility tree. It is not the same as `visibility: hidden` or `opacity: 0`.

### Width and sizing properties

`width`, `height`, `min-width`, `max-width`, `min-height`, `max-height`, `inline-size`, `block-size`, `min-inline-size`, `max-inline-size`, `min-block-size`, `max-block-size`, `aspect-ratio`, `box-sizing`, `contain-intrinsic-size`, and related logical dimensions.

### Overflow

```css
.scroller {
  overflow: auto;
  overflow-x: auto;
  overflow-y: hidden;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
```

Related properties include `overflow-wrap`, `word-break`, `text-overflow`, `white-space`, `clip`, `overflow-clip-margin`, and overscroll-behavior axes.

# 10. Positioning, Stacking, and Containing Blocks

```css
.header { position: sticky; top: 0; z-index: 10; }
.dialog-layer { position: fixed; inset: 0; }
.badge { position: absolute; inset-block-start: 0; inset-inline-end: 0; }
```

Positioning modes: `static`, `relative`, `absolute`, `fixed`, and `sticky`.

Important related properties: `top`, `right`, `bottom`, `left`, logical inset properties (`inset`, `inset-block`, `inset-inline`, etc.), `z-index`, `float`, `clear`, `isolation`, `inset-area` in anchor positioning contexts, `anchor-name`, `position-anchor`, `position-area`, `position-try`, `position-try-fallbacks`, and other anchor-positioning features where supported.

Stacking contexts may be created by positioned elements with non-auto `z-index`, transforms, opacity below 1, filters, isolation, certain containment, and several other properties. A huge `z-index` cannot escape its ancestor's stacking context.

# 11. Typography and Text Styling

```css
@font-face {
  font-family: "Product Sans";
  src: url("/fonts/product.woff2") format("woff2");
  font-style: normal;
  font-weight: 100 900;
  font-display: swap;
}

body {
  font-family: "Product Sans", system-ui, sans-serif;
  font-size: 1rem;
  line-height: 1.6;
  letter-spacing: normal;
}

h1 {
  font-size: clamp(2.25rem, 5vw, 5rem);
  font-weight: 800;
  line-height: 1.05;
  text-wrap: balance;
}
```

Important text/font properties: `font`, `font-family`, `font-size`, `font-style`, `font-weight`, `font-stretch`, `font-variant`, `font-feature-settings`, `font-variation-settings`, `font-optical-sizing`, `font-kerning`, `font-synthesis`, `font-display` within `@font-face`, `line-height`, `letter-spacing`, `word-spacing`, `text-align`, `text-align-last`, `text-decoration`, `text-decoration-color`, `text-decoration-line`, `text-decoration-style`, `text-decoration-thickness`, `text-underline-offset`, `text-transform`, `text-indent`, `text-shadow`, `text-overflow`, `text-wrap`, `overflow-wrap`, `word-break`, `hyphens`, `white-space`, `writing-mode`, `direction`, `unicode-bidi`, `vertical-align`, `line-clamp` (compatibility-dependent), and `tab-size`.

# 12. Backgrounds, Borders, Shadows, and Effects

```css
.hero {
  background-color: #0b0b12;
  background-image: radial-gradient(circle at 70% 20%, #625cff 0, transparent 35%),
                    linear-gradient(120deg, #10101b, #1a1230);
  background-position: center;
  background-size: cover;
  background-repeat: no-repeat;
  border: 1px solid rgb(255 255 255 / .16);
  border-radius: 1.5rem;
  box-shadow: 0 1rem 3rem rgb(0 0 0 / .25);
}
```

Related properties: `background`, `background-attachment`, `background-blend-mode`, `background-clip`, `background-origin`, `background-position`, `background-repeat`, `background-size`, `border`, `border-block`, `border-inline`, border side/width/style/color longhands, `border-radius`, `border-image`, `outline`, `outline-offset`, `box-shadow`, `text-shadow`, `filter`, `backdrop-filter`, `opacity`, and `mix-blend-mode`.

# 13. Flexbox Layout

```css
.row {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  align-content: center;
  gap: 1rem;
}

.row > * { flex: 1 1 15rem; min-width: 0; }
```

Container properties: `flex-direction`, `flex-wrap`, `flex-flow`, `justify-content`, `align-items`, `align-content`, `gap`, `row-gap`, `column-gap`.

Item properties: `order`, `flex`, `flex-grow`, `flex-shrink`, `flex-basis`, `align-self`.

- Main axis is determined by `flex-direction`.
- `justify-content` distributes space along the main axis.
- `align-items` aligns items along the cross axis.
- `flex: 1` is a shorthand; understand how its basis/grow/shrink behavior works for the layout you need.
- Prefer `gap` to margins between flex children where practical.

# 14. CSS Grid Layout

```css
.products {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
  gap: 1.25rem;
}

.featured { grid-column: 1 / -1; }
```

Grid concepts and properties: `grid-template-columns`, `grid-template-rows`, `grid-template-areas`, `grid-template`, `grid-auto-columns`, `grid-auto-rows`, `grid-auto-flow`, `grid-column`, `grid-row`, `grid-area`, `grid`, `justify-items`, `align-items`, `place-items`, `justify-content`, `align-content`, `place-content`, `justify-self`, `align-self`, `place-self`, `gap`, `row-gap`, `column-gap`, `subgrid`, and named lines.

```css
.layout {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar main"
    "footer footer";
  grid-template-columns: 16rem minmax(0, 1fr);
}
.header { grid-area: header; }
.sidebar { grid-area: sidebar; }
.main { grid-area: main; }
.footer { grid-area: footer; }
```

# 15. Responsive Design and Media Queries

```css
.page { padding-inline: 1rem; }
.grid { display: grid; grid-template-columns: 1fr; gap: 1rem; }

@media (min-width: 48rem) {
  .page { padding-inline: 2rem; }
  .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (min-width: 72rem) {
  .grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
```

Media query features include viewport `width`/`height`, `orientation`, `aspect-ratio`, `resolution`, `hover`, `pointer`, `any-hover`, `any-pointer`, `prefers-color-scheme`, `prefers-reduced-motion`, `prefers-contrast`, `forced-colors`, `color-gamut`, `scripting`, display mode, and other environment/media capabilities, with support varying by feature.

```css
@media (prefers-color-scheme: dark) {
  :root { color-scheme: dark; --surface: #15151b; --text: #f6f6f7; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
  }
}
```

Use mobile-first CSS, test real content widths, avoid relying only on device labels, and ensure keyboard and touch users can access all controls.

# 16. Container Queries and Modern Responsive Patterns

```css
.product-list { container-type: inline-size; container-name: products; }

@container products (min-width: 35rem) {
  .product-card { display: grid; grid-template-columns: 9rem minmax(0, 1fr); }
}
```

Container query properties/features include `container`, `container-name`, `container-type`, `@container`, and container-relative units like `cqi`, `cqw`, `cqb`, and `cqh` where supported.

### Intrinsic sizing helpers

```css
width: min(100%, 72rem);
width: max(20rem, 50%);
width: clamp(18rem, 60vw, 60rem);
```

Related functions: `min()`, `max()`, `clamp()`, `fit-content()`, `min-content`, `max-content`, `minmax()`, and `repeat()`.

# 17. Images, Video, Object Fit, and Aspect Ratio

```css
.thumbnail {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  object-position: center;
  border-radius: 1rem;
}

.avatar { width: 4rem; aspect-ratio: 1; object-fit: cover; border-radius: 50%; }
```

Related properties: `object-fit`, `object-position`, `aspect-ratio`, `image-rendering`, `image-orientation`, `image-resolution` where supported, `background-size`, `background-position`, and `vertical-align` for inline images.

# 18. Forms, Buttons, Tables, and UI States

```css
.field { display: grid; gap: .4rem; }
.field input, .field select, .field textarea {
  width: 100%;
  padding: .8rem 1rem;
  border: 1px solid #b8bac5;
  border-radius: .6rem;
}
.field input:focus-visible {
  outline: 3px solid #a5a0ff;
  outline-offset: 2px;
}
.field input:invalid:not(:placeholder-shown) { border-color: #bd2c2c; }
button { cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .6; }
```

Useful form pseudo-classes: `:required`, `:optional`, `:valid`, `:invalid`, `:in-range`, `:out-of-range`, `:read-only`, `:read-write`, `:placeholder-shown`, `:checked`, `:indeterminate`, `:disabled`, `:enabled`, `:focus`, `:focus-visible`, `:focus-within`, and `:user-invalid` where supported.

Table properties/patterns include `border-collapse`, `border-spacing`, `caption-side`, `table-layout`, `empty-cells`, `vertical-align`, and responsive wrappers with `overflow-x: auto`.

# 19. Transforms: 2D and 3D

## 19.1 2D transforms

```css
.transform-demo {
  transform: translate(10px, 5px) rotate(4deg) scale(1.05) skewX(-3deg);
  transform-origin: center;
}
```

Functions include `translate()`, `translateX()`, `translateY()`, `rotate()`, `scale()`, `scaleX()`, `scaleY()`, `skew()`, `skewX()`, `skewY()`, and `matrix()`.

Individual transform properties are available in modern browsers:

```css
.demo {
  translate: 10px 5px;
  rotate: 4deg;
  scale: 1.05;
}
```

Use either the individual properties or `transform` intentionally; be aware of how transform composition and order work.

## 19.2 3D transforms

```css
.scene {
  perspective: 900px;
  perspective-origin: 50% 50%;
}
.card-3d {
  transform-style: preserve-3d;
  transform: rotateX(8deg) rotateY(-14deg) translateZ(10px);
  backface-visibility: hidden;
  transform-origin: center;
}
```

3D transform functions:

- `translate3d(x, y, z)`
- `translateZ(z)`
- `rotate3d(x, y, z, angle)`
- `rotateX(angle)`, `rotateY(angle)`, `rotateZ(angle)`
- `scale3d(x, y, z)`, `scaleZ(z)`
- `perspective(distance)`
- `matrix3d(...)`

Related properties: `perspective`, `perspective-origin`, `transform-style`, `transform-origin`, `backface-visibility`, `transform-box`, and `transform`. Note that `transform-style: preserve-3d` is not inherited. Some properties that require grouping/flattening can force flattening of descendants, so inspect effects if a 3D scene looks unexpectedly flat.

### 3D cube example

HTML:

```html
<div class="scene">
  <div class="cube">
    <div class="face front">Front</div>
    <div class="face back">Back</div>
    <div class="face right">Right</div>
    <div class="face left">Left</div>
    <div class="face top">Top</div>
    <div class="face bottom">Bottom</div>
  </div>
</div>
```

CSS:

```css
.scene { width: 12rem; height: 12rem; perspective: 800px; margin: 5rem auto; }
.cube { width: 100%; height: 100%; position: relative; transform-style: preserve-3d; animation: cube-spin 10s linear infinite; }
.face {
  position: absolute; inset: 0; display: grid; place-items: center;
  border: 2px solid white; color: white; font-weight: 700;
  background: rgb(80 70 220 / .8); backface-visibility: hidden;
}
.front  { transform: translateZ(6rem); }
.back   { transform: rotateY(180deg) translateZ(6rem); }
.right  { transform: rotateY(90deg) translateZ(6rem); }
.left   { transform: rotateY(-90deg) translateZ(6rem); }
.top    { transform: rotateX(90deg) translateZ(6rem); }
.bottom { transform: rotateX(-90deg) translateZ(6rem); }
@keyframes cube-spin { to { transform: rotateX(360deg) rotateY(360deg); } }
```

## 19.3 Interactive 3D tilt

Pure CSS hover tilt:

```css
.tilt-card { transform: perspective(900px) rotateX(0) rotateY(0); transition: transform 350ms ease; }
.tilt-card:hover { transform: perspective(900px) rotateX(4deg) rotateY(-6deg) translateY(-4px); }
```

A tilt responding continuously to pointer coordinates usually needs JavaScript to calculate pointer position and update custom properties. Provide a non-motion fallback and account for touch devices and `prefers-reduced-motion`.

# 20. Transitions and Keyframe Animations

## 20.1 Transitions

```css
.button {
  transform: translateY(0);
  background-color: #625cff;
  transition: transform 180ms ease, background-color 180ms ease;
}
.button:hover { transform: translateY(-2px); background-color: #5148e8; }
```

Properties: `transition`, `transition-property`, `transition-duration`, `transition-timing-function`, `transition-delay`, and `transition-behavior` where supported. Use `transition: all` sparingly because it can animate unwanted properties.

Timing functions: `linear`, `ease`, `ease-in`, `ease-out`, `ease-in-out`, `cubic-bezier(x1, y1, x2, y2)`, `steps(count, position)`, `step-start`, and `step-end`.

## 20.2 Keyframes

```css
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-1rem); }
}
.floating { animation: float 3s ease-in-out infinite; }
```

Animation properties: `animation`, `animation-name`, `animation-duration`, `animation-timing-function`, `animation-delay`, `animation-iteration-count`, `animation-direction`, `animation-fill-mode`, `animation-play-state`, `animation-timeline`, `animation-range`, and `animation-composition` as supported.

```css
.pulse {
  animation-name: pulse;
  animation-duration: 1.8s;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  animation-direction: alternate;
  animation-fill-mode: both;
}
@keyframes pulse { from { scale: 1; } to { scale: 1.06; } }
```

Animation composition modes can include `replace`, `add`, and `accumulate` where supported. Keyframes can use `from`, `to`, and percentages.

## 20.3 Reusable animation patterns

```css
@keyframes fade-up {
  from { opacity: 0; transform: translateY(1rem); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
  from { background-position: 100% 0; }
  to { background-position: -100% 0; }
}
@keyframes spin { to { rotate: 1turn; } }
@keyframes glow {
  from { box-shadow: 0 0 0 rgb(98 92 255 / 0); }
  to { box-shadow: 0 0 2rem rgb(98 92 255 / .55); }
}
```

## 20.4 Animating intrinsic size

Newer CSS features for interpolating sizes such as `auto` have browser-support constraints. Some browsers support `interpolate-size: allow-keywords` or `calc-size()` patterns; do not assume universal support.

```css
.panel {
  interpolate-size: allow-keywords;
  transition: height 250ms ease;
}
```

For broader compatibility, use grid row transitions, `max-height` with care, or JavaScript/Web Animations API when a precise measured height is required.

# 21. Scroll-Driven Animations and Timelines

Scroll-driven animations use scroll progress instead of only elapsed time. They are a modern CSS feature; always test target browsers and provide graceful fallbacks.

### Reading progress bar

```css
.reading-progress {
  position: fixed;
  inset: 0 auto auto 0;
  width: 100%;
  height: 4px;
  transform: scaleX(0);
  transform-origin: left;
  background: #625cff;
  animation: read-progress linear both;
  animation-timeline: scroll(root block);
}
@keyframes read-progress { to { transform: scaleX(1); } }
```

### View timeline reveal

```css
.reveal {
  opacity: 0;
  transform: translateY(2rem);
  animation: reveal-in linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 80%;
}
@keyframes reveal-in { to { opacity: 1; transform: translateY(0); } }
```

Timeline concepts/properties include `animation-timeline`, `animation-range`, `scroll-timeline`, `scroll-timeline-name`, `scroll-timeline-axis`, `view-timeline`, `view-timeline-name`, `view-timeline-axis`, `view-timeline-inset`, `timeline-scope`, and the `scroll()`/`view()` timeline functions, depending on feature support.

**Fallback:** If scroll-driven animations are unsupported, the content should remain visible and usable. Do not make essential content depend on a scroll animation.

# 22. “4D-Like” UI: Time + 3D + Scroll + Interaction

CSS does not have a standard fourth spatial axis called “4D.” In web design, “4D-like” usually means a 3D scene that changes over time, with scroll progress or user interaction adding another dimension of behavior. It is an artistic description, not a CSS language feature.

## 22.1 Time-based 3D

```css
.orbit-scene { perspective: 1000px; }
.orbit-object {
  transform-style: preserve-3d;
  animation: orbit 12s linear infinite;
}
@keyframes orbit {
  from { transform: rotateY(0) rotateX(12deg); }
  to { transform: rotateY(1turn) rotateX(12deg); }
}
```

## 22.2 Scroll-progress depth effect

```css
@supports (animation-timeline: scroll()) {
  .parallax-layer {
    animation: depth-move linear both;
    animation-timeline: scroll(root block);
  }
  @keyframes depth-move {
    from { transform: translateY(-2rem) scale(1.05); }
    to { transform: translateY(2rem) scale(1); }
  }
}
```

## 22.3 Layered immersive hero

```css
.immersive-hero {
  min-height: 80svh;
  display: grid;
  place-items: center;
  overflow: clip;
  perspective: 1000px;
  background: radial-gradient(circle at 50% 30%, #27205a, #080810 70%);
}
.immersive-hero__layers {
  position: relative;
  transform-style: preserve-3d;
  animation: hero-drift 8s ease-in-out infinite alternate;
}
.immersive-hero__foreground {
  transform: translateZ(100px);
}
.immersive-hero__background {
  transform: translateZ(-120px) scale(1.2);
}
@keyframes hero-drift {
  from { transform: rotateX(2deg) rotateY(-3deg); }
  to { transform: rotateX(-2deg) rotateY(3deg); }
}
@media (prefers-reduced-motion: reduce) {
  .immersive-hero__layers { animation: none; }
}
```

## 22.4 View-transition effects

View Transitions can animate between visual states or document navigations when invoked through supporting browser APIs. CSS styles the transition pseudo-elements; JavaScript/framework routing often triggers the state change. Cross-document navigation support and advanced options depend on browser support.

```css
::view-transition-old(root) { animation: fade-out 180ms ease both; }
::view-transition-new(root) { animation: fade-in 240ms ease both; }
@keyframes fade-out { to { opacity: 0; } }
@keyframes fade-in { from { opacity: 0; } }
```

Use view transitions progressively and keep navigation functional if unsupported.

# 23. Filters, Masks, Clipping, Shapes, and Blending

```css
.image { filter: saturate(1.2) contrast(1.05); }
.glass { backdrop-filter: blur(16px); background: rgb(255 255 255 / .12); }
.clip { clip-path: polygon(0 0, 100% 0, 85% 100%, 0 100%); }
.circle { clip-path: circle(45% at 50% 50%); }
.photo { mask-image: linear-gradient(to bottom, black 75%, transparent); }
.blended { mix-blend-mode: screen; }
.layer { isolation: isolate; }
```

### Filter functions

`blur()`, `brightness()`, `contrast()`, `drop-shadow()`, `grayscale()`, `hue-rotate()`, `invert()`, `opacity()`, `saturate()`, and `sepia()`.

### Clip-path shapes

`inset()`, `circle()`, `ellipse()`, `polygon()`, and `path()` where supported. `shape()` and newer shape notations may be emerging; check compatibility.

### Related properties

`filter`, `backdrop-filter`, `clip-path`, `mask`, `mask-image`, `mask-mode`, `mask-position`, `mask-repeat`, `mask-size`, `mask-composite`, `shape-outside`, `shape-margin`, `shape-image-threshold`, `mix-blend-mode`, `background-blend-mode`, `isolation`, and `opacity`.

# 24. Gradients and Background Effects

```css
.linear { background: linear-gradient(135deg, #625cff, #ff5ca8); }
.radial { background: radial-gradient(circle at 50% 35%, #4f46e5, transparent 60%); }
.conic { background: conic-gradient(from 45deg, #625cff, #ff5ca8, #625cff); }
.repeating { background: repeating-linear-gradient(45deg, #111 0 10px, #222 10px 20px); }
```

Gradient functions: `linear-gradient()`, `repeating-linear-gradient()`, `radial-gradient()`, `repeating-radial-gradient()`, `conic-gradient()`, `repeating-conic-gradient()`. Use multiple backgrounds to layer effects:

```css
.glow-panel {
  background:
    radial-gradient(circle at 15% 10%, rgb(98 92 255 / .28), transparent 35%),
    linear-gradient(145deg, #151522, #09090f);
}
```

# 25. CSS Functions Reference

CSS has functional notation rather than general-purpose JavaScript-like functions. Many functions can be nested. This is a practical reference, not a guaranteed exhaustive list of every specialized or experimental grammar.

## 25.1 Math and sizing functions

- `calc(expression)` — calculate arithmetic using compatible CSS values.
- `min(value, ...)` — smallest argument.
- `max(value, ...)` — largest argument.
- `clamp(min, preferred, max)` — clamps a value within a range.
- `round(strategy?, value, interval)` — rounds to an interval where supported.
- `mod(dividend, divisor)` and `rem(dividend, divisor)` — remainder/modulo-style functions where supported.
- `abs(value)` and `sign(value)` — absolute value and sign where supported.
- `minmax(min, max)` — Grid track size.
- `fit-content(length)` — intrinsic size limit.
- `repeat(count, track-list)` — repeat Grid tracks.
- `calc-size(basis, calculation)` — intrinsic-size calculations where supported.

```css
width: min(100% - 2rem, 72rem);
font-size: clamp(1.5rem, 4vw, 4rem);
grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
```

## 25.2 Color functions

`rgb()`, `rgba()` (legacy-compatible syntax), `hsl()`, `hsla()` (legacy-compatible syntax), `hwb()`, `lab()`, `lch()`, `oklab()`, `oklch()`, `color()`, `color-mix()`, `light-dark()`, and relative color syntax where supported.

## 25.3 Transform functions

`matrix()`, `matrix3d()`, `translate()`, `translateX()`, `translateY()`, `translateZ()`, `translate3d()`, `rotate()`, `rotateX()`, `rotateY()`, `rotateZ()`, `rotate3d()`, `scale()`, `scaleX()`, `scaleY()`, `scaleZ()`, `scale3d()`, `skew()`, `skewX()`, `skewY()`, and `perspective()`.

## 25.4 Gradient functions

`linear-gradient()`, `repeating-linear-gradient()`, `radial-gradient()`, `repeating-radial-gradient()`, `conic-gradient()`, `repeating-conic-gradient()`.

## 25.5 Filter functions

`blur()`, `brightness()`, `contrast()`, `drop-shadow()`, `grayscale()`, `hue-rotate()`, `invert()`, `opacity()`, `saturate()`, `sepia()`.

## 25.6 Image, position, and timeline functions

`url()`, `image-set()`, `image()`, `cross-fade()` (support varies), `element()` (limited support), `attr()` (capabilities vary by context), `fit-content()`, `anchor()`, `anchor-size()`, `scroll()`, `view()`, `env()`, `var()`, `counter()`, `counters()`, `symbols()`, `leader()`, and `local()` in relevant CSS grammars and support contexts.

## 25.7 Easing functions

`linear()`, `cubic-bezier()`, `steps()`, `step-start`, `step-end`, `ease`, `ease-in`, `ease-out`, `ease-in-out`.

## 25.8 Environment and custom-property functions

```css
.safe-panel { padding-top: env(safe-area-inset-top, 0px); }
.panel { padding: var(--panel-space, 1rem); }
```

`env()` reads browser/user-agent environment variables such as safe-area insets. `var()` substitutes a custom property. Modern CSS specifications include developing/custom-function features, but do not assume a CSS `@function` implementation is available in every target browser.

# 26. At-Rules Reference

At-rules begin with `@`. Major at-rules and their common purposes:

- `@charset` — character encoding declaration when required; must be placed at the beginning of a stylesheet.
- `@import` — imports another stylesheet.
- `@namespace` — declares XML namespaces for namespace-aware selectors.
- `@media` — conditions on media/device/user preferences.
- `@supports` — feature-query support detection.
- `@container` — container queries.
- `@layer` — cascade layers.
- `@scope` — limits selector matching to a DOM scope where supported.
- `@starting-style` — defines starting values for entry transitions where supported.
- `@font-face` — declares a font resource.
- `@font-feature-values` — named font feature values for supported font features.
- `@keyframes` — animation keyframes.
- `@property` — registers custom properties.
- `@counter-style` — custom counter presentation.
- `@page` — paged/print layout rules.
- `@supports` — feature tests, including selector/property tests.
- `@document` — historically specified but not broadly supported; avoid relying on it.
- `@viewport` — legacy/obsolete in modern workflows; use viewport metadata in HTML.
- `@position-try` — fallback positions in anchor positioning where supported.
- `@view-transition` — view-transition opt-in/control where supported.
- `@font-palette-values` — color palette choices for applicable fonts where supported.
- `@-ms-viewport`, `@-webkit-keyframes` and other prefixed rules are legacy/vendor-specific; use standard syntax unless supporting a documented older target.

Examples:

```css
@supports (display: grid) {
  .layout { display: grid; }
}

@media (width >= 48rem) {
  .layout { grid-template-columns: 16rem 1fr; }
}

@layer base {
  body { margin: 0; }
}
```

# 27. Modern CSS Features

## 27.1 CSS nesting

```css
.card {
  padding: 1rem;
  & h2 { margin-block-start: 0; }
  &:hover { box-shadow: 0 1rem 2rem rgb(0 0 0 / .12); }
  @media (width >= 50rem) { padding: 1.5rem; }
}
```

Native CSS nesting is not identical to Sass nesting in every edge case. Use valid selectors and check browser requirements.

## 27.2 Anchor positioning

Anchor positioning can connect an anchored element, such as a tooltip, to another element. Newer syntax and browser support evolve, so treat this as progressive enhancement.

```css
.anchor { anchor-name: --trigger; }
.tooltip {
  position: absolute;
  position-anchor: --trigger;
  position-area: block-end;
  margin-block-start: .5rem;
}
```

Exact properties and syntax are still worth verifying against current browser compatibility references.

## 27.3 Scrollbar and overscroll

`scrollbar-gutter`, `scrollbar-color`, `scrollbar-width`, `overscroll-behavior`, `scroll-padding`, `scroll-margin`, `scroll-snap-type`, `scroll-snap-align`, `scroll-snap-stop`, and `scroll-behavior` can improve scrolling UX. Browser-specific scrollbar styling differs.

## 27.4 View transitions

CSS can style pseudo-elements generated by the View Transitions API. The state change/transition often must be initiated by JavaScript or navigation behavior. Feature-detect and keep functionality available without animation.

# 28. Accessibility, Motion Sensitivity, and Inclusive UI

```css
:focus-visible {
  outline: 3px solid #8c83ff;
  outline-offset: 3px;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important;
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
}
```

Guidelines:

- Never remove visible keyboard focus without providing a suitable alternative.
- Do not encode meaning only in color; also use text, icons, patterns, or labels.
- Maintain readable contrast and support zoom/reflow.
- Keep interactive targets usable on touch screens.
- Respect `prefers-reduced-motion`; avoid flashing and unnecessary constant motion.
- Avoid hiding essential content behind hover-only interactions.
- Use semantic HTML. CSS cannot repair missing semantic structure by itself.
- Do not use generated content as the only source of essential information.
- For forced-colors modes, test whether custom backgrounds/outlines need adjustment; avoid disabling user-selected high-contrast modes without a compelling reason.

# 29. Performance and Maintainable CSS

- Animate `transform` and `opacity` where practical; they are often more efficient than animating layout properties, but still profile the actual page.
- Avoid excessive blur/filter layers, large fixed shadows, huge paint areas, and many simultaneously animated nodes on low-powered devices.
- Use `will-change` sparingly and only after profiling; permanent blanket use can waste memory.
- Reduce duplicate selectors and deep specificity.
- Use `min-width: 0` on grid/flex children when content overflows unexpectedly.
- Prefer responsive images and modern image formats in HTML, with CSS controlling crop/layout.
- Avoid layout thrashing from scripts that read/write layout repeatedly; this concern belongs to the JavaScript rendering pipeline as well as CSS choices.
- Test on a real phone and under CPU/network throttling when performance matters.

### Containment

```css
.card-list-item { contain: layout paint; }
```

Containment (`contain`, `container-type`, `content-visibility`, and intrinsic-size helpers) can reduce rendering work but changes formatting, containment, or sizing behavior. Adopt it only after understanding its effects.

# 30. CSS Architecture and Naming

### BEM-style naming

```css
.product-card { }
.product-card__title { }
.product-card__price { }
.product-card--featured { }
```

### Component and utility approach

```css
.button { padding: .75rem 1rem; border-radius: .7rem; }
.button--primary { background: var(--brand); color: white; }
.u-visually-hidden {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
}
```

The visually-hidden technique must be used carefully: the content remains available to assistive technology in typical cases, but can be removed from interaction/layout in some implementations. Do not apply it to focusable controls without appropriate handling.

Use design tokens, consistent spacing/type scales, low-specificity selectors, and component ownership. Choose a methodology that your team can maintain rather than mixing multiple naming systems arbitrarily.

# 31. Debugging and Troubleshooting

Common problems:

1. **CSS rule not working:** check selector, syntax, cascade, specificity, layer order, inheritance, media queries, and computed styles.
2. **Unexpected overflow:** check long words, image dimensions, `min-width`, grid tracks, flex basis, and viewport units.
3. **`z-index` seems ignored:** inspect stacking contexts and containing elements.
4. **Sticky element fails:** inspect ancestor overflow, scroll container, and inset properties.
5. **3D becomes flat:** check `transform-style: preserve-3d`, perspective placement, face placement, and properties that cause flattening.
6. **Animation does not run:** verify animation name, duration, iteration count, timeline support, initial/final values, and reduced-motion rules.
7. **Mobile viewport jump:** consider `dvh`, `svh`, and `lvh` rather than assuming `100vh` matches the visible viewport on every device.
8. **Font looks different:** confirm font request path, network loading, font format, weight mapping, and fallback stack.

Useful browser DevTools tabs: Elements/Inspector, Styles, Computed, Layout (Flex/Grid), Animations, Accessibility, Performance, and Coverage where available.

# 32. Practical Patterns and Complete Examples

## 32.1 Premium responsive card

```html
<article class="feature-card">
  <span class="feature-card__tag">NEW</span>
  <h2>Build something remarkable</h2>
  <p>A responsive card with clear hierarchy and subtle motion.</p>
  <a class="feature-card__link" href="#details">Explore feature <span aria-hidden="true">→</span></a>
</article>
```

```css
:root { --brand: #625cff; --surface: #15151e; --text: #f8f8ff; }
.feature-card {
  position: relative;
  display: grid;
  gap: 1rem;
  width: min(100%, 25rem);
  padding: clamp(1.25rem, 4vw, 2rem);
  color: var(--text);
  background: radial-gradient(circle at 80% 0, rgb(98 92 255 / .28), transparent 45%), var(--surface);
  border: 1px solid rgb(255 255 255 / .14);
  border-radius: 1.5rem;
  box-shadow: 0 1rem 3rem rgb(0 0 0 / .22);
  transition: transform 220ms ease, border-color 220ms ease, box-shadow 220ms ease;
}
.feature-card:hover {
  transform: translateY(-5px);
  border-color: rgb(150 142 255 / .6);
  box-shadow: 0 1.5rem 3.5rem rgb(0 0 0 / .32);
}
.feature-card__tag { justify-self: start; padding: .25rem .6rem; border-radius: 999px; background: var(--brand); font-size: .75rem; font-weight: 800; }
.feature-card h2 { margin: 0; font-size: clamp(1.4rem, 3vw, 2rem); line-height: 1.1; text-wrap: balance; }
.feature-card p { margin: 0; color: #c5c5d1; }
.feature-card__link { color: #d0ccff; font-weight: 700; text-decoration-thickness: .08em; text-underline-offset: .2em; }
.feature-card__link:focus-visible { outline: 3px solid #a6a0ff; outline-offset: 4px; }
@media (prefers-reduced-motion: reduce) { .feature-card { transition: none; } }
```

## 32.2 Responsive app layout

```css
.app-shell {
  min-height: 100dvh;
  display: grid;
  grid-template-rows: auto 1fr auto;
}
.app-body { display: grid; grid-template-columns: 15rem minmax(0, 1fr); }
.sidebar { border-inline-end: 1px solid #ddd; }
.content { min-width: 0; padding: clamp(1rem, 3vw, 2rem); }
@media (max-width: 48rem) { .app-body { grid-template-columns: 1fr; } .sidebar { border-inline-end: 0; border-block-end: 1px solid #ddd; } }
```

## 32.3 Neon animated border

```css
.neon-card {
  position: relative;
  isolation: isolate;
  border-radius: 1rem;
  background: #11111b;
  color: white;
}
.neon-card::before {
  content: "";
  position: absolute;
  z-index: -1;
  inset: -2px;
  border-radius: inherit;
  background: conic-gradient(from var(--angle, 0turn), #625cff, #00e5ff, #ff5ca8, #625cff);
  animation: border-spin 5s linear infinite;
}
@keyframes border-spin { to { --angle: 1turn; } }
@property --angle { syntax: "<angle>"; inherits: false; initial-value: 0turn; }
@media (prefers-reduced-motion: reduce) { .neon-card::before { animation: none; } }
```

Custom-property animation depends on `@property` support; provide a static border fallback if target browsers do not support registration.

## 32.4 Flip card

```html
<div class="flip-card">
  <div class="flip-card__inner">
    <div class="flip-card__face flip-card__front">Front</div>
    <div class="flip-card__face flip-card__back">Back content</div>
  </div>
</div>
```

```css
.flip-card { width: 18rem; height: 12rem; perspective: 900px; }
.flip-card__inner { position: relative; width: 100%; height: 100%; transform-style: preserve-3d; transition: transform 600ms cubic-bezier(.2,.75,.2,1); }
.flip-card:hover .flip-card__inner, .flip-card:focus-within .flip-card__inner { transform: rotateY(180deg); }
.flip-card__face { position: absolute; inset: 0; display: grid; place-items: center; padding: 1rem; border-radius: 1rem; background: #292342; color: white; backface-visibility: hidden; }
.flip-card__back { transform: rotateY(180deg); background: #4b3ad4; }
@media (prefers-reduced-motion: reduce) { .flip-card__inner { transition: none; } }
```

Provide a real keyboard-operable button/control if flipping reveals information or actions; hover alone is not enough for touch/keyboard access.

# 33. Common Properties by Category — Quick Reference

This practical list groups commonly used standard CSS properties. It is not an exhaustive index of every current CSS property or vendor-specific extension.

### Layout and box model
`display`, `visibility`, `box-sizing`, `width`, `height`, `min-width`, `max-width`, `min-height`, `max-height`, `inline-size`, `block-size`, `margin`, `margin-block`, `margin-inline`, `padding`, `padding-block`, `padding-inline`, `border`, `border-radius`, `outline`, `overflow`, `overflow-x`, `overflow-y`, `overflow-wrap`, `box-shadow`, `aspect-ratio`, `gap`, `row-gap`, `column-gap`.

### Position and layout systems
`position`, `inset`, `top`, `right`, `bottom`, `left`, `z-index`, `float`, `clear`, `isolation`, `flex`, `flex-basis`, `flex-direction`, `flex-wrap`, `flex-flow`, `flex-grow`, `flex-shrink`, `justify-content`, `align-content`, `align-items`, `align-self`, `order`, `grid`, `grid-template`, `grid-template-columns`, `grid-template-rows`, `grid-template-areas`, `grid-auto-flow`, `grid-column`, `grid-row`, `grid-area`, `justify-items`, `justify-self`, `place-items`, `place-content`, `place-self`.

### Typography
`color`, `font`, `font-family`, `font-size`, `font-weight`, `font-style`, `font-stretch`, `font-variant`, `font-feature-settings`, `font-variation-settings`, `line-height`, `letter-spacing`, `word-spacing`, `text-align`, `text-align-last`, `text-decoration`, `text-decoration-color`, `text-decoration-line`, `text-decoration-style`, `text-decoration-thickness`, `text-transform`, `text-indent`, `text-shadow`, `text-overflow`, `text-wrap`, `white-space`, `word-break`, `hyphens`, `writing-mode`, `direction`, `vertical-align`, `list-style`, `list-style-position`, `list-style-type`, `tab-size`.

### Background and visual effects
`background`, `background-color`, `background-image`, `background-size`, `background-position`, `background-repeat`, `background-attachment`, `background-origin`, `background-clip`, `background-blend-mode`, `border-image`, `box-shadow`, `text-shadow`, `opacity`, `filter`, `backdrop-filter`, `mix-blend-mode`, `mask`, `mask-image`, `clip-path`, `object-fit`, `object-position`, `image-rendering`, `accent-color`, `caret-color`, `color-scheme`.

### Animation and transforms
`transform`, `transform-origin`, `transform-style`, `transform-box`, `translate`, `rotate`, `scale`, `perspective`, `perspective-origin`, `backface-visibility`, `transition`, `transition-property`, `transition-duration`, `transition-timing-function`, `transition-delay`, `animation`, `animation-name`, `animation-duration`, `animation-timing-function`, `animation-delay`, `animation-iteration-count`, `animation-direction`, `animation-fill-mode`, `animation-play-state`, `animation-timeline`, `animation-range`, `will-change`.

### Lists, tables, columns and printing
`list-style`, `list-style-image`, `list-style-position`, `list-style-type`, `border-collapse`, `border-spacing`, `caption-side`, `table-layout`, `empty-cells`, `columns`, `column-count`, `column-width`, `column-gap`, `column-rule`, `column-span`, `break-before`, `break-after`, `break-inside`, `page-break-before` (legacy), `orphans`, `widows`.

### Scrolling and snapping
`scroll-behavior`, `scroll-margin`, `scroll-margin-top`, `scroll-padding`, `scroll-padding-top`, `scroll-snap-type`, `scroll-snap-align`, `scroll-snap-stop`, `overscroll-behavior`, `scrollbar-color`, `scrollbar-width`, `scrollbar-gutter`.

### Containment and rendering
`contain`, `contain-intrinsic-size`, `content-visibility`, `container`, `container-name`, `container-type`, `appearance`, `will-change`, `pointer-events`, `user-select`, `touch-action`, `resize`, `cursor`, `visibility`.

### SVG-related CSS properties
`fill`, `fill-opacity`, `fill-rule`, `stroke`, `stroke-width`, `stroke-linecap`, `stroke-linejoin`, `stroke-dasharray`, `stroke-dashoffset`, `stroke-opacity`, `paint-order`.

# 34. Practice Projects and Learning Roadmap

## Beginner
1. Profile card using box model, fonts, borders and shadows.
2. Responsive navbar using flexbox and media queries.
3. Product gallery using Grid and `object-fit`.
4. Login form with focus, validation, and disabled states.

## Intermediate
5. Responsive admin dashboard with sidebar, grid, and data table.
6. Dark/light theme using custom properties and `color-scheme`.
7. Animated pricing cards with transition and reduced-motion support.
8. Scroll progress bar and section-reveal animation with graceful fallback.

## Advanced
9. CSS 3D card flip and cube with keyboard/touch-friendly alternatives.
10. Premium landing page with layered gradients, responsive type, and motion.
11. Design system with cascade layers, tokens, components, and utilities.
12. Accessible responsive component gallery documenting browser support.

### Recommended learning order

`Syntax → Selectors → Cascade → Box Model → Typography → Flexbox → Grid → Responsive Design → Variables → Forms → Pseudo-Classes → Transitions → Keyframes → 3D Transforms → Scroll Animations → Accessibility → Performance → Design System`

### Completion checklist

- [ ] Explain cascade, specificity, inheritance and layers.
- [ ] Build a responsive layout with Grid and Flexbox.
- [ ] Use rem, %, viewport and container units appropriately.
- [ ] Style keyboard focus, forms, hover and disabled states.
- [ ] Create dark/light themes with custom properties.
- [ ] Build transitions and `@keyframes` animations.
- [ ] Build a working 3D transform scene.
- [ ] Make motion respect reduced-motion settings.
- [ ] Use responsive images, aspect ratio, and intrinsic sizing.
- [ ] Debug computed styles and stacking contexts in DevTools.
- [ ] Check compatibility for modern features before shipping.
- [ ] Test with keyboard, touch, zoom, and reduced-motion preferences.

# 35. Official Documentation

The official MDN CSS reference is the best index for checking syntax, all known standard properties, selectors, functions, at-rules, data types, and browser compatibility:

- CSS Reference: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference
- CSS Guides: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides
- Selectors: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_selectors
- CSS Flexbox: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_flexible_box_layout
- CSS Grid: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout
- Transforms: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Transforms
- Animations: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Animations
- Scroll-driven animations: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations
- Container queries: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment/Container_queries
- Accessibility: https://developer.mozilla.org/en-US/docs/Web/Accessibility

---

## Final note

CSS is continuously evolving. Treat this guide as a broad course and practical reference, then use the official documentation for the exact grammar and compatibility of a specific property/function. The 3D and “4D-like” recipes are starting points: tune motion intensity, test on real devices, and always provide a usable reduced-motion alternative.
