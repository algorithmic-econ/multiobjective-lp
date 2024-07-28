from pulp import LpSolver, LpSolverDefault, lpSum

from model.multi_objective_lp import MultiObjectiveLpProblem


class SummedObjectivesLpSolver(LpSolver):
    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        lp.objective = lpSum(lp.objectives)
        return LpSolverDefault.actualSolve(lp)
