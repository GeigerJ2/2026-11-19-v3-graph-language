###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide 04: structured inputs with nested ``PortModel`` namespaces.

Declares ``Scaling``/``Settings`` with per-field defaults and help text, wires them through
:func:`scaled_volume` and the ``configured`` graph, runs ``volume=10.0`` with
``settings={'scaling': {}}`` so defaults fill the nested fields (``11.57625``), and renders the
stored provenance to ``generated/04_port_model.svg``.
"""

import argparse
import math
import typing as t
from pathlib import Path

from aiida.engine import PortField, PortModel, graph, run_get_node, task
from aiida.tools.visualization import Graph as ProvenanceGraph


class Scaling(PortModel):
    """Cell scaling options."""

    factor: t.Annotated[float, PortField(help='Cell scale factor.')] = 1.05


class Settings(PortModel):
    """Top-level settings namespace carrying scaling options and a label."""

    scaling: Scaling
    label: str = 'demo'


@task
def scaled_volume(volume: float, settings: Settings) -> float:
    """Scale ``volume`` by the cubed scaling factor.

    :param volume: the unscaled cell volume.
    :param settings: attribute-accessible namespace mapping (not a ``Settings`` instance).
    :return: the scaled volume.
    """
    return volume * settings.scaling.factor**3


@graph
def configured(volume: float, settings: Settings) -> float:
    """Wire the whole ``settings`` namespace into :func:`scaled_volume`."""
    return scaled_volume(volume=volume, settings=settings)


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    :return: the parsed arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='graph-examples', help='AiiDA profile to load.')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).resolve().parent / 'generated',
        help='Directory for the rendered provenance SVG.',
    )
    return parser.parse_args()


def main() -> None:
    """Validate, run, check, and render the ``configured`` graph."""
    args = _parse_args()
    from aiida import load_profile

    load_profile(args.profile)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    configured.build()

    outputs, root = run_get_node(configured, volume=10.0, settings={'scaling': {}})
    assert root.is_finished_ok
    assert math.isclose(outputs['result'].value, 11.57625)
    assert math.isclose(root.inputs.volume.value, 10.0)
    assert math.isclose(root.inputs.settings.scaling.factor.value, 1.05)
    assert root.inputs.settings.label.value == 'demo'

    viz = ProvenanceGraph(graph_attr={'rankdir': 'LR'})
    viz.recurse_descendants(root, annotate_links='both', include_process_inputs=True)
    svg_path = viz.graphviz.render(filename='04_port_model', directory=str(output_dir), format='svg', cleanup=False)
    print(f'root pk={root.pk} result={outputs["result"].value} svg={svg_path}')


if __name__ == '__main__':
    main()
