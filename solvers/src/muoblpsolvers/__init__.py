import logging

from muoblpsolvers.expanding_approvals import ExpandingApprovals
from muoblpsolvers.greedy_solver import GreedySolver
from muoblpsolvers.method_of_equal_shares_add1_solver import (
    MethodOfEqualSharesAdd1Solver,
)
from muoblpsolvers.method_of_equal_shares_constrains_solver import (
    MethodOfEqualSharesConstrainsSolver,
)
from muoblpsolvers.method_of_equal_shares_exponential_solver import (
    MethodOfEqualSharesExponentialSolver,
)
from muoblpsolvers.method_of_equal_shares_utility_solver import (
    MethodOfEqualSharesUtilitySolver,
)
from muoblpsolvers.phragmen import PhragmenSolver
from muoblpsolvers.single_transferable_vote import SingleTransferableVote
from muoblpsolvers.solid_coalition_refinement import SolidCoalitionRefinement
from muoblpsolvers.summed_objectives_lp_solver import SummedObjectivesLpSolver

logger = logging.getLogger(__name__)

logger.addHandler(logging.NullHandler())
