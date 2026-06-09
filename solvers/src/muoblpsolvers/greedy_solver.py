import logging

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal, lpSum

from muoblpsolvers.election_solver import ElectionSolver

logger = logging.getLogger(__name__)


class GreedySolver(ElectionSolver):
    name = "Greedy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        vars = [x for x in lp.variables() if x.name != "__dummy"]
        for x in vars:
            x.varValue = 0

        utility = lpSum(
            lp.objectives_weights.get(y.name, 1) * y for y in lp.objectives
        )
        weight = lpSum(y / (-y.constant) for y in lp.constraints.values())
        vars.sort(
            key=lambda x: utility.get(x, 0) / weight.get(x), reverse=True
        )

        for x in vars:
            if utility.get(x, 0) <= 0:
                break
            x.varValue = 1
            if not self.is_feasible(lp):
                x.varValue = 0

        lp.assignStatus(LpStatusOptimal)
        return lp.status
