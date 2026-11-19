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

<<< @/scripts/s01_multiply_add_workchain.py#example python

::right::

<v-click>

<<< @/scripts/s02_multiply_add_graph.py#example python

</v-click>

<v-click>

- **Less code and less indirection**
- **Static verification**

</v-click>


---
layout: two-cols-header
layoutClass: dense
---

# Debugging WorkChains

::left::

<<< @/scripts/s03_debug_workchain.py#example python

::right::

- `flag=True`: result is `value + 1`.
- `flag=False`: `finish` raises at runtime for `ctx`:

<br>

<<< @/scripts/expected_missing_context.txt text


---
layout: two-cols-header
layoutClass: dense
---

# Debugging graphs

::left::

<<< @/scripts/s04_debug_graph.py#example python

<<< @/scripts/s04_debug_graph.py#build python

<v-click>

<<< @/scripts/expected_build_error.txt text

</v-click>

::right::

<v-click>

**Fix: bind `total` before the `if`, or add an `else` arm**

<<< @/scripts/s05_fix_prior_binding.py#example python

<<< @/scripts/s06_fix_else_binding.py#example python

- Missing binding: source line, column, suggested fixes.
- `build()`: no profile or inputs.
- Task bodies still can fail at runtime.

</v-click>

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
  <ConceptCode file="concept_01.py" region="example" highlights="[]" />
</div>

<ConceptCode file="concept_02.py" region="example" highlights="[[&quot;@calcfunction&quot;, &quot;concept-function&quot;]]" />
<div class="concept-arrow concept-function"><strong>Calculation</strong><span>⟶</span></div>
<ConceptCode file="concept_03.py" region="example" highlights="[[&quot;@task&quot;, &quot;concept-function&quot;], [&quot;x: int, y: int&quot;, &quot;concept-ports&quot;], [&quot;int&quot;, &quot;concept-ports&quot;]]" />

<ConceptCode file="concept_04.py" region="example" highlights="[[&quot;spec.input(&#x27;x&#x27;, valid_type=Int)&quot;, &quot;concept-ports&quot;], [&quot;spec.input(&#x27;y&#x27;, valid_type=Int)&quot;, &quot;concept-ports&quot;], [&quot;spec.input(&#x27;z&#x27;, valid_type=Int)&quot;, &quot;concept-ports&quot;], [&quot;spec.output(&#x27;result&#x27;, valid_type=Int)&quot;, &quot;concept-ports&quot;]]" />
<div class="concept-arrow concept-ports"><strong>Ports &amp; types</strong><span>⟶</span></div>
<ConceptCode file="concept_05.py" region="example" highlights="[[&quot;x: int, y: int, z: int&quot;, &quot;concept-ports&quot;], [&quot;int&quot;, &quot;concept-ports&quot;]]" />

<ConceptCode file="concept_06.py" region="example" highlights="[[&quot;spec.outline(cls.multiply, cls.add, cls.result)&quot;, &quot;concept-task&quot;], [&quot;self.ctx.product&quot;, &quot;concept-state&quot;], [&quot;multiply(&quot;, &quot;concept-function&quot;], [&quot;self.inputs.x, self.inputs.y)&quot;, &quot;concept-function&quot;], [&quot;self.submit(&quot;, &quot;concept-task&quot;], [&quot;ArithmeticAddCalculation,&quot;, &quot;concept-task&quot;], [&quot;x=self.ctx.product,&quot;, &quot;concept-task&quot;], [&quot;y=self.inputs.z,&quot;, &quot;concept-task&quot;], [&quot;addition&quot;, &quot;concept-state&quot;]]" />
<div class="concept-arrow concept-task"><strong>Steps &amp; submit</strong><span>⟶</span><strong class="concept-state">Context → values</strong></div>
<ConceptCode file="concept_07.py" region="example" highlights="[[&quot;product&quot;, &quot;concept-state&quot;], [&quot;multiply(x=x, y=y)&quot;, &quot;concept-function&quot;], [&quot;addition&quot;, &quot;concept-state&quot;], [&quot;add_calc(x=product, y=z)&quot;, &quot;concept-task&quot;]]" />

