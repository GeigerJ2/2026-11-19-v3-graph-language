###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Contextual fragment from the WorkChain/graph concept table; not a standalone workflow."""

from aiida.engine import graph


# region example
@graph
def multiply_add(x: int, y: int, z: int) -> int:
    # endregion example
    raise NotImplementedError('Signature fragment; see s02_multiply_add_graph.py for the full graph.')
