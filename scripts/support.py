###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execution context omitted from the slides: arithmetic tasks and a local code."""

import tempfile

from aiida.engine import task
from aiida.orm import Code


@task
def add(x: int, y: int) -> int:
    """Create the sum as a stored task output."""
    return x + y


@task
def multiply(x: int, y: int) -> int:
    """Create the product as a stored task output."""
    return x * y


@task
def record(value: int) -> int:
    """Materialize an inline result at an explicit task boundary."""
    return value


def ensure_code() -> Code:
    """Create or reuse the local bash code referenced as ``add@localhost``.

    The calculation work directory is retained so stored RemoteData references remain valid.

    :return: an installed code for the arithmetic addition CalcJob.
    """
    from aiida.common.exceptions import NotExistent
    from aiida.orm import Computer, InstalledCode, load_code, load_computer

    try:
        return load_code('add@localhost')
    except NotExistent:
        pass
    try:
        computer = load_computer('localhost')
    except NotExistent:
        computer = Computer(
            label='localhost',
            hostname='localhost',
            transport_type='core.local',
            scheduler_type='core.direct',
            workdir=tempfile.mkdtemp(prefix='aiida-slide-calculations-'),
        ).store()
    if not computer.is_configured:
        computer.configure()
    if computer.get_default_mpiprocs_per_machine() is None:
        computer.set_default_mpiprocs_per_machine(1)
    return InstalledCode(
        label='add',
        computer=computer,
        filepath_executable='/bin/bash',
        default_calc_job_plugin='core.arithmetic.add',
    ).store()
