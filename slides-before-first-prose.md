---
theme: seriph
title: Graph language for aiida-core v3
transition: fade
colorSchema: light
---

<div class="flex items-center gap-10" style="height: 100%">
<div class="title-hero" style="flex: 1 1 auto">

# Graph language for aiida-core v3

**Julian Geiger, Alexander Goscinski** · MSD GM · PSI · 19 November 2026

</div>
<div style="flex: 0 0 310px">
  <img src="/logos/aiida/logo_AiiDA.png" alt="AiiDA" style="height: 48px" />
</div>
</div>

---

# Contents

1. Motivation
2. Separating build and run time
3. Control flow
4. Data flow
5. Interfaces and reuse
6. Case study
7. Execution

---
layout: section
---

# Motivation

---
layout: two-cols-header
layoutClass: side-by-side
---

# MultiplyAdd as WorkChain and as graph

::left::

```python
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import ToContext, WorkChain, calcfunction
from aiida.orm import Code, Int


@calcfunction
def multiply(x, y):
    return x * y


class MultiplyAddWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int)
        spec.input('z', valid_type=Int)
        spec.input('code', valid_type=Code)
        spec.outline(
            cls.multiply,
            cls.add,
            cls.result,
        )
        spec.output('result', valid_type=Int)

    def multiply(self):
        self.ctx.product = multiply(self.inputs.x, self.inputs.y)

    def add(self):
        future = self.submit(
            ArithmeticAddCalculation,
            x=self.ctx.product,
            y=self.inputs.z,
            code=self.inputs.code,
        )
        return ToContext(addition=future)

    def result(self):
        self.out('result', self.ctx.addition.outputs.sum)
```

::right::

```python
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import graph, task
from aiida.orm import Code

add_calc = task(ArithmeticAddCalculation)


@task
def multiply(x: int, y: int) -> int:
    return x * y


@graph
def multiply_add(x: int, y: int, z: int, code: Code) -> int | float:
    product = multiply(x=x, y=y)
    total = add_calc(x=product, y=z, code=code)
    return total.sum
```

---

# Advantages over WorkChains

- **Less code:**
  - The function signature replaces `spec.input` and `spec.output`.
  - The function body replaces the outline and its step methods.
  - Named values replace `submit`, `ToContext`, and `self.ctx`.
- **Static checks before launch:** `build()` checks names, wiring, and types without running tasks, and reports the offending source line.
- **No plugin infrastructure:**
  - Graphs are defined in modules, scripts, or notebooks, without entry points or packaging.
  - Each submission carries the graph structure and a pickled copy of every task.
- **Concurrency from data flow:** the graph process submits every task whose inputs are ready.
- **Declared failures as values:** `Result[..., Errors]` outputs branch and retry in the graph body.
- **Reuse:** `task(...)` wraps existing CalcJobs and WorkChains; graphs nest as subgraphs.

---

# WorkChain concepts in a graph

<div class="concept-map concept-comparison">
<div class="concept-heading">WorkChain<small></small></div>
<div></div>
<div class="concept-heading">Graph
  <pre class="concept-code"><code>add_calc = task(ArithmeticAddCalculation)</code></pre>
</div>

<pre class="concept-code"><code><span class="concept-function">@calcfunction</span>
def multiply(x, y):
    return x * y</code></pre>
<div class="concept-arrow concept-function"><strong>Calculation</strong><span>⟶</span></div>
<pre class="concept-code"><code><span class="concept-function">@task</span>
def multiply(<span class="concept-ports">x: int, y: int</span>) -&gt; <span class="concept-ports">int</span>:
    return x * y</code></pre>

<pre class="concept-code"><code>        <span class="concept-ports">spec.input('x', valid_type=Int)</span>
        <span class="concept-ports">spec.input('y', valid_type=Int)</span>
        <span class="concept-ports">spec.input('z', valid_type=Int)</span>
        <span class="concept-ports">spec.output('result', valid_type=Int)</span></code></pre>
<div class="concept-arrow concept-ports"><strong>Ports &amp; types</strong><span>⟶</span></div>
<pre class="concept-code"><code>@graph
def multiply_add(
    <span class="concept-ports">x: int, y: int, z: int</span>
) -&gt; <span class="concept-ports">int</span>:</code></pre>

