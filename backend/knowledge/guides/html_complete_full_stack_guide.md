# Complete HTML Guide for Full-Stack Web Development

**HTML syntax • Elements • Attributes • Forms • Accessibility • Metadata • Media • Browser APIs • JavaScript DOM methods**

> **Scope note:** HTML is a markup language, not a programming language, so HTML itself does not define functions in the way JavaScript does. It defines document structure with elements and attributes. This guide also includes common JavaScript DOM methods and browser APIs used to read and update HTML because those are essential when building websites. There is no finite official count of “100% of HTML”; the standard and browser APIs evolve over time. This guide is a broad practical reference, not a promise to enumerate every browser-specific API or future feature.

## Table of Contents

1. What HTML Is
2. A Complete HTML Document
3. HTML Syntax Rules
4. Elements, Tags, Attributes, and Nesting
5. Text, Headings, Paragraphs, and Line Breaks
6. Semantic Page Structure
7. Links and URL Syntax
8. Images and Responsive Images
9. Audio and Video
10. Lists
11. Tables
12. Forms: Complete Reference
13. Form Validation and Submission
14. Global Attributes
15. Data Attributes and ARIA
16. Metadata, SEO, and Social Sharing
17. Scripts, Stylesheets, and Resource Hints
18. Embedded Content: iframe, object, embed
19. SVG, MathML, and Canvas
20. Interactive HTML Elements
21. Templates and Web Components
22. HTML Entities and Special Characters
23. Accessibility Checklist
24. Security Considerations
25. Performance and Loading
26. HTML with CSS and JavaScript
27. DOM: Finding and Updating HTML
28. DOM Events and Event Handling
29. Forms with JavaScript
30. Browser Storage and HTML-Related APIs
31. File Upload and Drag-and-Drop Concepts
32. Progressive Enhancement and Responsive Design
33. Deprecated and Obsolete Elements to Avoid
34. Common Errors and Debugging
35. Full Working Website Example
36. Element Quick Reference
37. Attribute Quick Reference
38. Practice Projects
39. Full-Stack Learning Roadmap
40. Official References

---

# 1. What HTML Is

HTML means **HyperText Markup Language**. It describes the structure and meaning of content on the web. Browsers parse HTML into a Document Object Model (DOM), which CSS can style and JavaScript can manipulate.

- **HTML:** structure and semantics.
- **CSS:** appearance, layout, animation, and responsive styling.
- **JavaScript / TypeScript:** logic, interactions, API calls, and dynamic behavior.
- **Backend:** server-side logic, authentication, authorization, and data processing.
- **Database:** persistent application data.

HTML elements usually consist of an opening tag, content, and a closing tag. Some elements are **void elements**, and cannot have child content or closing tags.

---

# 2. A Complete HTML Document

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="A simple example website.">
  <title>My Website</title>
  <link rel="stylesheet" href="styles.css">
  <script src="app.js" defer></script>
</head>
<body>
  <header>
    <h1>Welcome</h1>
  </header>

  <main>
    <p>This page uses valid HTML structure.</p>
    <button type="button" id="helloButton">Say hello</button>
  </main>

  <footer>
    <small>&copy; 2026 My Website</small>
  </footer>
</body>
</html>
```

### Document parts

- `<!doctype html>`: requests standards mode in modern browsers.
- `<html lang="en">`: root element and document language.
- `<head>`: metadata, title, CSS links, scripts, and resource hints.
- `<meta charset="UTF-8">`: character encoding.
- `<meta name="viewport" ...>`: mobile viewport configuration.
- `<title>`: page title in the browser tab and commonly a search result title.
- `<body>`: visible document content.

The browser can repair malformed HTML, but relying on automatic repair makes bugs harder to diagnose. Use a validator and proper nesting.

---

# 3. HTML Syntax Rules

## 3.1 Start tags, end tags, and content

```html
<p>This is a paragraph.</p>
<strong>Important text</strong>
```

## 3.2 Attributes

```html
<a href="https://example.com" target="_blank" rel="noopener noreferrer">
  Open example
</a>
```

An attribute generally appears in the start tag as `name="value"`. Quoted values are recommended for consistency and safety.

## 3.3 Void elements

Void elements do not wrap content and do not have end tags. Common ones include:

`<area>`, `<base>`, `<br>`, `<col>`, `<embed>`, `<hr>`, `<img>`, `<input>`, `<link>`, `<meta>`, `<source>`, `<track>`, `<wbr>`.

Correct:

```html
<img src="logo.png" alt="Company logo">
<br>
<input type="text" name="username">
```

Incorrect in HTML syntax: `<img></img>` or `<input>content</input>`.

## 3.4 Nesting

Correct nesting:

```html
<p>Read the <strong>important</strong> note.</p>
```

Do not put block containers such as `<div>` inside a `<p>`. Close nested elements in the reverse order in which they were opened.

## 3.5 Comments

```html
<!-- This note is not displayed as page content. -->
```

Do not put secrets in comments. Users can inspect delivered HTML.

## 3.6 Attribute values and boolean attributes

Boolean attributes are true when present and false when absent. The string value `"false"` does not turn a boolean attribute off.

```html
<input required disabled>
<button type="button" autofocus>Continue</button>
```

To enable a boolean attribute, include it. To disable it, omit it.

## 3.7 Case and whitespace

HTML tag and attribute names are ASCII case-insensitive, but lowercase is the standard convention. Whitespace in ordinary text is generally collapsed visually; whitespace in `<pre>` and some other contexts is preserved.

---

# 4. Elements, Tags, Attributes, and Nesting

An **element** is the parsed node, a **tag** is the markup notation, and an **attribute** configures an element.

```html
<a class="nav-link" href="/about" aria-current="page">About</a>
```

- Element: anchor.
- Attributes: `class`, `href`, `aria-current`.
- Text content: `About`.

### Content categories (conceptual overview)

- **Metadata content:** `<title>`, `<meta>`, `<link>`, `<style>`, `<script>` in relevant contexts.
- **Flow content:** most elements allowed in the body.
- **Phrasing content:** text and inline semantic elements.
- **Heading content:** `<h1>`–`<h6>`.
- **Sectioning content:** `<article>`, `<aside>`, `<nav>`, `<section>`.
- **Embedded content:** `<img>`, `<video>`, `<audio>`, `<iframe>`, `<canvas>`, SVG, and others.
- **Interactive content:** links, buttons, form controls, `<details>`, `<summary>`, `<select>`, and others.
- **Form-associated content:** form controls and related elements.

Content models are contextual. Not every element can contain every other element; consult the element reference when unsure.

---

# 5. Text, Headings, Paragraphs, and Line Breaks

```html
<h1>Main page heading</h1>
<h2>Major section</h2>
<h3>Subsection</h3>
<p>A paragraph of text.</p>
<p>Second paragraph with <strong>important</strong> and <em>emphasized</em> text.</p>
<p><mark>Highlighted</mark> text, <small>small print</small>, and <del>removed</del> content.</p>
<p>Water is H<sub>2</sub>O. A square is x<sup>2</sup>.</p>
<p>Use <code>npm run dev</code> to start the project.</p>
<pre><code>function greet() {
  console.log("Hello");
}</code></pre>
<blockquote cite="https://example.com/source">
  <p>A block quotation.</p>
