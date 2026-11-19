###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Contextual fragment from the WorkChain/graph concept table; not a standalone workflow."""

from support import multiply

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import ToContext, WorkChain


class OutlineFragment(WorkChain):
    @classmethod
    def define(cls, spec):
        # region example
        spec.outline(cls.multiply, cls.add, cls.result)

    def multiply(self):
        self.ctx.product = multiply(self.inputs.x, self.inputs.y)

    def add(self):
        future = self.submit(
            ArithmeticAddCalculation,
            x=self.ctx.product,
            y=self.inputs.z,
        )
        return ToContext(addition=future)

    # endregion example

    def result(self):
        self.out('result', self.ctx.addition.outputs.sum)
