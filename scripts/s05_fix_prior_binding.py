###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 05: Debugging graphs.

Status: runnable. See README.md for execution context.
"""

from support import add

from aiida.engine import graph


@graph
def fixed(value: int, flag: bool) -> int:

    # region example
    total = value
    if flag:
        total = add(x=value, y=1)
    # endregion example
    return total


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=5)