<pre class="concept-code"><code>        <span class="concept-task">spec.outline(cls.multiply, cls.add, cls.result)</span>

    def multiply(self):
        <span class="concept-state">self.ctx.product</span> = <span class="concept-function">multiply(</span>
            <span class="concept-function">self.inputs.x, self.inputs.y)</span>
    def add(self):
        future = <span class="concept-task">self.submit(ArithmeticAddCalculation,</span>
            <span class="concept-task">x=self.ctx.product, y=self.inputs.z)</span>
        return ToContext(<span class="concept-state">addition</span>=future)</code></pre>
<div class="concept-arrow concept-task"><strong>Steps &amp; submit</strong><span>⟶</span><strong class="concept-state">Context → values</strong></div>
<pre class="concept-code"><code>    <span class="concept-state">product</span> = <span class="concept-function">multiply(x=x, y=y)</span>
    <span class="concept-state">addition</span> = <span class="concept-task">add_calc(x=product, y=z)</span></code></pre>

<pre class="concept-code"><code>    def result(self):
        <span class="concept-return">self.out('result',</span>
                 self.ctx.<span class="concept-state">addition</span>.outputs.sum<span class="concept-return">)</span></code></pre>
<div class="concept-arrow concept-return"><strong>Outputs</strong><span>⟶</span></div>
<pre class="concept-code"><code>    <span class="concept-return">return</span> <span class="concept-state">addition</span>.sum</code></pre>
</div>


---

# Graph body and task code

| | `@task` | `@graph` body |
| --- | --- | --- |
| Role | Computation | Orchestration |
| Language | Arbitrary Python | Limited Python subset |
| Validation | Ports at declaration; body at runtime | Wiring at build; values at runtime |
| Interpreter | Python | AiiDA |
| Process | New child per executed call | Same graph process |
| Parallelism | Independent calls: separate workers? | Submits all ready calls |
| Provenance | Data inputs and outputs are nodes | Inline state is checkpointed |

---

<!-- Original slide by Alexander Goscinski (934314f), kept for discussion. -->

# Graph language vs. task code

@Julian This is slop but i wanted to create a slide that explains the difference between the two without going into details: 

graph: aiida interpreted (limited subset of python) / task: python interpreted (arbitrary python)

graph: same aiida process (not parallelizable) / task: new aiida process (parallelizable)

<div class="code-boundaries">
<pre class="code-boundaries-source"><code><span class="code-boundaries-graph">@graph
def multiply_add(x: int, y: int, z: int) -&gt; int:</span>
    <span class="code-boundaries-graph">product =</span> <span class="code-boundaries-task">multiply(x=x, y=y)</span>
    <span class="code-boundaries-graph">total =</span> <span class="code-boundaries-task">add_calc(x=product, y=z)</span>
    <span class="code-boundaries-graph">return total.sum</span></code></pre>
<div class="code-boundaries-label code-boundaries-graph-label">
<span class="code-boundaries-pointer">←</span>
<div><strong>Graph statements</strong><p>AiiDA runtime · limited Python subset</p><b>Same graph process</b></div>
</div>

<pre class="code-boundaries-source"><code><span class="code-boundaries-task">@task</span>
def multiply(x: int, y: int) -&gt; int:
    <span class="code-boundaries-task">return x * y</span></code></pre>
<div class="code-boundaries-label code-boundaries-task-label">
<span class="code-boundaries-pointer">←</span>
<div><strong>Task call &amp; body</strong><p>Python · arbitrary Python code</p><b>New AiiDA process per call</b><p>Can run on different daemon workers*</p></div>
</div>
</div>

<div class="code-boundaries-note"><code>add_calc = task(ArithmeticAddCalculation)</code><br/>* All ready tasks are submitted before waiting; available daemon workers can execute them in parallel.<br/>Here, addition depends on multiplication, so these two task calls run in sequence.</div>

---
layout: section
---

# Separating build and run time

---
layout: two-cols-header
layoutClass: dense
---

# Debugging WorkChains

The spec is valid, but one execution path leaves a context value unset.

::left::

