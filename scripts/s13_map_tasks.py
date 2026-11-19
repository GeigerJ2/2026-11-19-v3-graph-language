###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 13: Map and reduce.

Status: shared-definitions. See README.md for execution context.
"""

# region example
from aiida.engine import task
from aiida.orm import DataList, StructureData


@task
def expand_cell(structure: StructureData) -> StructureData:
    scaled = structure.clone()
    scaled.set_cell([[1.05 * component for component in vector] for vector in structure.cell])
    return scaled


@task
def mean_cell_volume(structures: DataList[StructureData]) -> float:
    if not structures:
        raise ValueError('empty structure list')
    total = 0.0
    for structure in structures:
        total += structure.get_cell_volume()
    return total / len(structures)


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=13)
