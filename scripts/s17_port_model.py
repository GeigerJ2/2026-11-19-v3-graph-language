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
import typing as t

from aiida.engine import PortField, PortModel, task


class Scaling(PortModel):
    factor: t.Annotated[float, PortField(help='Cell scale factor.')] = 1.05


class Settings(PortModel):
    scaling: Scaling
    label: str = 'demo'


@task
def scaled_volume(volume: float, settings: Settings) -> float:
    return volume * settings.scaling.factor**3


# endregion example


if __name__ == '__main__':
    from run_all import main

    main(default_snippet=17)