```python
from aiida.engine import WorkChain, calcfunction, if_
from aiida.orm import Bool, Int


@calcfunction
def increment(value: Int) -> Int:
    return value + 1


class ConditionalCtxChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('value', valid_type=Int)
        spec.input('flag', valid_type=Bool)
        spec.output('result', valid_type=Int)
        spec.outline(
            if_(cls.should_add)(cls.add_one),
            cls.finish,
        )

    def should_add(self):
        return self.inputs.flag.value

    def add_one(self):
        self.ctx.total = increment(self.inputs.value)

    def finish(self):
        self.out('result', self.ctx.total)
```

::right::

- `flag=True`: `add_one` runs, then `finish`; `result` is `value + 1`.
- A test of only `flag=True` passes; the bug surfaces when a run takes the other path.
- `flag=False`: `add_one` is skipped. The process excepts at runtime, in `finish`, one step after the cause:

```text
AttributeError: 'AttributeDict' object has no attribute 'total'
```


---
layout: two-cols-header
layoutClass: dense
---

# Debugging graphs

The same bug in a graph fails when `build()` is called, before any launch.

::left::

```python
from aiida.engine import graph, task


@task
def add(x: int, y: int) -> int:
    return x + y


@graph
def broken(value: int, flag: bool) -> int:
    if flag:
        total = add(x=value, y=1)
    return total


broken.build()
```

**Fix: bind `total` before the `if`, or add an `else` arm**

```python
total = value
if flag:
    total = add(x=value, y=1)
```

```python
if flag:
    total = add(x=value, y=1)
else:
    total = add(x=value, y=2)
```

::right::

```text
GraphLanguageError: broken.py:11:5: __main__:broken:
  without an `else` arm the branch keeps the prior
  binding, so `total` must be assigned before the `if`;
  assign it first or add an `else` arm instead
    if flag:
    ^
```

- The error names the cause (the binding missing on the `else` path), the source line, and the column.
- `build()` needs no profile, inputs, or launch, so a test or notebook cell catches the bug.

<div class="verdict">

`build()` checks wiring, not task bodies; runtime tests remain necessary.

</div>

---

# Validation at build, launch, and run time

<br>

**Build**

- `build()` checks syntax, wiring, and static contracts without running tasks or creating nodes.
- Errors name the source line and column, as well as the fix.

**Launch**

- Fills inputs and defaults.
- Binds `runtime_config` per placement.
- Rejects unknown placements and missing execution inputs, naming the placement.

**Run**

- Re-checks branch conditions, fails tasks with missing outputs, and maps declared failures to error arms.
- Checkpoints finished task nodes, scope progress, and inline values; a restarted graph reuses finished work.

---
layout: section
---

# Control flow

---
layout: two-cols-header
---

# Branching

One graph process evaluates the branch and starts one task process.

::left::

**Task: ordinary Python**

```python
from aiida.engine import graph, task


@task
def add(x: int, y: int) -> int:
    return x + y
```

- The `GraphProcess` (stored as a `GraphNode`) evaluates `flag` and starts the selected task.
- The task runs as its own process (`CalcFunctionNode`), executes its Python body, and creates the result node.
- Separate processes are not separate workers: daemon execution may use different workers; a local run uses one interpreter.

::right::

**Graph: orchestration**

```python
@graph
def choose(x: int, flag: bool) -> int:
    if flag:
        chosen = add(x=x, y=1)
    else:
        chosen = add(x=x, y=2)
    return chosen
```

---

# Provenance of a branch run

<img class="provenance" src="/assets/choose-provenance.svg" alt="AiiDA-generated provenance from stored nodes and links" />

<div class="caption">

Provenance of a local run (`x=10, flag=True → result=11`): declared input names are preserved; `CREATE` and `RETURN` share one result node. Node identifiers are illustrative.

</div>

- The graph run is one process node; branch arms, loop iterations, nested graphs, and map items create no intermediate process nodes.
- Each task run is a child process node, with a call link named after its placement, such as `branch_1__add`.
- The task creates the result node (`CREATE`); the graph returns the same node (`RETURN`).

---
layout: two-cols-header
layoutClass: dense
---

# Subgraphs and conditional expressions

::left::

```python
from aiida.engine import graph, task


@task
def multiply(x: int, y: int) -> int:
    return x * y


@task
def add(x: int, y: int) -> int:
    return x + y


@graph
def multiply_add(x: int, y: int, z: int) -> int:
    product = multiply(x=x, y=y)
    return add(x=product, y=z)
```

