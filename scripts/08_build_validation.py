###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide 08: the same missing-binding bug fails at build time in a graph.

``broken`` binds ``total`` on only one branch, so ``broken.build()`` raises
before any process runs and the broken graph leaves no provenance behind. The
fixed graph binds ``total`` on both branches, runs each flag value, and
renders both provenances.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from aiida.common.exceptions import GraphLanguageError
from aiida.engine import graph, run_get_node, task
from aiida.orm import ProcessNode


@task
def add(x: int, y: int) -> int:
    """Return the sum of ``x`` and ``y``."""
    return x + y


@graph
def broken(value: int, flag: bool) -> int:
    """Bind ``total`` on only one path; the ``flag=False`` path has no binding."""
    if flag:
        total = add(x=value, y=1)
    return total


@graph
def fixed(value: int, flag: bool) -> int:
    """Bind ``total`` on both paths."""
    if flag:
        total = add(x=value, y=1)
    else:
        total = add(x=value, y=2)
    return total


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    :return: the parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='graph-examples', help='AiiDA profile to load.')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).resolve().parent / 'generated',
        help='Directory for the rendered SVG provenance.',
    )
    return parser.parse_args()


def render_provenance(root: ProcessNode, output_dir: Path, stem: str) -> str:
    """Render the provenance of ``root`` to an SVG file.

    :param root: the graph process node to visualize.
    :param output_dir: directory receiving the rendered file.
    :param stem: filename stem (without extension) for the rendering.
    :return: the path of the rendered SVG file.
    """
    from aiida.tools.visualization import Graph

    output_dir.mkdir(parents=True, exist_ok=True)
    viz = Graph(graph_attr={'rankdir': 'LR'})
    viz.recurse_descendants(root, annotate_links='both', include_process_inputs=True)
    return str(viz.graphviz.render(filename=stem, directory=str(output_dir), format='svg', cleanup=False))


def main() -> None:
    """Reject the broken graph, then run and render both fixed branches."""
    from aiida import load_profile

    args = parse_args()
    load_profile(args.profile)

    try:
        broken.build()
    except GraphLanguageError as exc:
        assert 'else' in str(exc), f'unexpected build message: {exc}'
        print(f'broken.build() rejected as expected: {exc}')
    else:
        msg = 'broken.build() unexpectedly succeeded; the invalid graph must fail before any run'
        raise AssertionError(msg)
    # The broken graph never ran, so it has no provenance to render.

    fixed.build()

    outputs_true, root_true = run_get_node(fixed, value=10, flag=True)
    assert root_true.is_finished_ok
    assert outputs_true['result'].value == 11
    path_true = render_provenance(root_true, args.output_dir, '08_fixed_true')
    print(f'fixed flag=True<{root_true.pk}> finished: {root_true.is_finished_ok} result=11 path={path_true}')

    outputs_false, root_false = run_get_node(fixed, value=10, flag=False)
    assert root_false.is_finished_ok
    assert outputs_false['result'].value == 12
    path_false = render_provenance(root_false, args.output_dir, '08_fixed_false')
    print(f'fixed flag=False<{root_false.pk}> finished: {root_false.is_finished_ok} result=12 path={path_false}')


if __name__ == '__main__':
    main()