</blockquote>
<p><q>A short inline quotation.</q></p>
<p><abbr title="HyperText Markup Language">HTML</abbr> structures web pages.</p>
<p><cite>Example Book Title</cite></p>
<p><time datetime="2026-10-18">October 18, 2026</time></p>
<p><data value="SKU-123">Product 123</data></p>
<p><b>Attention-grabbing text</b> and <i>alternate voice</i> text.</p>
<p><u>Annotated text</u>; <s>no longer accurate</s>.</p>
<p>Author: <bdi>نص مختلط</bdi></p>
<p><bdo dir="rtl">This text has right-to-left direction.</bdo></p>
<p>Long<wbr>unbroken<wbr>word</p>
<p>First line<br>Second line</p>
<hr>
```

### Main text elements

- Headings: `<h1>` through `<h6>`.
- Paragraph: `<p>`.
- Importance: `<strong>`; stress emphasis: `<em>`.
- Generic inline container: `<span>`.
- Generic block container: `<div>`.
- Line break: `<br>`; thematic break: `<hr>`.
- Preformatted text: `<pre>`; code fragment: `<code>`.
- Citation, quotation, abbreviation, time, and data: `<cite>`, `<blockquote>`, `<q>`, `<abbr>`, `<time>`, `<data>`.
- Inserted and deleted text: `<ins>`, `<del>`.
- Superscript and subscript: `<sup>`, `<sub>`.

Avoid choosing elements just for their default appearance. Use semantic meaning first and CSS for appearance.

---

# 6. Semantic Page Structure

```html
<body>
  <header>
    <a href="/" aria-label="Example home">Example</a>
    <nav aria-label="Main navigation">
      <ul>
        <li><a href="/products">Products</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </nav>
  </header>

  <main id="main-content">
    <article>
      <header>
        <h1>Article title</h1>
        <p>Published <time datetime="2026-10-18">October 18, 2026</time></p>
      </header>
      <section aria-labelledby="intro-heading">
        <h2 id="intro-heading">Introduction</h2>
        <p>Article content.</p>
      </section>
    </article>
    <aside aria-label="Related content">Related content</aside>
  </main>

  <footer><p>Copyright information</p></footer>
</body>
```

### Common semantic elements

`<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<aside>`, `<footer>`, `<address>`, `<figure>`, and `<figcaption>`.

- Use one clear primary `<main>` region for the page content.
- `<section>` normally represents a thematic section and often has a heading.
- `<article>` is a self-contained composition that could stand independently.
- `<nav>` marks a major navigation area.
- `<aside>` contains tangentially related content.
- `<figure>` and `<figcaption>` associate media or illustrations with a caption.
- `<address>` provides contact information for the nearest article or page owner; it is not a generic address styling tag.

---

# 7. Links and URL Syntax

```html
<a href="https://developer.mozilla.org/" target="_blank" rel="noopener noreferrer">
  MDN reference
</a>
<a href="/products">Internal route</a>
<a href="#pricing">Jump to pricing</a>
<a href="mailto:hello@example.com">Send email</a>
<a href="tel:+911234567890">Call</a>
<a href="report.pdf" download>Download report</a>

<section id="pricing">
  <h2>Pricing</h2>
</section>
```

Useful anchor attributes: `href`, `target`, `rel`, `download`, `hreflang`, `type`, `referrerpolicy`, `ping` (specialized). Use `rel="noopener noreferrer"` for links opened in a new tab when appropriate. Do not use `href="#"` as a substitute for a button. Use `<button>` to perform actions.

URL parts commonly include a scheme (`https:`), hostname, optional port, path, query (`?q=html`), and fragment (`#section`).

---

# 8. Images and Responsive Images

```html
<img
  src="images/team-800.jpg"
  alt="The development team at a planning meeting"
  width="800"
  height="533"
  loading="lazy"
  decoding="async">
```

### Responsive sources

```html
<img
  src="photo-800.jpg"
  srcset="photo-480.jpg 480w, photo-800.jpg 800w, photo-1200.jpg 1200w"
  sizes="(max-width: 600px) 100vw, (max-width: 1000px) 80vw, 800px"
  alt="Mountain landscape"
  width="1200"
  height="800">
```

### Picture and art direction

```html
<picture>
  <source media="(max-width: 600px)" srcset="portrait-small.webp" type="image/webp">
  <source srcset="landscape-large.webp" type="image/webp">
  <img src="landscape-large.jpg" alt="A landscape at sunrise" width="1200" height="700">
</picture>
```

- Provide meaningful `alt` text for informative images.
- Use `alt=""` for purely decorative images when appropriate.
- Set `width` and `height` to help reserve layout space.
- Use `loading="lazy"` for appropriate below-the-fold images, not usually for the page's main hero image.
- SVG can be embedded with `<img>`, directly as inline `<svg>`, or through other methods depending on use case.

### Image maps

```html
<img src="map.jpg" alt="Map of regions" usemap="#regions" width="600" height="400">
<map name="regions">
  <area shape="rect" coords="20,20,200,120" href="/north" alt="Northern region">
</map>
```

---

# 9. Audio and Video

```html
<video controls width="720" poster="poster.jpg" preload="metadata">
  <source src="movie.webm" type="video/webm">
  <source src="movie.mp4" type="video/mp4">
  <track kind="captions" src="captions-en.vtt" srclang="en" label="English" default>
  Your browser does not support this video.
</video>

<audio controls preload="metadata">
  <source src="audio.ogg" type="audio/ogg">
  <source src="audio.mp3" type="audio/mpeg">
  Your browser does not support this audio.
</audio>
```

Relevant media attributes: `controls`, `autoplay`, `muted`, `loop`, `preload`, `poster`, `playsinline`, `width`, `height`, and `crossorigin` where supported. Autoplay with sound is commonly blocked and can harm accessibility; do not depend on it.

`<track>` supports subtitles/captions, descriptions, chapters, and metadata, depending on `kind`. WebVTT files typically use the `.vtt` extension.

---

# 10. Lists

```html
<ul>
  <li>Unordered item</li>
  <li>Another item</li>
</ul>

<ol start="3" reversed>
  <li>Third item</li>
  <li>Second item</li>
</ol>

<ol>
  <li>Prepare
    <ol>
      <li>Install tools</li>
      <li>Create a project</li>
    </ol>
  </li>
</ol>

<dl>
  <dt>HTML</dt>
  <dd>Markup language for web documents.</dd>
  <dt>CSS</dt>
  <dd>Style rules for documents.</dd>
</dl>
```

- `<ul>`: unordered list.
- `<ol>`: ordered list; supports `start`, `reversed`, and `type`.
- `<li>`: list item.
- `<dl>`, `<dt>`, `<dd>`: description list, term, and description.

---

# 11. Tables

Use tables for tabular data, not general page layout.

```html
<table>
  <caption>Monthly sales</caption>
  <thead>
    <tr>
      <th scope="col">Month</th>
      <th scope="col">Sales</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">January</th>
      <td>120</td>
    </tr>
    <tr>
      <th scope="row">February</th>
      <td>150</td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <th scope="row">Total</th>
      <td>270</td>
    </tr>
  </tfoot>
</table>
```

