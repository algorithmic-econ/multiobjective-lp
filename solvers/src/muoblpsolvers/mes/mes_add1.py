import logging
import warnings

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpSolver

from muoblpsolvers.election_solver import validate_election_program
from muoblpsolvers.utils import bindings_available, set_solved

from .common import prepare_mes_parameters

logger = logging.getLogger(__name__)


class MethodOfEqualSharesAdd1Solver(LpSolver):
    name = "MethodOfEqualSharesAdd1"

    def available(self) -> bool:
        return bindings_available()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **_):
        if self.timeLimit is not None:
            warnings.warn(
                f"{self.name} does not support timeLimit; "
                "solving without limit"
            )
        validate_election_program(lp)
        from muoblpbindings import equal_shares_add1

        (
            projects,
            costs,
            voters,
            approvals_utilities,
            total_utilities,
            total_budget,
        ) = prepare_mes_parameters(lp, msg=self.msg)

        if self.msg:
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

        if self.msg:
            logger.info("SOLVER END")

        set_solved(lp, selected)
        return lp.status
