###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 10: Two languages, two execution boundaries.

Status: runnable. See README.md for execution context.
"""

from s09_numpy_task import summarize

from aiida.engine import graph


# region example
@graph
def analyze(values: list[float]) -> float:
    mean = summarize(values=values)
    return mean


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=10)