::right::

```python
@graph
def outer(x: int, y: int, z: int) -> int:
    inner = multiply_add(x=x, y=y, z=z)
    return add(x=inner, y=x)


@graph
def choose_scaled(value: int, flag: bool) -> int:
    chosen = (value + 1) if flag else (value - 1)
    return add(x=chosen, y=0)
```

- A called graph runs as a scope of the same graph process; it creates no child workflow node.
- `x if condition else y` runs only the selected side. Here both sides are inline arithmetic, so the branch itself creates no process.

---
layout: two-cols-header
layoutClass: dense
---

# Declared failures

::left::

```python
from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, Result
from aiida.engine import graph, task


class DivisionErrors(ExitCodeEnum):
    ZERO_DENOMINATOR = ExitCode(410, 'The denominator is zero.')


@task
def divide(
    numerator: float, denominator: float
) -> Result[float, DivisionErrors]:
    if denominator == 0:
        return Err(DivisionErrors.ZERO_DENOMINATOR)
    return Ok(numerator / denominator)


@task
def recover_zero(error: DivisionErrors) -> float:
    return 0.0
```

::right::

```python
@graph
def ratio_or_zero(numerator: float, denominator: float) -> float:
    value, error = divide(
        numerator=numerator, denominator=denominator
    )
    if error is None:
        selected = value
    else:
        selected = recover_zero(error=error)
    return selected
```

- The call unpacks into `(value, error)`; exactly one of them is present.
- A declared failure sets the task's exit status but counts as completed, so the graph branches on it and finishes successfully.
- Undeclared failures and exceptions fail the graph with `ERROR_TASK_FAILED`.

---
layout: two-cols-header
layoutClass: dense
---

# Retrying a declared failure

Retry only the declared failure, and stop when the retry budget is used.

::left::

```python
from aiida.engine import Err, ExitCode, ExitCodeEnum, Ok, Result
from aiida.engine import graph, task


class StepErrors(ExitCodeEnum):
    UNSTABLE = ExitCode(410, 'Unstable step.')


@task
def run_step(x: int, attempt: int) -> Result[int, StepErrors]:
    if attempt < 1:
        return Err(StepErrors.UNSTABLE)
    return Ok(x + 1)


@task
def ensure(value: int | None) -> None:
    if value is None:
        raise ValueError('the step never succeeded.')
```

::right::

```python
@graph
def restartable(x: int, max_retries: int, attempt: int = 0) -> int:
    value, error = run_step(x=x, attempt=attempt)
    while error is StepErrors.UNSTABLE and attempt < max_retries:
        attempt = attempt + 1
        value, error = run_step(x=x, attempt=attempt)
    checked = ensure(value=value)
    return value
```

- `error is StepErrors.UNSTABLE` retries only that member; any other outcome ends the loop.
- `attempt` starts at 0; `max_retries` counts repeats after the first call.
- The counter is inline state, not a child process. `ensure` fails the graph when every attempt failed.

---
layout: section
---

# Data flow

---
layout: two-cols-header
layoutClass: dense
---

# Parallel map and reduction

Expand each structure independently; average the volumes after all items finish.

::left::

```python
from aiida.engine import graph, par_map, task
from aiida.orm import DataList, StructureData


@task
def expand_cell(structure: StructureData) -> StructureData:
    scaled = structure.clone()
    scaled.set_cell(
        [
            [1.05 * component for component in vector]
            for vector in structure.cell
        ]
    )
    return scaled


@task
def mean_cell_volume(structures: DataList) -> float:
    if not structures:
        raise ValueError('empty structure list')
    total = 0.0
    for structure in structures:
        total += structure.get_cell_volume()
    return total / len(structures)
```

::right::

<div class="flow">
<span class="box">DataList</span>→<span class="stack"><span class="box">expand_cell</span><span class="box">expand_cell</span><span class="box">expand_cell</span></span>→<span class="box">DataList</span>→<span class="box">mean_cell_volume</span>
</div>

```python
@graph
def mean_expanded_volume(structures: DataList) -> float:
    expanded = par_map(expand_cell, structures)
    return mean_cell_volume(structures=expanded)
```

