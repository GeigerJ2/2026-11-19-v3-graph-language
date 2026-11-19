###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 20: CalcJob and WorkChain tasks.

Status: runnable. See README.md for execution context.
"""

from s19_existing_processes import integrated


def demo():

    # region example
    from aiida.engine import run_get_node
    from aiida.orm import load_code

    code = load_code('add@localhost')
    options = {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}
    outputs, node = run_get_node(
        integrated,
        inputs={'x': 2, 'y': 3, 'z': 4},
        runtime_config={
            'multiply_add': {'code': code},
            'add_calc': {
                'code': code,
                'metadata': {'options': options},
            },
        },
    )
    # endregion example
    return outputs, node


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=20)
