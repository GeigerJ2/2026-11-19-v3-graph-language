---

theme: seriph
title: Graph language for aiida-core v3
transition: fade
colorSchema: light

---

<div class="flex items-center gap-10" style="height: 100%">
<div class="title-hero" style="flex: 1 1 auto">

# Graph language for aiida-core v3

**Julian Geiger, Alexander Goscinski** · MSD GM · PSI — 19 November 2026

</div>
<div style="flex: 0 0 310px">
  <img src="/logos/aiida/logo_AiiDA.png" alt="AiiDA" style="height: 48px" />
</div>
</div>

---
layout: two-cols

---

# Same multiply-add, as WorkChain and as graph

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
            cls.multiply, cls.add,
            cls.validate_result, cls.result)
        spec.output('result', valid_type=Int)
        spec.exit_code(400, 'ERROR_NEGATIVE_NUMBER',
            message='The result is a negative number.')

    def multiply(self):
        self.ctx.product = multiply(
            self.inputs.x, self.inputs.y)

    def add(self):
        future = self.submit(ArithmeticAddCalculation,
            x=self.ctx.product, y=self.inputs.z,
            code=self.inputs.code)
        return ToContext(addition=future)

    def validate_result(self):
        result = self.ctx.addition.outputs.sum
        if result.value < 0:
            return self.exit_codes.ERROR_NEGATIVE_NUMBER

    def result(self):
        self.out('result',
            self.ctx.addition.outputs.sum)
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
def multiply_add(x: int, y: int,
        z: int, code: Code) -> int:
    product = multiply(x=x, y=y)
    total = add_calc(x=product, y=z,
        code=code)
    return total.sum
```

layout: default
class: aiida-slide

---

# Less code, checked earlier

- **Less to write:** a function signature instead of `spec`, outline steps, and `ctx` bookkeeping.
- **Checked before launch:** `build()` validates wiring, types, and contracts; nothing runs, nothing is created.
- **Runs anywhere:** plain Python, defined in a script or notebook, submitted directly — no entry points, no plugin packaging.
- **Clean provenance:** inline state never becomes a node; the run is a single process with ordinary task children.

---
layout: default
class: aiida-slide

---

# Three gates: build, submit, run

**Build time.** `build()` checks syntax, wiring, and static contracts. A missing binding fails here, with the source line:

```python
@graph
def broken(value: int, flag: bool) -> int:
    if flag:
        total = add(x=x, y=1)
    return total

broken.build()
```

```text
GraphLanguageError: bad.py:9:5: __main__:bad:
  without an `else` arm the branch keeps the prior
  binding, so `total` must be assigned before the
  `if`; assign it first or add an `else` arm instead
    if flag:
    ^
```

**Submit time.** Launch fills inputs and defaults, binds `runtime_config` per placement, and rejects unknown placements or missing execution inputs — naming the placement.

**Run time.** Branch conditions are re-checked, tasks with missing outputs fail, and declared failures map to error arms. Checkpoints keep finished task nodes, scope progress, and inline values, so a restarted graph reuses work instead of resubmitting it.

---

# Where WorkChain concepts go

Each WorkChain concept has a graph counterpart. Nothing structural is decided at run time.

- `spec.input` / `spec.output` become function parameters and the return annotation, checked by `build()`.
- `spec.outline` steps become straight-line code; `if_` becomes `if`, `while_` becomes `while`.
- `submit` + `to_context` become a direct call; outputs arrive as named values.
- `self.ctx` resume state becomes carried loop state and inline values, checkpointed without stored nodes.
- `self.out(...)` becomes `return`: the graph returns existing nodes.
- `spec.exit_code` becomes `Result[..., Errors]` with `Err(...)`; declared outcomes branch and retry in the graph.

<div class="verdict" >

Existing CalcJobs and WorkChains slot in as tasks, unchanged.

</div>

---

# Control flow: orchestration and computation

One graph process schedules one selected task process.

**Ordinary Python — task body**

```python
@task
def add(x: int, y: int) -> int:
    return x + y
```

**Graph language — compiled orchestration**

```python
@graph
def choose(x: int, flag: bool) -> int:
    if flag:
        chosen = add(x=x, y=1)
    else:
        chosen = add(x=x, y=2)
    return chosen
