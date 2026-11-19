###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 15: Placement names and partial bindings.

Status: shared-definitions. See README.md for execution context.
"""

# region example
from aiida.engine import task


@task
def add(x: int, y: int) -> int:
    return x + y


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=15)
