from typing import Dict

from muoblpsolvers.mes_add1.MethodOfEqualSharesAdd1Solver import (
    MethodOfEqualSharesAdd1Solver,
)
from muoblpsolvers.mes_constrains.MethodOfEqualSharesConstrainsSolver import (
    MethodOfEqualSharesConstrainsSolver,
)
from muoblpsolvers.mes_utils.MethodOfEqualSharesUtilitySolver import (
    MethodOfEqualSharesUtilitySolver,
)
from muoblpsolvers.summed.SummedObjectivesLpSolver import (
    SummedObjectivesLpSolver,
)
from pulp import LpSolver


from helpers.runners.model import Solver


def get_solver(solver_type: Solver, solver_options: Dict | None) -> LpSolver:
    if solver_type == "SUMMING":
        return SummedObjectivesLpSolver("use-gurobi" in solver_options)
    if solver_type == "MES_UTILS":
        return MethodOfEqualSharesUtilitySolver()
    if solver_type == "MES_ADD1":
        return MethodOfEqualSharesAdd1Solver()
    if solver_type == "MES_CONSTRAINT":
        return MethodOfEqualSharesConstrainsSolver(solver_options)
    if solver_type == "MES_EXPONENTIAL":
        return MethodOfEqualSharesConstrainsSolver(solver_options)
    raise Exception("Strategy not implemented for the solver type")
