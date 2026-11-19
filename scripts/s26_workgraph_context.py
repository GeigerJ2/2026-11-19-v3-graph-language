###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 26: Branch results: Python binding vs. graph interpretation.

Status: workgraph-reference. See README.md for execution context.
"""


def comparison(If, add, multiply, wg, first_sum):  # noqa: N803 - WorkGraph names its context manager If.

    # region example
    with If(first_sum < 0):
        second_sum = add(x=first_sum, y=2).result
        wg.ctx.result = second_sum

    with If(first_sum >= 0):
        product = multiply(x=first_sum, y=3).result
        wg.ctx.result = product

    final_sum = add(x=wg.ctx.result, y=1).result
    final_sum << second_sum
    final_sum << product
    # endregion example
    return final_sum


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=26)
