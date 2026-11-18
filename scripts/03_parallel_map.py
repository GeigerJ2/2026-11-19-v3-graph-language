###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide 03: parallel map over structures, then sequential reduction.

Fan-out applies :func:`expand_cell` to each ``StructureData`` in a ``DataList``
independently via :func:`~aiida.engine.par_map`; fan-in averages the expanded
cell volumes in the single :func:`mean_cell_volume` task. A ``for`` loop is
supported inside ``@task`` bodies, never inside ``@graph`` bodies.

The representative run expands three empty cubic structures with lattice
parameters 2, 3 and 4 Angstrom by the documented ``SCALE_FACTOR`` and checks
the mean expanded volume against the analytically expected value.
"""

import argparse
import math
from pathlib import Path

from aiida.engine import graph, par_map, run_get_node, task
from aiida.orm import DataList, StructureData

SCALE_FACTOR = 1.05
"""Isotropic scale applied to each lattice vector; volumes grow by ``SCALE_FACTOR ** 3``."""


@task
def expand_cell(structure: StructureData) -> StructureData:
    """Return a scaled copy of ``structure``, leaving the input node untouched.

    The stored input must never be mutated, so scaling applies to an unstored
    :meth:`~aiida.orm.StructureData.clone`, not to ``structure`` itself.

    :param structure: input structure, left unmodified.
    :return: unstored copy with each lattice vector scaled by ``SCALE_FACTOR``.
    """
    scaled = structure.clone()
    scaled.set_cell([[component * SCALE_FACTOR for component in vector] for vector in structure.cell])
    return scaled


@task
def mean_cell_volume(structures: DataList) -> float:
    """Average the cell volumes of the mapped structures.

    :param structures: mapped ``StructureData`` nodes.
    :return: mean cell volume in Angstrom cubed.
    :raises ValueError: if the mapped list is empty.
    """
    if not structures:
        msg = 'empty structure list'
        raise ValueError(msg)
    total = 0.0
    for structure in structures:
        total += structure.get_cell_volume()
    return total / len(structures)


@graph
def mean_expanded_volume(structures: DataList) -> float:
    """Expand each structure in parallel, then average the expanded volumes."""
    expanded = par_map(expand_cell, structures)
    return mean_cell_volume(structures=expanded)


def _cubic_structure(lattice: float) -> StructureData:
    """Build an unstored empty cubic structure with the given lattice parameter.

    :param lattice: cubic lattice parameter in Angstrom.
    :return: unstored structure with cell volume ``lattice ** 3``.
    """
    return StructureData(cell=[[lattice, 0.0, 0.0], [0.0, lattice, 0.0], [0.0, 0.0, lattice]])


def main() -> None:
    """Run the slide workflow against a profile and render its stored provenance."""
    parser = argparse.ArgumentParser(description='Slide 03: parallel map, then sequential reduction.')
    parser.add_argument('--profile', default='graph-examples', help='AiiDA profile to load for the run.')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).resolve().parent / 'generated',
        help='Directory for the rendered provenance SVG.',
    )
    args = parser.parse_args()

    from aiida import load_profile

    load_profile(args.profile)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mean_expanded_volume.build()

    lattices = (2.0, 3.0, 4.0)
    structures = DataList([_cubic_structure(lattice) for lattice in lattices])
    expected = sum(lattice**3 for lattice in lattices) / len(lattices) * SCALE_FACTOR**3

    outputs, root = run_get_node(mean_expanded_volume, structures=structures)
    assert root.is_finished_ok
    for member, lattice in zip(structures, lattices, strict=True):
        assert math.isclose(member.get_cell_volume(), lattice**3, rel_tol=1e-12)
    result = outputs['result'].value
    assert math.isclose(result, expected, rel_tol=1e-9)

    from aiida.tools.visualization import Graph as ProvenanceGraph

    viz = ProvenanceGraph(graph_attr={'rankdir': 'LR'})
    viz.recurse_descendants(root, annotate_links='both', include_process_inputs=True)
    svg_path = viz.graphviz.render(filename='03_parallel_map', directory=str(output_dir), format='svg', cleanup=False)
    print(f'root pk={root.pk} result={result} svg={svg_path}')


if __name__ == '__main__':
    main()
