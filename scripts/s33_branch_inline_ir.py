###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 33: Who interprets the `if`—and what does GraphIR see?.

Status: runnable. See README.md for execution context.
"""

from support import record

from aiida.engine import graph


# region example
@graph
def choose_graph(x: int, y: int) -> int:
    if x < 0:
        result = x + y
    else:
        result = x * y
    return record(value=result)


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=33)
