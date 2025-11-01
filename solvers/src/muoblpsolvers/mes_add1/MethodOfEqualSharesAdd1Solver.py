import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpbindings import equal_shares_add1
from pulp import LpSolver

from muoblpsolvers.common import (
    prepare_mes_parameters,
    set_selected_candidates,
)

logger = logging.getLogger(__name__)


class MethodOfEqualSharesAdd1Solver(LpSolver):
    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **_):
        (
            projects,
            costs,
            voters,
            approvals_utilities,
            total_utilities,
            total_budget,
        ) = prepare_mes_parameters(lp)

        start_time = time.time()
        logger.info("SOLVER START")

        selected = equal_shares_add1(
            voters,
            projects,
            costs,
            approvals_utilities,
            total_utilities,
            total_budget,
        )
        set_selected_candidates(lp, selected)

        logger.info("SOLVER END", extra={"time": time.time() - start_time})
