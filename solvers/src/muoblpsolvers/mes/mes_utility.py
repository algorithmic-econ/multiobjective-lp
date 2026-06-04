import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpbindings import equal_shares_utils
from pulp import LpSolver

from muoblpsolvers.utils import set_solved

from .common import prepare_mes_parameters

logger = logging.getLogger(__name__)


class MethodOfEqualSharesUtilitySolver(LpSolver):

    name = "MethodOfEqualSharesUtility"

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
