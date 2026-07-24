# CME Bank Design System

The design system for CME Bank products — tokens, components, and the guidance for using them.
Accessible by default, themeable without duplication, and dependency-free.

---

## What's in here

```
cme-bank-design-system/
├── tokens.css        Single source of truth for every visual value
├── components.css    The component library
├── site.css          Documentation site chrome (not part of the system)
├── index.html        The documentation site
├── tokens.json       DTCG tokens, generated from tokens.css
├── build.py          Produces dist/
└── dist/             Build output — deploy this
```

**`tokens.css` is the source of truth.** `tokens.json` is generated from it, never edited by hand.
If you change a value, change it there and re-run the build.

Every colour primitive carries its provenance inline — `[file]` means the hex already existed in the
CompLib Figma library, `[derived]` means it was interpolated because the library had no usable colour
at that lightness, with the reason stated. **42 of 63 steps come from the library.**

---

## Running it locally

No build step is needed to view the docs — it's static HTML.

```bash
cd cme-bank-design-system
python -m http.server 8000
# open http://localhost:8000
```

To regenerate `dist/` and `tokens.json`:

```bash
python build.py
```

That produces a self-contained `dist/index.html` with all CSS inlined (useful for sharing as a
single file), plus copies of the raw stylesheets so `dist/` can also be served as-is.

---

## Publishing

The site is static, so anything that serves files will host it.

### GitHub Pages

```bash
git init
git add .
git commit -m "CME Bank Design System v1.0.0"
git branch -M main
git remote add origin https://github.com/<you>/cme-bank-design-system.git
git push -u origin main
```

Then in the repo: **Settings → Pages → Source: `main` / root**. It'll be live at
`https://<you>.github.io/cme-bank-design-system/` within a minute or two.

To publish only the built output, push `dist/` to a `gh-pages` branch instead:

```bash
python build.py
git subtree push --prefix dist origin gh-pages
```

### Netlify or Vercel

Drag the folder onto the dashboard, or connect the repo. Settings:

| Field | Value |
|---|---|
| Build command | `python build.py` |
| Publish directory | `dist` |

### Anywhere else

Upload `dist/` to any static host — S3, Cloudflare Pages, an nginx box, an internal server. There is
no server-side code and no runtime dependency.

---

## Using the system in a product

```html
<link rel="stylesheet" href="tokens.css">
<link rel="stylesheet" href="components.css">

<button class="cme-btn cme-btn--primary">Open account</button>
```

`tokens.css` must load first — everything else resolves against it.

### Fonts

The system expects **Open Sans** (customer-facing products) and **Roboto** (back-office). It falls
back to the system UI font if they're absent, so nothing breaks, but load them for accuracy:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&family=Roboto:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

### Theming

Dark mode follows the OS automatically. To override:

```html
<html data-theme="dark">    <!-- force dark -->
<html data-theme="light">   <!-- force light -->
<html>                      <!-- follow the OS -->
```

---

## Two portals, one component set

CME Bank runs two products from this library. They are **not** two component sets — they are the same
components under two brand themes, switched with one attribute:

```html
<body data-portal="customer">     <!-- green, Open Sans, roomy, 12px radius -->
<body data-portal="backoffice">   <!-- blue, Roboto, dense, 4px radius -->
```

|  | Customer portal | Back-office portal |
|---|---|---|
| Brand | `green-500` `#9CC53E` | `blue-400` `#376EEC` |
| Label on brand | `green-900` — dark | white |
| Typeface | Open Sans | Roboto |
| Control height | 44px — touch-ready | 36px — dense |
| Radius | 12px — soft | 4px — tight |
| Base type | 14px | 12px |

Portal composes with light/dark independently: **2 portals × 2 modes = 4 combinations, one component
set.** All 24 foreground/background pairs across those four combinations are verified.

### Why the label colour flips

The customer green is a *light* hue, so its label must be dark — white on it measures 2.56:1 and
fails. The back-office blue is *dark* enough to carry white at 4.56:1. `--action-primary-fg` absorbs
the difference, so the button component never knows which portal it is in.

### Adding a portal difference

Put it in the portal block in `tokens.css`, never in a component:

```css
[data-portal="backoffice"] {
  --radius-control: var(--radius-md);
  --action-primary-bg: var(--blue-400);
}
```

**Never fork a component to theme it.** That is how the original library ended up with five parallel
button implementations. If a component needs to differ between portals, the difference belongs in a
token.

---

## The one architectural rule

Three tiers, referenced in one direction only:

```
Primitives  →  Semantic  →  Components
--green-500    --action-primary-bg    .cme-btn--primary
```

**Components reference semantic tokens. Semantic tokens reference primitives. Never skip a layer.**

A component that reaches straight for `--green-500` cannot be themed, and will break the day the
brand changes. If the semantic token you need doesn't exist, add it to `tokens.css` rather than
reaching past it — that's a two-line change that keeps the system intact.

---

## Adding to the system

