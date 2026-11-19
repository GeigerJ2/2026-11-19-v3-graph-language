###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Slide snippet 17: Structured inputs with PortModel.

Status: shared-definitions. See README.md for execution context.
"""

# region example
from aiida.engine import PortModel, task


# region declarations
class Scaling(PortModel):
    factor: float = 1.05


class Settings(PortModel):
    scaling: Scaling
    label: str = 'demo'


class VolumeResult(PortModel):
    volume: float


@task
def scaled_volume(volume: float, settings: Settings) -> VolumeResult:
    return VolumeResult(volume=volume * settings.scaling.factor**3)


# endregion declarations
# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=17)
