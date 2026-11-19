# Slide snippets and verified provenance

The Python in [`../slides.md`](../slides.md) is imported directly from these files
using Slidev's `<<< ...#region` syntax. Edit the source here, not a second copy in
the Markdown. The three merged slides use generated excerpts so they retain native
Python syntax highlighting. Refresh them after editing their source scripts:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/sync_slide_code.py
```

`verify_snippets.py` checks that these excerpts match the canonical source regions. The concept table uses `ConceptCode.vue` to preserve its custom
colors while reading the nine `concept_*.py` fragments from disk. The two error
excerpts are external `.txt` snippets as well.

The previous scripts, renderer, and generated artifacts are preserved unchanged
in [`../backup_scripts/`](../backup_scripts/). The renderer in this folder is a
copy of that existing `render_provenance.py`, not a new diagram generator.

## Run everything

From the repository root:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/run_all.py
uv run python pres/2026-11-19-v3-graph-language/scripts/verify_snippets.py
```

By default, execution creates a **fresh isolated SQLite profile in a temporary
directory** and prints its configuration path. It does not use or modify your
normal AiiDA profile. The directory is retained, not deleted: the stored process
PKs and UUIDs in the results refer to this database. No daemon, database service,
or message broker is needed.

Requirements: this checkout's `uv` environment, NumPy, Graphviz's `dot`, and
`/bin/bash` for the local arithmetic CalcJobs. All are used through the project's
existing APIs. The CalcJob examples create a `localhost` computer and an
`add@localhost` bash code in the selected profile; calculation work directories
are retained for the stored `RemoteData` references.

To explicitly opt into an existing profile instead:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/run_all.py --profile graph-examples
```

This stores new nodes in that profile and may create the demo computer and code.
It does not change polling options.

## Run one example

Every `sNN_*.py` file is also an entry point. Shared-definition snippets delegate
to the graph that exercises them; intentionally unsupported snippets report their
status without fabricating a run.

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/s14_map_reduce.py
uv run python pres/2026-11-19-v3-graph-language/scripts/run_all.py --snippet 22 24
```

Use `--output-dir` and `--assets-dir` for a separate partial-run report:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/run_all.py --snippet 24 \
  --output-dir /tmp/slide-retry --assets-dir /tmp/slide-retry/assets
```

Each invocation overwrites its `results.json`, Markdown index, gallery, and
same-named diagrams. A failed execution saves a partial report with
`completed: false` and exits unsuccessfully; unexpected errors are not suppressed.

## Outputs

- [`generated/results.json`](generated/results.json): process PKs, UUIDs, scalar
  results, statuses, retained profile location, and rendering paths. Diagram paths
  are relative to the presentation directory.
- [`generated/README.md`](generated/README.md): clickable index of the verified
  provenance diagrams and notes for non-executable examples.
- `generated/*.dot`: unmodified AiiDA-generated provenance graphs.
- [`../public/assets/provenance/`](../public/assets/provenance/): styled SVGs.
- [`../public/assets/provenance/index.html`](../public/assets/provenance/index.html):
  browsable diagram gallery (also served at `/assets/provenance/index.html` by Slidev).

`run_all.py` builds graph definitions before execution, checks numerical results,
and traverses **real stored nodes and links** with `aiida.tools.visualization.Graph`.
It then passes the resulting DOT files to the existing renderer. No hand-drawn
nodes, branches, or checkpoint boundaries are presented as provenance.

`verify_snippets.py` checks Python syntax, every slide import and source region,
concept-fragment coverage, image references, and the rendered SVG node sets and
edge counts against the original DOT graphs. Use `--sources-only` to check source
files without requiring an execution report.

You can restyle a saved graph without loading a profile or rerunning its workflow:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/render_provenance.py \
  pres/2026-11-19-v3-graph-language/scripts/generated/s24_denominator_0.dot
```

Pass `--output-dir .../public/assets/provenance` to overwrite a gallery SVG;
the renderer's original default remains `public/assets/`.

## Source inventory and execution policy

[`snippets.json`](snippets.json) maps all **34 Python snippets and nine concept
fragments** to their slide titles and execution policies. The source-file numbers
are snippet IDs, not slide numbers, so adding prose slides does not rename files.

| IDs | Example | Verification |
| --- | --- | --- |
| 01–02 | MultiplyAdd WorkChain vs graph | Both return `10`, using real local CalcJobs. |
| 03 | Missing WorkChain context | True branch returns `5`; false branch raises the expected `AttributeError`; both have provenance. |
| 04 | Broken graph | `build()` must reject the missing binding. No execution means no provenance. |
| 05–06 | Fixed branch bindings | Both boolean branches are run: prior binding gives `11`/`10`; explicit else gives `11`/`12`. |
| 07–08 | Task vs inline interpreter | Both compute `10`; an explicit `record` wrapper materializes the inline helper's output. |
| 09–10 | NumPy task and graph | Both return mean `2.0`. |
| 11–12 | Task vs inline checkpoints | Both return `10`; diagrams show their different task boundaries, not a crash-recovery claim. |
| 13–14 | Typed structure map/reduce | Returns `38.201625`; input structures remain unchanged. |
| 15–16 | Placement names and partial bindings | Aliased placements return `8`; `partial(...)` is rejected in this checkout and recorded as unsupported. |
| 17–18 | PortModel | Nested defaults produce `11.57625`. |
| 19–20 | Existing processes/runtime config | WorkChain and CalcJob integration returns `14`. |
| 21–22 | Declared failures | Normal division returns `4.0`; zero denominator selects a `0.0` fallback. |
| 24 | Retry loop | Reuses the displayed `divide` task and returns `value` directly. Zero denominator retries to `12.0`; normal division gives `4.0`; zero retry budget finishes without a result output because no explicit failure guard remains. All three roots are rendered. |
| 25–26 | WorkGraph comparison | Contextual WorkGraph builder fragments, not runnable AiiDA graph-language workflows; no AiiDA provenance is claimed. |
| 27 | Graph branch binding | Both branches return `1`/`7`. |
| 28 | Explicit checkpoint proposal | `checkpoint()` is unimplemented; kept as proposal source, not executed. |
| 29 | Automatic checkpoint proposal | Runs the current arithmetic baseline, returning `20`; does **not** claim proposed per-statement persistence. |
| 30–31 | Branch provenance comparison | Both task and graph variants return `1`/`6`; both branches are rendered. |
| 32–33 | Branch interpreter comparison | Both variants return `1`/`6`; inline operations are not invented provenance nodes. |
| 34–35 | Arithmetic provenance comparison | Both return `20`, with different task boundaries. |

The `concept_*.py` files are explicitly contextual fragments, including a graph
signature and WorkChain method excerpts. They are syntax-checked and displayed
from source; the corresponding complete workflows in snippets 01–02 supply the
real executable comparison.

The declared-failure slide hardcodes its fallback as `0.0`. Its `ratio_or_zero`
graph is executed as a helper inside `stored_ratio_or_zero`; a final `record_ratio`
task materializes the selected scalar for the root workflow's stored output.
This execution boundary is outside the displayed snippet, not a recovery task.

Expected failure paths deliberately emit AiiDA exception reports. The runner
checks these failures and still succeeds. The prototype `partial` and checkpoint
examples are not patched into the engine or silently replaced with different code.

## Presentation build

```bash
cd pres/2026-11-19-v3-graph-language
bun run build
```

Building the presentation resolves snippet imports but does not execute workflows.
The old GraphIR illustrations remain in `public/assets/`; their original generators
are archived in `backup_scripts/`. New provenance-comparison images in the appendix
use the verified outputs from this folder.