<ConceptCode file="concept_08.py" region="example" highlights="[[&quot;self.out(&#x27;result&#x27;,&quot;, &quot;concept-return&quot;], [&quot;addition&quot;, &quot;concept-state&quot;], [&quot;)&quot;, &quot;concept-return&quot;]]" />
<div class="concept-arrow concept-return"><strong>Outputs</strong><span>⟶</span></div>
<ConceptCode file="concept_09.py" region="example" highlights="[[&quot;return&quot;, &quot;concept-return&quot;], [&quot;addition&quot;, &quot;concept-state&quot;]]" />
</div>


---

# Python executes task bodies and AiiDA executes graphs

<div class="grid grid-cols-2 gap-8 interpreter-comparison">
<div>

<div class="arithmetic-highlight execution-python">
<h3><img src="/logos/python.svg" alt="Python logo" /> Task · Python interpreter</h3>

<<< @/scripts/s07_task_interpreter.py#example python

</div>

<img src="/assets/12-multiply-add-task-ir.svg" alt="GraphIR contains only an opaque multiply_add_task placement, with x, y, z inputs and a result output." />

<!--
**`ProcessTask(multiply_add_task)`** · Python executes the whole body. The arithmetic and local `product` are opaque to GraphIR.
-->
</div>
<div>

<div class="arithmetic-highlight execution-aiida">
<h3><img src="/logos/aiida/logo_AiiDA.png" alt="AiiDA logo" /> Inline graph · AiiDA graph process</h3>

<<< @/scripts/s08_inline_interpreter.py#example python

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

<<< @/scripts/s09_numpy_task.py#example python

</div>
<div class="execution-logo">
<img src="/logos/python.svg" alt="Python logo" />
<strong>Python interpreter</strong>
<span>Arbitrary Python</span>
</div>
</div>
<div class="execution-panel execution-aiida">
<div>

<<< @/scripts/s10_numpy_graph.py#example python

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

# Checkpointing and Provenance

<div class="grid grid-cols-2 gap-8 checkpoint-provenance">
<div>

### Task calls

<<< @/scripts/s11_task_checkpoints.py#example python


</div>
<div>

### Inline operations

<<< @/scripts/s12_inline_checkpoints.py#example python

```python
@graph
def count(n: int) -> int:
    i = 0
    while i < n:
        i = i + 1
    doubled = i * 2
    return record(value=doubled)  # checkpoint
```
</div>
</div>

<div class="mt-6">

- Provenance is stored at task boundaries.
- Checkpoints are written on graph process state changes.
- (De)coupling of checkpointing and provenance TBD (see later slide)

</div>

<style>
.checkpoint-provenance {
  --slidev-code-font-size: 11px;
  --slidev-code-line-height: 15px;
}
.checkpoint-provenance h3 { margin: 0.4rem 0; }
</style>

<!--
multiply, add, and record are @task functions; record returns its argument as a stored
node, because a root graph cannot return a new inline value.
The graph checkpoints on every process state change: entering waiting after a step
submits tasks, and again on resume.
Inline values live in the scope state (GraphRun.scopes[...]['values']) and are
serialized into that checkpoint.
A restart skips inline operations that already have a value.
Provenance records task calls and their data nodes; inline values are checkpointed, not stored.
Checkpointing does not preserve an instruction pointer inside a task body.
-->

---
layout: section
---

# Writing workflows

---
layout: two-cols-header
layoutClass: dense map-reduce-layout
---

# Map and reduce

::left::

<div class="map-reduce-code map-stage">
<div class="stage-label"></div>

<<< @/scripts/s13_map_tasks.py#map_excerpt python

</div>

<div class="map-reduce-code reduce-stage">
<div class="stage-label"></div>

<<< @/scripts/s13_map_tasks.py#reduce_excerpt python

</div>

<div class="map-reduce-code graph-stage">
<div class="stage-label"></div>

<ConceptCode file="s14_map_reduce.py" region="example" highlight-line="expanded = par_map(expand_cell, structures)" highlights='[["structures", "collection-token"], ["expanded", "collection-token"]]' />

</div>

::right::

