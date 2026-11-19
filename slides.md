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
- **Daemon execution:** one `GraphProcess`, recorded as a `GraphNode`.
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
| Process | Separate AiiDA process per call | Same graph process |
| Parallelism | Independent calls can use separate workers | Submits all ready calls before waiting |
| Provenance | Data inputs and outputs are nodes | Inline state is checkpointed |

---

<!-- Original slide by Alexander Goscinski (934314f), kept for discussion. -->

# Graph language vs. task code

@Julian This is slop but i wanted to create a slide that explains the difference between the two without going into details:

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
<div><strong>Task call &amp; body</strong><p>Python · arbitrary Python</p><b>Separate AiiDA process per call</b><p>Independent calls: separate workers*</p></div>
</div>
</div>

<div class="code-boundaries-note"><code>add_calc = task(ArithmeticAddCalculation)</code><br/>* Ready tasks can run on separate daemon workers. Here, addition waits for multiplication.</div>

---
layout: section
---

# Separating build and run time

---
class: branch-binding
---

# Branch results: Python binding vs. graph interpretation

**WorkGraph executes the builder in Python. The graph language interprets the control flow at run time.**

<div class="grid grid-cols-3 gap-5">
<div>

### WorkGraph: no runtime selection

```python
with If(first_sum < 0):
    result = add(
        x=first_sum, y=2).result

with If(first_sum >= 0):
    result = multiply(
        x=first_sum, y=3).result

final_sum = add(
    x=result, y=1).result
```

<img class="workgraph-dependency" src="/assets/workgraph-overwritten-binding.svg" alt="Only the multiplication output is wired to the final addition; the conditional addition has no connection to it." />

Both `with` bodies execute **while building**. Python overwrites `result` with the multiplication socket—even when that task will be skipped.

</div>
<div>

### WorkGraph: context + ordering

```python
with If(first_sum < 0):
    second_sum = add(x=first_sum, y=2).result
    wg.ctx.result = second_sum

with If(first_sum >= 0):
    product = multiply(x=first_sum, y=3).result
    wg.ctx.result = product

final_sum = add(x=wg.ctx.result, y=1).result
final_sum << second_sum
final_sum << product
```

<img class="workgraph-dependency" src="/assets/workgraph-context-ordering.svg" alt="Both conditional tasks write ctx.result; solid edges carry values and dashed wait edges order the final addition after both branches resolve." />

The taken task populates context at runtime. Explicit waits prevent an early read; the untaken branch is skipped.

</div>
<div>

### Graph language: selected output

```python
# Inside an @graph function:
if first_sum < 0:
    result = add(
        x=first_sum, y=2)
else:
    result = multiply(
        x=first_sum, y=3)

final_sum = add(
    x=result, y=1)
```

The compiler creates a **branch placement with one output**. The runtime runs only the selected arm. `final_sum` depends on the branch output—not on shared context.

</div>
</div>

<div class="verdict">The wait is not forgotten: the selected producer → branch output → consumer dependency is encoded in the graph.</div>

<style>
.branch-binding {
  --slidev-code-font-size: 10px;
  --slidev-code-line-height: 14px;
}
.branch-binding h3 {
  font-size: 0.9rem;
  margin: 0.7rem 0;
}
.branch-binding .grid p {
  font-size: 12px;
  line-height: 1.45;
}
.branch-binding .verdict {
  margin-top: 0.5rem;
}
.branch-binding .workgraph-dependency {
  width: 100%;
  height: 86px;
  object-fit: contain;
  margin-top: 0.5rem;
}
</style>

<!--
In WorkGraph, If is a context manager that records zone membership. It is not a Python if:
Python executes both with bodies when constructing the workflow, so the second assignment
wins in the builder's local namespace. For first_sum < 0, result therefore still points
to the skipped multiplication, not the executed addition. Adding a wait alone cannot fix
that incorrect value reference.

The context workaround records both possible runtime writers. The executed task exports
its result to ctx; context reads do not automatically establish a producer dependency,
so both branches must be resolved before the final task reads the slot.

The new @graph body is parsed, not executed as ordinary builder Python. Lowering creates
a BranchControl with two body templates and a common output. The final task reads that
output. The interpreter chooses one arm, waits for its scope, and exposes its result.
Use if/else to state the mutually exclusive choice explicitly rather than asking the
compiler to prove that two independent tests are complementary. Independent side-effect
ordering still requires after=.
-->

