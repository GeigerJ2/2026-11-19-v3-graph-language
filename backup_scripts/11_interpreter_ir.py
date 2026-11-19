###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Compile and visualize the task boundary versus inline graph control flow."""

import json
from pathlib import Path

from graphviz import Digraph

from aiida.engine import graph, task
from aiida.engine.processes.graphs.ir import BranchControl, GraphIR, InlineOperation, ProcessTask
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.engine.processes.graphs.viz import to_mermaid


@task
def choose_task(x: int, y: int) -> int:
    """Perform the whole computation in Python."""
    if x < 0:
        result = x + y
    else:
        result = x * y
    return result


@task
def record(value: int) -> int:
    """Create the stored result from the inline orchestration value."""
    return value


@graph
def task_boundary(x: int, y: int) -> int:
    """Place the Python task in a graph for the IR comparison."""
    return choose_task(x=x, y=y)


@graph
def choose_graph(x: int, y: int) -> int:
    """Expose the condition and arithmetic in the workflow IR."""
    if x < 0:
        result = x + y
    else:
        result = x * y
    return record(value=result)


def draw(spec: GraphIR, target: Path) -> None:
    """Render a compact view of the compiled IR, collapsing region port wiring."""
    dot = Digraph(graph_attr={'rankdir': 'LR', 'bgcolor': 'transparent', 'ranksep': '0.2'})
    dot.attr(
        'node',
        fontname='Arial',
        fontsize='14',
        style='rounded,filled',
        fillcolor='#eff6ff',
        color='#94a3b8',
        height='0.3',
    )
    dot.attr('edge', fontname='Arial', fontsize='11', color='#64748b', arrowsize='0.6')
    dot.node('inputs', 'inputs: x, y', shape='ellipse')
    branches = [p for p in spec.tasks if isinstance(p, BranchControl)]
    if not branches:
        assert len(spec.tasks) == 1 and isinstance(spec.tasks[0], ProcessTask)
        dot.node('task', 'ProcessTask\\n' + spec.tasks[0].name, shape='box', fillcolor='#fff7ed')
        dot.edge('inputs', 'task')
        last = 'task'
    else:
        (branch,) = branches
        (comparison,) = [p for p in spec.tasks if isinstance(p, InlineOperation)]
        assert comparison.operation == 'lt'
        dot.node('test', 'InlineOperation(lt)\\nx < 0', shape='box')
        dot.node('branch', 'BranchControl', shape='diamond')
        dot.edge('inputs', 'test', label='x')
        dot.edge('test', 'branch', label='condition')
        dot.edge('inputs', 'branch', label='x, y')
        dot.node('join', 'selected result', shape='ellipse')
        for side, body, expression, operation in [
            ('true', branch.body, 'x + y', 'add'),
            ('false', branch.otherwise, 'x * y', 'mul'),
        ]:
            (arm,) = body.tasks
            assert isinstance(arm, InlineOperation) and arm.operation == operation
            dot.node(side, f'InlineOperation({operation})\\n{expression}', shape='box')
            dot.edge('branch', side, label=side)
            dot.edge(side, 'join')
        (record_task,) = [p for p in spec.tasks if isinstance(p, ProcessTask)]
        dot.node('record', 'ProcessTask\\n' + record_task.name, shape='box', fillcolor='#fff7ed')
        dot.edge('join', 'record')
        last = 'record'
    dot.node('output', 'output: result', shape='ellipse')
    dot.edge(last, 'output')
    target.write_bytes(dot.pipe(format='svg'))


def main() -> None:
    """Build, inspect, and render the actual IR without running any processes."""
    generated = Path(__file__).resolve().parent / 'generated'
    assets = Path(__file__).resolve().parents[1] / 'public' / 'assets'
    generated.mkdir(parents=True, exist_ok=True)
    for name, workflow in [('task', task_boundary), ('graph', choose_graph)]:
        workflow.build()
        spec = compile_graph(workflow)
        if name == 'task':
            assert len(spec.tasks) == 1 and isinstance(spec.tasks[0], ProcessTask)
        else:
            branches = [placement for placement in spec.tasks if isinstance(placement, BranchControl)]
            assert len(branches) == 1
            assert any(isinstance(placement, InlineOperation) for placement in spec.tasks)
            for arm in (branches[0].body, branches[0].otherwise):
                assert len(arm.tasks) == 1 and isinstance(arm.tasks[0], InlineOperation)
        stem = f'11-{name}-ir'
        (generated / f'{stem}.json').write_text(json.dumps(spec.to_dict(), indent=2) + '\n')
        (generated / f'{stem}.mmd').write_text(to_mermaid(spec))
        target = assets / f'{stem}.svg'
        draw(spec, target)
        print(f'{workflow.__name__}: {spec.task_names}, SVG={target}')


if __name__ == '__main__':
    main()
