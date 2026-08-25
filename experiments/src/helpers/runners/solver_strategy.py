from muoblpsolvers import (
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
)
from pulp import LpSolver

from helpers.runners.model import Solver

SOLVERS: dict[Solver, type[LpSolver]] = {
    Solver.SUMMING: SummedObjectivesLpSolver,
    Solver.MES_UTILS: MethodOfEqualSharesUtilitySolver,
    Solver.MES_ADD1: MethodOfEqualSharesAdd1Solver,
    Solver.MES_CONSTRAINT: MethodOfEqualSharesConstrainsSolver,
    Solver.MES_EXPONENTIAL: MethodOfEqualSharesExponentialSolver,
    Solver.PHRAGMEN: PhragmenSolver,
    Solver.GREEDY: GreedySolver,
    Solver.STV: SingleTransferableVote,
    Solver.SOLID_COALITION_REFINEMENT: SolidCoalitionRefinement,
    Solver.EXPANDING_APPROVALS: ExpandingApprovals,
}


def get_solver(solver_type: Solver, solver_options: dict | None) -> LpSolver:
    if solver_type not in SOLVERS:
        raise Exception("Strategy not implemented for the solver type")
    # options are keyword args of the solver constructor (pulp optionsDict)
    return SOLVERS[solver_type](**(solver_options or {}))