```

A `GraphProcess` drives the graph, evaluates `flag`, and schedules the selected task. The task runs the Python body and creates the result node. Daemon execution may use different workers.

<div class="refs center">

Recorded provenance of a local run (`x=10, flag=True → result=11`): declared input names are preserved; `CREATE` and `RETURN` share one result node. Node identifiers are illustrative.

</div>

![AiiDA-generated provenance from stored nodes and links](/assets/choose-provenance.svg)

---

# Retry: handle a declared failure

Retry only the expected failure code, and stop when the retry budget is used.

```python
@graph
def restartable(x: int, max_retries: int,
                attempt: int = 0) -> int:
    value, error = run_step(x=x, attempt=attempt)
    while error is not None and attempt < max_retries:
        attempt = attempt + 1
        value, error = run_step(x=x, attempt=attempt)
    checked = ensure(value=value)
    return value
```

- `Result[int, StepErrors]` unpacks into `(value, error)`; `UNSTABLE` (410) plus remaining budget retries, `Ok(value)` finishes.
- The counter is inline state, not another child process. `ensure` fails the graph if all attempts failed.

---

# Parallel map, then sequential reduction

Expand each structure independently; average volumes after all complete.

```python
@graph
def mean_expanded_volume(
    structures: DataList,
) -> float:
    expanded = par_map(expand_cell, structures)
    return mean_cell_volume(structures=expanded)

@task
def mean_cell_volume(structures: DataList) -> float:
    if not structures:
        raise ValueError('empty structure list')
    total = 0.0
    for structure in structures:
        total += structure.get_cell_volume()
    return total / len(structures)
```

- `par_map` fans one unary task out over an owned `DataList`; a `for`-loop is supported inside `@task`, not inside `@graph`.
- All items dispatch before waiting; the result preserves order and the collector builds the container.

---

# PortModel: declare a structured interface

One schema defines nested ports, defaults and help text — for both tasks and graphs.

```python
from aiida.engine import PortModel

class Scaling(PortModel):
    factor: Annotated[float, PortField(help='Cell scale factor.')] = 1.05

class Settings(PortModel):
    scaling: Scaling
    label: str = 'demo'

@task
def scaled_volume(volume: float, settings: Settings) -> float:
    return volume * settings.scaling.factor ** 3
```

- Each field becomes its own input node; `settings={'scaling': {}}` fills the defaults (`11.57625` for volume `10.0`).

---

# Pydantic: reuse the schema, not its runtime

`BaseModel` declarations adapt to the same typed port namespaces as `PortModel`.

```python
from pydantic import BaseModel, Field

class PydanticScaling(BaseModel):
    factor: float = Field(default=1.05, description='Cell scale factor.')

class PydanticSettings(BaseModel):
    scaling: PydanticScaling
    label: str = 'demo'
```

- Nested models, defaults, and `Field(description=...)` help text work; leaves accept `str`, `int`, `float`, `bool` and their optional forms.
- Tasks receive attribute-accessible mappings, not model instances. Validators and aliases are rejected at declaration; check values inside the `@task`.

---

# Reuse existing CalcJobs and WorkChains

Wrap the process class with `task(...)`, then wire its named inputs and outputs.

```python
multiply_add = task(MultiplyAddWorkChain)
add_calc = task(ArithmeticAddCalculation)

@graph
def integrated(x: int, y: int, z: int) -> int | float:
    prepared = multiply_add(x=x, y=y, z=z)
    total = add_calc(x=prepared.result, y=z)
    return total.sum

outputs, node = run_get_node(
    integrated,
    inputs={'x': 2, 'y': 3, 'z': 4},
    runtime_config={
        'add_calc': {
            'code': code,
            'metadata': {'options': options},
        },
    },
)
```

- Execution settings travel separately from scientific inputs, under `runtime_config`.
- Both stay normal child processes with provenance.

---

# WorkChain: a missing context value

A spec can be valid while a context value is missing on one execution path.

```python
class ConditionalCtxChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
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

- `flag = True`: `add_one → finish`, `result = value + 1`.
- `flag = False`: `add_one` skipped, `finish` raises `AttributeError: no attribute 'total'`. A test of only `flag=True` misses this bug.

---

# Same bug: rejected before build

Graph build checks both paths without running tasks or supplying inputs.

```python
@graph
def broken(value: int, flag: bool) -> int:
    if flag:
        total = add(x=value, y=1)
    return total

broken.build()
```

- `flag = False` leaves `total` with no binding: `GraphLanguageError: bind total before the if, or add an else arm`.
- WorkChain: the skipped path fails at runtime. Graph: invalid wiring fails during build.

<div class="verdict" >

Catch the missing binding before submission. This checks wiring, not task-body correctness; runtime tests are still needed.

</div>
