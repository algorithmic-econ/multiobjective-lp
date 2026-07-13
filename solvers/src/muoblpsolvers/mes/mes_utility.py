import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpSolver

from muoblpsolvers.utils import bindings_available, set_solved

from .common import prepare_mes_parameters

logger = logging.getLogger(__name__)


class MethodOfEqualSharesUtilitySolver(LpSolver):
    name = "MethodOfEqualSharesUtility"

    def available(self) -> bool:
        return bindings_available()

    def actualSolve(self, lp: MultiObjectiveLpProblem):
        from muoblpbindings import equal_shares_utils

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
        selected = equal_shares_utils(
            list(voters.keys()),
            projects,
            costs,
            approvals_utilities,
            total_utilities,
            total_budget,
        )
        logger.info("SOLVER END", extra={"time": (time.time() - start_time)})

        set_solved(lp, selected)
        return lp.status
