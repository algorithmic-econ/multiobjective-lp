import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpSolver

from muoblpsolvers.utils import bindings_available, set_solved

logger = logging.getLogger(__name__)


class SingleTransferableVote(LpSolver):
    name = "SingleTransferableVote"

    def available(self) -> bool:
        return bindings_available()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs) -> int:
        from muoblpbindings import single_transferable_vote

        start_time = time.time()
        logger.info("SOLVER START")
        selected = single_transferable_vote(lp)
        logger.info("SOLVER END", extra={"time": time.time() - start_time})

        set_solved(lp, selected)
        return lp.status