### A new token

1. Add the primitive to Tier 1 in `tokens.css` if the raw value doesn't exist yet.
2. Add the semantic token to Tier 2, referencing that primitive.
3. Add it to **both** the dark-mode blocks — the `@media` query *and* `[data-theme="dark"]`.
   Missing one causes the toggle to work but the OS preference not to, or vice versa.
4. Run `python build.py` to regenerate `tokens.json`.
5. Verify contrast if it's a foreground/background pair (see below).

### A new component

Follow the six steps in the *Contributing* section of the docs site. The one that matters most:

> **The rule of two.** A component earns a place in the shared system when a *second* team needs it.
> Before that, it lives locally in your product. Most one-off components never find a second consumer,
> and promoting them early is how component libraries sprawl.

Build it in `components.css` using semantic tokens only — no hex values, no primitive references, no
magic numbers.

---

## Verifying contrast

Every foreground/background pair shipped in `tokens.css` has been checked against WCAG 2.1 in both
themes. When you add a pair, check it too:

```python
def contrast(hex_a, hex_b):
    def lum(h):
        h = h.lstrip('#')
        c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
        c = [x/12.92 if x <= 0.03928 else ((x+0.055)/1.055)**2.4 for x in c]
        return 0.2126*c[0] + 0.7152*c[1] + 0.0722*c[2]
    l1, l2 = sorted([lum(hex_a), lum(hex_b)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)

print(contrast('#384913', '#9DCA35'))   # 5.13 — primary button, passes AA
```

Thresholds: **4.5:1** body text, **3:1** large text and control borders (WCAG 1.4.11).
Disabled controls are exempt under WCAG 1.4.3.

### Known deliberate exception

Disabled text sits at 3.5:1. This is intentional and permitted — dimming is how "unavailable" reads.
Don't reuse the disabled colour for ordinary secondary text; use `--text-secondary` or
`--text-tertiary` for that.

---

## Scaling beyond CSS

`tokens.json` is in [DTCG format](https://tr.designtokens.org/format/), so it feeds
[Style Dictionary](https://styledictionary.com/) directly to emit platform-native token files:

```bash
npm install -D style-dictionary
npx style-dictionary build
```

That gets you Swift, Kotlin, JS, and SCSS outputs from the same source, which is the path to keeping
iOS and Android in sync with the web without hand-maintaining three palettes.

---

## Copying component code

Every component example on the docs site has a **Copy HTML** button. It serialises the live DOM of the
example beside it, so the markup you paste is the exact node that renders on the page — there is no
separately authored snippet that can drift out of sync.

The copied markup assumes two things:

1. `tokens.css` and `components.css` are loaded, and an ancestor carries `data-portal` to pick the brand.
2. Icons resolve from the sprite — markup with `<use href="#i-…">` needs the icon sprite included once
   per page.

## Roadmap — framework components

Importable React (or Vue / Web Components) are a deliberate **next** step, not a gap:

| Tier | What ships | Status |
|---|---|---|
| 1 · Tokens + CSS | Design tokens, accessible CSS components, copyable markup. Any framework. | **Shipping** |
| 2 · Framework components | Importable components emitting these classes, bound to Figma via Code Connect. | Roadmap |

Tier 2 is **gated, not skipped**. A design system's value is that components are consumed, not
re-interpreted — that is what stops one button being built five ways. But shipping components nobody
owns is worse than shipping none: they fall behind, teams stop trusting them, and they fork. So tier 2
requires, first:

- a framework the org standardises on — one, not three parallel wrappers;
- a named owner and maintenance model for the coded components;
- Code Connect binding each component to its Figma node;
- the CSS layer staying the source of truth — components wrap it, never re-style.

Design owns tokens, specs, accessibility contracts and the Figma library. Engineering owns the coded
components. Code Connect binds the two.

---

## Versioning

| Change | Release | What you owe consumers |
|---|---|---|
| New token or component | minor | Changelog entry |
| Value changed within stated intent | minor | Changelog + visual diff |
| Token renamed or removed | major | Deprecate for one minor first |
| Component API changed | major | Migration note, before and after |
| Accessibility correction | patch | Ship immediately, document after |

Nothing is deleted without notice: mark it deprecated with a pointer to its replacement, announce it,
keep both working for one minor version, then remove at the next major with a migration note.

---

## Relationship to the Figma library

The Figma file carries matching variable collections:

- **`DS 1 · Primitives`** — 85 variables, hidden from publishing
- **`DS 2 · Semantic`** — 42 variables with Light and Dark modes
- **Text styles** — the nine-step scale in Open Sans and Roboto
- **`DS · Foundations`** page — specimen sheet and a light/dark comparison

Token names match between Figma and CSS, so a value changed in one has an obvious counterpart in the
other. Keeping them in sync is currently manual — if this system grows, wiring `tokens.json` into the
Figma variables via the REST API is the natural next step.

---

## License

Internal to CME Bank.
