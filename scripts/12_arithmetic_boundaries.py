###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Compare arithmetic in Python, inline GraphIR, and separate workflow tasks."""

import argparse
import json
from pathlib import Path

from graphviz import Digraph
from render_provenance import render

from aiida import load_profile
from aiida.common.links import LinkType
from aiida.engine import graph, run_get_node, task
from aiida.engine.processes.graphs.ir import GraphIR, InlineOperation, ProcessTask
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.engine.processes.graphs.viz import to_mermaid
from aiida.tools.visualization import Graph


@task
def arithmetic_task(x: int, y: int, z: int) -> int:
    """Compute both operations in one Python task."""
    total = x + y
    product = total * z
    return product


@task
def record(value: int) -> int:
    """Create a stored result for the inline workflow."""
    return value


@task
def add(x: int, y: int) -> int:
    """Return the sum."""
    return x + y


@task
def multiply(x: int, y: int) -> int:
    """Return the product."""
    return x * y


@graph
def task_boundary(x: int, y: int, z: int) -> int:
    """Place the opaque Python task in GraphIR."""
    return arithmetic_task(x=x, y=y, z=z)


@graph
def arithmetic_inline(x: int, y: int, z: int) -> int:
    """Evaluate the arithmetic inside the graph process."""
    total = x + y
    product = total * z
    return record(value=product)


@graph
def arithmetic_steps(x: int, y: int, z: int) -> int:
    """Make both computations separate child processes."""
    total = add(x=x, y=y)
    product = multiply(x=total, y=z)
    return product


@task
def multiply_add_task(x: int, y: int, z: int) -> int:
    """Compute multiplication followed by addition in Python."""
    product = x * y
    total = product + z
    return total


@graph
def multiply_add_boundary(x: int, y: int, z: int) -> int:
    """Place the multiply-add task for the execution-boundary slide."""
    return multiply_add_task(x=x, y=y, z=z)


@graph
def multiply_add_inline(x: int, y: int, z: int) -> int:
    """Return inline arithmetic for a parent graph to consume, not a root launch."""
    product = x * y
    total = product + z
    return total


def draw(spec: GraphIR, target: Path) -> None:
    """Render the actual flat IR placements and data dependencies left to right."""
    dot = Digraph(graph_attr={'rankdir': 'LR', 'bgcolor': 'transparent', 'ranksep': '0.3'})
    dot.attr('node', fontname='Arial', fontsize='13', style='rounded,filled', color='#94a3b8')
    dot.attr('edge', fontname='Arial', fontsize='10', color='#64748b', arrowsize='0.6')
    for name, routes in spec.inputs.items():
        dot.node('in_' + name, name, shape='ellipse', fillcolor='#eff6ff')
        for route in routes:
            dot.edge('in_' + name, route.task, label=route.port)
    for placement in spec.tasks:
        inline = isinstance(placement, InlineOperation)
        label = f'InlineOperation({placement.operation})' if inline else f'ProcessTask\n{placement.name}'
        dot.node(
            placement.name,
            label,
            shape='box',
            fillcolor='#eaf9f6' if inline else '#fffbea',
            color='#86bfb5' if inline else '#b8bec0',
        )
    for edge in spec.dependencies:
        dot.edge(edge.source, edge.target, label=f'{edge.source_port} → {edge.target_port}')
    for name, endpoint in spec.outputs.items():
        assert not isinstance(endpoint, dict)
        dot.node('out_' + name, name, shape='ellipse', fillcolor='#eff6ff')
        dot.edge(endpoint.task if endpoint.task is not None else 'in_' + endpoint.port, 'out_' + name)
    target.write_bytes(dot.pipe(format='svg'))


def main() -> None:
    """Compile, execute, verify, and visualize the three arithmetic variants."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='graph-examples')
    args = parser.parse_args()
    load_profile(args.profile)
    generated = Path(__file__).resolve().parent / 'generated'
    assets = Path(__file__).resolve().parents[1] / 'public' / 'assets'
    generated.mkdir(parents=True, exist_ok=True)
    for name, workflow in [('task', multiply_add_boundary), ('inline', multiply_add_inline)]:
        workflow.build()
        spec = compile_graph(workflow)
        if name == 'inline':
            assert len(spec.tasks) == 2
            assert all(isinstance(placement, InlineOperation) for placement in spec.tasks)
            assert [placement.operation for placement in spec.tasks] == ['mul', 'add']
        stem = f'12-multiply-add-{name}-ir'
        (generated / f'{stem}.json').write_text(json.dumps(spec.to_dict(), indent=2) + '\n')
        (generated / f'{stem}.mmd').write_text(to_mermaid(spec))
        draw(spec, assets / f'{stem}.svg')

    for name, workflow in [('task', task_boundary), ('inline', arithmetic_inline), ('steps', arithmetic_steps)]:
        workflow.build()
        spec = compile_graph(workflow)
        kinds = [type(placement) for placement in spec.tasks]
        assert (
            kinds
            == {
                'task': [ProcessTask],
                'inline': [InlineOperation, InlineOperation, ProcessTask],
                'steps': [ProcessTask, ProcessTask],
            }[name]
        )
        if name == 'inline':
            assert [placement.operation for placement in spec.tasks[:2]] == ['add', 'mul']
        stem = f'12-{name}'
        (generated / f'{stem}-ir.json').write_text(json.dumps(spec.to_dict(), indent=2) + '\n')
        (generated / f'{stem}-ir.mmd').write_text(to_mermaid(spec))
        draw(spec, assets / f'{stem}-ir.svg')
        # The slide contrasts the standalone task with the inline root workflow.
        executable = arithmetic_task if name == 'task' else workflow
        outputs, root = run_get_node(executable, x=2, y=3, z=4)
        result = outputs if name == 'task' else outputs['result']
        assert root.is_finished_ok and result.value == 20
        children = root.called
        assert len(children) == {'task': 0, 'inline': 1, 'steps': 2}[name]
        assert [child.process_label for child in children] == {
            'task': [],
            'inline': ['record'],
            'steps': ['add', 'multiply'],
        }[name]
        creators = result.base.links.get_incoming(link_type=LinkType.CREATE).all()
        assert len(creators) == 1
        assert creators[0].node.uuid == (root if name == 'task' else children[-1]).uuid
        if name != 'task':
            returned = root.base.links.get_outgoing(link_type=LinkType.RETURN).all()
            assert len(returned) == 1 and returned[0].node.uuid == result.uuid
        viz = Graph(graph_attr={'rankdir': 'LR'})
        viz.recurse_descendants(root, annotate_links='both', include_process_inputs=True)
        viz.graphviz.render(filename=stem, directory=str(generated), format='svg', cleanup=False)
        render(generated / stem, assets)
        print(f'{name}: IR={spec.task_names}, root={root.pk}, children={len(children)}, result=20')


if __name__ == '__main__':
    main()
