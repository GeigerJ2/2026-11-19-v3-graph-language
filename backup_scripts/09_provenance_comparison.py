###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Compare provenance of inline multiplication and a multiplication task."""

import argparse
from importlib import import_module
from pathlib import Path

from aiida import load_profile
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import graph, run_get_node, task
from aiida.orm import Code

add_calc = task(ArithmeticAddCalculation)

# ---


@graph
def multiply_add_0(x: int, y: int, z: int, code: Code) -> int | float:
    product = x * y
    total = add_calc(x=product, y=z, code=code)
    return total.sum


# ---


@task
def multiply(x: int, y: int) -> int:
    return x * y


@graph
def multiply_add_1(x: int, y: int, z: int, code: Code) -> int | float:
    product = multiply(x=x, y=y)
    total = add_calc(x=product, y=z, code=code)
    return total.sum


def main() -> None:
    """Run both graphs and render their stored provenance to SVG."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='graph-examples', help='AiiDA profile to load.')
    parser.add_argument('--code', help='Existing installed bash code (defaults to the demo localhost code).')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent / 'generated')
    args = parser.parse_args()

    load_profile(args.profile)
    # Reuse the local CalcJob setup and provenance renderer from the integration example.
    integration = import_module('06_existing_processes')
    code = integration.get_or_create_demo_code(args.code)
    options = {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}, 'withmpi': False}

    for workflow in (multiply_add_0, multiply_add_1):
        workflow.build()
        outputs, root = run_get_node(
            workflow,
            inputs={'x': 2, 'y': 3, 'z': 4, 'code': code},
            runtime_config={'add_calc': {'metadata': {'options': options}}},
        )
        assert root.is_finished_ok
        assert outputs['result'].value == 10
        path = integration.render_provenance(root, args.output_dir, f'09_{workflow.__name__}')
        print(f'{workflow.__name__}<{root.pk}>: result=10 svg={path}')


if __name__ == '__main__':
    main()
