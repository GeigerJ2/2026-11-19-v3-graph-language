###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 23: Iterating on a declared failure.

Status: shared-definitions. See README.md for execution context.
"""

from aiida.engine import task


# region example
@task
def require_value(value: float | None) -> float:
    if value is None:
        msg = 'No division attempt succeeded.'
        raise ValueError(msg)
    return value


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=23)