Table-related elements: `<table>`, `<caption>`, `<thead>`, `<tbody>`, `<tfoot>`, `<tr>`, `<th>`, `<td>`, `<colgroup>`, `<col>`.

`colspan` and `rowspan` let cells span columns and rows. Give header cells appropriate `scope`; complex tables may need more deliberate header associations.

---

# 12. Forms: Complete Reference

```html
<form action="/signup" method="post" autocomplete="on">
  <fieldset>
    <legend>Create an account</legend>

    <label for="fullName">Full name</label>
    <input id="fullName" name="fullName" type="text" autocomplete="name" required minlength="2" maxlength="80">

    <label for="email">Email</label>
    <input id="email" name="email" type="email" autocomplete="email" required>

    <label for="password">Password</label>
    <input id="password" name="password" type="password" autocomplete="new-password" required minlength="10">

    <label for="role">Role</label>
    <select id="role" name="role" required>
      <option value="">Choose a role</option>
      <option value="developer">Developer</option>
      <option value="designer">Designer</option>
    </select>

    <label for="about">About you</label>
    <textarea id="about" name="about" rows="4" maxlength="500"></textarea>

    <label><input type="checkbox" name="terms" required> I accept the terms</label>
    <button type="submit">Create account</button>
    <button type="reset">Reset</button>
  </fieldset>
</form>
```

## 12.1 The `<form>` element

Main attributes: `action`, `method`, `enctype`, `autocomplete`, `name`, `novalidate`, `target`, `accept-charset`, `rel`. The form's actual accepted attributes depend on the standard and browser implementation.

- `method="get"`: sends form values in the URL query in normal browser submission.
- `method="post"`: sends the form data in the request body.
- `enctype="multipart/form-data"`: generally used for file uploads.
- `autocomplete`: controls browser autofill hints.
- `novalidate`: disables built-in validation for that form submission.

## 12.2 Common `<input>` types

```html
<input type="text">
<input type="search">
<input type="email">
<input type="password">
<input type="tel">
<input type="url">
<input type="number" min="1" max="100" step="1">
<input type="range" min="0" max="100" value="50">
<input type="date">
<input type="time">
<input type="datetime-local">
<input type="month">
<input type="week">
<input type="checkbox">
<input type="radio" name="plan" value="basic">
<input type="file" accept="image/*" multiple>
<input type="color" value="#3366ff">
<input type="hidden" name="csrfToken" value="server-issued-token">
<input type="submit" value="Submit">
<input type="reset" value="Reset">
<input type="button" value="Action">
<input type="image" src="submit.png" alt="Submit form">
```

Important note: a hidden field is not a secure place for secrets. Server-side code must validate and authorize every submitted value.

## 12.3 Labels, buttons, and grouping

- `<label for="fieldId">` associates a label with an element whose ID matches.
- `<button type="submit">` submits the form.
- `<button type="button">` does not submit by default.
- `<button type="reset">` resets controls to their initial values.
- `<fieldset>` groups controls.
- `<legend>` names a fieldset.
- `<output>` displays a result.
- `<datalist>` provides suggestions for compatible controls.
- `<select>`, `<option>`, `<optgroup>` implement selection controls.
- `<textarea>` is a multiline text field.

## 12.4 Validation attributes

`required`, `min`, `max`, `step`, `minlength`, `maxlength`, `pattern`, `multiple`, and `type` can participate in browser validation where applicable.

```html
<input name="postalCode" pattern="[0-9]{6}" inputmode="numeric" required aria-describedby="postalHelp">
<small id="postalHelp">Enter a six-digit postal code.</small>
```

Client-side validation improves the user experience but is not a security boundary. Validate data on the server as well.

## 12.5 File inputs

```html
<label for="avatar">Profile image</label>
<input id="avatar" name="avatar" type="file" accept="image/png,image/jpeg" required>
```

`accept` is only a file-picker hint, not proof that a file is safe. Server code must check file size, content, authorization, and allowed formats.

---

# 13. Form Validation and Submission

HTML offers native constraint validation and JavaScript can enhance it.

```html
<form id="contactForm">
  <label for="contactEmail">Email</label>
  <input id="contactEmail" name="email" type="email" required>
  <button type="submit">Send</button>
  <p id="formMessage" role="status"></p>
</form>
<script src="form.js" defer></script>
```

```js
const form = document.querySelector("#contactForm");
const message = document.querySelector("#formMessage");

form?.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!(form instanceof HTMLFormElement)) return;

  if (!form.reportValidity()) return;

  const data = new FormData(form);
  console.log(Object.fromEntries(data.entries()));
  if (message) message.textContent = "Form passed browser validation.";
});
```

Useful HTML form control properties and methods exposed through DOM interfaces include `value`, `checked`, `disabled`, `required`, `validity`, `validationMessage`, `checkValidity()`, `reportValidity()`, `setCustomValidity()`, `focus()`, and `select()` depending on the element.

---

# 14. Global Attributes

Global attributes are available on most HTML elements, though their meaning varies by element.

| Attribute | Purpose |
|---|---|
| `id` | Unique document identifier |
| `class` | CSS/JS grouping token(s) |
| `style` | Inline CSS declarations; avoid for large styling systems |
| `title` | Advisory text, not a replacement for a visible label |
| `lang` | Language of element content |
| `dir` | Text direction: `ltr`, `rtl`, or `auto` |
| `hidden` | Indicates content is not currently meant to be presented |
| `tabindex` | Focus order/focusability; use carefully |
| `autofocus` | Requests initial focus where supported; do not overuse |
| `contenteditable` | Makes content editable: `true`, `false`, or `plaintext-only` |
| `draggable` | Enables HTML drag-and-drop behavior where supported |
| `spellcheck` | Requests spell checking |
| `translate` | Hints whether text should be translated |
| `accesskey` | Keyboard shortcut hint; conflicts can occur |
| `inputmode` | Virtual keyboard hint |
| `enterkeyhint` | Virtual keyboard action hint |
| `autocapitalize` | Text capitalization hint |
| `data-*` | Custom data attributes |
| `role` | ARIA role where needed |
| `aria-*` | Accessibility states/properties |
| `slot` | Slot assignment for Web Components |
| `part` | Exposes a shadow-tree part for styling |
| `is` | Customized built-in element mechanism where supported |
| `nonce` | CSP nonce on relevant elements |

Example:

```html
<article id="product-42" class="product featured" data-product-id="42" lang="en">
  <h2>Example product</h2>
</article>
```

Read `data-*` with JavaScript:

```js
const product = document.querySelector("[data-product-id]");
console.log(product?.dataset.productId);
```

For `data-user-id`, JavaScript uses `dataset.userId` (kebab-case becomes camelCase).

---

# 15. Data Attributes and ARIA

## 15.1 ARIA basics

ARIA helps communicate roles, names, and states to assistive technologies. Prefer native semantic elements first.

```html
<button type="button" aria-expanded="false" aria-controls="extraDetails">
  More details
</button>
<div id="extraDetails" hidden>
  Additional information.
</div>
```

