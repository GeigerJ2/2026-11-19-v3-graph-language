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
# checkpoint() is intentionally undefined: this is an unimplemented syntax proposal.

"""Slide snippet 28: Thoughts: checkpoint after each graph statement.

Status: unimplemented-proposal. See README.md for execution context.
"""

from support import record

from aiida.engine import graph


# region example
@graph
def arithmetic_inline(x: int, y: int, z: int) -> int:
    total = x + y
    checkpoint()

    product = total * z
    checkpoint()

    return record(value=product)
    # ← Checkpoint at task wait / resume


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=28)