<div class="map-reduce-diagram graph-stage">
<div class="stage-label">mean_expanded_volume</div>
<svg viewBox="0 0 340 365" role="img" aria-label="A DataList fans out to three independent expand_cell tasks in teal. Their outputs are collected into a DataList, then reduced by mean_cell_volume in purple. The blue frame represents graph orchestration.">
  <defs>
    <marker id="map-reduce-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
    </marker>
  </defs>
  <g fill="none" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#map-reduce-arrow)">
    <path d="M170 48 V70 H59 V104" />
    <path d="M170 48 V104" />
    <path d="M170 48 V70 H281 V104" />
    <path d="M59 150 V180 H145 V204" />
    <path d="M170 150 V204" />
    <path d="M281 150 V180 H195 V204" />
    <path d="M170 246 V290" />
  </g>
  <g font-family="Arial, sans-serif" text-anchor="middle">
    <rect x="110" y="8" width="120" height="40" rx="8" fill="#fff7d6" stroke="#d97706" />
    <text x="170" y="33" fill="#b45309" font-size="7">DataList</text>
    <text x="170" y="94" fill="#0f766e" font-size="6.5" font-weight="600"></text>
    <g fill="#e6f7f2" stroke="#0f766e">
      <rect x="10" y="110" width="98" height="40" rx="8" />
      <rect x="121" y="110" width="98" height="40" rx="8" />
      <rect x="232" y="110" width="98" height="40" rx="8" />
    </g>
    <g fill="#0f766e" font-size="6.5" font-weight="500" font-family="ui-monospace, monospace">
      <text x="59" y="135">expand_cell</text>
      <text x="170" y="135">expand_cell</text>
      <text x="281" y="135">expand_cell</text>
    </g>
    <rect x="110" y="204" width="120" height="42" rx="8" fill="#fff7d6" stroke="#d97706" />
    <text x="170" y="230" fill="#b45309" font-size="7">DataList</text>
    <text x="170" y="273" fill="#6d28d9" font-size="6.5" font-weight="600"></text>
    <rect x="78" y="290" width="184" height="44" rx="8" fill="#f3edff" stroke="#8b5cf6" />
    <text x="170" y="317" fill="#6d28d9" font-size="7" font-weight="500" font-family="ui-monospace, monospace">mean_cell_volume</text>
    <text x="170" y="356" fill="#64748b" font-size="6.5"></text>
  </g>
</svg>
</div>

