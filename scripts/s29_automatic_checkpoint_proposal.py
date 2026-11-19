###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 29: Thoughts: checkpoint after each graph statement.

Status: current-baseline-only. See README.md for execution context.
"""

from support import record

from aiida.engine import graph


# region example
@graph
def arithmetic_inline(x: int, y: int, z: int) -> int:
    total = x + y
    # ← Checkpoint: total saved

    product = total * z
    # ← Checkpoint: product saved

    return record(value=product)
    # ← Checkpoint at task wait / resume


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=29)
