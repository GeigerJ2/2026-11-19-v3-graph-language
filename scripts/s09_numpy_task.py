###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 09: Two languages, two execution boundaries.

Status: runnable. See README.md for execution context.
"""

from aiida.engine import task


# region example
@task
def summarize(values: list[float]) -> float:
    import numpy as np

    array = np.asarray(values)
    filtered = array[np.isfinite(array)]
    return float(np.mean(filtered))


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=9)