<style>
.map-reduce-layout { grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr); }
.map-reduce-code {
  border: 1px solid;
  border-left-width: 4px;
  border-radius: 9px;
  padding: 6px 9px;
  margin-bottom: 9px;
  --slidev-code-font-size: 11px;
  --slidev-code-line-height: 14px;
}
.map-reduce-code .stage-label,
.map-reduce-diagram .stage-label { font-size: 11px; font-weight: 700; margin-bottom: 4px; }
.map-reduce-code.map-stage { background: #e6f7f2; border-color: #0f766e; }
.map-reduce-code.map-stage .stage-label { color: #0f766e; }
.map-reduce-code.reduce-stage { background: #f3edff; border-color: #8b5cf6; }
.map-reduce-code.reduce-stage .stage-label { color: #6d28d9; }
.map-reduce-code.graph-stage { background: #eff6ff; border-color: #3b82f6; }
.map-reduce-code.graph-stage .stage-label,
.map-reduce-diagram.graph-stage .stage-label { color: #1d4ed8; }
.map-reduce-code pre,
.map-reduce-code pre code { background: transparent !important; box-shadow: none !important; }
.map-reduce-code .concept-code { margin: 0; font-size: var(--slidev-code-font-size); line-height: var(--slidev-code-line-height); }
.map-reduce-diagram { margin: 12px 0 0 12px; padding: 14px; border: 1px solid #3b82f6; border-radius: 12px; background: #f8fbff; }
.map-reduce-diagram .stage-label { font-family: ui-monospace, monospace; font-size: 8px; font-weight: 500; }
.map-reduce-diagram svg { width: 100%; max-height: 365px; }
.map-reduce-diagram svg text { font-size: 12px !important; font-weight: 400 !important; }
.map-reduce-diagram .stage-label { font-size: 8px !important; }
</style>

---
layout: two-cols-header
layoutClass: dense port-model-layout
---

# Structured inputs/outputs with PortModel

::left::

<<< @/scripts/s17_port_model.py#declarations python

<<< @/scripts/s18_configured.py#example python

<<< @/scripts/s18_configured.py#launch python

::right::



<style>
.port-model-layout {
  grid-template-columns: minmax(0, 1.9fr) minmax(0, 1fr);
  --slidev-code-font-size: 11px;
  --slidev-code-line-height: 13px;
}
</style>

---
layout: two-cols-header
layoutClass: dense larger-workflow-code
---

# CalcJob and WorkChain tasks

::left::

<<< @/scripts/s19_existing_processes.py#example python

::right::

<<< @/scripts/s20_runtime_config.py#example python

::bottom::


---
layout: default
layoutClass: dense larger-workflow-code declared-failures-layout
---

# Declared failures

<div class="declared-failures-code">

<<< @/scripts/generated/declared_failures.py#example python

</div>


---
layout: default
layoutClass: dense larger-workflow-code declared-failures-layout
---

# Iterating on a declared failure

<div class="declared-failures-code">

<<< @/scripts/generated/retry_loop.py#example python

</div>

---
layout: default
layoutClass: dense placement-code-layout
---

# Placement names and partial bindings

<div class="declared-failures-code">

<<< @/scripts/generated/placements.py#example python

</div>

---
layout: section
---

# Project development

---
class: branch-binding
---

# Parsing instead of executing

**WorkGraph executes the builder in Python. The graph language interprets the control flow at run time.**

<div class="grid grid-cols-3 gap-5">
<div>

### WorkGraph: no runtime selection

<<< @/scripts/s25_workgraph_binding.py#example python

<img class="workgraph-dependency" src="/assets/workgraph-overwritten-binding.svg" alt="Only the multiplication output is wired to the final addition; the conditional addition has no connection to it." />

Both `with` bodies execute **while building**. Python overwrites `result` with the multiplication socket—even when that task will be skipped.

</div>
<div>

### WorkGraph: context + ordering

<<< @/scripts/s26_workgraph_context.py#example python

<img class="workgraph-dependency" src="/assets/workgraph-context-ordering.svg" alt="Both conditional tasks write ctx.result; solid edges carry values and dashed wait edges order the final addition after both branches resolve." />

The taken task populates context at runtime. Explicit waits prevent an early read; the untaken branch is skipped.

</div>
<div>

### Graph language: selected output

<<< @/scripts/s27_graph_binding.py#example python

The compiler creates a **branch placement with one output**. The runtime runs only the selected arm. `final_sum` depends on the branch output—not on shared context.

</div>
</div>


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

<div class="grid grid-cols-2 gap-8 statement-checkpoints">
<div>

### Explicit · choose checkpoint locations

<<< @/scripts/s28_explicit_checkpoint_proposal.py#example python

**`checkpoint()`** persists progress at explicitly chosen graph boundaries.

</div>
<div>

### Automatic · checkpoint every statement

<<< @/scripts/s29_automatic_checkpoint_proposal.py#example python

**`runtime_config={"graph_inline_persistence": True}`** persists each completed graph statement automatically.

</div>
</div>

<!--
If execution stops after saving `total`, restore it and continue with `product`—without recomputing the addition.
-->

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
backup_scripts/12_arithmetic_boundaries.py validates the existing IR, outputs, and provenance;
it does NOT verify the proposed per-statement persistence guarantee.
-->

---

# Evaluation process

### Loop 1 Porting existing plugins

<div class="workflow-eval-loop">
<div><strong>Rewrite</strong><span>qe + koopmans plugins<br/>in the graph language</span></div>
<b>→</b>
<div><strong>Identify problems</strong><span>What is missing or awkward<br/>in the rewrite?</span></div>
<b>→</b>
<div><strong>Revise</strong><span>Revise the language<br/></span></div>
</div>
<div class="workflow-eval-return">
<svg viewBox="0 0 900 40" preserveAspectRatio="none" role="img" aria-label="Revise loops back to Rewrite">
  <defs>
    <marker id="eval-porting-return" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0 0 L10 5 L0 10 Z" fill="#1d4ed8" />
    </marker>
  </defs>
  <path d="M765 0 V20 Q765 30 755 30 H145 Q135 30 135 20 V1" fill="none" stroke="#1d4ed8" stroke-width="1.6" vector-effect="non-scaling-stroke" marker-end="url(#eval-porting-return)" />
</svg>
</div>

### Loop 2 WorkGraph users try the language

<div class="workflow-eval-loop">
<div><strong>Explore</strong><span>Give the language to people that<br/> used WorkGrap and let them play</span></div>
<b>→</b>
<div><strong>Collect feedback</strong><span>Where do they get stuck?<br/>What feels unnatural?</span></div>
<b>→</b>
<div><strong>Revise</strong><span>Revise the language<br/></span></div>
</div>
<div class="workflow-eval-return">
<svg viewBox="0 0 900 40" preserveAspectRatio="none" role="img" aria-label="Revise loops back to Explore">
  <defs>
    <marker id="eval-users-return" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0 0 L10 5 L0 10 Z" fill="#1d4ed8" />
    </marker>
  </defs>
  <path d="M765 0 V20 Q765 30 755 30 H145 Q135 30 135 20 V1" fill="none" stroke="#1d4ed8" stroke-width="1.6" vector-effect="non-scaling-stroke" marker-end="url(#eval-users-return)" />
</svg>
</div>

<style>
.workflow-eval-loop { display: flex; gap: 12px; align-items: stretch; margin: 0.7rem 0 0; }
.workflow-eval-loop > div { flex: 1; padding: 0.8rem 1rem; border: 1px solid #94a3b8; border-radius: 8px; background: #f8fafc; }
.workflow-eval-loop strong { display: block; color: #1d4ed8; }
.workflow-eval-loop span { display: block; margin-top: 0.4rem; font-size: 12px; line-height: 1.5; }
.workflow-eval-loop > b { color: #64748b; align-self: center; }
.workflow-eval-return { height: 36px; margin-bottom: 0.8rem; }
.workflow-eval-return svg { display: block; width: 100%; height: 100%; overflow: visible; }
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

# Backup slides

---

# What provenance records: tasks and data—not the `if`

<div class="grid grid-cols-2 gap-8 interpreter-comparison">
<div>

### Computation inside one task

<!--
<<< @/scripts/s30_branch_task.py#example python
-->

<img src="/assets/provenance/s30_input_-2-slides.svg" alt="Stored provenance: x and y are inputs of choose_task, which creates result 1." />

One calculation **creates** the result. Its internal Python operations are not separate nodes.

</div>
<div>

### Graph calling arithmetic tasks

<!--
<<< @/scripts/s31_branch_graph.py#example python
-->

<img src="/assets/provenance/s31_input_-2-slides.svg" alt="Stored provenance: choose_graph calls add, which creates result 1; choose_graph returns that same data node." />

The selected task **creates** the result; the root workflow **returns** it. No node for the `if` or untaken task.

</div>
</div>

Actual runs: **x = −2, y = 3 → result = 1** · `scripts/run_all.py --snippet 30 31`

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

<<< @/scripts/s32_branch_task_ir.py#example python

<img src="/assets/11-task-ir.svg" alt="GraphIR sees one opaque choose_task placement between inputs and output; its Python if and arithmetic are not represented." />

**`ProcessTask(choose_task)`** · The Python `if` and arithmetic are opaque to GraphIR.

</div>
<div>

### Graph · AiiDA graph process

<<< @/scripts/s33_branch_inline_ir.py#example python

<img src="/assets/11-graph-ir.svg" alt="GraphIR contains an inline comparison, BranchControl, inline addition and multiplication arms, and a record task consuming the selected result." />

**`InlineOperation(lt)` → `BranchControl`** · Both arms contain an `InlineOperation`; the selected result feeds `ProcessTask(record)`.

</div>
</div>

Compact views of compiled **GraphIR**, not provenance. `GraphRun` inside `GraphProcess` interprets the right-hand structure.



<!--
backup_scripts/11_interpreter_ir.py compiles and validates the actual definitions without
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

<<< @/scripts/s34_arithmetic_task.py#example python

<img src="/assets/provenance/s34_arithmetic_task-slides.svg" alt="Actual provenance: x, y, z are inputs of arithmetic_task, which creates result 20." />

The task consumes **x, y, z** and creates **20**. The intermediate **5** is not a data node.

</div>
<div>

### One inline graph + output task

<<< @/scripts/s35_arithmetic_inline.py#example python

<img src="/assets/provenance/s35_arithmetic_inline-slides.svg" alt="Actual provenance: arithmetic_inline consumes x, y, z and calls record with the computed value; record creates the result that the graph returns." />

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
