###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 04: Debugging graphs.

Status: expected-build-error. See README.md for execution context.
"""

# region example
from aiida.engine import graph, task


@task
def add(x: int, y: int) -> int:
    return x + y


@graph
def broken(value: int, flag: bool) -> int:
    if flag:
        total = add(x=value, y=1)
    return total


# endregion example


def demonstrate_build_error():
    # region build
    broken.build()
    # endregion build


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=4)
