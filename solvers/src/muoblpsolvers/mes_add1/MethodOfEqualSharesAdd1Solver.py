import time
from pulp import LpSolver

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpbindings import equal_shares_add1

from muoblpsolvers.common import (
    prepare_mes_parameters,
    set_selected_candidates,
)


class MethodOfEqualSharesAdd1Solver(LpSolver):
    """
    Info:
        Methods of Equal Shares Add1 solver
    """

    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        (
            projects,
            costs,
            voters,
            approvals_utilities,
            total_utilities,
            total_budget,
        ) = prepare_mes_parameters(lp)

        start_time = time.time()
        print(f"STARTING MES_ADD1 {start_time}")
        selected = equal_shares_add1(
            voters,
            projects,
            costs,
            approvals_utilities,
            total_utilities,
            total_budget,
        )
        print(f"FINISHED MES_ADD1 {time.time() - start_time}")

        set_selected_candidates(lp, selected)
        return
