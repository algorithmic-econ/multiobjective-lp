from typing import List

import pulp
from pulp import LpAffineExpression, LpMaximize, LpMinimize, LpProblem

from muoblp.utils.lpWriterUtils import expression_to_lp_format

# Override line limit for writeLP to output single line values
pulp.const.LpCplexLPLineSize = 100000


class MultiObjectiveLpProblem(LpProblem):
    def __init__(
        self,
        name: str,
        sense: LpMaximize | LpMinimize = LpMaximize,
        objectives: list[LpAffineExpression] = [],
        objectives_weights: dict[str, int] = {},
    ) -> None:
        super().__init__(name, sense=sense)
        self._objectives = objectives
        self._objectives_weights = objectives_weights
        self._objectives_voter_groups: dict[str, list[str]] = {}

    @property
    def objectives(self) -> List[LpAffineExpression]:
        return self._objectives

    def set_objectives(self, objectives: List[LpAffineExpression]) -> None:
        self._objectives = objectives

    @property
    def objectives_weights(self) -> dict[str, int]:
        return self._objectives_weights

    def set_objectives_weights(
        self, objectives_weights: dict[str, int]
    ) -> None:
        self._objectives_weights = objectives_weights

    @property
    def objectives_voter_groups(self) -> dict[str, list[str]]:
        return self._objectives_voter_groups

    def set_objectives_voter_groups(
        self, objectives_voter_groups: dict[str, list[str]]
    ) -> None:
        self._objectives_voter_groups = objectives_voter_groups

    # TODO: Decide how to handle fixObjective and restoreObjective

    def writeLP(self, filename, writeSOS=1, mip=1, max_length=100):
        super().writeLP(filename, writeSOS, mip, max_length)
        with open(filename, "a", encoding="utf-8") as file:
            file.write("OBJECTIVES:\n")
            for objective in self.objectives:
                file.write(expression_to_lp_format(objective))
            file.write("END_OBJECTIVES:\n")
            file.write("WEIGHTS:\n")
            for name, weight in self.objectives_weights.items():
                file.write(f"{name}: {weight}\n")
            file.write("END_WEIGHTS:\n")
        return

    # TODO: override __iadd__ to append objective to the list of objectives
