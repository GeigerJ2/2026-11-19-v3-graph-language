# AiiDA graph language for authoring workflows

An editable Slidev presentation.

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

- `slides.md`: slide content, external snippet imports, and diagrams.
- `scripts/`: Python snippet sources, execution checks, and provenance rendering ([guide](scripts/README.md)).
- `scripts/generated/README.md`: index of verified provenance diagrams.
- `backup_scripts/`: the previous scripts and generated artifacts, preserved as an archive.
- `components/ConceptCode.vue`: source-backed, color-highlighted concept-table snippets.
- `styles/index.css`: shared presentation styles, loaded automatically by Slidev.
- `public/assets/choose-provenance.svg`: AiiDA-generated provenance diagram used on slide 1.
- `package.json` and `bun.lock`: presentation tooling and pinned dependencies.

The snippets illustrate the AiiDA v3 graph-authoring API. The slides read their
Python directly from `scripts/`; building the presentation does not execute it.
Run and verify the supported examples, including real stored provenance diagrams:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/run_all.py
uv run python pres/2026-11-19-v3-graph-language/scripts/verify_snippets.py
```

Run these commands from the aiida-core repository root. By default, execution uses
a new isolated SQLite profile outside the repository, without a daemon or broker.
See the [script guide](scripts/README.md) for individual examples, diagram outputs,
and explicit limitations for proposals and comparison fragments.

Original Figma deck: https://www.figma.com/slides/zJuxqS9c2ainR2Q81eUEQp
