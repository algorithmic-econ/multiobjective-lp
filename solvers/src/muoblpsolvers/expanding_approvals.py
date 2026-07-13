import logging
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpSolver

from muoblpsolvers.election_solver import validate_election_program
from muoblpsolvers.utils import bindings_available, set_solved

logger = logging.getLogger(__name__)


class ExpandingApprovals(LpSolver):
    name = "ExpandingApprovals"

    def available(self) -> bool:
        return bindings_available()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs) -> int:
        validate_election_program(lp)
        from muoblpbindings import expanding_approvals

        start_time = time.time()
        logger.info("SOLVER START")
        selected = expanding_approvals(lp)
        logger.info("SOLVER END", extra={"time": time.time() - start_time})

        set_solved(lp, selected)
        return lp.status
