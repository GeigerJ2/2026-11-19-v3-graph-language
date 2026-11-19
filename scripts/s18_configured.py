###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 18: Structured inputs with PortModel.

Status: runnable. See README.md for execution context.
"""

from s17_port_model import Settings, scaled_volume

from aiida.engine import graph, run_get_node


# region example
@graph
def configured(volume: float, settings: Settings) -> float:
    result = scaled_volume(volume=volume, settings=settings)
    return result.volume


# endregion example


def demo():
    # region launch
    outputs, node = run_get_node(
        configured,
        volume=10.0,
        settings={'scaling': {}},
    )
    # endregion launch
    return outputs, node


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=18)
