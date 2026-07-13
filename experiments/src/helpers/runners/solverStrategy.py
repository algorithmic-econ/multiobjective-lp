from muoblpsolvers import (
    GreedySolver,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesExponentialSolver,
    MethodOfEqualSharesUtilitySolver,
    PhragmenSolver,
    SummedObjectivesLpSolver,
)
from pulp import LpSolver

from helpers.runners.model import Solver

SOLVERS: dict[Solver, type[LpSolver]] = {
    "SUMMING": SummedObjectivesLpSolver,
    "MES_UTILS": MethodOfEqualSharesUtilitySolver,
    "MES_ADD1": MethodOfEqualSharesAdd1Solver,
    "MES_CONSTRAINT": MethodOfEqualSharesConstrainsSolver,
    "MES_EXPONENTIAL": MethodOfEqualSharesExponentialSolver,
    "PHRAGMEN": PhragmenSolver,
    "GREEDY": GreedySolver,
}


def get_solver(solver_type: Solver, solver_options: dict | None) -> LpSolver:
    if solver_type not in SOLVERS:
        raise Exception("Strategy not implemented for the solver type")
    # options are keyword args of the solver constructor (pulp optionsDict)
    return SOLVERS[solver_type](**(solver_options or {}))
