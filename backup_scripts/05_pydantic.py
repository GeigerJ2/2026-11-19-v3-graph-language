###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide 05: reuse a pydantic schema as a typed port namespace.

Declares equivalent ``PydanticScaling``/``PydanticSettings`` models with defaults and
``Field(description=...)`` help text, adapts them to port namespaces for
:func:`scaled_volume_pydantic` and the ``configured_pydantic`` graph, runs ``volume=10.0`` with
``settings={'scaling': {}}`` so defaults fill the nested fields (``11.57625``), and renders the
stored provenance to ``generated/05_pydantic.svg``.
"""

import argparse
import math
from pathlib import Path

from pydantic import BaseModel, Field

from aiida.engine import graph, run_get_node, task
from aiida.tools.visualization import Graph as ProvenanceGraph


class PydanticScaling(BaseModel):
    """Cell scaling options."""

    factor: float = Field(default=1.05, description='Cell scale factor.')


class PydanticSettings(BaseModel):
    """Top-level settings namespace carrying scaling options and a label."""

    scaling: PydanticScaling
    label: str = 'demo'


@task
def scaled_volume_pydantic(volume: float, settings: PydanticSettings) -> float:
    """Scale ``volume`` by the cubed scaling factor.

    :param volume: the unscaled cell volume.
    :param settings: attribute-accessible namespace mapping (not a ``BaseModel`` instance).
    :return: the scaled volume.
    """
    return volume * settings.scaling.factor**3


@graph
def configured_pydantic(volume: float, settings: PydanticSettings) -> float:
    """Wire the whole ``settings`` namespace into :func:`scaled_volume_pydantic`."""
    return scaled_volume_pydantic(volume=volume, settings=settings)


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
    """Validate, run, check, and render the ``configured_pydantic`` graph."""
    args = _parse_args()
    from aiida import load_profile

    load_profile(args.profile)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    configured_pydantic.build()

    outputs, root = run_get_node(configured_pydantic, volume=10.0, settings={'scaling': {}})
    assert root.is_finished_ok
    assert math.isclose(outputs['result'].value, 11.57625)
    assert math.isclose(root.inputs.volume.value, 10.0)
    assert math.isclose(root.inputs.settings.scaling.factor.value, 1.05)
    assert root.inputs.settings.label.value == 'demo'

    viz = ProvenanceGraph(graph_attr={'rankdir': 'LR'})
    viz.recurse_descendants(root, annotate_links='both', include_process_inputs=True)
    svg_path = viz.graphviz.render(filename='05_pydantic', directory=str(output_dir), format='svg', cleanup=False)
    print(f'root pk={root.pk} result={outputs["result"].value} svg={svg_path}')


if __name__ == '__main__':
    main()
