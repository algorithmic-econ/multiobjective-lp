from pulp import LpSolver, lpSum, PULP_CBC_CMD

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
        lp.setObjective(lpSum(lp.objectives))
        return PULP_CBC_CMD(msg=False).actualSolve(lp)
