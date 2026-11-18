###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide 06: reuse existing ``CalcJob`` and ``WorkChain`` processes in a graph.

Runs the integrated ``MultiplyAddWorkChain`` -> ``ArithmeticAddCalculation``
graph with ``x=2``, ``y=3``, ``z=4`` (expected result ``14``) and renders the
stored provenance to SVG. The ``code`` execution input is supplied to
both tasks through the current ``runtime_config`` launch channel (scheduler
options only for the ``add_calc`` ``CalcJob``); the ``MultiplyAddWorkChain``
spec accepts ``code`` and ``x``/``y``/``z`` only, so it must not receive
``metadata.options``.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import graph, run_get_node, task
from aiida.orm import Code, ProcessNode
from aiida.workflows.arithmetic.multiply_add import MultiplyAddWorkChain

multiply_add = task(MultiplyAddWorkChain)
add_calc = task(ArithmeticAddCalculation)


@graph
def integrated(x: int, y: int, z: int) -> int | float:
    """Multiply ``x`` by ``y``, add ``z``, then add ``z`` once more."""
    prepared = multiply_add(x=x, y=y, z=z)
    total = add_calc(x=prepared.result, y=z)
    return total.sum


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
    parser.add_argument(
        '--code',
        default=None,
        help='Label of an existing installed code to reuse (else a demo localhost code is used).',
    )
    return parser.parse_args()


def get_or_create_demo_code(label: str | None = None) -> Code:
    """Return a localhost bash ``InstalledCode`` for the demo.

    :param label: label of an existing code to load, if given.
    :return: the existing or newly stored code.
    """
    from aiida.common.exceptions import NotExistent
    from aiida.orm import Computer, InstalledCode, load_code, load_computer

    if label is not None:
        return load_code(label=label)

    computer_label = 'graph-demo-localhost'
    try:
        computer = load_computer(label=computer_label)
    except NotExistent:
        workdir = tempfile.mkdtemp(prefix='aiida-graph-demo-')
        computer = Computer(
            label=computer_label,
            hostname='localhost',
            description='Demo localhost computer for graph language slides (slide 06).',
            transport_type='core.local',
            scheduler_type='core.direct',
            workdir=workdir,
        )
        computer.store()
        computer.configure()
    if not computer.is_configured:
        computer.configure()
    # The inner ``ArithmeticAddCalculation`` submitted by ``MultiplyAddWorkChain`` relies on its spec-default
    # resources (``num_machines=1``, ``num_mpiprocs_per_machine=1``); pin the computer default as well so the
    # scheduler never sees an incomplete resource set.
    if computer.get_default_mpiprocs_per_machine() is None:
        computer.set_default_mpiprocs_per_machine(1)

    code_label = 'graph-demo-bash'
    try:
        return load_code(label=code_label)
    except NotExistent:
        return InstalledCode(
            label=code_label,
            description='Demo bash code for graph language slides (slide 06).',
            computer=computer,
            filepath_executable='/bin/bash',
            default_calc_job_plugin='core.arithmetic.add',
        ).store()


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
    """Run the integrated graph and render its provenance."""
    from aiida import load_profile

    args = parse_args()
    load_profile(args.profile)
    code = get_or_create_demo_code(args.code)

    integrated.build()

    options = {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}, 'withmpi': False}
    runtime_config = {
        'multiply_add': {'code': code},
        'add_calc': {'code': code, 'metadata': {'options': options}},
    }
    outputs, root = run_get_node(integrated, inputs={'x': 2, 'y': 3, 'z': 4}, runtime_config=runtime_config)
    assert root.is_finished_ok
    assert outputs['result'].value == 14

    path = render_provenance(root, args.output_dir, '06_integrated')
    print(f'integrated<{root.pk}> finished: {root.is_finished_ok} result=14 path={path}')


if __name__ == '__main__':
    main()