The attributes must reflect the actual UI state. `aria-expanded="false"` alone does not hide content; HTML/CSS/JavaScript must implement the behavior.

## 15.2 Common ARIA attributes

- `aria-label`, `aria-labelledby`, `aria-describedby`
- `aria-hidden`
- `aria-expanded`
- `aria-controls`
- `aria-current`
- `aria-pressed`
- `aria-selected`
- `aria-live`, `aria-atomic`, `aria-busy`
- `aria-invalid`, `aria-required`
- `aria-haspopup`
- `aria-disabled`

Use a real `<button>` for actions and `<a href="...">` for navigation. Avoid inventing custom roles when native controls already provide the right semantics.

---

# 16. Metadata, SEO, and Social Sharing

```html
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Accessible Storefront | Example</title>
  <meta name="description" content="Browse practical products and helpful guides.">
  <meta name="theme-color" content="#111827">
  <link rel="canonical" href="https://example.com/store">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" href="/icon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <meta property="og:title" content="Accessible Storefront">
  <meta property="og:description" content="Browse products and guides.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://example.com/store">
  <meta property="og:image" content="https://example.com/social-preview.jpg">
</head>
```

### Important metadata elements and attributes

- `<title>`: unique, descriptive page title.
- `<meta charset="UTF-8">`: character encoding.
- `<meta name="viewport">`: mobile viewport configuration.
- `<meta name="description">`: search-result summary hint.
- `<link rel="canonical">`: preferred URL when appropriate.
- `<link rel="icon">`: site icon.
- `og:*`: Open Graph social preview metadata.
- `twitter:*`: X/Twitter card metadata, where used.
- `robots` meta: indexing directives; use only when intended.

No metadata guarantees a specific search ranking or social preview. Keep metadata accurate and consistent with visible content.

---

# 17. Scripts, Stylesheets, and Resource Hints

## 17.1 CSS

```html
<link rel="stylesheet" href="styles.css">
<style>
  .notice { color: darkgreen; }
</style>
```

## 17.2 JavaScript loading modes

```html
<script src="app.js" defer></script>
<script async src="analytics.js"></script>
<script type="module" src="main.js"></script>
<script type="module" src="app.js" defer></script>
```

- Classic scripts without `async`/`defer` can block HTML parsing when encountered.
- `defer` runs a classic external script after parsing and preserves document order among deferred classic scripts.
- `async` runs when available; execution order is not guaranteed among async scripts.
- Module scripts defer by default and support imports/exports.
- Avoid inline event-handler attributes such as `onclick="..."`; use `addEventListener()` in JavaScript.

## 17.3 Resource hints

```html
<link rel="preconnect" href="https://api.example.com">
<link rel="dns-prefetch" href="//cdn.example.com">
<link rel="preload" href="/fonts/site.woff2" as="font" type="font/woff2" crossorigin>
<link rel="prefetch" href="/next-page-data.json" as="fetch" crossorigin>
```

Use hints selectively. Incorrect preload or excessive preconnect hints may waste bandwidth.

## 17.4 Base URL

```html
<base href="https://example.com/docs/">
```

A document can have at most one `<base>` element. It affects relative URLs in the document, including link targets. Use it only when you understand its effects.

---

# 18. Embedded Content: iframe, object, embed

```html
<iframe
  src="https://www.youtube-nocookie.com/embed/VIDEO_ID"
  title="Product demonstration video"
  loading="lazy"
  referrerpolicy="strict-origin-when-cross-origin"
  allow="accelerometer; encrypted-media; picture-in-picture"
  allowfullscreen>
</iframe>
```

- `<iframe>` embeds another browsing context.
- `<object>` can embed an external resource and provide fallback content.
- `<embed>` is for external embedded content; use only where appropriate.
- `<param>` is associated with legacy object embedding patterns and should not be used for new general implementations.

For untrusted embedded pages, understand sandboxing and permissions. Example:

```html
<iframe src="https://example.org/widget" title="Example widget" sandbox="allow-scripts" loading="lazy"></iframe>
```

Do not casually add powerful sandbox permissions. A sandbox can block capabilities; allowing scripts and same-origin together may undermine the protection for same-origin content. Configure only the permissions the embedded experience truly needs.

---

# 19. SVG, MathML, and Canvas

## 19.1 Inline SVG

```html
<svg viewBox="0 0 100 100" role="img" aria-labelledby="iconTitle" width="100" height="100">
  <title id="iconTitle">Green circle</title>
  <circle cx="50" cy="50" r="40" fill="green"></circle>
</svg>
```

SVG includes elements such as `<svg>`, `<g>`, `<path>`, `<circle>`, `<rect>`, `<line>`, `<ellipse>`, `<polygon>`, `<polyline>`, `<text>`, `<defs>`, `<linearGradient>`, and `<use>`. SVG has its own syntax and attributes; consult the SVG reference for the complete vocabulary.

## 19.2 Canvas

```html
<canvas id="chart" width="600" height="300">
  A chart showing monthly sales.
</canvas>
<script defer>
  const canvas = document.querySelector("#chart");
  const context = canvas instanceof HTMLCanvasElement ? canvas.getContext("2d") : null;
  if (context) {
    context.fillStyle = "#2563eb";
    context.fillRect(20, 20, 160, 80);
  }
</script>
```

Canvas drawing uses JavaScript APIs; the HTML element itself defines the drawing surface. Supply meaningful fallback content and an accessible representation of important chart information.

## 19.3 MathML

MathML can represent mathematical notation. For example, a document may include a `<math>` element with presentation elements such as `<mfrac>`, `<mi>`, `<mn>`, `<mo>`, and `<msup>`. Consult the MathML reference for supported syntax and browser compatibility.

---

# 20. Interactive HTML Elements

## 20.1 Details and summary

```html
<details>
  <summary>Read more</summary>
  <p>Additional information appears when expanded.</p>
</details>
```

The `open` attribute makes `<details>` expanded initially. Multiple details elements may use `name` for exclusive-open accordion-like behavior in supporting browsers.

## 20.2 Dialog

```html
<button type="button" id="openDialog">Open dialog</button>
<dialog id="confirmDialog" aria-labelledby="dialogTitle">
  <h2 id="dialogTitle">Confirm action</h2>
  <p>Continue with this action?</p>
  <form method="dialog">
    <button value="cancel">Cancel</button>
    <button value="confirm">Confirm</button>
  </form>
</dialog>
<script>
  const openButton = document.querySelector("#openDialog");
  const dialog = document.querySelector("#confirmDialog");
  if (openButton instanceof HTMLButtonElement && dialog instanceof HTMLDialogElement) {
    openButton.addEventListener("click", () => dialog.showModal());
  }
</script>
```

Dialog methods include `show()`, `showModal()`, and `close()`. The `cancel` and `close` events can be handled in JavaScript. A modal must still have a clear accessible name, usable keyboard interaction, and meaningful controls.

## 20.3 Popover

```html
<button type="button" popovertarget="helpPopover">Help</button>
<div id="helpPopover" popover>
  This is supplemental help text.
</div>
```

The Popover API supports attributes and behavior such as `popover`, `popovertarget`, and `popovertargetaction`, with browser compatibility depending on the specific feature. Use a sensible fallback where older browser support matters.

