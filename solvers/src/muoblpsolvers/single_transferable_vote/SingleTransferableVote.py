import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpbindings import single_transferable_vote
from pulp import LpSolver, LpStatusOptimal

logger = logging.getLogger(__name__)


class SingleTransferableVote(LpSolver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def available(self) -> bool:
        return True

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs) -> int:
        start_time = time.time()
        logger.info("SOLVER START")
        selected = single_transferable_vote(lp)
        logger.info("SOLVER END", extra={"time": time.time() - start_time})

        vals = {
            x.name: int(x.name in selected)
            for x in lp.variables()
        }
        lp.assignStatus(LpStatusOptimal)
        lp.assignVarsVals(vals)

        return lp.status
