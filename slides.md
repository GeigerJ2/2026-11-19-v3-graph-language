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

1. Motivation (JG)
2. Concepts (JG)
3. Writing workflows (AG)
4. Project development (AG)

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

# Concepts

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

# Python executes task bodies; AiiDA executes graphs

<div class="grid grid-cols-2 gap-8 interpreter-comparison">
<div>

<div class="arithmetic-highlight execution-python">
<h3><img src="/logos/python.svg" alt="Python logo" /> Task · Python interpreter</h3>

```python
@task
def multiply_add_task(x: int, y: int, z: int) -> int:
    product = x * y
    total = product + z
    return total
```

</div>

<img src="/assets/12-multiply-add-task-ir.svg" alt="GraphIR contains only an opaque multiply_add_task placement, with x, y, z inputs and a result output." />

<!--
**`ProcessTask(multiply_add_task)`** · Python executes the whole body. The arithmetic and local `product` are opaque to GraphIR.
-->
</div>
<div>

<div class="arithmetic-highlight execution-aiida">
<h3><img src="/logos/aiida/logo_AiiDA.png" alt="AiiDA logo" /> Inline graph · AiiDA graph process</h3>

```python
@graph
def multiply_add_inline(x: int, y: int, z: int) -> int:
    product = x * y
    total = product + z
    return total
```

</div>

<img src="/assets/12-multiply-add-inline-ir.svg" alt="GraphIR contains only inline multiplication feeding inline addition, which supplies the output." />

<!--
**`InlineOperation(mul)` → `InlineOperation(add)`** · The graph runtime evaluates both operations.
-->
</div>
</div>

