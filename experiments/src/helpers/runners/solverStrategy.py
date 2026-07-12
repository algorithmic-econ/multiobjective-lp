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


def get_solver(solver_type: Solver, solver_options: dict | None) -> LpSolver:
    solver_options = solver_options or {}
    if solver_type == "SUMMING":
        return SummedObjectivesLpSolver("use-gurobi" in solver_options)
    if solver_type == "MES_UTILS":
        return MethodOfEqualSharesUtilitySolver()
    if solver_type == "MES_ADD1":
        return MethodOfEqualSharesAdd1Solver()
    if solver_type == "MES_CONSTRAINT":
        return MethodOfEqualSharesConstrainsSolver(solver_options)
    if solver_type == "MES_EXPONENTIAL":
        return MethodOfEqualSharesExponentialSolver(solver_options)
    if solver_type == "PHRAGMEN":
        return PhragmenSolver(solver_options)
    if solver_type == "GREEDY":
        return GreedySolver()

    raise Exception("Strategy not implemented for the solver type")
