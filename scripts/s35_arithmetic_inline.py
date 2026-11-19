###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 35: Two operations: what does provenance record?.

Status: runnable. See README.md for execution context.
"""

from support import record

from aiida.engine import graph


# region example
@graph
def arithmetic_inline(x: int, y: int, z: int) -> int:
    total = x + y
    product = total * z
    return record(value=product)


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=35)
