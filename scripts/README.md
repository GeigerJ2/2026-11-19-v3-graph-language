# Runnable slide examples

One standalone Python script per slide in [`../slides.md`](../slides.md).
Each script validates its expected outcomes and generates real provenance diagrams
from stored AiiDA nodes using `aiida.tools.visualization.Graph` **inside the script**.
There is no separate rendering step and no hand-drawn substitute for provenance.

## Requirements

Run from the aiida-core repository root with its `uv` environment:

- This checkout's graph-language API and project dependencies.
- An initialized AiiDA profile. The scripts default to `graph-examples`; use
  `--profile YOUR_PROFILE` to select another existing profile.
- Graphviz's `dot` executable on `PATH` for SVG rendering.
- For slide 06, a local `/bin/bash` executable and local process execution.

All examples execute locally through `run_get_node`; no daemon or message broker
is required. They store nodes in the selected profile, including the deliberately
failed examples. They do not change the profile's polling configuration.

## Run

Run a single example:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/01_control_flow.py
```

Choose a profile and output directory:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/03_parallel_map.py \
  --profile graph-examples --output-dir /tmp/graph-slide-provenance
```

Run all eight sequentially, stopping if an example fails its checks:

```bash
for script in pres/2026-11-19-v3-graph-language/scripts/[0-9][0-9]_*.py; do
  uv run python "$script" --profile graph-examples || break
done
```

Each script prints its root process PK, result or expected failure status, and
rendered SVG path. By default, SVGs and Graphviz source files go into `generated/`
next to the scripts, independent of the current working directory. Re-running an
example creates new stored provenance and overwrites its diagram files.

## Examples and expected outcomes

| Slide | Script | Checks and diagrams |
| --- | --- | --- |
| 01 | `01_control_flow.py` | `choose(10, True) = 11`, `choose(10, False) = 12`; two SVGs showing the selected task. |
| 02 | `02_retry.py` | Two declared unstable attempts followed by success, returning `10`; zero retry budget causes the guard task to fail and the graph to finish with exit status `400`. Two SVGs. |
| 03 | `03_parallel_map.py` | Expand three cubic structures by a linear factor of `1.05`, then reduce their volumes to `38.201625`. Checks the original structures were not mutated. One SVG. |
| 04 | `04_port_model.py` | Nested `PortModel` defaults produce `11.57625`; checks the per-field input nodes. One SVG. |
| 05 | `05_pydantic.py` | Equivalent Pydantic declaration produces `11.57625`, with the same per-field input checks. One SVG. |
| 06 | `06_existing_processes.py` | An existing multiply-add WorkChain followed by an addition CalcJob produces `14`. One SVG including nested processes. |
| 07 | `07_missing_context.py` | The true path returns `5`; the false path raises the expected missing-`ctx.total` `AttributeError`. Two SVGs, including the excepted WorkChain. |
| 08 | `08_build_validation.py` | Rejects the broken graph during `build()`, then executes both fixed branches, returning `11` and `12`. Two SVGs for the fixed graph. |

Slides 02 and 07 intentionally log exception tracebacks. Their scripts verify the
expected failures and still exit successfully. Other failures are not suppressed.
The invalid graph on slide 08 never executes, so it has **no stored provenance**;
only its fixed version can have provenance rendered.

## Slide 06: local execution setup

Without `--code`, the integration example creates or reuses a demo computer named
`graph-demo-localhost` (`core.local` transport, `core.direct` scheduler) and an
installed code named `graph-demo-bash` (`/bin/bash`, `core.arithmetic.add`). Its work
directory is created under the system temporary directory and is retained for
AiiDA's remote-folder references. The script does not delete computers, codes,
calculation directories, or stored nodes.

To use an existing compatible installed bash code instead:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/06_existing_processes.py \
  --profile graph-examples --code 'your-bash-code@your-computer'
```

This script uses the current `runtime_config` API instead of the slide's obsolete
`task_metadata` keyword. The code is supplied to both placements through execution
configuration; explicit scheduler options apply to `add_calc`. The stock
`MultiplyAddWorkChain` does not expose scheduler options and uses its internal
arithmetic CalcJob's resource defaults.

## Presentation-only DOT → SVG styling

`render_provenance.py` restyles existing AiiDA-generated DOT digraphs without
loading a profile or executing any workflows. It requires Graphviz's `dot` and
the project's Python `graphviz` package. Run from this presentation directory:

```bash
uv run python scripts/render_provenance.py \
  scripts/generated/09_multiply_add_0 \
  scripts/generated/09_multiply_add_1
```

The slide-ready SVGs are written to `public/assets/09_multiply_add_0-slides.svg`
and `public/assets/09_multiply_add_1-slides.svg`. Use `--output-dir` to change the
destination. The source DOT and original SVGs remain untouched. Every node, edge,
and label is preserved, including PKs, execution states, and link types; only
layout and styling change. The renderer supports flat AiiDA digraphs, not nested
subgraphs.

## Standalone annotations

The retry, structure, and model examples use eager annotations. This preserves
concrete type objects when tasks defined in `__main__` are serialized; postponed
annotation strings can otherwise lose their type-name globals in this execution
path. No engine code is patched by these examples.

## Interpreter comparison

`10_interpreters.py` runs the task-body and graph-body `if` examples for both
branches (`x=-2` and `x=2`, with `y=3`). It asserts the result, root input links,
selected child task, result creator, and workflow return link. It saves original
AiiDA DOT/SVG files under `generated/` and styled SVGs under `public/assets/`.

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/10_interpreters.py \
  --profile graph-examples
```

These provenance SVGs are retained as a separate comparison. The `choose_graph` node is the
root workflow process, not a node for the condition. Its selected `add` child
creates the result, which the root returns. The positive-input run calls only
`multiply`. Both cases were verified in an isolated local SQLite profile.

## GraphIR interpreter visualization

The interpreter slide now uses `11_interpreter_ir.py`, not provenance diagrams:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/11_interpreter_ir.py
```

No profile is required. The script builds both graphs, checks the actual IR
placement kinds and inline operations, and saves full JSON/Mermaid under
`generated/`, plus compact SVG views under `public/assets/`. The left-hand task
is placed in a minimal wrapper graph: its Python body is opaque to GraphIR.
The right-hand graph has an inline comparison and inline arithmetic in both
branch arms. The final `record` task creates a stored return value, as required
for a root workflow. The compact SVG collapses region port wiring and shows the
branch output as a selected-result connector, not an executable placement.

## Arithmetic boundaries

`12_arithmetic_boundaries.py` generates the three arithmetic comparison slides:

```bash
uv run python pres/2026-11-19-v3-graph-language/scripts/12_arithmetic_boundaries.py \
  --profile graph-examples
```

It compiles and runs `(x + y) * z` as one Python task, inline graph operations
followed by a `record` task, and separate `add`/`multiply` tasks. All three were
verified with `x=2, y=3, z=4`, producing `20`. Assertions check IR placement kinds,
inline operator kinds, child processes, output creators, and workflow returns.
The generated JSON/Mermaid, IR SVGs, and stored-provenance SVGs are retained.
The checkpoint slide describes the proposed per-statement persistence design,
explicitly labeled as not yet implemented for inline statements. This script
verifies current execution structure, not the proposed checkpoint guarantee,
and does not simulate crash recovery.

## Verification

All eight scripts were executed sequentially with the `graph-examples` profile,
without a daemon or broker, and produced twelve SVGs. The SVGs and their Graphviz
sources are generated artifacts, not portable copies of the profile's database.
