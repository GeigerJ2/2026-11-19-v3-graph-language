###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 25: Branch results: Python binding vs. graph interpretation.

Status: workgraph-reference. See README.md for execution context.
"""


def comparison(If, add, multiply, wg, first_sum):  # noqa: N803 - WorkGraph names its context manager If.

    # region example
    with If(first_sum < 0):
        result = add(x=first_sum, y=2).result

    with If(first_sum >= 0):
        result = multiply(x=first_sum, y=3).result

    final_sum = add(x=result, y=1).result
    # endregion example
    return final_sum


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=25)
