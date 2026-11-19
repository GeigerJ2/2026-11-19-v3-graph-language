###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 27: Branch results: Python binding vs. graph interpretation.

Status: runnable. See README.md for execution context.
"""

from support import add, multiply

from aiida.engine import graph


@graph
def selected_branch(first_sum: int) -> int:

    # region example
    # Inside an @graph function:
    if first_sum < 0:
        result = add(x=first_sum, y=2)
    else:
        result = multiply(x=first_sum, y=3)

    final_sum = add(x=result, y=1)
    # endregion example
    return final_sum


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=27)
