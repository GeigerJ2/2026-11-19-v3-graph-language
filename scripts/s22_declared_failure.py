###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 22: Declared failures.

Status: runnable. See README.md for execution context.
"""

from s21_division_task import divide, recover_zero

from aiida.engine import graph


# region example
@graph
def ratio_or_zero(numerator: float, denominator: float) -> float:
    value, error = divide(numerator=numerator, denominator=denominator)
    if error is None:
        selected = value
    else:
        selected = recover_zero(error=error)
    return selected


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=22)