- `par_map` applies a one-input task to every element of a `DataList`; `for` loops belong in `@task` bodies.
- All items start before the graph waits; the result keeps the element order, and a collector task builds the container.

---

# Inline collections

Comprehensions and indexing over typed lists and mappings run inside the graph process.

```python
from aiida.engine import graph, task


@task
def sum_values(values: list[int]) -> int:
    return sum(values)


@graph
def scaled_filtered(values: list[int], scale: int) -> int:
    scaled = [item * scale for item in values if item > 0]
    return sum_values(values=scaled)
```

- `list[T]` and `dict[str, T]` annotations give every element a declared type; inline results create no process and no node.
- A root graph returns task outputs, so `sum_values` stores the result computed from the inline list.

---
layout: two-cols-header
layoutClass: dense
---

# Placement names and partial bindings

::left::

```python
from aiida.engine import graph, task


@task
def add(x: int, y: int) -> int:
    return x + y
```

- `.alias('name')` names one placement. Calling a task twice without aliases fails `build()`.
- `partial(add, y=y)` binds inputs once; each call places `add` independently. `partial` needs no import in a graph body.

::right::

```python
@graph
def two_steps(x: int, y: int) -> int:
    first = add.alias('scf')(x=x, y=y)
    return add.alias('nscf')(x=first, y=y)


@graph
def add_shifted(x: int, y: int) -> int:
    add_y = partial(add, y=y)
    first = add_y.alias('first')(x=x)
    return add_y.alias('second')(x=first)
```

---
layout: section
---

# Interfaces and reuse

---
layout: two-cols-header
layoutClass: dense
---

# Structured inputs with PortModel

One schema declares nested ports, defaults, and help text for tasks and graphs.

::left::

```python
from typing import Annotated

from aiida.engine import PortField, PortModel
from aiida.engine import graph, run_get_node, task


class Scaling(PortModel):
    factor: Annotated[
        float, PortField(help='Cell scale factor.')
    ] = 1.05


class Settings(PortModel):
    scaling: Scaling
    label: str = 'demo'


@task
def scaled_volume(volume: float, settings: Settings) -> float:
    return volume * settings.scaling.factor**3
```

::right::

```python
@graph
def configured(volume: float, settings: Settings) -> float:
    return scaled_volume(volume=volume, settings=settings)


run_get_node(configured, volume=10.0, settings={'scaling': {}})
```

- Each field becomes its own port and input node: `settings.scaling.factor` → `Float(1.05)`, `settings.label` → `Str('demo')`.
- `settings={'scaling': {}}` fills the nested defaults; the result is `11.57625`.

---
layout: two-cols-header
layoutClass: dense
---

# Pydantic models as port namespaces

`BaseModel` declarations map to the same typed port namespaces as `PortModel`.

::left::

```python
from aiida.engine import graph, run_get_node, task
from pydantic import BaseModel, Field


class PydanticScaling(BaseModel):
    factor: float = Field(
        default=1.05, description='Cell scale factor.'
    )


class PydanticSettings(BaseModel):
    scaling: PydanticScaling
    label: str = 'demo'


@task
def scaled_volume(
    volume: float, settings: PydanticSettings
) -> float:
    return volume * settings.scaling.factor**3
```

::right::

```python
@graph
def configured_pydantic(
    volume: float, settings: PydanticSettings
) -> float:
    return scaled_volume(volume=volume, settings=settings)


run_get_node(
    configured_pydantic, volume=10.0, settings={'scaling': {}}
)
```

- Nested models, defaults, and `Field(description=...)` help text become ports; leaves accept `str`, `int`, `float`, `bool`, and their optional forms.
- Tasks receive attribute-accessible mappings, not model instances; model methods are unavailable.
- AiiDA ports check types. Validators and field aliases are rejected at declaration; check values inside the `@task`.

---
layout: two-cols-header
layoutClass: dense
---

# CalcJob and WorkChain tasks

Wrap the process class with `task(...)`, then wire its named inputs and outputs.

::left::

