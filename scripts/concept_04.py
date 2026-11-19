###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Contextual fragment from the WorkChain/graph concept table; not a standalone workflow."""

from aiida.orm import Int


def declare(spec):
    # region example
    spec.input('x', valid_type=Int)
    spec.input('y', valid_type=Int)
    spec.input('z', valid_type=Int)
    spec.output('result', valid_type=Int)


# endregion example
