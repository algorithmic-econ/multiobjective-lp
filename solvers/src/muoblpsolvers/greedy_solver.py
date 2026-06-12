import logging

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpBinary, LpInteger, LpStatusOptimal, lpSum

from muoblpsolvers.election_solver import ElectionSolver

logger = logging.getLogger(__name__)


class GreedySolver(ElectionSolver):
    name = "Greedy"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        if self.msg:
            for expr in lp.objectives:
                for x in expr:
                    if (
                        x.cat != LpInteger or x.lowBound != 0 or x.upBound != 1
                    ) and x.cat != LpBinary:
                        print(
                            f"Warning: Variable {x.name} is not binary but treated as one"
                        )

        vars = [x for x in lp.variables() if x.name != "__dummy"]
        for x in vars:
            x.varValue = 0

        utility = lpSum(
            lp.objectives_weights.get(expr.name, 1) * expr
            for expr in lp.objectives
        )
        cost = lpSum(
            expr / (-expr.constant) for expr in lp.constraints.values()
        )

        vars.sort(key=lambda x: utility.get(x, 0) / cost.get(x), reverse=True)

        for x in vars:
            if utility.get(x, 0) <= 0:
                if self.msg:
                    print(
                        f"variable={x.name} has non-positive coeff, terminating"
                    )
                break
            x.varValue = 1
            if self.is_feasible(lp):
                if self.msg:
                    print(
                        f"electing: variable={x.name}, coeff={utility.get(x, 0)}, avg_cost={cost.get(x, 0)}"
                    )
            else:
                x.varValue = 0
                if self.msg:
                    print(
                        f"skipping: variable={x.name}, coeff={utility.get(x, 0)}, avg_cost={cost.get(x, 0)}"
                    )

        lp.assignStatus(LpStatusOptimal)
        return lp.status
