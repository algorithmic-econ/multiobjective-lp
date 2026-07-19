from pulp import LpSolver, lpSum, PULP_CBC_CMD, GUROBI_CMD

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem


class SummedObjectivesLpSolver(LpSolver):
    """

    Info:
        Example dummy solver that sums multiple objectives.
        Parameter flag to use gurobi solver instead of default PULP one.
    """

    name = "SummedObjectives"

    def __init__(
        self,
        mip=True,
        msg=True,
        options=None,
        timeLimit=None,
        *,
        use_gurobi: bool = False,
        **kwargs,
    ):
        super().__init__(
            mip=mip,
            msg=msg,
            options=options,
            timeLimit=timeLimit,
            use_gurobi=use_gurobi,
            **kwargs,
        )

    def available(self) -> bool:
        return True

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        """
        Parameters:
            lp: Instance of MultiObjectiveLpProblem
        """
        lp.setObjective(lpSum(lp.objectives))
        solver_cmd = (
            GUROBI_CMD(msg=self.msg, timeLimit=self.timeLimit)
            if self.optionsDict["use_gurobi"]
            else PULP_CBC_CMD(msg=self.msg, timeLimit=self.timeLimit)
        )
        return solver_cmd.actualSolve(lp)