## 20.4 Progress and meter

```html
<label for="uploadProgress">Upload progress</label>
<progress id="uploadProgress" max="100" value="65">65%</progress>

<label for="storageUsage">Storage usage</label>
<meter id="storageUsage" min="0" max="100" low="30" high="80" optimum="20" value="45">45%</meter>
```

`<progress>` represents task completion. `<meter>` represents a scalar measurement within a known range. Use labels and accessible text as needed.

---

# 21. Templates and Web Components

## 21.1 Template element

```html
<template id="cardTemplate">
  <article class="card">
    <h2 class="card-title"></h2>
    <p class="card-description"></p>
  </article>
</template>
<div id="cardList"></div>
<script>
  const template = document.querySelector("#cardTemplate");
  const list = document.querySelector("#cardList");
  if (template instanceof HTMLTemplateElement && list) {
    const clone = template.content.cloneNode(true);
    list.append(clone);
  }
</script>
```

`<template>` stores inert markup that can be cloned. It does not render its contents until inserted into the document. Avoid inserting untrusted strings with `innerHTML`; use text properties or safe DOM construction.

## 21.2 Custom elements and shadow DOM (JavaScript APIs)

HTML allows custom element names containing a hyphen, such as `<user-card>`, when registered appropriately through JavaScript.

```html
<user-card></user-card>
<script>
  class UserCard extends HTMLElement {
    constructor() {
      super();
      const shadow = this.attachShadow({ mode: "open" });
      shadow.innerHTML = `<style>:host { display: block; }</style><slot></slot>`;
    }
  }
  if (!customElements.get("user-card")) {
    customElements.define("user-card", UserCard);
  }
</script>
```

This example demonstrates the APIs, but interpolating untrusted strings into `innerHTML` is unsafe. For real components, build DOM nodes safely, use CSS modules/templates, and consider lifecycle callbacks such as `connectedCallback()`, `disconnectedCallback()`, `attributeChangedCallback()`, and observed attributes.

Relevant Web Components APIs include `customElements.define()`, `HTMLElement`, `attachShadow()`, `ShadowRoot`, `<slot>`, and the `<template>` element. Custom elements are an HTML platform extension powered by JavaScript, not just markup alone.

---

# 22. HTML Entities and Special Characters

Use character references for reserved characters and symbols where required.

| Character | Reference |
|---|---|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&apos;` in HTML contexts that support the named reference, or `&#39;` |
| Non-breaking space | `&nbsp;` |
| Copyright | `&copy;` |
| Registered trademark | `&reg;` |
| Trademark | `&trade;` |
| Euro | `&euro;` |
| Em dash | `&mdash;` |

Numeric references use decimal form such as `&#169;` or hexadecimal form such as `&#xA9;`. In ordinary text, an ampersand starting a character reference must be handled correctly. Use UTF-8 for regular Unicode text.

Do not use `&nbsp;` repeatedly as a layout technique; use CSS for layout.

---

# 23. Accessibility Checklist

- Set the page language with `<html lang="en">` (or the actual primary language).
- Give every page a useful `<title>`.
- Use a logical heading hierarchy and semantic landmarks.
- Associate form controls with visible labels.
- Provide suitable `alt` text for informative images.
- Use buttons for actions and links for navigation.
- Ensure keyboard operability and visible focus styles (implemented with CSS).
- Ensure status messages can be announced when necessary, e.g. with a suitable `role="status"` or live region.
- Use ARIA only when native HTML is insufficient.
- Associate errors and instructions with controls using text and `aria-describedby` when appropriate.
- Do not rely on color alone to convey meaning.
- Caption videos and provide transcripts or other alternatives when appropriate.
- Test with keyboard-only navigation, browser accessibility tools, and screen readers when possible.

Example skip link:

```html
<a class="skip-link" href="#main-content">Skip to main content</a>
<header>...</header>
<main id="main-content" tabindex="-1">...</main>
```

CSS is needed to visually hide or reveal a skip link on focus; do not use the HTML `hidden` attribute when the goal is to make content available on keyboard focus.

---

# 24. Security Considerations

HTML is delivered to clients and can be inspected. Do not put passwords, secret API keys, private tokens, or authorization logic in markup.

## Safer practices

- Avoid inline event attributes such as `onclick`; use event listeners and a strict Content Security Policy where suitable.
- Avoid placing untrusted input into `innerHTML`; use `textContent`, safe templating, or a well-vetted sanitizer when rich HTML is a requirement.
- Validate and authorize all meaningful actions on the server.
- Use HTTPS in production.
- For external links opened in a new tab, use appropriate `rel` values such as `noopener noreferrer` where appropriate.
- Review iframe `sandbox`, `allow`, and permissions carefully.
- Do not treat `accept` on file inputs as a security validation.
- Use framework protections against XSS and follow framework guidance; do not disable escaping casually.
- Understand cookies, SameSite, CSRF protections, CORS, CSP, and server-side session management when connecting HTML forms to a backend.
- A hidden field, `data-*` attribute, disabled button, or client-side role check is not authorization.

## `innerHTML` versus `textContent`

```js
const output = document.querySelector("#output");
const userInput = "<img src=x onerror=alert(1)>";
if (output) output.textContent = userInput; // displayed as text
```

Avoid treating user-controlled strings as markup. Security-sensitive cases need broader application-level controls as well.

---

# 25. Performance and Loading

- Optimize image file sizes and dimensions.
- Prefer modern image formats where appropriate and provide fallbacks as needed.
- Set image dimensions to reduce layout shifts.
- Lazy-load appropriate offscreen images and iframes.
- Use `defer` or module scripts for many ordinary application scripts.
- Preload only genuinely critical resources.
- Reduce unnecessary third-party scripts.
- Split large CSS and JavaScript bundles at the application/build-tool level.
- Keep DOM trees and repeated updates reasonable.
- Test on mobile devices and slower networks.

Example:

```html
<img src="team.webp" alt="Team meeting" width="1000" height="650" loading="lazy" decoding="async">
<script src="app.js" defer></script>
```

Use `loading="lazy"` thoughtfully; critical above-the-fold content should not be delayed.

---

# 26. HTML with CSS and JavaScript

A common file layout:

```text
my-site/
├── index.html
├── styles.css
├── app.js
└── assets/
    ├── logo.svg
    └── images/
```

`index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Task List</title>
  <link rel="stylesheet" href="styles.css">
  <script src="app.js" defer></script>
</head>
<body>
  <main class="app">
    <h1>Task list</h1>
    <form id="taskForm">
      <label for="taskInput">New task</label>
      <input id="taskInput" name="task" required maxlength="120">
      <button type="submit">Add task</button>
    </form>
    <ul id="taskList" aria-label="Tasks"></ul>
    <p id="status" role="status"></p>
  </main>
</body>
</html>
```

`styles.css`:

```css
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, sans-serif; line-height: 1.5; }
.app { width: min(100% - 2rem, 42rem); margin: 3rem auto; }
form { display: flex; flex-wrap: wrap; gap: .75rem; }
input { flex: 1; min-width: 12rem; }
button, input { font: inherit; padding: .6rem .8rem; }
:focus-visible { outline: 3px solid royalblue; outline-offset: 2px; }
```

