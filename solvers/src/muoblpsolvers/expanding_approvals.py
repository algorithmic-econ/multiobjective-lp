import logging
import warnings

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
        if self.timeLimit is not None:
            warnings.warn(
                f"{self.name} does not support timeLimit; "
                "solving without limit"
            )
        validate_election_program(lp)
        from muoblpbindings import expanding_approvals

        if self.msg:
            logger.info("SOLVER START")
        selected = expanding_approvals(lp)
        if self.msg:
            logger.info("SOLVER END")

        set_solved(lp, selected)
        return lp.status
