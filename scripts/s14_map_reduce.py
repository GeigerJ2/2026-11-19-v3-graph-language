###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 14: Map and reduce.

Status: runnable. See README.md for execution context.
"""

from s13_map_tasks import expand_cell, mean_cell_volume

from aiida.engine import graph, par_map
from aiida.orm import DataList, StructureData


# region example
@graph
def mean_expanded_volume(structures: DataList[StructureData]) -> float:
    expanded = par_map(expand_cell, structures)
    return mean_cell_volume(structures=expanded)


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=14)
