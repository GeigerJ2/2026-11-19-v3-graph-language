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

from s21_division_task import divide

from aiida.engine import graph, task


# region example
@graph
def ratio_or_zero(numerator: float, denominator: float) -> float:
    value, error = divide(numerator=numerator, denominator=denominator)
    if error is None:
        selected = value
    else:
        selected = 0.0
    return selected


# endregion example


@task
def record_ratio(value: float) -> float:
    """Materialize the helper's inline fallback when running it as a root workflow."""
    return value


@graph
def stored_ratio_or_zero(numerator: float, denominator: float) -> float:
    """Execute the slide's helper with an explicit stored output boundary."""
    selected = ratio_or_zero(numerator=numerator, denominator=denominator)
    return record_ratio(value=selected)


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=22)
