###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide 01: control flow with the ``choose`` graph.

One graph process schedules exactly one of two ``add`` task processes,
selected by the ``flag`` input. Both branches run and each provenance
diagram is rendered with the AiiDA ``Graph`` visualizer.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from aiida import load_profile
from aiida.engine import graph, run_get_node, task
from aiida.orm import ProcessNode
from aiida.tools.visualization import Graph


@task
def add(x: int, y: int) -> int:
    """Return the sum of two integers.

    :param x: the first addend.
    :param y: the second addend.
    :return: ``x + y``.
    """
    return x + y


@graph
def choose(x: int, flag: bool) -> int:
    """Return ``x + 1`` when ``flag`` holds, otherwise ``x + 2``.

    :param x: the value both arms read.
    :param flag: selects the taken arm.
    :return: the taken arm's task output.
    """
    if flag:
        chosen = add(x=x, y=1)
    else:
        chosen = add(x=x, y=2)
    return chosen


def render_provenance(root: ProcessNode, stem: str, output_dir: Path) -> Path:
    """Render the stored provenance of ``root`` to an SVG file.

    :param root: the stored graph process node to visualize.
    :param stem: the filename stem, without extension.
    :param output_dir: the directory receiving the rendered file.
    :return: the path of the rendered SVG file.
    """
    provenance = Graph(graph_attr={'rankdir': 'LR'})
    provenance.recurse_descendants(root, annotate_links='both', include_process_inputs=True)
    rendered = provenance.graphviz.render(filename=stem, directory=str(output_dir), format='svg', cleanup=False)
    return Path(rendered)


def main() -> None:
    """Validate, run, and visualize both arms of ``choose``."""
    parser = argparse.ArgumentParser(description='Run slide 01: control flow.')
    parser.add_argument('--profile', default='graph-examples', help='The AiiDA profile to load.')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).resolve().parent / 'generated',
        help='The directory receiving the rendered SVG files.',
    )
    args = parser.parse_args()

    load_profile(args.profile)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    choose.build()

    for flag, expected, stem in [
        (True, 11, '01-choose-flag-true'),
        (False, 12, '01-choose-flag-false'),
    ]:
        outputs, root = run_get_node(choose, x=10, flag=flag)
        assert root.is_finished_ok
        assert outputs['result'].value == expected
        svg = render_provenance(root, stem, args.output_dir)
        print(f'choose(x=10, flag={flag}): root pk={root.pk}, result={expected}, svg={svg}')


if __name__ == '__main__':
    main()
