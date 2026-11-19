###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 11: Checkpointing and Provenance.

Status: runnable. See README.md for execution context.
"""

from support import add, multiply

from aiida.engine import graph


# region example
@graph
def calculate(x: int, y: int, z: int) -> int:
    product = multiply(x=x, y=y)  # checkpoint
    total = add(x=product, y=z)  # checkpoint
    return total


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=11)
