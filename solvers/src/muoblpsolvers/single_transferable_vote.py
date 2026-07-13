import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpbindings import single_transferable_vote
from pulp import LpSolver

from muoblpsolvers.utils import set_solved

logger = logging.getLogger(__name__)


class SingleTransferableVote(LpSolver):
    name = "SingleTransferableVote"

    def available(self) -> bool:
        return True

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs) -> int:
        start_time = time.time()
        logger.info("SOLVER START")
        selected = single_transferable_vote(lp)
        logger.info("SOLVER END", extra={"time": time.time() - start_time})

        set_solved(lp, selected)
        return lp.status
