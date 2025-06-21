# import time
from typing import TypedDict

from pulp import LpSolver
# from muoblpbindings import equal_shares_utils

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

# from muoblpsolvers.common import (
#     prepare_mes_parameters,
# )


class SolverOptions(TypedDict):
    budget_init: int


class MethodOfEqualSharesExponentialSolver(LpSolver):
    """
    Info:
        Method Of Equal Shares Exponential variant solver
    """

    def __init__(self, solver_options):
        super().__init__()
        self.solver_options = solver_options

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        print(
            f"Starting MethodOfEqualSharesExponentialSolver {self.solver_options}"
        )
        """
        Parameters:
            lp: Instance of MultiObjectiveLpProblem
        """
        # projects, costs, voters, approvals_utilities, total_utilities, total_budget = (
        #     prepare_mes_parameters(lp)
        # )
