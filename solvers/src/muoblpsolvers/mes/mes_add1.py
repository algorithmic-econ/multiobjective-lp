import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpbindings import equal_shares_add1
from pulp import LpSolver

from muoblpsolvers.utils import set_solved

from .common import prepare_mes_parameters

logger = logging.getLogger(__name__)


class MethodOfEqualSharesAdd1Solver(LpSolver):
    name = "MethodOfEqualSharesAdd1"

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

        # TODO: weight-aware via binding update
        selected = equal_shares_add1(
            list(voters.keys()),
            projects,
            costs,
            approvals_utilities,
            total_utilities,
            total_budget,
        )

        logger.info("SOLVER END", extra={"time": time.time() - start_time})

        set_solved(lp, selected)
        return lp.status
