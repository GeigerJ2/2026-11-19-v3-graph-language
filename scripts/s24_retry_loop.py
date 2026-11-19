###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 24: Iterating on a declared failure.

Status: runnable. See README.md for execution context.
"""

from s21_division_task import DivisionErrors, divide
from s23_require_value import require_value

from aiida.engine import graph


# region example
@graph
def retry_ratio(numerator: float, denominator: float, max_retries: int = 3) -> float:
    attempt = 0
    value, error = divide.alias('initial')(numerator=numerator, denominator=denominator)
    while error is DivisionErrors.ZERO_DENOMINATOR and attempt < max_retries:
        denominator = denominator + 1.0
        attempt = attempt + 1
        value, error = divide.alias('retry')(numerator=numerator, denominator=denominator)
    return require_value(value=value)


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=24)
