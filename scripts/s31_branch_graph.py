###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 31: What provenance records: tasks and data—not the `if`.

Status: runnable. See README.md for execution context.
"""

from support import add, multiply

from aiida.engine import graph


# region example
@graph
def choose_graph(x: int, y: int) -> int:
    if x < 0:
        result = add(x=x, y=y)
    else:
        result = multiply(x=x, y=y)
    return result


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=31)