`app.js`:

```js
const form = document.querySelector("#taskForm");
const input = document.querySelector("#taskInput");
const list = document.querySelector("#taskList");
const status = document.querySelector("#status");

form?.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!(input instanceof HTMLInputElement) || !(list instanceof HTMLUListElement)) return;
  const taskText = input.value.trim();
  if (!taskText) {
    input.focus();
    return;
  }

  const item = document.createElement("li");
  item.textContent = taskText;
  list.append(item);
  input.value = "";
  input.focus();
  if (status) status.textContent = "Task added.";
});
```

This small example shows the separation: HTML structure, CSS presentation, and JavaScript behavior.

---

# 27. DOM: Finding and Updating HTML

HTML is parsed into a DOM tree. JavaScript can access that tree through browser APIs. These APIs are **JavaScript/browser APIs, not HTML syntax**.

## 27.1 Selecting elements

```js
const firstButton = document.querySelector("button");
const allCards = document.querySelectorAll(".card");
const byId = document.getElementById("main-content");
const byClass = document.getElementsByClassName("card");
const byTag = document.getElementsByTagName("p");
```

`querySelector()` returns the first matching element or `null`. `querySelectorAll()` returns a static `NodeList` of matches.

## 27.2 Reading and updating

```js
const heading = document.querySelector("h1");
if (heading) {
  heading.textContent = "Updated heading";
  heading.classList.add("highlight");
  heading.setAttribute("aria-live", "polite");
}
```

Common properties and methods:

- `textContent`: text within a node and its descendants.
- `innerHTML`: parses/reads HTML markup; dangerous with untrusted input.
- `innerText`: rendered text behavior, which may trigger layout work.
- `classList.add()`, `.remove()`, `.toggle()`, `.contains()`.
- `getAttribute()`, `setAttribute()`, `removeAttribute()`, `hasAttribute()`.
- `dataset`: access `data-*` values.
- `style`: access inline CSS declarations; prefer classes for reusable styling.
- `matches()` and `closest()`: match a selector or find a matching ancestor.

## 27.3 Creating and removing elements

```js
const item = document.createElement("li");
item.textContent = "New item";
document.querySelector("ul")?.append(item);
item.remove();
```

Other common methods: `append()`, `prepend()`, `before()`, `after()`, `replaceWith()`, `replaceChildren()`, `cloneNode()`, `insertAdjacentElement()`, and `insertAdjacentText()`.

## 27.4 Node relationships

Properties include `parentElement`, `parentNode`, `children`, `childNodes`, `firstElementChild`, `lastElementChild`, `nextElementSibling`, and `previousElementSibling`.

## 27.5 Document and focus helpers

Common APIs include `document.title`, `document.URL`, `document.activeElement`, `document.createElement()`, `document.createTextNode()`, `document.createDocumentFragment()`, `document.getSelection()`, element `focus()`, and `blur()`.

The exact methods available depend on the interface (`Element`, `HTMLElement`, `HTMLInputElement`, and so on). Consult MDN for the specific DOM type.

---

# 28. DOM Events and Event Handling

Prefer `addEventListener()` instead of inline handler attributes.

```html
<button id="saveButton" type="button">Save</button>
<p id="saveStatus" role="status"></p>
<script src="events.js" defer></script>
```

```js
const button = document.querySelector("#saveButton");
const status = document.querySelector("#saveStatus");

button?.addEventListener("click", (event) => {
  console.log(event.type, event.target);
  if (status) status.textContent = "Saved.";
});
```

### Common event types

- Mouse and pointer: `click`, `dblclick`, `pointerdown`, `pointerup`, `pointermove`, `mouseenter`, `mouseleave`.
- Keyboard: `keydown`, `keyup` (use semantic controls, not keyboard-only custom buttons).
- Forms: `submit`, `input`, `change`, `reset`, `invalid`, `focus`, `blur`.
- Clipboard: `copy`, `cut`, `paste`.
- Drag and drop: `dragstart`, `dragover`, `drop`, `dragend`.
- Document/lifecycle: `DOMContentLoaded`, `load`, `pageshow`, `pagehide`, `visibilitychange`.
- Network: `online`, `offline`.
- Media: `play`, `pause`, `ended`, `timeupdate`, `volumechange`.

Not every element emits every event. Some event details and browser behavior vary.

### Event object and event flow

```js
element.addEventListener("click", (event) => {
  event.preventDefault(); // stop the default action when appropriate
  event.stopPropagation(); // stop propagation when truly needed
  console.log(event.target, event.currentTarget);
});
```

- `target`: origin of the event.
- `currentTarget`: element whose listener is running.
- `preventDefault()`: prevents a cancelable default action.
- `stopPropagation()`: stops further propagation.
- `stopImmediatePropagation()`: also stops later listeners on the same target.

Events can capture down the tree, run on targets, and bubble up (not every event bubbles). Avoid stopping propagation without a strong reason.

### Event delegation

```js
document.querySelector("#taskList")?.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Element)) return;
  const removeButton = target.closest("button[data-remove]");
  if (!removeButton) return;
  removeButton.closest("li")?.remove();
});
```

Delegation is useful for lists whose items are created dynamically.

---

# 29. Forms with JavaScript

```js
const form = document.querySelector("#contactForm");

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!(form instanceof HTMLFormElement)) return;
  if (!form.reportValidity()) return;

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());
  console.log(payload);
});
```

Common form APIs:

- `new FormData(form)` and `formData.entries()`, `.get()`, `.getAll()`, `.append()`, `.set()`, `.delete()`.
- `form.checkValidity()` and `form.reportValidity()`.
- `control.setCustomValidity(message)`.
- `control.validity` and `control.validationMessage`.
- `form.reset()`.
- `form.requestSubmit()` (preferred to simulate a user submit action; direct `form.submit()` bypasses submit events and constraint validation).
- Input-specific properties such as `value`, `checked`, `files`, `selectionStart`, and `selectionEnd`.

Always perform critical validation and authorization on the server. Browser-side validation can be bypassed.

---

# 30. Browser Storage and HTML-Related APIs

## 30.1 Local and session storage

```js
localStorage.setItem("theme", "dark");
const theme = localStorage.getItem("theme");
localStorage.removeItem("theme");
localStorage.clear();

sessionStorage.setItem("draft", "temporary value");
```

Do not store sensitive secrets or long-lived authentication tokens in browser storage without understanding the risks, especially XSS exposure.

## 30.2 Cookies

Cookies can be set with `document.cookie`, but secure authentication cookies are commonly configured by the server with appropriate attributes such as `HttpOnly`, `Secure`, and `SameSite`. JavaScript cannot read `HttpOnly` cookies. For authentication, use a well-reviewed design and server guidance.

## 30.3 Clipboard, URL, history, and location

```js
const currentURL = new URL(window.location.href);
currentURL.searchParams.set("q", "html");
console.log(currentURL.toString());

history.pushState({ page: 2 }, "", "?page=2");
console.log(window.location.pathname);
```

Clipboard APIs generally require a secure context and may require user permission or a direct user gesture:

