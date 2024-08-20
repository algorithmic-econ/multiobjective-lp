from pulp import LpSolver, LpSolverDefault, lpSum

from src.model.multi_objective_lp import MultiObjectiveLpProblem


class SummedObjectivesLpSolver(LpSolver):
    """
    Info: SummedObjectivesLpSolver
        Example dummy solver that sums multiple objectives.
    """

    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        lp.objective = lpSum(lp.objectives)
        return LpSolverDefault.actualSolve(lp)
