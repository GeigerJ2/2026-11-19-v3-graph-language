###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 07: Python executes task bodies; AiiDA executes graphs.

Status: runnable. See README.md for execution context.
"""

from aiida.engine import task


# region example
@task
def multiply_add_task(x: int, y: int, z: int) -> int:
    product = x * y
    total = product + z
    return total


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=7)