```js
async function copyText(text) {
  await navigator.clipboard.writeText(text);
}
```

Handle rejections and provide a fallback when necessary.

## 30.4 ResizeObserver, IntersectionObserver, MutationObserver

- `ResizeObserver`: responds to element size changes.
- `IntersectionObserver`: observes intersections, often used for lazy loading and visibility.
- `MutationObserver`: observes DOM mutations.

These are browser JavaScript APIs, not HTML functions. Disconnect observers when they are no longer needed.

---

# 31. File Upload and Drag-and-Drop Concepts

HTML file input:

```html
<label for="upload">Select an image</label>
<input id="upload" name="upload" type="file" accept="image/*">
```

JavaScript file metadata:

```js
const input = document.querySelector("#upload");
input?.addEventListener("change", () => {
  if (!(input instanceof HTMLInputElement)) return;
  const file = input.files?.[0];
  if (!file) return;
  console.log(file.name, file.type, file.size);
});
```

`URL.createObjectURL(file)` can create a temporary local URL for preview; call `URL.revokeObjectURL(url)` when done. File names and MIME type reported by the client are not proof that a file is safe. Validate again on the server.

Drag-and-drop uses events such as `dragover` and `drop`; call `preventDefault()` where the browser's default behavior needs to be canceled. Provide an equivalent keyboard-accessible file picker.

---

# 32. Progressive Enhancement and Responsive Design

- Start with valid semantic HTML.
- Make core content accessible without requiring visual styling.
- Add CSS layout and responsive media queries.
- Add JavaScript enhancements without making essential controls unusable if scripting fails.
- Support keyboard and assistive technology interactions.
- Use native elements instead of custom elements when native behavior meets the need.

Responsive viewport metadata:

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

Use CSS for responsive breakpoints; HTML's `<picture>`, `srcset`, and `sizes` let the browser choose image sources for screen conditions and resource needs.

---

# 33. Deprecated and Obsolete Elements to Avoid

Avoid obsolete elements such as `<font>`, `<center>`, `<marquee>`, `<big>`, `<strike>`, `<tt>`, `<frameset>`, `<frame>`, `<applet>`, `<dir>`, and `<acronym>` in new documents. The `<blink>` element was never standardized as a normal modern HTML element. Use CSS and semantic elements instead.

Also avoid obsolete presentational attributes such as `align`, `bgcolor`, and old table layout attributes. Use CSS for presentation. Some obsolete features may still render for compatibility but should not be used in new code.

---

# 34. Common Errors and Debugging

1. Missing or incorrect document structure: add doctype, language, charset, viewport, title, and body content.
2. Invalid nesting: ensure tags are nested according to the element content model.
3. Repeated IDs: IDs should be unique within the document.
4. Images without suitable `alt` text.
5. Inputs without labels.
6. Using a link to trigger an action or a button to navigate when the semantic element is wrong.
7. Using `href="#"` for dummy navigation.
8. Using `innerHTML` with untrusted content.
9. Forgetting a form submit button defaults to submit within a form; use `type="button"` for non-submit actions.
10. Using client-side validation as the only security validation.
11. Loading a script before the needed DOM exists without `defer`, modules, or deliberate initialization.
12. Incorrect asset paths or URL bases.
13. Missing `name` attributes on form controls expected to be submitted.
14. Missing `value` attributes on option controls when a stable value is needed.
15. Assuming every browser API is available in every browser.

Useful checks:

- Browser DevTools Console and Elements panel.
- Network panel for failed CSS, JS, images, and requests.
- HTML conformance checker/validator.
- Accessibility tools and keyboard testing.
- Device emulation plus real-device testing.

---

# 35. Full Working Website Example

