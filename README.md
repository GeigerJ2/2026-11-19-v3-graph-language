# AiiDA graph language for authoring workflows

An eight-slide, editable Slidev presentation.

## Run with Bun

```bash
bun install --frozen-lockfile
bun run dev
```

## Build and export

```bash
bun run build    # Static presentation in dist/
bun run export   # PDF export (requires Chromium)
```

If the export browser is missing, install it once:

```bash
bunx playwright install chromium
```

## Source files

- `slides.md`: slide content, code snippets, and diagrams.
- `styles/index.css`: shared presentation styles, loaded automatically by Slidev.
- `public/assets/choose-provenance.svg`: AiiDA-generated provenance diagram used on slide 1.
- `package.json` and `bun.lock`: presentation tooling and pinned dependencies.

The snippets illustrate the AiiDA v3 graph-authoring API; building the presentation
does not execute or validate the Python examples. The provenance SVG records a
local run; its node identifiers are illustrative.

Original Figma deck: https://www.figma.com/slides/zJuxqS9c2ainR2Q81eUEQp
