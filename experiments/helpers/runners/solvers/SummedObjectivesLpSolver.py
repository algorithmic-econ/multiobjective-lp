from pulp import LpSolver, LpSolverDefault, lpSum

from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem


class SummedObjectivesLpSolver(LpSolver):
    """

    Info:
        Example dummy solver that sums multiple objectives.

    """

    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        """
        Parameters:
            lp: Instance of MultiObjectiveLpProblem
        """
        lp.objective = lpSum(lp.objectives)
        return LpSolverDefault.actualSolve(lp)