<!--
`GraphRun` inside `GraphProcess` interprets the workflow. Task bodies run in the Python interpreter of their child processes.
-->
<style>
.interpreter-comparison {
  --slidev-code-font-size: 11px;
  --slidev-code-line-height: 15px;
}
.interpreter-comparison h3 { font-size: 1rem; margin: 0.4rem 0; }
.interpreter-comparison img { width: 100%; height: 190px; margin-top: 0.4rem; }
.interpreter-comparison p { font-size: 12px; margin: 0.4rem 0; }
.arithmetic-highlight { padding: 10px 12px; border: 1px solid; border-radius: 12px; }
.arithmetic-highlight.execution-python { background: #fffbea; border-color: #d8cf9b; }
.arithmetic-highlight.execution-aiida { background: #eaf9f6; border-color: #86bfb5; }
.arithmetic-highlight h3 { display: flex; align-items: center; gap: 10px; }
.interpreter-comparison .arithmetic-highlight h3 img { width: 48px; height: 28px; margin: 0; object-fit: contain; }
.arithmetic-highlight .slidev-code-wrapper,
.arithmetic-highlight pre,
.arithmetic-highlight pre code { background: transparent !important; box-shadow: none !important; }
</style>

<!--
The task IR is viewed from the minimal task_boundary graph that places multiply_add_task.
The inline graph explicitly represents add and mul operations, but they do not create
child processes or provenance nodes. The right-hand function is an inline graph helper:
its scalar output can feed a parent graph. It is not a standalone root workflow returning
newly computed scalar data; a root must return stored data from a task or its inputs.
-->

---

# Two languages, two execution boundaries

<div class="execution-panels">
<div class="execution-panel execution-python">
<div>

```python
@task
def summarize(values: list[float]) -> float:
    import numpy as np
    array = np.asarray(values)
    filtered = array[np.isfinite(array)]
    return float(np.mean(filtered))
```

</div>
<div class="execution-logo">
<img src="/logos/python.svg" alt="Python logo" />
<strong>Python interpreter</strong>
<span>Arbitrary Python</span>
</div>
</div>
<div class="execution-panel execution-aiida">
<div>

```python
@graph
def analyze(values: list[float]) -> float:
    mean = summarize(values=values)
    return mean
```

</div>
<div class="execution-logo">
<img src="/logos/aiida/logo_AiiDA.png" alt="AiiDA logo" />
<strong>Graph runtime</strong>
<span>GraphProcess · GraphRun</span>
</div>
</div>
</div>

**Libraries inside tasks. Workflow statements inside graphs.**

<style>
.execution-panels {
  display: grid;
  gap: 18px;
  margin: 1.2rem 0;
  --slidev-code-font-size: 13px;
  --slidev-code-line-height: 21px;
}
.execution-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  align-items: center;
  gap: 24px;
  padding: 14px 20px;
  border-radius: 12px;
  border: 1px solid;
}
.execution-python { background: rgba(255, 212, 59, 0.10); border-color: rgba(55, 118, 171, 0.25); }
.execution-aiida { background: rgba(20, 184, 166, 0.08); border-color: rgba(15, 118, 110, 0.25); }
.execution-panel pre { background: transparent !important; box-shadow: none !important; }
.execution-logo { display: flex; flex-direction: column; align-items: center; gap: 7px; text-align: center; }
.execution-logo img { width: 100px; height: 48px; object-fit: contain; }
.execution-logo strong { font-size: 14px; }
.execution-logo span { font-size: 11px; color: #64748b; }
</style>

<!--
Task bodies are arbitrary Python; task workers need the libraries installed.
Imports, NumPy calls, array indexing, and arbitrary library objects deliberately
stay outside the graph language. They are supported inside tasks instead.
The graph is parsed/lowered to GraphIR. GraphRun interprets it inside GraphProcess.
This is an architectural boundary, not a claim that NumPy could never be interpreted.
Python logo: Devicon python-original.svg, https://github.com/devicons/devicon
(Devicon distribution under MIT; Python logo remains its owners' trademark).
-->

---

# Current: task calls checkpoint; inline operations do not

<div class="grid grid-cols-2 gap-8 statement-checkpoints">
<div>

### Separate tasks · checkpoint boundaries

```python
@graph
def calculate(x: int, y: int, z: int) -> int:
    product = multiply(x=x, y=y)
    # ← Checkpoint: wait / resume

    total = add(x=product, y=z)
    # ← Checkpoint: wait / resume

    return total
```

Each call is a **`ProcessTask`**. The workflow checkpoints at task wait / resume boundaries, retaining completed task results.

</div>
<div>

### Inline operations · no boundary between them

```python
@graph
def calculate(x: int, y: int, z: int) -> int:
    product = x * y
    # No checkpoint here

    total = product + z
    # No checkpoint here

    return record(value=total)
    # ← Checkpoint: task wait / resume
```

Each arithmetic step is an **`InlineOperation`**. Both execute in one scheduling step; only the final task call introduces a wait / resume boundary.

</div>
</div>

**Current behavior:** separate task calls provide recovery boundaries; inline arithmetic may be replayed since the last checkpoint.

<!--
Both examples are graph functions; the distinction is task placement versus inline
operations, not Python function bodies versus graph bodies.
multiply and add are declared @tasks performing multiplication and addition.
Their implementations are omitted to focus on scheduling boundaries.
The scheduler dispatches multiply, waits, then dispatches add only after its dependency
succeeds. Process-state transitions persist progress when persistence is enabled.
The arrows are conceptual wait/resume boundaries, not literal per-call checkpoint
instructions or an exactly-once guarantee around external side effects.
The inline graph evaluates mul and add in one scheduling step before dispatching record.
record(value) is a task returning its argument as stored data, required for root output.
Checkpointing does not preserve an instruction pointer inside arbitrary Python tasks.
This slide describes current behavior; the next slide describes a proposed design.
-->

---
layout: section
---

# Writing workflows

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
layout: two-cols-header
---

# Read and query the branch output

::left::

**Read the public workflow output**

```python
from aiida.engine import run_get_node
from aiida.orm import load_node

outputs, root = run_get_node(
    choose, x=10, flag=True,
)
assert outputs['result'].value == 11

# Later, in another session:
saved = load_node(root.pk)
result = saved.outputs.result
assert result.value == 11
```

The graph exposes the selected result. No need to inspect branch names or child tasks.

::right::

**Query the stored RETURN link**

```python
from aiida.orm import GraphNode, Int, QueryBuilder

query = QueryBuilder()
query.append(
    GraphNode,
    filters={'id': root.pk},
    tag='workflow',
)
query.append(
    Int,
    with_incoming='workflow',
    edge_filters={
        'type': 'return',
        'label': 'result',
    },
    project='*',
)
result, = query.one()
assert result.value == 11
```

The query follows **workflow → RETURN → result**, regardless of which branch ran.

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

# Project development

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

# Thoughts: checkpoint after each graph statement

**Two proposals · neither implemented yet**

<div class="grid grid-cols-2 gap-8 statement-checkpoints">
<div>

### Explicit · choose checkpoint locations

```python
@graph
def arithmetic_inline(x: int, y: int, z: int) -> int:
    total = x + y
    checkpoint()

    product = total * z
    checkpoint()

    return record(value=product)
    # ← Checkpoint at task wait / resume
```

**`checkpoint()`** persists progress at explicitly chosen graph boundaries.

</div>
<div>

### Automatic · checkpoint every statement

```python
@graph
def arithmetic_inline(x: int, y: int, z: int) -> int:
    total = x + y
    # ← Checkpoint: total saved

    product = total * z
    # ← Checkpoint: product saved

    return record(value=product)
    # ← Checkpoint at task wait / resume
```

**`runtime_config={"graph_inline_persistence": True}`** persists each completed graph statement automatically.

</div>
</div>

If execution stops after saving `total`, restore it and continue with `product`—without recomputing the addition.

<style>
.statement-checkpoints {
  --slidev-code-font-size: 11px;
  --slidev-code-line-height: 16px;
}
.statement-checkpoints h3 { font-size: 1rem; margin: 0.7rem 0; }
.statement-checkpoints p { font-size: 13px; }
</style>

<!--
This slide describes the intended design, NOT current runtime behavior.
graph_inline_persistence is a proposed runtime_config option; its name and API are
not implemented or finalized. Opting in would enable the inline statement boundaries
shown here; leaving it disabled would retain current wait/resume checkpointing.
An alternative proposal is a checkpoint() statement inside @graph, letting authors
choose explicit durable boundaries instead of checkpointing every inline statement.
checkpoint() would be a graph-language intrinsic handled by the graph runtime, not
an ordinary task or arbitrary Python function. This syntax is also unimplemented.
Today inline operations can execute in one scheduling step; persistence happens at
process-state transitions, not after every inline assignment. Implementing the target
requires explicit durable boundaries when advancing the interpreter's statement-level
progress, including inline values and control-flow scope state.

The proposed guarantee is a checkpoint after each completed executable graph statement,
not after every physical source line, comment, decorator, or function signature.
The checkpoint records enough information to resume at the next unfinished step.
Task calls additionally need their pending/completed identities persisted; an unfinished
call is reattached to its existing child process rather than blindly submitted again.
Wait/resume boundaries are drawn schematically around the return task call.

Task bodies remain arbitrary Python and do not acquire instruction-level recovery.
A crash before a checkpoint completes may replay work since the preceding saved state.
Checkpointing alone does not provide exactly-once guarantees for external side effects.
scripts/12_arithmetic_boundaries.py validates the existing IR, outputs, and provenance;
it does NOT verify the proposed per-statement persistence guarantee.
-->

---

# Design through workflow evaluation

### Loop 1 · We port real plugins

<div class="workflow-eval-loop">
<div><strong>1 · Rewrite</strong><span>QE + Koopmans workflows<br/>in the graph language</span></div>
<b>→</b>
<div><strong>2 · Identify problems</strong><span>What is missing or awkward<br/>in the rewrite?</span></div>
<b>→</b>
<div><strong>3 · Solve</strong><span>Choose a design change<br/>and update the rewrite</span></div>
</div>
<div class="workflow-eval-return">↶ Revisit the workflows with the revised design</div>

### Loop 2 · WorkGraph users try the language

<div class="workflow-eval-loop">
<div><strong>1 · Explore</strong><span>Give the language to WorkGraph<br/>users and let them play</span></div>
<b>→</b>
<div><strong>2 · Collect feedback</strong><span>Where do they get stuck?<br/>What feels unnatural?</span></div>
<b>→</b>
<div><strong>3 · Iterate</strong><span>Revise the language<br/>and give it back to users</span></div>
</div>
<div class="workflow-eval-return">↶ Another round of hands-on use and feedback</div>

<style>
.workflow-eval-loop { display: flex; gap: 12px; align-items: center; margin: 0.7rem 0 0.4rem; }
.workflow-eval-loop > div { flex: 1; padding: 0.8rem 1rem; border: 1px solid #94a3b8; border-radius: 8px; background: #f8fafc; }
.workflow-eval-loop strong { display: block; color: #1d4ed8; }
.workflow-eval-loop span { display: block; margin-top: 0.4rem; font-size: 12px; line-height: 1.5; }
.workflow-eval-loop > b { color: #64748b; }
.workflow-eval-return { text-align: center; color: #64748b; margin-bottom: 1.3rem; font-size: 12px; }
</style>

<!--
Two distinct three-stage evaluation loops.
First, we rewrite workflows from the QE and Koopmans plugins ourselves, identify
concrete problems in those rewrites, and decide how to solve them in the design.
Second, we give the language to people who have used WorkGraph, ask them to explore
it, collect their feedback, and iterate. This is not the same as co-authoring each
plugin rewrite with its authors.
-->

---
layout: section
---

# Appendix

---

# What provenance records: tasks and data—not the `if`

<div class="grid grid-cols-2 gap-8 interpreter-comparison">
<div>

### Computation inside one task

```python
@task
def choose_task(x: int, y: int) -> int:
    if x < 0:
        result = x + y
    else:
        result = x * y
    return result
```

<img src="/assets/10-task-add-slides.svg" alt="Stored provenance: x and y are inputs of choose_task, which creates result 1." />

One calculation **creates** the result. Its internal Python operations are not separate nodes.

</div>
<div>

### Graph calling arithmetic tasks

```python
@graph
def choose_graph(x: int, y: int) -> int:
    if x < 0:
        result = add(x=x, y=y)
    else:
        result = multiply(x=x, y=y)
    return result
```

<img src="/assets/10-graph-add-slides.svg" alt="Stored provenance: choose_graph calls add, which creates result 1; choose_graph returns that same data node." />

The selected task **creates** the result; the root workflow **returns** it. No node for the `if` or untaken task.

</div>
</div>

Actual runs: **x = −2, y = 3 → result = 1** · `scripts/10_interpreters.py`

<!--
This restores the earlier provenance comparison, with verified AiiDA-generated SVGs.
Unlike the preceding GraphIR slide, the right-hand graph deliberately calls arithmetic
TASKS rather than using inline arithmetic. That makes the selected add calculation
visible in provenance. With the preceding inline version, provenance instead contains
only the root workflow and the final record task; the inline condition and arithmetic
remain in GraphIR/runtime state, not separate provenance nodes.
The verification script checks both branch outcomes, the selected child, CREATE,
RETURN, and input links. Diagram styling preserves all actual nodes and links.
-->

---

# Who interprets the `if`—and what does GraphIR see?

<div class="grid grid-cols-2 gap-8 interpreter-comparison">
<div>

### Task · Python interpreter

```python
@task
def choose_task(x: int, y: int) -> int:
    if x < 0:
        result = x + y
    else:
        result = x * y
    return result
```

<img src="/assets/11-task-ir.svg" alt="GraphIR sees one opaque choose_task placement between inputs and output; its Python if and arithmetic are not represented." />

**`ProcessTask(choose_task)`** · The Python `if` and arithmetic are opaque to GraphIR.

</div>
<div>

### Graph · AiiDA graph process

```python
@graph
def choose_graph(x: int, y: int) -> int:
    if x < 0:
        result = x + y
    else:
        result = x * y
    return record(value=result)
```

<img src="/assets/11-graph-ir.svg" alt="GraphIR contains an inline comparison, BranchControl, inline addition and multiplication arms, and a record task consuming the selected result." />

**`InlineOperation(lt)` → `BranchControl`** · Both arms contain an `InlineOperation`; the selected result feeds `ProcessTask(record)`.

</div>
</div>

Compact views of compiled **GraphIR**, not provenance. `GraphRun` inside `GraphProcess` interprets the right-hand structure.



<!--
scripts/11_interpreter_ir.py compiles and validates the actual definitions without
running any processes. It saves complete JSON and Mermaid IR alongside compact SVG
views. Region port wiring is collapsed; the selected-result node represents the
branch output, not an additional executable placement.
The left task has no GraphIR body. Its placement is shown as seen from the minimal
task_boundary graph that calls it. Python alone interprets that task's condition.
The right graph uses inline arithmetic: the comparison and both branch operations
are InlineOperation placements. No arithmetic child process is submitted.
record(value) is a task returning value, required here to create a stored result:
a root workflow cannot return a newly computed inline scalar. It is not needed
to evaluate the branch and does not hide the branch's arithmetic.
GraphIR contains both arms statically; at runtime only one arm scope executes.
Provenance would record the root and record task, but not the inline if or arithmetic.
-->

---

# Two operations: what does provenance record?

<div class="grid grid-cols-2 gap-8 interpreter-comparison">
<div>

### One Python task

```python
@task
def arithmetic_task(x: int, y: int, z: int) -> int:
    total = x + y
    product = total * z
    return product
```

<img src="/assets/12-task-slides.svg" alt="Actual provenance: x, y, z are inputs of arithmetic_task, which creates result 20." />

The task consumes **x, y, z** and creates **20**. The intermediate **5** is not a data node.

</div>
<div>

### One inline graph + output task

```python
@graph
def arithmetic_inline(x: int, y: int, z: int) -> int:
    total = x + y
    product = total * z
    return record(value=product)
```

<img src="/assets/12-inline-slides.svg" alt="Actual provenance: arithmetic_inline consumes x, y, z and calls record with the computed value; record creates the result that the graph returns." />

The graph calls `record` and returns its output. Inline **+** and **×** are in GraphIR, not provenance.

</div>
</div>

Actual runs: **x = 2, y = 3, z = 4 → result = 20** · Original inputs remain linked to the root graph.

<!--
These are real AiiDA-generated diagrams, with all node and link labels preserved.
The inline value passed to record is materialized as an input Data node; record creates
its own output Data node. That input has no calculation creator for the inline arithmetic.
Do not mistake that materialization for provenance of add or multiply.
The script asserts output values, child counts, result creators, and workflow returns.
-->

---
layout: section
---

# Backup slides

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

# Provenance of a branch run

<img class="provenance" src="/assets/choose-provenance.svg" alt="AiiDA-generated provenance from stored nodes and links" />

<div class="caption">

Local run: `x=10, flag=True → result=11`. Illustrative node IDs.

</div>

- Branches, loops, subgraphs, maps share one graph process.
- Separate task processes; hierarchical call labels (`branch_1__add`).
- Task creates (`CREATE`); graph returns (`RETURN`) the same node.
