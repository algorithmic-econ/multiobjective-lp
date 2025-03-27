from typing import List

import pulp
from pulp import LpProblem, LpAffineExpression, LpMaximize, LpMinimize

from muoblp.utils.lpWriterUtils import expression_to_lp_format

# Override line limit for writeLP to output single line values
pulp.const.LpCplexLPLineSize = 100000


class MultiObjectiveLpProblem(LpProblem):
    def __init__(
        self,
        name: str,
        sense: LpMaximize | LpMinimize = LpMaximize,
        objectives: List[LpAffineExpression] = None,
    ) -> None:
        super().__init__(name, sense=sense)
        self._objectives = objectives

    @property
    def objectives(self) -> List[LpAffineExpression]:
        return self._objectives

    def setObjectives(self, objectives: List[LpAffineExpression]) -> None:
        self._objectives = objectives

    # TODO: Decide how to handle fixObjective and restoreObjective

    def writeLP(self, filename, writeSOS=1, mip=1, max_length=100):
        super().writeLP(filename, writeSOS, mip, max_length)
        with open(filename, "a", encoding="utf-8") as file:
            file.write("OBJECTIVES:\n")
            for objective in self.objectives:
                file.write(expression_to_lp_format(objective))
            file.write("END_OBJECTIVES:\n")
        return

    # TODO: override __iadd__ to append objective to the list of objectives
