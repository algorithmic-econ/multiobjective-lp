from muoblpsolvers.greedy.GreedySolver import GreedySolver
from muoblpsolvers.mes_add1.MethodOfEqualSharesAdd1Solver import (
    MethodOfEqualSharesAdd1Solver,
)
from muoblpsolvers.mes_constrains.MethodOfEqualSharesConstrainsSolver import (
    MethodOfEqualSharesConstrainsSolver,
)
from muoblpsolvers.mes_exponential.MethodOfEqualSharesExponentialSolver import (
    MethodOfEqualSharesExponentialSolver,
)
from muoblpsolvers.mes_utils.MethodOfEqualSharesUtilitySolver import (
    MethodOfEqualSharesUtilitySolver,
)
from muoblpsolvers.phragmen.PhragmenSolver import PhragmenSolver
from muoblpsolvers.summed.SummedObjectivesLpSolver import (
    SummedObjectivesLpSolver,
)
from pulp import LpSolver

from helpers.runners.model import Solver


def get_solver(solver_type: Solver, solver_options: dict | None) -> LpSolver:
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
