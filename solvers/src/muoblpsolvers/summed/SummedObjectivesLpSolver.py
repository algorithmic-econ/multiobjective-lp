from pulp import LpSolver, lpSum, PULP_CBC_CMD, GUROBI_CMD

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem


class SummedObjectivesLpSolver(LpSolver):
    """

    Info:
        Example dummy solver that sums multiple objectives.
        Parameter flag to use gurobi solver instead of default PULP one.
    """

    def __init__(self, use_gurobi: bool = False):
        super().__init__()
        self.use_gurobi = use_gurobi

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        """
        Parameters:
            lp: Instance of MultiObjectiveLpProblem
        """
        lp.setObjective(lpSum(lp.objectives))
        solver_cmd = (
            GUROBI_CMD() if self.use_gurobi else PULP_CBC_CMD(msg=False)
        )
        return solver_cmd.actualSolve(lp)
