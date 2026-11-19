###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: F821
# mypy: disable-error-code=name-defined
# The partial intrinsic is a slide example that this checkout currently rejects.

"""Slide snippet 16: Placement names and partial bindings.

Status: partially-supported; partial bindings are not implemented in this checkout. See README.md for execution context.
"""

from s15_placement_task import add

from aiida.engine import graph


# region example
@graph
def two_steps(x: int, y: int) -> int:
    first = add.alias('scf')(x=x, y=y)
    return add.alias('nscf')(x=first, y=y)


@graph
def add_shifted(x: int, y: int) -> int:
    add_y = partial(add, y=y)
    first = add_y.alias('first')(x=x)
    return add_y.alias('second')(x=first)


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=16)