```python
from aiida.calculations.arithmetic.add import (
    ArithmeticAddCalculation,
)
from aiida.engine import graph, task
from aiida.workflows.arithmetic.multiply_add import (
    MultiplyAddWorkChain,
)

multiply_add = task(MultiplyAddWorkChain)
add_calc = task(ArithmeticAddCalculation)


@graph
def integrated(x: int, y: int, z: int) -> int | float:
    prepared = multiply_add(x=x, y=y, z=z)
    total = add_calc(x=prepared.result, y=z)
    return total.sum
```

::right::

```python
from aiida.engine import run_get_node
from aiida.orm import load_code

code = load_code('add@localhost')
options = {
    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}
}
outputs, node = run_get_node(
    integrated,
    inputs={'x': 2, 'y': 3, 'z': 4},
    runtime_config={
        'multiply_add': {'code': code},
        'add_calc': {
            'code': code,
            'metadata': {'options': options},
        },
    },
)
```

- `multiply_add` keeps its outline and children and computes `x * y + z`; `add_calc` adds `z` to that result.
- The graph only connects them and returns the existing `sum` node; both run as ordinary child processes with provenance.
- `code` and `metadata` are execution settings: they travel under `runtime_config`, separate from the scientific inputs.

---
layout: section
---

# Case study

---

# Koopmans case study

A koopmans developer ported a WorkGraph workflow to the graph language and reported what it lacked.

- The workflow runs `Wannier90WorkChain` once per projection block, with the same structure, k-point grid, and band k-points for every block, then merges the Hamiltonians.
- WorkGraph: a Python `for` loop over the blocks makes one call per block.
- Graph language: `par_map` over the blocks replaces the loop.
- The first port needed helper tasks for two things the language now covers: inputs shared by all mapped calls, and list arithmetic on the grid.

---
layout: two-cols-header
layoutClass: dense
---

# Koopmans case study: shared inputs for mapped calls

::left::

**First port**

```python
# bundle: task copying shared inputs into one DataDict per block
# unpack: task reading them back out of one item


@graph
def wannierize_one(item: DataDict) -> ...:
    inputs = unpack(item=item)
    return Wannierize(
        structure=inputs.structure,
        block=inputs.block,
        mesh=inputs.mesh,
        bands_kpoints=inputs.bands_kpoints,
    )


# in wannierize_blocks
items = bundle(
    blocks=blocks,
    structure=structure,
    mesh=mesh,
    bands_kpoints=bands_kpoints,
)
results = par_map(wannierize_one, items)
```

::right::

**Now**

```python
# in wannierize_blocks
configured = partial(
    Wannierize,
    structure=structure,
    mesh=mesh,
    bands_kpoints=bands_kpoints,
)
results = par_map(configured, blocks)
```

- `partial` fixes the shared inputs; `par_map` maps the remaining `block` input.
- Shared nodes travel as ordinary input wires, so every `Wannierize` run links to the original structure.
- Mapping a `DataDict` keeps its keys and insertion order.

---
layout: two-cols-header
layoutClass: dense
---

# Koopmans case study: list arithmetic inline

::left::

**First port**

```python
@task
def scale_grid(grid: list[int], factor: int) -> list[int]:
    return [n * factor for n in grid]


# in wannierize_blocks
mesh = scale_grid(grid=grid, factor=factor)
```

::right::

**Now**

```python
# in wannierize_blocks
mesh = [n * factor for n in grid]
```

- The comprehension runs inside the graph process: no task, no node, and its value is checkpointed.
- Typed `list[T]` and `dict[str, T]` ports support indexing and comprehensions.

---

# Koopmans case study: open points

- `par_map` needs an `orm.DataDict` or `orm.DataList`, not a typed Python mapping such as `dict[str, Block]`.
- Inline `sum(...)`, generator expressions, and `tuple(...)` are unsupported, so `count_wann` stays a task.
- Positivity and grid-length constraints are runtime checks in a task, not annotations.
- Per-item metadata, such as one call link label per block, is unsupported; `.alias(...)` names a placement, not a map item.

---
layout: section
---

# Runtime

---

# Execution

- `submit` launches one `GraphProcess`, recorded as a `GraphNode`; daemon workers run it like any other process.
- Each step of the graph process submits every task whose inputs are ready, then waits for them.
- Independent tasks run concurrently; loop iterations run one at a time.
- Inline values are checkpointed with the graph process, so a restarted graph resumes counters and conditions.
