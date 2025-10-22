import logging
import time
from typing import TypedDict

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpSolver

from muoblpsolvers.common import (
    prepare_mes_parameters,
)
from muoblpsolvers.mes_exponential.mes_exponential import (
    equal_shares_exponential,
)

logger = logging.getLogger(__name__)


class SolverOptions(TypedDict):
    budget_init: int


class MethodOfEqualSharesExponentialSolver(LpSolver):
    def __init__(self, solver_options):
        super().__init__()
        self.solver_options: SolverOptions = solver_options

    def actualSolve(self, lp: MultiObjectiveLpProblem, **_):
        logger.info("Start solver", extra={"options": self.solver_options})

        start_time = time.time()
        (
            projects,
            costs,
            voters,
            approvals_utilities,
            total_utilities,
            total_budget,
        ) = prepare_mes_parameters(lp)

        equal_shares_exponential(
            voters,
            projects,
            costs,
            approvals_utilities,
            total_utilities,
            lp,
            self.solver_options["budget_init"],
        )

        logger.info("Finish solver", extra={"time": time.time() - start_time})