---
layout: two-cols-header
layoutClass: dense
---

# Debugging WorkChains

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

- `flag=True`: result is `value + 1`.
- `flag=False`: `finish` raises:

```text
AttributeError: 'AttributeDict' object has no attribute 'total'
```


---
layout: two-cols-header
layoutClass: dense
---

# Debugging graphs

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

- Missing binding: source line, column, suggested fixes.
- `build()`: no profile or inputs.

<div class="verdict">

Task bodies still need runtime tests.

</div>

---

# Validation at build, launch, and run time

<br>

**Build**

- Syntax, wiring, contracts; no execution or nodes.
- Source line, column, suggested fixes.

**Launch**

- Inputs, defaults, per-placement `runtime_config`.
- Errors identify invalid placements or missing execution inputs.

**Run**

- Condition types, required outputs, declared failures.
- Restarts restore progress and inline state; completed tasks are reused.

---
layout: section
---

# Control flow

---
layout: two-cols-header
---

# Branching

::left::

**Task: ordinary Python**

```python
from aiida.engine import graph, task


@task
def add(x: int, y: int) -> int:
    return x + y
```

- Graph tests `flag`; only the selected task runs.
- Task: `CalcFunctionNode`, with a stored result.
- Local: one interpreter. Daemon: workers may differ.

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

Local run: `x=10, flag=True → result=11`. Illustrative node IDs.

</div>

- Branches, loops, subgraphs, maps share one graph process.
- Separate task processes; hierarchical call labels (`branch_1__add`).
- Task creates (`CREATE`); graph returns (`RETURN`) the same node.

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

- Subgraphs share the graph process.
- Conditional expressions evaluate only the selected side.

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

- `(value, error)`: exactly one is present.
- Declared error: nonzero task status, available to the graph.
- Other failures: graph exits with `ERROR_TASK_FAILED`.

---
layout: two-cols-header
layoutClass: dense
---

# Retrying a declared failure

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

- `UNSTABLE`: retry within budget.
- `max_retries`: repeats after the initial call.
- Loop iterations run sequentially.
- Counter: inline. All attempts failed: `ensure` fails the graph.

---
layout: section
---

# Data flow

---
layout: two-cols-header
layoutClass: dense
---

# Parallel map and reduction

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

- `par_map`: one call per item, all submitted before waiting.
- Collector stores results in input order.
- `for` loops: task bodies only.

---

# Inline collections

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

- `list[T]` and `dict[str, T]` declare element types.
- Inline expressions run in the graph process; values are checkpointed.
- `sum_values` stores the scientific result.

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

- Placement: one call site; repeated calls need unique aliases.
- `partial`: shared input bindings; no import.

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

- Fields become input nodes: `Float(1.05)`, `Str('demo')`.
- Empty `scaling` uses defaults; result: `11.57625`.

---
layout: two-cols-header
layoutClass: dense
---

# Pydantic models as port namespaces

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

- Nested ports, defaults, help text.
- Fields: `str`, `int`, `float`, `bool`, optionally `None`.
- Task inputs: attribute-accessible mappings, without model methods.
- Validators and aliases rejected; value checks belong in tasks.

---
layout: two-cols-header
layoutClass: dense
---

# CalcJob and WorkChain tasks

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

::bottom::

- `task(...)`: existing CalcJobs and WorkChains, unchanged.
- Graph returns the CalcJob's existing `sum` node.
- `runtime_config`: `code`, `metadata`.

---
layout: section
---

# Koopmans case study

---

# Koopmans case study

- One `Wannier90WorkChain` per block, then merge Hamiltonians.
- Shared structure, k-point grid, band k-points.
- WorkGraph `for` → `par_map`.
- Feedback: shared inputs (`partial`), inline grid arithmetic.

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

- `partial`: shared inputs; `par_map`: one `block` per call.
- Shared node identities preserved.
- `DataDict`: keys and insertion order preserved.

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

- Comprehension: same graph process, checkpointed value.
- `list[T]` and `dict[str, T]`: indexing and comprehensions.

---

# Koopmans case study: open points

- Map inputs: `DataDict`, `DataList`; typed Python mappings unsupported.
- Inline `sum`, generators, `tuple` unsupported; `count_wann` stays a task.
- Positivity, grid length: runtime checks in tasks.
- Per-item metadata unsupported; `.alias(...)` names the whole map.