This example includes semantic structure, accessible labels, cards, a form, and a script. Save it as `index.html` to try it.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="A small HTML learning demo.">
  <title>HTML Learning Demo</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font: 1rem/1.5 system-ui, sans-serif; color: #1f2937; }
    header, footer { padding: 1rem; background: #111827; color: white; }
    main { width: min(100% - 2rem, 56rem); margin: 2rem auto; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 1rem; }
    .card { border: 1px solid #d1d5db; border-radius: .75rem; padding: 1rem; }
    form { display: grid; gap: .5rem; max-width: 28rem; margin-top: 2rem; }
    input, button { font: inherit; padding: .65rem; }
    :focus-visible { outline: 3px solid #2563eb; outline-offset: 2px; }
  </style>
  <script defer>
    document.addEventListener("DOMContentLoaded", () => {
      const form = document.querySelector("#feedbackForm");
      const input = document.querySelector("#feedback");
      const output = document.querySelector("#feedbackStatus");

      form?.addEventListener("submit", (event) => {
        event.preventDefault();
        if (!(form instanceof HTMLFormElement) || !(input instanceof HTMLInputElement)) return;
        if (!form.reportValidity()) return;
        if (output) output.textContent = `Thanks for your feedback: ${input.value.trim()}`;
        form.reset();
      });
    });
  </script>
</head>
<body>
  <a href="#main" class="skip-link">Skip to main content</a>
  <header>
    <p><strong>HTML Learning Demo</strong></p>
    <nav aria-label="Main navigation">
      <a href="#features" style="color:white">Features</a>
      <a href="#feedback" style="color:white">Feedback</a>
    </nav>
  </header>
  <main id="main">
    <section aria-labelledby="page-title">
      <h1 id="page-title">Learn HTML by Example</h1>
      <p>This example brings together accessible, semantic HTML and small JavaScript behavior.</p>
    </section>

    <section id="features" aria-labelledby="features-heading">
      <h2 id="features-heading">Features</h2>
      <div class="cards">
        <article class="card">
          <h3>Semantic markup</h3>
          <p>Use elements that communicate the meaning of content.</p>
        </article>
        <article class="card">
          <h3>Accessible forms</h3>
          <p>Connect labels and controls so they are easier to use.</p>
        </article>
        <article class="card">
          <h3>Responsive layout</h3>
          <p>Use CSS Grid to adapt card layouts to different widths.</p>
        </article>
      </div>
    </section>

    <section aria-labelledby="feedback-heading">
      <h2 id="feedback-heading">Feedback</h2>
      <form id="feedbackForm">
        <label for="feedback">Your feedback</label>
        <input id="feedback" name="feedback" required maxlength="200">
        <button type="submit">Send feedback</button>
      </form>
      <p id="feedbackStatus" role="status" aria-live="polite"></p>
    </section>
  </main>
  <footer><small>&copy; 2026 HTML Learning Demo</small></footer>
</body>
</html>
```

Note: inline `style` in this demonstration is only to keep the example self-contained. Real projects should generally use a separate stylesheet and a deliberate Content Security Policy.

---

# 36. Element Quick Reference

The lists below cover the standard HTML element families most developers regularly encounter. Exact conformance rules and browser support vary by element; check the reference pages for details.

## Document and metadata

`html`, `head`, `title`, `base`, `link`, `meta`, `style`, `body`.

## Sectioning and landmarks

`header`, `nav`, `main`, `section`, `article`, `aside`, `footer`, `address`, `h1`, `h2`, `h3`, `h4`, `h5`, `h6`, `hgroup`.

## Grouping and text

`div`, `p`, `hr`, `pre`, `blockquote`, `ol`, `ul`, `menu`, `li`, `dl`, `dt`, `dd`, `figure`, `figcaption`, `search`, `span`, `br`, `wbr`.

## Inline semantics

`a`, `em`, `strong`, `small`, `s`, `cite`, `q`, `dfn`, `abbr`, `ruby`, `rt`, `rp`, `data`, `time`, `code`, `var`, `samp`, `kbd`, `sub`, `sup`, `i`, `b`, `u`, `mark`, `bdi`, `bdo`, `span`.

## Edits

`ins`, `del`.

## Images and media

`img`, `picture`, `source`, `audio`, `video`, `track`, `map`, `area`.

## Embedded and graphics content

`iframe`, `embed`, `object`, `param` (legacy association), `canvas`, SVG `svg`, MathML `math`.

## Scripts and reusable content

`script`, `noscript`, `template`, `slot`.

## Lists and tables

`ul`, `ol`, `menu`, `li`, `dl`, `dt`, `dd`, `table`, `caption`, `colgroup`, `col`, `thead`, `tbody`, `tfoot`, `tr`, `th`, `td`.

## Forms

`form`, `label`, `input`, `button`, `select`, `datalist`, `optgroup`, `option`, `textarea`, `output`, `progress`, `meter`, `fieldset`, `legend`.

## Interactive elements

`details`, `summary`, `dialog`, and popover attributes on suitable elements.

## Web Components

Custom elements are registered using JavaScript; related HTML primitives include `template` and `slot`.

This is a practical inventory. For an exhaustive standards index, use the official reference linked below; new experimental or emerging features can change over time.

---

# 37. Attribute Quick Reference

## Global attributes (selected)

`id`, `class`, `style`, `title`, `lang`, `dir`, `hidden`, `tabindex`, `accesskey`, `autofocus`, `contenteditable`, `draggable`, `spellcheck`, `translate`, `inputmode`, `enterkeyhint`, `autocapitalize`, `data-*`, `role`, `aria-*`, `slot`, `part`, `nonce`, `is`.

## Links

`href`, `target`, `rel`, `download`, `hreflang`, `type`, `referrerpolicy`.

## Images

`src`, `alt`, `width`, `height`, `srcset`, `sizes`, `loading`, `decoding`, `fetchpriority`, `usemap`, `ismap`.

## Media

`src`, `controls`, `autoplay`, `muted`, `loop`, `preload`, `poster`, `playsinline`, `kind`, `srclang`, `label`, `default`.

## Forms and controls

`action`, `method`, `enctype`, `autocomplete`, `novalidate`, `name`, `value`, `type`, `required`, `disabled`, `readonly`, `checked`, `selected`, `multiple`, `min`, `max`, `step`, `minlength`, `maxlength`, `pattern`, `placeholder`, `accept`, `capture`, `rows`, `cols`, `wrap`, `for`, `form`, `formaction`, `formenctype`, `formmethod`, `formnovalidate`, `formtarget`, `list`, `size`.

## Scripts and resources

`src`, `type`, `async`, `defer`, `crossorigin`, `integrity`, `referrerpolicy`, `nomodule`, `nonce`, `media`, `href`, `rel`, `as`, `fetchpriority`.

## Embedded contexts

`src`, `srcdoc`, `title`, `name`, `width`, `height`, `loading`, `allow`, `allowfullscreen`, `sandbox`, `referrerpolicy`.

Attribute applicability differs by element. Do not assume any listed attribute is valid or meaningful on every element.

---

# 38. Practice Projects

1. **Profile page:** headings, paragraphs, links, images, lists, semantic sections.
2. **Contact form:** labels, input types, constraints, status messages, JavaScript submit handler.
3. **Product page:** images, price table, details/summary, accessible calls to action.
4. **Media gallery:** picture, responsive images, video captions, keyboard-friendly controls.
5. **Documentation site:** navigation, table of contents, landmarks, accessible code examples.
6. **Task list:** create/update/delete list items through the DOM; store non-sensitive preferences locally.
7. **File preview page:** file input, image preview with object URLs, validation and safe cleanup.
8. **Dashboard shell:** semantic regions, forms, tables, accessible dialog interactions.
9. **React migration practice:** take a static HTML page and convert it into reusable React components after learning JSX/TSX differences.
10. **Full-stack contact form:** HTML form → frontend validation → backend endpoint → database save → success/error state.

For each project, verify in the browser, use keyboard navigation, test narrow mobile widths, validate the HTML, check the console and network requests, and avoid claiming features are implemented unless they actually work.

---

# 39. Full-Stack Learning Roadmap

1. HTML document structure, semantic elements, links, lists, tables, forms, attributes, accessibility.
2. CSS basics, box model, Flexbox, Grid, responsive design, variables, transitions, focus styles.
3. JavaScript variables, operators, conditions, loops, functions, arrays, objects, modules, async/await.
4. DOM selection, events, forms, HTTP requests, JSON, browser APIs.
5. Git, command line, package management, developer tools, linting and formatting.
6. Frontend framework (React, Angular, Vue, or another stack) and TypeScript if applicable.
7. Backend runtime/framework, REST APIs, validation, authentication, authorization, database design.
8. Testing, logging, error handling, security, accessibility, performance, deployment and monitoring.

HTML is essential but it is only one layer of a full-stack application. Browser HTML does not securely implement authentication, persistence, or server authorization by itself.

---

# 40. Official References

Use these references alongside this guide for exact conformance rules, full element/attribute inventories, examples, compatibility, and newer APIs.

- **MDN HTML reference:** https://developer.mozilla.org/en-US/docs/Web/HTML/Reference
- **MDN HTML elements:** https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements
- **MDN HTML attributes:** https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes
- **MDN global attributes:** https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes
- **MDN HTML forms guide:** https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms
- **MDN DOM introduction:** https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model/Introduction
- **MDN event reference:** https://developer.mozilla.org/en-US/docs/Web/API/Event
- **MDN Web APIs:** https://developer.mozilla.org/en-US/docs/Web/API
- **WHATWG HTML Living Standard:** https://html.spec.whatwg.org/
- **W3C Nu HTML Checker:** https://validator.w3.org/nu/
- **Web Content Accessibility Guidelines (WCAG):** https://www.w3.org/WAI/standards-guidelines/wcag/

---

## Final Checklist

- [ ] Understand a valid HTML document and standards mode.
- [ ] Know semantic elements and content nesting rules.
- [ ] Use links, images, lists, and tables correctly.
- [ ] Build accessible forms and understand native validation.
- [ ] Know global attributes, ARIA, metadata, scripts, and resource hints.
- [ ] Add media, embedded content, SVG/canvas where needed.
- [ ] Use `details`, `dialog`, templates, and Web Components appropriately.
- [ ] Understand HTML security and performance basics.
- [ ] Manipulate HTML through DOM APIs and events using JavaScript.
- [ ] Validate pages and test accessibility, responsive behavior, and actual functionality.

**Remember:** HTML provides structure. CSS provides presentation. JavaScript/TypeScript provides behavior. Backend code and databases provide server-side application logic and persistent data.
