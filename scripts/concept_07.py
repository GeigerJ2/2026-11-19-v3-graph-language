###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Contextual fragment from the WorkChain/graph concept table; not a standalone workflow."""

from support import multiply

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import graph, task

add_calc = task(ArithmeticAddCalculation)


@graph
def body_fragment(x: int, y: int, z: int) -> int | float:
    # region example
    product = multiply(x=x, y=y)
    addition = add_calc(x=product, y=z)
    # endregion example
    return addition.sum
