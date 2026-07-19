import logging

from muoblpsolvers.expanding_approvals import ExpandingApprovals
from muoblpsolvers.greedy_solver import GreedySolver
from muoblpsolvers.mes import (
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesExponentialSolver,
    MethodOfEqualSharesUtilitySolver,
)
from muoblpsolvers.phragmen import PhragmenSolver
from muoblpsolvers.registration import register_solvers
from muoblpsolvers.single_transferable_vote import SingleTransferableVote
from muoblpsolvers.solid_coalition_refinement import SolidCoalitionRefinement
from muoblpsolvers.summed_objectives_lp_solver import SummedObjectivesLpSolver

__all__ = [
    "ExpandingApprovals",
    "GreedySolver",
    "MethodOfEqualSharesAdd1Solver",
    "MethodOfEqualSharesConstrainsSolver",
    "MethodOfEqualSharesExponentialSolver",
    "MethodOfEqualSharesUtilitySolver",
    "PhragmenSolver",
    "SingleTransferableVote",
    "SolidCoalitionRefinement",
    "SummedObjectivesLpSolver",
    "register_solvers",
]

logger = logging.getLogger(__name__)

logger.addHandler(logging.NullHandler())

register_solvers()
