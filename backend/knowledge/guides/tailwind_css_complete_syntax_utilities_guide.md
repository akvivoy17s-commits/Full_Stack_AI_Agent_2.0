# Tailwind CSS — Complete Syntax, Utilities, Variants & Full-Stack UI Guide

> A practical reference for Tailwind CSS: installation, utility classes, responsive design, state variants, theme customization, CSS directives, animation, accessibility, React integration, and production workflows.

**Documentation checked:** 18 October 2026  
**Release reference checked:** Tailwind CSS **v4.3.3** on the official release page. Verify the current version and your framework compatibility before installing.  
**Main syntax covered:** Tailwind CSS v4 (CSS-first configuration). A dedicated section explains common v3 differences.

> **Scope note:** Tailwind utilities are generated from a large and extensible set of CSS properties, values, variants, theme tokens, arbitrary values, and plugin-defined utilities. This guide covers the major built-in utility families and syntax patterns; it cannot guarantee a literal, permanent inventory of every possible class or future API. Use the official utility reference linked at the end to confirm a specific class.

---

## Contents

1. [What Tailwind CSS Is](#1-what-tailwind-css-is)
2. [How Utility Classes Work](#2-how-utility-classes-work)
3. [Install Tailwind CSS v4](#3-install-tailwind-css-v4)
4. [Tailwind v4 vs v3](#4-tailwind-v4-vs-v3)
5. [Core Class Syntax](#5-core-class-syntax)
6. [Responsive Design](#6-responsive-design)
7. [State and Modifier Variants](#7-state-and-modifier-variants)
8. [Layout and Display](#8-layout-and-display)
9. [Position, Z-Index and Overflow](#9-position-z-index-and-overflow)
10. [Flexbox](#10-flexbox)
11. [CSS Grid](#11-css-grid)
12. [Spacing: Margin, Padding and Gap](#12-spacing-margin-padding-and-gap)
13. [Sizing and Aspect Ratio](#13-sizing-and-aspect-ratio)
14. [Typography](#14-typography)
15. [Colors and Opacity](#15-colors-and-opacity)
16. [Backgrounds and Gradients](#16-backgrounds-and-gradients)
17. [Borders, Radius and Outline](#17-borders-radius-and-outline)
18. [Shadows, Opacity and Blending](#18-shadows-opacity-and-blending)
19. [Filters and Backdrop Filters](#19-filters-and-backdrop-filters)
20. [Transforms and 3D Effects](#20-transforms-and-3d-effects)
21. [Transitions and Animations](#21-transitions-and-animations)
22. [Interactivity and Scroll](#22-interactivity-and-scroll)
23. [Tables, Lists and Content](#23-tables-lists-and-content)
24. [SVG and Accessibility Utilities](#24-svg-and-accessibility-utilities)
25. [Arbitrary Values and Properties](#25-arbitrary-values-and-properties)
26. [CSS-First Theme Customization](#26-css-first-theme-customization)
27. [Directives and Custom Utilities](#27-directives-and-custom-utilities)
28. [Dark Mode and Design Tokens](#28-dark-mode-and-design-tokens)
29. [Reusable Components and `@apply`](#29-reusable-components-and-apply)
30. [Source Detection and Dynamic Classes](#30-source-detection-and-dynamic-classes)
31. [React / Next.js Integration](#31-react--nextjs-integration)
32. [Forms and Common UI Patterns](#32-forms-and-common-ui-patterns)
33. [Accessibility and Motion Preferences](#33-accessibility-and-motion-preferences)
34. [Performance and Production Build](#34-performance-and-production-build)
35. [Debugging Common Problems](#35-debugging-common-problems)
36. [Tailwind v3 Reference](#36-tailwind-v3-reference)
37. [Utility Family Cheat Sheet](#37-utility-family-cheat-sheet)
38. [Learning Roadmap](#38-learning-roadmap)
39. [Official Documentation](#39-official-documentation)

---

## 1. What Tailwind CSS Is

Tailwind CSS is a utility-first CSS framework. Instead of writing a unique CSS class for every component, you combine small utility classes directly in HTML/JSX.

```html
<button class="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700">
  Save changes
</button>
```

This expresses border radius, background color, padding, font weight, text color, and hover state without a separate component-specific CSS rule.

### Benefits
- Fast styling directly in markup or JSX.
- Responsive styling with prefixes like `sm:`, `md:`, and `lg:`.
- Interaction states such as `hover:`, `focus-visible:`, and `disabled:`.
- Design tokens through CSS theme variables.
- Arbitrary values for unusual measurements or CSS values.
- Build-time generation of CSS, normally without a runtime styling engine.

### Tailwind is not
- A JavaScript component library.
- A replacement for semantic HTML.
- A JavaScript animation engine.
- A backend framework.
- A guarantee that a UI is accessible or responsive automatically.

Tailwind scans source files for class candidates and generates matching CSS. It does not interpret arbitrary runtime string concatenation reliably; see [Source detection and dynamic classes](#30-source-detection-and-dynamic-classes).

---

## 2. How Utility Classes Work

A class commonly corresponds to a CSS declaration or a short group of declarations.

| Tailwind class | Rough CSS meaning |
|---|---|
| `block` | `display: block` |
| `flex` | `display: flex` |
| `grid` | `display: grid` |
| `hidden` | `display: none` |
| `p-4` | padding based on the spacing scale |
| `mx-auto` | horizontal margins set to auto |
| `w-full` | width: 100% |
| `max-w-xl` | maximum width from the width scale |
| `font-semibold` | semibold font weight |
| `text-center` | text-align: center |
| `rounded-lg` | border radius from the radius scale |
| `shadow-lg` | box shadow from the shadow scale |
| `hover:bg-blue-700` | background changes on hover |
| `md:grid-cols-3` | three grid columns at the `md` breakpoint and above |

Classes are independent pieces you can combine:

```html
<section class="mx-auto max-w-6xl px-4 py-12 md:px-8 lg:py-20">
  <h1 class="text-3xl font-bold tracking-tight md:text-5xl">
    Build better interfaces
  </h1>
</section>
```

Tailwind Preflight includes a base reset. Existing projects that combine Tailwind with legacy CSS frameworks should test base styling carefully.

---

## 3. Install Tailwind CSS v4

Follow the installation path for your build tool. The Vite path is a strong choice for modern frontend projects.

### Vite

```bash
npm create vite@latest my-project
cd my-project
npm install
npm install tailwindcss @tailwindcss/vite
```

`vite.config.ts`:

```ts
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [tailwindcss()],
});
```

Your main CSS file (for example, `src/style.css`):

```css
@import "tailwindcss";
```

Import that stylesheet from the application's entry file if the framework does not already do so:

```ts
import './style.css';
```

Run:

```bash
npm run dev
```

### Tailwind CLI

```bash
npm install tailwindcss @tailwindcss/cli
```

Input CSS:

```css
@import "tailwindcss";
```

A general CLI pattern is:

```bash
npx @tailwindcss/cli -i ./src/input.css -o ./dist/output.css --watch
```

Check `npx @tailwindcss/cli --help` for exact flags in the installed release.

### PostCSS

Install the v4 PostCSS integration when the build tool uses PostCSS:

```bash
npm install tailwindcss @tailwindcss/postcss postcss
```

Configure `@tailwindcss/postcss` as the plugin according to the official docs for your build system. In v4, do not blindly copy old v3 PostCSS configurations.

### Important installation notes
- Tailwind v4 uses `@import "tailwindcss";` in CSS.
- Framework-specific setups (Next.js, Angular, Nuxt, SvelteKit, Laravel, etc.) can have their own integration instructions.
- The Play CDN is appropriate for experiments and quick demos, not the recommended production build.
- Keep `tailwindcss`, the adapter/plugin, and framework versions compatible.

---

## 4. Tailwind v4 vs v3

Tailwind v4 moved to a CSS-first configuration model and changed some utilities and setup assumptions.

| Area | v4 approach | Common v3 approach |
|---|---|---|
| CSS entry | `@import "tailwindcss";` | `@tailwind base; @tailwind components; @tailwind utilities;` |
| Main config | CSS `@theme` variables | `tailwind.config.js` / `.ts` |
| Vite | `@tailwindcss/vite` | Usually PostCSS plugin setup |
| PostCSS plugin | `@tailwindcss/postcss` | `tailwindcss` plugin |
| Source detection | Automatic scanning, with `@source` controls | `content` paths in config |
| Custom utility | CSS `@utility` | Config theme/plugin or CSS layer |
| Theme variables | CSS custom properties via `@theme` | `theme` / `extend` config |
| Browser support | Updated to modern browser capabilities | V3 supported older browser ranges |

Legacy JavaScript config/plugin support exists for migration cases, but v4 CSS-first configuration is the new default. Follow the [upgrade guide](https://tailwindcss.com/docs/upgrade-guide) rather than changing package versions without adapting the setup.

Some class names changed over time. Don't assume every v3 utility name works in v4.

---

## 5. Core Class Syntax

### Basic utility

```html
<div class="p-4 text-lg font-medium"></div>
```

### Variant syntax

```html
<button class="bg-blue-600 hover:bg-blue-700 focus-visible:ring-2">
  Submit
</button>
```

General form:

```text
variant:utility
variant1:variant2:utility
```

Examples:

```html
<div class="md:flex lg:gap-8"></div>
<button class="disabled:cursor-not-allowed disabled:opacity-50"></button>
<li class="first:pt-0 last:border-b-0"></li>
```

### Negative values

```html
<div class="-mt-4 -translate-y-1"></div>
```

Only utilities that support negative values accept them. For arbitrary CSS values, v4 generally uses syntax like `top-[-12px]` or `-mt-[3rem]`; test the exact utility because canonicalization can differ by version.

### Important modifier

```html
<div class="!mt-0"></div>
```

The important modifier can be useful when an intentional override is necessary, but widespread use often signals conflicting CSS or unclear component ownership. Confirm the exact syntax supported by the installed version.

### Important whole stylesheet

An important strategy can be configured via the import in versions that support it, for example:

```css
@import "tailwindcss" important;
```

Use only when integrating with a codebase that requires it; it changes cascade behavior.

---

## 6. Responsive Design

Tailwind is mobile-first: an unprefixed class applies at all viewport sizes, while breakpoint-prefixed classes apply at that breakpoint and above.

Common default breakpoints:

| Prefix | Common default minimum width |
|---|---:|
| `sm:` | `40rem` / 640px |
| `md:` | `48rem` / 768px |
| `lg:` | `64rem` / 1024px |
| `xl:` | `80rem` / 1280px |
| `2xl:` | `96rem` / 1536px |

Theme customization can change breakpoint values. These are minimum-width breakpoints, not mutually exclusive devices.

```html
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
  ...
</div>
```

This means one column by default, two columns at `sm` and above, three at `lg`, and four at `xl`.

### Responsive spacing and text

```html
<section class="px-4 py-8 sm:px-6 md:px-10 md:py-16 lg:py-24">
  <h1 class="text-3xl sm:text-4xl lg:text-6xl">Responsive heading</h1>
</section>
```

### Max-width range variants

Tailwind supports variants such as `max-sm:` for below a breakpoint. It also supports arbitrary breakpoint ranges in documented syntax:

```html
<div class="md:max-lg:flex"></div>
```

Use range variants when a style is meant to apply only within a range.

### Container queries

Container queries respond to a parent's container size rather than only the viewport. Typical syntax uses `@container` and variants such as `@md:`:

```html
<div class="@container">
  <article class="flex flex-col @md:flex-row">
    ...
  </article>
</div>
```

A container name can also be set using the relevant container utility. Verify exact defaults and naming syntax in the current docs.

### Custom breakpoints

Tailwind v4 theme variables can customize breakpoints:

```css
@import "tailwindcss";

@theme {
  --breakpoint-3xl: 120rem;
}
```

Then you can use variants such as `3xl:grid-cols-6` in source classes.

---

## 7. State and Modifier Variants

### Pointer and keyboard states

```html
<button class="hover:bg-indigo-700 focus:outline-2 focus:outline-offset-2 focus:outline-indigo-600">
  Action
</button>
```

Common variants include:
- `hover:`
- `focus:`
- `focus-within:`
- `focus-visible:`
- `active:`
- `visited:`
- `target:`
- `enabled:`
- `disabled:`
- `checked:`
- `indeterminate:`
- `required:`
- `valid:`
- `invalid:`
- `in-range:`
- `out-of-range:`
- `placeholder-shown:`
- `autofill:`
- `read-only:`

Example:

```html
<input class="border p-3 invalid:border-red-600 focus-visible:outline-2 disabled:bg-gray-100" />
```

### Structural variants

```html
<li class="first:rounded-t-lg last:rounded-b-lg odd:bg-slate-50 even:bg-white">
  ...
</li>
```

Common variants: `first:`, `last:`, `only:`, `odd:`, `even:`, `empty:`, `nth-*` where supported, and `has-*`.

### Group and peer

```html
<a class="group flex items-center gap-3">
  <span class="text-slate-700 group-hover:text-blue-700">Open profile</span>
  <span class="transition-transform group-hover:translate-x-1">→</span>
</a>
```

`group-*` styles a descendant based on a parent carrying `group`.

```html
<label>
  <input type="checkbox" class="peer sr-only" />
  <span class="peer-checked:bg-blue-600">Toggle</span>
</label>
```

`peer-*` uses a sibling state; source order and sibling relationships matter.

### Parent, child, and arbitrary selectors

```html
<div class="[&>p]:mt-4">
  <p>Paragraph</p>
</div>
```

Useful documented forms include:
- `group-hover:*`
- `peer-checked:*`
- `has-[:checked]:*`
- `[&:nth-child(3)]:*`
- `**:*` for descendants (check current selector docs)
- `[&>svg]:size-5`

Don't use complex selector variants as a substitute for a clear reusable component structure.

### Attribute / data variants

```html
<button data-state="active" class="data-[state=active]:bg-blue-600">
  Tab
</button>
```

You can use ARIA-related variants and arbitrary attribute selectors where supported:

```html
<div aria-expanded="true" class="aria-expanded:font-semibold"></div>
```

### Dark mode

```html
<div class="bg-white text-slate-900 dark:bg-slate-950 dark:text-white">
  ...
</div>
```

The dark-mode trigger can be configured for system preference or a manual class/data attribute. See [Dark mode](https://tailwindcss.com/docs/dark-mode).

### Motion and preference variants

```html
<div class="motion-safe:animate-bounce motion-reduce:animate-none"></div>
<div class="contrast-more:border-2"></div>
<div class="print:hidden"></div>
```

Common environment variants include `motion-safe:`, `motion-reduce:`, `contrast-more:`, `contrast-less:`, `forced-colors:`, `portrait:`, `landscape:`, and `print:`.

---

## 8. Layout and Display

### Display utilities

```text
block inline inline-block flex inline-flex grid inline-grid
hidden flow-root contents table table-row table-cell list-item
```

Examples:

```html
<div class="hidden md:block">Desktop-only content</div>
<nav class="flex items-center">...</nav>
<div class="grid">...</div>
```

Use `hidden` for layout visibility. For visually hidden-but-accessible content, use `sr-only`.

### Box sizing

```text
box-border box-content
```

Tailwind's base styles generally make elements use `box-sizing: border-box`.

### Aspect ratio and columns

```html
<div class="aspect-video overflow-hidden rounded-xl">
  <img class="h-full w-full object-cover" src="/hero.jpg" alt="Landscape" />
</div>

<div class="columns-2 gap-6 md:columns-3">...</div>
```

Common aspect classes include `aspect-square`, `aspect-video`, `aspect-auto`, and arbitrary ratios like `aspect-[4/3]`.

### Floats and clear

```text
float-start float-end float-right float-left float-none
clear-start clear-end clear-both clear-left clear-right clear-none
```

Floats are mainly useful for text wrapping around media; use flex/grid for ordinary page layouts.

### Isolation

```html
<div class="isolate">...</div>
```

`isolate` creates a new stacking context, useful for controlled overlay layering.

---

## 9. Position, Z-Index and Overflow

### Position

```text
static fixed absolute relative sticky
```

```html
<header class="sticky top-0 z-50">...</header>
<div class="relative">
  <span class="absolute right-2 top-2">New</span>
</div>
```

### Insets

Common utilities include:
- `top-*`, `right-*`, `bottom-*`, `left-*`
- `inset-*`
- `inset-x-*`, `inset-y-*`
- logical directions such as `inset-s-*`, `inset-e-*`
- arbitrary values like `top-[18px]`

```html
<div class="absolute inset-0"></div>
<div class="fixed bottom-4 right-4"></div>
```

Logical inset utilities are useful for writing directions. Check migration notes before copying old `start-*`/`end-*` classes from historical versions.

### Z-index

```text
z-auto z-0 z-10 z-20 z-30 z-40 z-50
```

Also supports arbitrary/custom values, e.g. `z-[100]`. A higher z-index cannot escape an ancestor stacking context.

### Overflow

```text
overflow-auto overflow-hidden overflow-clip overflow-visible overflow-scroll
overflow-x-auto overflow-x-hidden overflow-y-auto overflow-y-scroll
```

### Visibility and overscroll

```text
visible invisible collapse
overscroll-auto overscroll-contain overscroll-none
overscroll-x-auto overscroll-y-contain
```

`invisible` reserves layout space; `hidden` removes the element from layout.

---

## 10. Flexbox

### Activate flex layout

```html
<div class="flex items-center justify-between gap-4">
  <div>Brand</div>
  <nav>Links</nav>
</div>
```

### Direction and wrapping

```text
flex-row flex-row-reverse flex-col flex-col-reverse
flex-wrap flex-wrap-reverse flex-nowrap
```

```html
<div class="flex flex-col gap-3 md:flex-row md:items-center">
  ...
</div>
```

### Alignment

`justify-*` distributes along the main axis:

```text
justify-start justify-end justify-center justify-between
justify-around justify-evenly justify-stretch justify-normal
```

`items-*` aligns items along the cross axis:

```text
items-start items-end items-center items-baseline items-stretch
```

Other alignment families: `content-*`, `self-*`, `justify-items-*`, `justify-self-*`, `place-items-*`, `place-content-*`, `place-self-*`.

### Grow, shrink, basis

```text
grow grow-0 shrink shrink-0
basis-auto basis-full basis-1/2 basis-1/3 basis-64
```

Common `flex` utilities include `flex-1`, `flex-auto`, `flex-initial`, and `flex-none`.

### Order and gap

```html
<div class="flex gap-4">
  <aside class="order-2 md:order-1">Sidebar</aside>
  <main class="order-1 md:order-2 flex-1">Main</main>
</div>
```

Flex `order` changes visual placement, not DOM order or keyboard reading order. Avoid using it to create a confusing accessibility experience.

---

## 11. CSS Grid

### Columns and rows

```html
<div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
  <article>One</article>
  <article>Two</article>
  <article>Three</article>
  <article>Four</article>
</div>
```

Common patterns:
```text
grid-cols-1 grid-cols-2 grid-cols-3 ... grid-cols-12
grid-rows-1 grid-rows-2 ... grid-rows-6
grid-cols-none grid-rows-none
```

Arbitrary template definitions:

```html
<div class="grid grid-cols-[240px_minmax(0,1fr)] gap-6">...</div>
<div class="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-5">...</div>
```

Spaces inside arbitrary values are often written as underscores.

### Column/row spans

```text
col-auto col-span-1 col-span-2 col-span-full
col-start-1 col-end-4
row-auto row-span-2 row-span-full
row-start-1 row-end-3
```

```html
<div class="grid grid-cols-4 gap-4">
  <div class="col-span-2">Wide card</div>
  <div>Card</div>
  <div class="row-span-2">Tall card</div>
</div>
```

### Auto placement and sizing

Common utilities include `grid-flow-row`, `grid-flow-col`, `grid-flow-dense`, `auto-cols-auto`, `auto-cols-fr`, `auto-rows-auto`, and `auto-rows-fr`. Check the utility reference for exact available scale values.

---

## 12. Spacing: Margin, Padding and Gap

### Padding

```text
p-* px-* py-* pt-* pr-* pb-* pl-*
ps-* pe-*      (logical inline start/end)
```

Examples:
```html
<div class="p-4 px-6 py-8 md:p-10"></div>
```

### Margin

```text
m-* mx-* my-* mt-* mr-* mb-* ml-*
ms-* me-*      (logical inline start/end)
-mt-4          (negative margin, where supported)
mx-auto        (auto horizontal margin)
```

### Gap

```text
gap-* gap-x-* gap-y-*
```

```html
<div class="flex gap-4 md:gap-8">...</div>
```

Tailwind's spacing scale is theme-based. Common values include `0`, `px`, `0.5`, `1`, `1.5`, `2`, `2.5`, `3`, `3.5`, `4`, `5`, `6`, `8`, `10`, `12`, `16`, `20`, `24`, and larger steps. Values are not a complete hand-authored list: arbitrary and theme-defined values are also possible.

```html
<div class="mt-[23px] p-[clamp(1rem,3vw,3rem)]"></div>
```

Don't memorize every number. Learn the pattern and consult the scale when necessary.

---

## 13. Sizing and Aspect Ratio

### Width and height

```text
w-* min-w-* max-w-*
h-* min-h-* max-h-*
size-*          (width and height together)
```

Common examples:

```html
<div class="w-full max-w-5xl mx-auto"></div>
<div class="size-12 rounded-full"></div>
<div class="min-h-screen"></div>
<div class="h-dvh"></div>
```

Other commonly useful values include:
- `w-auto`, `w-full`, `w-screen`, `w-fit`, `w-min`, `w-max`
- `h-auto`, `h-full`, `h-screen`, `h-dvh`, `h-fit`
- `min-h-0`, `min-w-0` for flex/grid overflow handling
- max-width scale classes such as `max-w-sm`, `max-w-xl`, `max-w-2xl`, `max-w-prose`, and `max-w-screen-*`

### Fractions and arbitrary values

```html
<div class="w-1/2 md:w-2/3"></div>
<div class="w-[37rem]"></div>
<div class="h-[calc(100dvh-4rem)]"></div>
```

### Logical dimensions

Tailwind also supports logical sizing utilities such as `inline-size`, `min-inline-size`, `max-inline-size`, `block-size`, `min-block-size`, and `max-block-size` utility families. They are useful when supporting non-horizontal writing modes; refer to the official utility index for exact names and scales.

---

## 14. Typography

### Font family

```text
font-sans font-serif font-mono
font-[Family_Name]    (arbitrary font family)
```

Custom theme fonts are defined through `@theme`, shown later.

### Font size and line height

```text
text-xs text-sm text-base text-lg text-xl
text-2xl text-3xl text-4xl text-5xl text-6xl
text-7xl text-8xl text-9xl
leading-none leading-tight leading-snug leading-normal leading-relaxed leading-loose
```

```html
<h1 class="text-4xl font-bold leading-tight tracking-tight md:text-6xl">
  Dashboard
</h1>
```

### Weight, style, spacing

```text
font-thin font-extralight font-light font-normal font-medium
font-semibold font-bold font-extrabold font-black
italic not-italic
tracking-tighter tracking-tight tracking-normal tracking-wide tracking-wider
```

### Text alignment and wrapping

```text
text-left text-center text-right text-justify
text-start text-end
text-wrap text-nowrap text-balance text-pretty
truncate text-ellipsis text-clip
break-normal break-words break-all
whitespace-normal whitespace-nowrap whitespace-pre
whitespace-pre-line whitespace-pre-wrap
```

```html
<p class="line-clamp-3 text-pretty text-slate-600">
  Longer description ...
</p>
```

### Text decoration and transformation

```text
uppercase lowercase capitalize normal-case
underline overline line-through no-underline
decoration-solid decoration-dotted decoration-dashed decoration-wavy
underline-offset-*
decoration-*
```

### List and numeric text

```text
list-none list-disc list-decimal list-inside list-outside
tabular-nums proportional-nums lining-nums oldstyle-nums
ordinal slashed-zero
```

### Text columns and indentation

Tailwind provides line clamp, indent, hyphenation, word break, overflow-wrap, vertical alignment, and tab-size utilities. Find the precise utility in the official typography section if you need a less common property.

---

## 15. Colors and Opacity

### Text and background colors

```html
<p class="text-slate-700">Body copy</p>
<section class="bg-slate-950 text-white">...</section>
<button class="bg-blue-600 hover:bg-blue-700 text-white">Save</button>
```

Common palette families include neutral/slate/gray/zinc, red/orange/amber/yellow/lime/green/emerald/teal/cyan/sky/blue/indigo/violet/purple/fuchsia/pink/rose, and others shown in the current docs.

Basic patterns:

```text
text-{color}-{shade}
bg-{color}-{shade}
border-{color}-{shade}
ring-{color}-{shade}
fill-{color}-{shade}
stroke-{color}-{shade}
```

Examples: `text-red-600`, `bg-emerald-500`, `border-slate-200`, `ring-blue-500`.

### Opacity modifiers

```html
<div class="bg-black/50 text-white/90 border-white/20"></div>
```

Slash opacity is supported for many color utilities. Exact syntax depends on whether the utility uses a color token or a custom value.

### Arbitrary colors

```html
<div class="bg-[#0b1020] text-[#e2e8f0] border-[rgb(255_255_255_/_0.12)]"></div>
```

### Color themes

In v4 you can define or override color tokens in CSS with `@theme`, or use arbitrary CSS color values. The official [Colors docs](https://tailwindcss.com/docs/colors) cover palettes and color variables.

---

## 16. Backgrounds and Gradients

### Background size/position/repeat

```text
bg-auto bg-cover bg-contain
bg-center bg-top bg-bottom bg-left bg-right
bg-no-repeat bg-repeat bg-repeat-x bg-repeat-y bg-repeat-round bg-repeat-space
bg-fixed bg-local bg-scroll
```

### Background origin and clip

Utilities include `bg-origin-border`, `bg-origin-padding`, `bg-origin-content`, `bg-clip-border`, `bg-clip-padding`, `bg-clip-content`, and `bg-clip-text`.

### Gradients

```html
<div class="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500"></div>
```

Modern Tailwind supports gradient-direction utilities such as `bg-linear-to-r` and related directions in v4. Prefer the exact syntax from the installed version rather than assuming older `bg-gradient-to-*` examples are canonical.

Possible direction concepts: to top/right/bottom/left and diagonal combinations. Combine with `from-*`, `via-*`, and `to-*` color stops.

### Background images / overlays

```html
<div class="bg-[url('/images/hero.webp')] bg-cover bg-center"></div>
<div class="bg-[linear-gradient(120deg,rgba(2,6,23,.95),rgba(30,41,59,.25)),url('/hero.webp')] bg-cover"></div>
```

Use arbitrary values carefully; long inline arbitrary expressions can become hard to maintain. CSS classes or theme utilities may be clearer when a value is reused.

---

## 17. Borders, Radius and Outline

### Border width and style

```text
border border-0 border-2 border-4 border-x border-y border-t border-r border-b border-l
border-solid border-dashed border-dotted border-double border-hidden border-none
```

### Radius

```text
rounded-none rounded-sm rounded rounded-md rounded-lg rounded-xl rounded-2xl
rounded-3xl rounded-full
rounded-t-lg rounded-b-lg rounded-s-lg rounded-e-lg
rounded-tl-lg rounded-tr-lg rounded-bl-lg rounded-br-lg
```

### Border colors

```html
<div class="border border-slate-200"></div>
<div class="divide-y divide-slate-200">...</div>
```

### Outline and ring

```html
<input class="rounded-md border border-slate-300 outline-none focus-visible:ring-2 focus-visible:ring-blue-600" />
```

Common families include `outline-*`, `outline-offset-*`, `ring-*`, and `ring-offset-*`. Avoid removing focus indicators unless you replace them with a visible, accessible alternative.

### Divide utilities

```text
divide-x divide-y divide-x-reverse divide-y-reverse
divide-solid divide-dashed divide-dotted divide-none
divide-{color}
```

These are handy for borders between direct children in a list or menu.

---

## 18. Shadows, Opacity and Blending

### Box and text shadow

```text
shadow-2xs shadow-xs shadow-sm shadow shadow-md shadow-lg shadow-xl shadow-2xl shadow-none
text-shadow-2xs text-shadow-xs text-shadow-sm text-shadow text-shadow-md text-shadow-lg
```

Exact scales have evolved; use the current docs for supported names.

```html
<article class="rounded-2xl bg-white p-6 shadow-lg shadow-slate-900/10">
  ...
</article>
```

### Opacity

```text
opacity-0 opacity-5 opacity-10 opacity-20 opacity-25 opacity-30
opacity-40 opacity-50 opacity-60 opacity-70 opacity-75 opacity-80
opacity-90 opacity-95 opacity-100
```

Theme-defined and arbitrary opacity values may also work.

### Blend modes

```text
mix-blend-normal mix-blend-multiply mix-blend-screen mix-blend-overlay
mix-blend-darken mix-blend-lighten mix-blend-difference
bg-blend-normal bg-blend-multiply bg-blend-screen bg-blend-overlay
```

### Masks

Tailwind has utilities for mask clip/composite/image/mode/origin/position/repeat/size/type. They support visual fade/cutout effects but have more browser and value nuances than basic layout classes; consult the [mask utility reference](https://tailwindcss.com/docs/mask-image).

---

## 19. Filters and Backdrop Filters

### Filter utilities

Common families include:
- `blur-*`
- `brightness-*`
- `contrast-*`
- `drop-shadow-*`
- `grayscale`
- `hue-rotate-*`
- `invert`
- `saturate-*`
- `sepia`

```html
<img class="grayscale hover:grayscale-0 transition" src="/photo.jpg" alt="..." />
<div class="blur-sm"></div>
```

### Backdrop filter

```html
<header class="bg-white/70 backdrop-blur-lg">
  ...
</header>
```

Common backdrop variants include blur, brightness, contrast, grayscale, hue rotation, inversion, opacity, saturation, and sepia. Be aware of browser support and performance when applying heavy filters over large surfaces.

---

## 20. Transforms and 3D Effects

### Translate and scale

```html
<div class="translate-y-1 hover:-translate-y-1 transition-transform"></div>
<div class="scale-95 hover:scale-100 transition-transform"></div>
```

Utilities include `translate-x-*`, `translate-y-*`, logical translate utilities in relevant versions, `scale-*`, `scale-x-*`, `scale-y-*`, `rotate-*`, `skew-x-*`, and `skew-y-*`.

### Rotate

```html
<div class="rotate-3 hover:rotate-0 transition-transform"></div>
```

### Transform origin

```text
origin-center origin-top origin-bottom origin-left origin-right
origin-top-left origin-top-right origin-bottom-left origin-bottom-right
```

### Perspective and 3D

Tailwind v4 includes utilities for CSS concepts such as `perspective-*`, `perspective-origin-*`, `transform-style-preserve-3d`, and `backface-hidden` (check the current utility index for exact naming).

```html
<div class="perspective-distant">
  <div class="transform-3d rotate-y-12">3D panel</div>
</div>
```

3D utility support has changed across releases. Verify class names in the current docs; custom CSS is appropriate for unusual 3D scenes.

### Zoom

A `zoom-*` family is available in current utility documentation, but CSS `zoom` differs from transforms and should be used intentionally.

---

## 21. Transitions and Animations

### Transition utility

```html
<button class="transition duration-200 ease-out hover:-translate-y-0.5 hover:shadow-lg">
  Hover me
</button>
```

Common classes:
- `transition`
- `transition-all`
- `transition-colors`
- `transition-opacity`
- `transition-shadow`
- `transition-transform`
- `transition-none`
- `duration-*`
- `delay-*`
- `ease-linear`, `ease-in`, `ease-out`, `ease-in-out`

Only properties that support smooth interpolation animate. `transition-all` can animate more properties than intended, so prefer a targeted transition when possible.

### Built-in animation utilities

Common built-ins include `animate-spin`, `animate-ping`, `animate-pulse`, `animate-bounce`, and `animate-none`.

```html
<div class="animate-pulse rounded-lg bg-slate-200"></div>
```

### Define custom keyframes in v4

```css
@import "tailwindcss";

@theme {
  --animate-float: float 5s ease-in-out infinite;

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }
}
```

Use it as:

```html
<div class="animate-float">Floating card</div>
```

### Reduce motion

```html
<div class="motion-safe:animate-bounce motion-reduce:animate-none">
  ...
</div>
```

Make sure motion is not the only way that information is communicated; offer reduced-motion behavior for decorative effects.

---

## 22. Interactivity and Scroll

### Pointer and selection

```text
cursor-pointer cursor-not-allowed cursor-wait cursor-grab cursor-grabbing cursor-text cursor-default
pointer-events-none pointer-events-auto
select-none select-text select-all select-auto
```

### Appearance and form controls

```text
appearance-none accent-blue-600 caret-blue-600
```

Also available are utilities for color scheme, field sizing, resize, forced color adjustment, and related controls.

### Scroll and snapping

```text
scroll-auto scroll-smooth
scroll-m-4 scroll-mt-20 scroll-p-4 scroll-pt-20
snap-none snap-x snap-y snap-both snap-mandatory snap-proximity
snap-start snap-end snap-center snap-align-none
snap-normal snap-always
```

Example:

```html
<div class="flex snap-x snap-mandatory gap-4 overflow-x-auto scroll-smooth">
  <article class="w-72 shrink-0 snap-center">Card</article>
  <article class="w-72 shrink-0 snap-center">Card</article>
</div>
```

### Resize and touch actions

```text
resize resize-x resize-y resize-none
touch-auto touch-none touch-pan-x touch-pan-y touch-manipulation
```

### Scrollbar utilities

Tailwind current docs include scrollbar color, scrollbar width, and scrollbar gutter families. Availability and browser behavior varies; verify the specific utility before relying on a visual effect.

### Will-change

```html
<div class="will-change-transform"></div>
```

Use `will-change` only when a measured animation/performance issue benefits from it; unnecessary use can consume resources.

---

## 23. Tables, Lists and Content

### Tables

```text
border-collapse border-separate
border-spacing-* border-spacing-x-* border-spacing-y-*
table-auto table-fixed
caption-top caption-bottom
```

### Lists

```html
<ul class="list-disc space-y-2 pl-5">
  <li>First</li>
  <li>Second</li>
</ul>
```

Utilities include `list-none`, `list-disc`, `list-decimal`, `list-inside`, `list-outside`, and custom list image helpers.

### Generated content

The `before:` and `after:` variants can create pseudo-elements. Pseudo-element content can need a content utility and should usually remain decorative.

```html
<span class="before:mr-2 before:content-['•']">List item</span>
```

Avoid putting essential or screen-reader-only information solely into CSS generated content.

### Truncation

```html
<p class="truncate">A very long piece of text...</p>
<p class="line-clamp-2">A paragraph that should display no more than two lines.</p>
```

Ensure the full text remains accessible where important (for example, with appropriate content design, title text where helpful, or an expanded view).

---

## 24. SVG and Accessibility Utilities

### SVG fill and stroke

```html
<svg class="size-6 fill-current text-blue-600" viewBox="0 0 24 24" aria-hidden="true">
  ...
</svg>
```

Common families: `fill-*`, `stroke-*`, and `stroke-width-*`.

### Screen-reader visibility

```text
sr-only not-sr-only
```

```html
<button>
  <svg aria-hidden="true" class="size-5">...</svg>
  <span class="sr-only">Close menu</span>
</button>
```

### Focus and disabled states

```html
<button class="rounded-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-not-allowed disabled:opacity-50">
  Save
</button>
```

Never assume color alone communicates success/error. Pair color with text/icons or other cues. Use semantic HTML, associated labels, appropriate heading order, and keyboard-operable controls.

---

## 25. Arbitrary Values and Properties

Arbitrary values are for CSS values not available as built-in utilities or theme tokens.

### Arbitrary size/color

```html
<div class="w-[37rem] rounded-[18px] bg-[#101827]"></div>
```

### Arbitrary CSS property

```html
<div class="[mask-type:luminance] [text-wrap:pretty]"></div>
```

General pattern:

```text
[property:value]
```

### Arbitrary selectors

```html
<div class="[&>h2]:mb-4 [&>p]:text-slate-600">
  <h2>Heading</h2>
  <p>Paragraph</p>
</div>
```

### `calc()`, CSS variables and functions

```html
<div class="h-[calc(100dvh-5rem)] w-[calc(100%-2rem)]"></div>
<div class="bg-(--brand-color) text-(--text-color)"></div>
```

CSS variable shorthand support varies by utility and version; explicit arbitrary syntax such as `bg-[var(--brand-color)]` is also a clear fallback.

### Arbitrary variants

```html
<div class="[&:nth-child(3)]:font-bold"></div>
<div class="[@supports(display:grid)]:grid"></div>
```

### Important caution
- Use underscores for spaces in many arbitrary values.
- Avoid building class strings by concatenating arbitrary fragments.
- Keep complicated reusable styles in named utilities or a component class when that improves maintainability.
- If a candidate contains special punctuation, verify that your source file and formatter preserve it correctly.

---

## 26. CSS-First Theme Customization

Tailwind v4 uses CSS `@theme` blocks to define design tokens that create utility classes.

```css
@import "tailwindcss";

@theme {
  --font-display: "Inter", "sans-serif";
  --color-brand-50: oklch(0.97 0.02 265);
  --color-brand-500: oklch(0.58 0.22 265);
  --color-brand-700: oklch(0.42 0.18 265);
  --spacing: 0.25rem;
  --radius-card: 1rem;
  --breakpoint-3xl: 120rem;
}
```

Then use generated theme utilities:

```html
<div class="font-display rounded-card bg-brand-500 p-6 text-white 3xl:p-10">
  Brand component
</div>
```

### Common theme namespaces

Typical namespaces correspond to:
- `--color-*`: color utility values.
- `--font-*`: font families.
- `--text-*`: font-size utilities (related line-height tokens can also be defined).
- `--font-weight-*`: font weights.
- `--tracking-*`: letter spacing.
- `--leading-*`: line heights.
- `--spacing-*`: spacing utilities.
- `--breakpoint-*`: responsive variants.
- `--container-*`: max-width/container scales.
- `--radius-*`: corner radius utilities.
- `--shadow-*`: box shadow utilities.
- `--inset-shadow-*`, `--drop-shadow-*`, `--text-shadow-*`: specialized shadow families.
- `--blur-*`, `--perspective-*`, `--aspect-*`, `--ease-*`, `--animate-*`: other utility families.

The exact recognized namespaces are documented in the [Theme variables reference](https://tailwindcss.com/docs/theme). Use the namespace expected by the utility you want to generate.

### Define base CSS and custom properties

```css
:root {
  --app-surface: #0b1020;
  --app-foreground: #eef2ff;
}

body {
  background: var(--app-surface);
  color: var(--app-foreground);
}
```

Use ordinary CSS where that is clearer than utility composition. Theme tokens and normal CSS custom properties can coexist.

---

## 27. Directives and Custom Utilities

Tailwind v4 has several special CSS directives and at-rules.

### `@import`

```css
@import "tailwindcss";
```

Imports Tailwind into the stylesheet.

### `@theme`

Defines design tokens that Tailwind uses to generate utilities/variants.

```css
@theme {
  --color-brand: #635bff;
}
```

### `@utility`

Create a reusable utility class that participates in variant generation:

```css
@utility content-auto {
  content-visibility: auto;
}
```

Then use:

```html
<div class="content-auto lg:content-auto">...</div>
```

A functional utility can accept a value in documented syntax. Consult the custom utilities docs for type-aware functions and the current `@utility` syntax.

### `@variant`

Apply a variant to custom CSS:

```css
.card {
  @variant dark {
    background: #0f172a;
    color: white;
  }
}
```

Check current syntax and variant configuration details in [Functions and directives](https://tailwindcss.com/docs/functions-and-directives).

### `@apply`

Inline existing utility declarations inside custom CSS:

```css
.btn-primary {
  @apply rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white;
}
```

Use it selectively; component props or reusable markup often make the design intent easier to trace.

### `@source`

Explicitly include source files that automatic source detection would otherwise miss:

```css
@import "tailwindcss";
@source "../packages/ui";
@source inline("underline");
```

Exact `@source inline(...)` support and syntax should be checked against the installed v4 version. It is useful for monorepos or classes produced by external packages.

### `@reference`

Makes a stylesheet's theme/utilities available to another stylesheet without duplicating the generated CSS output. This can be useful for CSS modules or Vue/Svelte component style blocks; see the current docs.

### `@config` and `@plugin`

For migration and compatibility, v4 can load legacy JavaScript configuration or plugins through documented directives. CSS-first `@theme`/`@utility` is preferred for new code when sufficient. Some legacy config features are not automatically migrated into the v4 CSS cascade, so check the upgrade guide.

### CSS at-rules vs Tailwind runtime functions

Tailwind v4 also documents CSS functions such as `--spacing()` and `--alpha()` for use in theme/custom CSS contexts. For example:

```css
.card {
  padding: calc(var(--spacing) * 6);
}
```

Prefer documented native CSS custom properties/functions from your current Tailwind release. Older v3 functions and plugin APIs may not carry over unchanged.

---

## 28. Dark Mode and Design Tokens

### System-based dark mode

```html
<div class="bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
  ...
</div>
```

### Manual class-based dark mode

When the application controls dark mode, configure the variant to follow a class or data attribute using the current documentation. A common CSS-first pattern is:

```css
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));
```

Then toggling a `dark` class on the root makes `dark:*` variants apply. Confirm that this matches your current configuration and app's theme strategy.

### Design tokens

Use a small set of meaningful variables instead of spreading unrelated hex codes through every component:

```css
@theme {
  --color-surface: #0b0b10;
  --color-panel: #16161f;
  --color-accent: #e11d48;
  --color-copy: #f4f4f5;
}
```

Use tokens for background, foreground, borders, accent, status colors, spacing, radii, typography, and elevation. Keep contrast readable, particularly for text over gradients or images.

---

## 29. Reusable Components and `@apply`

Tailwind encourages extracting reusable UI components in your framework. For example, in React:

```tsx
type ButtonProps = {
  children: React.ReactNode;
  disabled?: boolean;
  onClick?: () => void;
};

export function Button({ children, disabled, onClick }: ButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="rounded-lg bg-indigo-600 px-4 py-2 font-semibold text-white transition hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {children}
    </button>
  );
}
```

A CSS component class can be useful for a repeated pattern:

```css
@import "tailwindcss";

@layer components {
  .panel {
    @apply rounded-2xl border border-slate-200 bg-white p-6 shadow-sm;
  }
}
```

For most React applications, reusing a component is usually more expressive than scattering `.btn`/`.card` classes everywhere. Use a class abstraction when it is useful for HTML templates or a consistent shared pattern.

### Conditional class names

Use a helper (or small arrays joined into a string) instead of runtime-built partial class names:

```tsx
const className = isActive
  ? 'bg-indigo-600 text-white'
  : 'bg-slate-100 text-slate-900';

return <button className={className}>Tab</button>;
```

Packages like `clsx` and `tailwind-merge` are common options for class composition and conflict resolution in component libraries. They are external tools, not part of Tailwind core.

---

## 30. Source Detection and Dynamic Classes

Tailwind scans templates and source files for complete class-name candidates. A class that only exists as a dynamically concatenated string may not be detected.

### Risky pattern

```tsx
// Tailwind may not detect generated values from this string construction.
const className = `bg-${color}-600`;
```

### Better pattern: complete candidates

```tsx
const colorClasses = {
  blue: 'bg-blue-600 hover:bg-blue-700',
  red: 'bg-red-600 hover:bg-red-700',
  green: 'bg-green-600 hover:bg-green-700',
};

const className = colorClasses[color] ?? colorClasses.blue;
```

The complete class candidates are visible in source. `@source` can include external directories and documented inline source syntax can safelist known candidates when needed.

In v3, this problem was commonly handled through `content` paths and a `safelist` in `tailwind.config.js`. In v4, source control uses automatic detection and CSS directives such as `@source`. Check the exact feature supported in the installed major.

---

## 31. React / Next.js Integration

Use the official guide for the framework and version. Tailwind classes live in `className` in JSX.

```tsx
export function DashboardCard() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">Monthly revenue</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight">$24,580</h2>
        </div>
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700">
          +12.4%
        </span>
      </div>
    </section>
  );
}
```

### Conditional variants

```tsx
<button
  className={[
    'rounded-lg px-4 py-2 font-medium transition',
    isActive ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-900',
    disabled ? 'cursor-not-allowed opacity-50' : 'hover:-translate-y-px',
  ].join(' ')}
  disabled={disabled}
>
  Continue
</button>
```

### Responsive layouts

```tsx
<div className="mx-auto grid max-w-7xl grid-cols-1 gap-5 px-4 sm:px-6 md:grid-cols-2 xl:grid-cols-3">
  {items.map(item => <Card key={item.id} item={item} />)}
</div>
```

Use stable React keys, semantic HTML and real handlers. Tailwind classes do not make a button functional; wire form actions, navigation, and loading/error states in application code.

---

## 32. Forms and Common UI Patterns

### Responsive page shell

```html
<div class="min-h-dvh bg-slate-50 text-slate-900">
  <header class="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur">
    <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
      <a class="text-lg font-bold tracking-tight" href="/">Brand</a>
      <nav class="hidden gap-6 md:flex">
        <a class="text-slate-600 hover:text-slate-950" href="#features">Features</a>
        <a class="text-slate-600 hover:text-slate-950" href="#pricing">Pricing</a>
      </nav>
      <a class="rounded-lg bg-indigo-600 px-4 py-2 font-semibold text-white hover:bg-indigo-700" href="#start">
        Get started
      </a>
    </div>
  </header>

  <main class="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:py-20">
    <section class="grid items-center gap-10 lg:grid-cols-2">
      <div>
        <p class="font-semibold text-indigo-600">Launch faster</p>
        <h1 class="mt-4 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
          Build a better product.
        </h1>
        <p class="mt-5 max-w-xl text-lg leading-8 text-slate-600">
          Responsive layout, clear hierarchy, and consistent spacing.
        </p>
        <div class="mt-8 flex flex-wrap gap-3">
          <a href="#start" class="rounded-lg bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700">Start now</a>
          <a href="#features" class="rounded-lg border border-slate-300 px-5 py-3 font-semibold hover:bg-white">Learn more</a>
        </div>
      </div>
      <div class="aspect-[4/3] rounded-3xl bg-gradient-to-br from-indigo-500 via-violet-500 to-pink-500 shadow-2xl"></div>
    </section>

    <section id="features" class="mt-20 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
      <article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg">
        <div class="size-11 rounded-xl bg-indigo-100"></div>
        <h2 class="mt-5 text-xl font-semibold">Feature title</h2>
        <p class="mt-2 text-slate-600">Describe the value of this feature.</p>
      </article>
    </section>
  </main>
</div>
```

### Accessible form field

```html
<div>
  <label for="email" class="mb-2 block text-sm font-medium text-slate-800">
    Email address
  </label>
  <input
    id="email"
    name="email"
    type="email"
    autocomplete="email"
    required
    class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 shadow-sm placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
    placeholder="you@example.com"
  />
  <p class="mt-2 text-sm text-slate-500">We'll only use this to contact you.</p>
</div>
```

### Loading state

```html
<button disabled class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-white disabled:opacity-60">
  <span class="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white" aria-hidden="true"></span>
  Loading…
</button>
```

Remember that loading/disabled states need actual application state and accessible status announcements where appropriate.

---

## 33. Accessibility and Motion Preferences

- Use semantic elements (`button`, `a`, `nav`, `main`, `label`, `input`) correctly.
- Ensure every input has an accessible label.
- Provide visible keyboard focus; `focus-visible:` is usually useful.
- Don't rely on color alone to communicate state.
- Keep text contrast sufficient on backgrounds and gradients.
- Provide keyboard interaction for custom menus, tabs, dialogs and popovers.
- Use `aria-hidden="true"` for decorative icons, not for content that matters to assistive technology.
- Avoid making non-interactive elements look like clickable controls.
- Honor reduced-motion preferences:

```html
<div class="transition motion-reduce:transition-none motion-safe:hover:-translate-y-1">
  ...
</div>
```

- Avoid `select-none` on large content areas when users may reasonably need to copy text.
- Hiding content with `hidden` usually removes it from layout/accessibility tree; `sr-only` is for content that remains available to screen readers.
- Test with keyboard, zoom, high contrast/forced-colors, and a screen reader when possible.

---

## 34. Performance and Production Build

Tailwind's build process outputs CSS for detected candidates. For good results:
- Use production build mode from your framework/build tool.
- Keep source detection correct for monorepos and external UI packages.
- Use complete class names rather than runtime-built partial strings.
- Avoid adding every third-party component source without needing it.
- Don't make hundreds of arbitrary unique values when a design token would be clearer.
- Avoid excessively large custom CSS selectors and unnecessary `@apply` cascades.
- Test production output rather than relying only on the dev server.
- Keep dependencies updated and review upgrade notes.
- Use image optimization, semantic HTML and performance profiling too; Tailwind does not optimize large images or expensive JavaScript automatically.

For a Vite app:

```bash
npm run build
npm run preview
```

Production CSS is generated by the integration configured for the project. Exact output paths and commands are framework-specific.

---

## 35. Debugging Common Problems

### Tailwind classes have no effect
- Confirm `@import "tailwindcss";` is in the CSS entry for v4.
- Confirm that the stylesheet is imported by the app.
- Confirm the Vite/PostCSS/CLI integration is installed and configured.
- Restart the dev server after build configuration changes.
- Check browser devtools for stylesheet loading and invalid candidates.

### Dynamic class names are missing
Use complete class candidates in a map rather than `` `bg-${color}-500` ``. Include external package sources with `@source` when required.

### A v3 tutorial does not work
Check whether it uses v3 `@tailwind` directives, `tailwind.config.js`, old utility names, plugin APIs, or an older PostCSS plugin. Use the v4 upgrade guide.

### Responsive styles are unexpected
Remember mobile-first semantics: `md:flex` applies at `md` and above. Breakpoints are minimum-width by default. A later class in HTML does not automatically mean a later CSS cascade; Tailwind sorts generated CSS by utility rules.

### `@apply` error
Ensure the utility exists in the compiled stylesheet context. CSS modules or isolated component styles may require `@reference` depending on setup. See the current functions/directives docs.

### Custom theme class does not generate
Check your `@theme` variable namespace and naming. For example, a theme token must be in the namespace that maps to the utility you want. Check spelling and that source files are included.

### Custom CSS overridden unexpectedly
Inspect CSS layers, selector specificity, important modifiers, and styles imported from component libraries. Prefer a deliberate token/utility fix rather than adding `!important` repeatedly.

### Layout overflows on mobile
Use `min-w-0` in flex/grid children, add responsive constraints, wrap long text, check fixed widths, and inspect images/media. Tailwind cannot automatically choose a suitable responsive layout for content.

---

## 36. Tailwind v3 Reference

This section is for maintaining old projects. Don't mix v3 and v4 configuration instructions without checking compatibility.

### Typical v3 CSS entry

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Typical v3 configuration

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx,vue}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          500: '#6366f1',
          700: '#4338ca',
        },
      },
      fontFamily: {
        display: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
```

### Typical v3 custom theme usage

```html
<div class="bg-brand-500 font-display text-white"></div>
```

### v3 configuration properties commonly used
- `content`: files that Tailwind scans.
- `theme`: replaces/defines scales.
- `theme.extend`: extends the defaults.
- `plugins`: adds plugin APIs/utilities/components.
- `darkMode`: configures dark mode strategy.
- `prefix`: prefixes generated class names.
- `important`: affects utility importance/selector strategy.
- `safelist`: forces candidates to be generated.
- `corePlugins`: selectively disables core plugins (legacy feature).

Refer to the archived/versioned v3 docs for exact keys and plugin APIs. The v4 CSS-first model is different.

---

## 37. Utility Family Cheat Sheet

| CSS concept | Common Tailwind family / examples |
|---|---|
| Display | `block`, `inline`, `flex`, `grid`, `hidden` |
| Position | `static`, `relative`, `absolute`, `fixed`, `sticky` |
| Insets | `top-*`, `inset-*`, `inset-x-*`, `inset-y-*` |
| Layering | `z-*`, `isolate` |
| Overflow | `overflow-*`, `overflow-x-*`, `overflow-y-*` |
| Flex | `flex-*`, `grow-*`, `shrink-*`, `basis-*`, `order-*` |
| Grid | `grid-cols-*`, `grid-rows-*`, `col-span-*`, `row-span-*` |
| Alignment | `items-*`, `content-*`, `justify-*`, `self-*`, `place-*` |
| Spacing | `p-*`, `m-*`, `gap-*`, `space-x-*`, `space-y-*` |
| Sizing | `w-*`, `h-*`, `size-*`, `min-w-*`, `max-w-*` |
| Typography | `font-*`, `text-*`, `leading-*`, `tracking-*` |
| Color | `text-*`, `bg-*`, `border-*`, `ring-*`, `fill-*`, `stroke-*` |
| Background | `bg-cover`, `bg-center`, `bg-repeat-*`, gradient utilities |
| Border | `border-*`, `rounded-*`, `divide-*`, `outline-*`, `ring-*` |
| Effects | `shadow-*`, `opacity-*`, blend/mask utilities |
| Filters | `blur-*`, `brightness-*`, `contrast-*`, `backdrop-blur-*` |
| Transform | `translate-*`, `rotate-*`, `scale-*`, `skew-*`, perspective utilities |
| Transition | `transition-*`, `duration-*`, `delay-*`, `ease-*` |
| Animation | `animate-*`, custom `--animate-*` tokens |
| Interactivity | `cursor-*`, `pointer-events-*`, `select-*`, `resize-*` |
| Scrolling | `scroll-*`, `snap-*`, `overscroll-*` |
| SVG | `fill-*`, `stroke-*`, `stroke-width-*` |
| Accessibility | `sr-only`, `not-sr-only`, `forced-color-adjust-*` |
| Variants | `sm:`, `md:`, `hover:`, `focus:`, `dark:`, `group-*`, `peer-*` |

These are families rather than a promise that every possible suffix exists for every prefix. Use the official utility index for exact values.

---

## 38. Learning Roadmap

1. Learn semantic HTML and core CSS (box model, flexbox, grid, positioning).
2. Install Tailwind v4 and understand the class/variant syntax.
3. Practice spacing, sizing, responsive breakpoints, typography, colors and borders.
4. Build cards, navbars, forms, dashboards, modal layouts and responsive grids.
5. Learn hover/focus/disabled/dark/motion variants and accessibility basics.
6. Define design tokens with `@theme`; add custom utilities only when needed.
7. Learn source scanning and dynamic class pitfalls in React/Next.js.
8. Build a full landing page, dashboard, and form flow; test at mobile/tablet/desktop widths.
9. Check production build output and use the official utility docs as a reference rather than trying to memorize every class.

**Practice project:** Create a responsive SaaS dashboard with a sidebar, mobile navigation, dark mode, stat cards, a filter bar, a paginated table, accessible forms, loading/empty/error states, and keyboard focus styling.

---

## 39. Official Documentation

### Tailwind CSS
- [Official docs](https://tailwindcss.com/docs)
- [Installation](https://tailwindcss.com/docs/installation)
- [Vite installation](https://tailwindcss.com/docs/installation/using-vite)
- [Framework guides](https://tailwindcss.com/docs/installation/framework-guides)
- [Utility-first styling](https://tailwindcss.com/docs/styling-with-utility-classes)
- [Hover, focus and states](https://tailwindcss.com/docs/hover-focus-and-other-states)
- [Responsive design](https://tailwindcss.com/docs/responsive-design)
- [Dark mode](https://tailwindcss.com/docs/dark-mode)
- [Theme variables](https://tailwindcss.com/docs/theme)
- [Colors](https://tailwindcss.com/docs/colors)
- [Adding custom styles](https://tailwindcss.com/docs/adding-custom-styles)
- [Detecting classes in source files](https://tailwindcss.com/docs/detecting-classes-in-source-files)
- [Functions and directives](https://tailwindcss.com/docs/functions-and-directives)
- [Preflight](https://tailwindcss.com/docs/preflight)
- [Utility index / category list](https://tailwindcss.com/docs/installation)
- [Upgrade guide](https://tailwindcss.com/docs/upgrade-guide)
- [Release history](https://github.com/tailwindlabs/tailwindcss/releases)
- [Playground](https://play.tailwindcss.com/)

### Related references
- [MDN CSS reference](https://developer.mozilla.org/en-US/docs/Web/CSS)
- [MDN responsive design](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design)
- [React documentation](https://react.dev/)
- [Vite documentation](https://vite.dev/)

---

## Final Notes

1. Learn the class pattern and utility families; do not try to memorize every combination.
2. This guide focuses on Tailwind CSS v4; use the dedicated v3 notes only when maintaining older projects.
3. Tailwind is a styling tool, not a component library or application logic framework.
4. Keep HTML semantic, interaction logic functional, and keyboard focus visible.
5. Confirm the installed version's official docs when using newer classes, CSS functions, directives, or uncommon utilities.
