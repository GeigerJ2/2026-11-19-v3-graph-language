###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Run the interpreter comparison, verify links, and render real provenance."""

import argparse
from pathlib import Path

from render_provenance import render

from aiida import load_profile
from aiida.common.links import LinkType
from aiida.engine import graph, run_get_node, task
from aiida.tools.visualization import Graph


@task
def choose_task(x: int, y: int) -> int:
    """Choose arithmetic inside an ordinary Python task."""
    if x < 0:
        result = x + y
    else:
        result = x * y
    return result


@task
def add(x: int, y: int) -> int:
    """Return the sum."""
    return x + y


@task
def multiply(x: int, y: int) -> int:
    """Return the product."""
    return x * y


@graph
def choose_graph(x: int, y: int) -> int:
    """Choose a task in the interpreted workflow."""
    if x < 0:
        result = add(x=x, y=y)
    else:
        result = multiply(x=x, y=y)
    return result


def main() -> None:
    """Verify both branches and render their stored provenance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='graph-examples')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent / 'generated')
    args = parser.parse_args()
    load_profile(args.profile)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    assets = Path(__file__).resolve().parents[1] / 'public' / 'assets'
    choose_graph.build()

    for x, expected, selected in [(-2, 1, 'add'), (2, 6, 'multiply')]:
        for kind, workflow in [('task', choose_task), ('graph', choose_graph)]:
            outputs, root = run_get_node(workflow, x=x, y=3)
            assert root.is_finished_ok, root.exit_message
            result = outputs if kind == 'task' else outputs['result']
            assert result.value == expected
            calls = root.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
            if kind == 'task':
                assert not root.called
                creators = root.base.links.get_outgoing(link_type=LinkType.CREATE).all()
                assert len(creators) == 1 and creators[0].node.uuid == result.uuid
            else:
                assert len(root.called) == len(calls) == 1
                child = calls[0].node
                assert child.process_label == selected, child.process_label
                assert child.is_finished_ok
                returned = root.base.links.get_outgoing(link_type=LinkType.RETURN).all()
                assert len(returned) == 1 and returned[0].node.uuid == result.uuid
                creators = result.base.links.get_incoming(link_type=LinkType.CREATE).all()
                assert len(creators) == 1 and creators[0].node.uuid == child.uuid
                assert not root.base.links.get_outgoing(link_type=LinkType.CREATE).all()
            inputs = root.base.links.get_incoming(
                link_type=LinkType.INPUT_CALC if kind == 'task' else LinkType.INPUT_WORK
            ).all()
            assert {entry.link_label for entry in inputs} == {'x', 'y'}
            viz = Graph(graph_attr={'rankdir': 'LR'})
            viz.recurse_descendants(root, annotate_links='both', include_process_inputs=True)
            stem = f'10-{kind}-{selected}'
            viz.graphviz.render(filename=stem, directory=str(args.output_dir), format='svg', cleanup=False)
            svg = render(args.output_dir / stem, assets)
            print(f'{kind}: x={x}, result={expected}, root={root.pk}, calls={len(calls)}, svg={svg}')


if __name__ == '__main__':
    main()
