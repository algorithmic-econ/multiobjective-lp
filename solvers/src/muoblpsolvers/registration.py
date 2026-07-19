"""Register muoblpsolvers solvers into PuLP's solver registry.

PuLP 3.3.2 exposes `pulp.getSolver(name)` / `pulp.listSolvers()`, both driven by
the module-level list `pulp.apis._all_solvers` (getSolver builds
`{cls.name: cls for cls in _all_solvers}`). Registration = append our solver
classes to that list in place; `register_solvers()` is idempotent (keyed on the
class object) and runs on `import muoblpsolvers`.

Appending classes never instantiates them, so registration stays bindings-free
(binding imports are lazy, inside each solver's `actualSolve`).
"""

import logging

import pulp.apis

from muoblpsolvers.expanding_approvals import ExpandingApprovals
from muoblpsolvers.greedy_solver import GreedySolver
from muoblpsolvers.mes import (
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesExponentialSolver,
    MethodOfEqualSharesUtilitySolver,
)
from muoblpsolvers.phragmen import PhragmenSolver
from muoblpsolvers.single_transferable_vote import SingleTransferableVote
from muoblpsolvers.solid_coalition_refinement import SolidCoalitionRefinement
from muoblpsolvers.summed_objectives_lp_solver import SummedObjectivesLpSolver

logger = logging.getLogger(__name__)

SOLVERS = [
    ExpandingApprovals,
    GreedySolver,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesExponentialSolver,
    MethodOfEqualSharesUtilitySolver,
    PhragmenSolver,
    SingleTransferableVote,
    SolidCoalitionRefinement,
    SummedObjectivesLpSolver,
]


def register_solvers() -> None:
    """Append muoblpsolvers solvers to `pulp.apis._all_solvers` (idempotent)."""
    for solver in SOLVERS:
        if solver not in pulp.apis._all_solvers:
            pulp.apis._all_solvers.append(solver)
            logger.debug("Registered solver %s in PuLP", solver.name)
