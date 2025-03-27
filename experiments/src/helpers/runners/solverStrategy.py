from typing import List

from muoblpsolvers.mes.MethodOfEqualSharesSolver import MethodOfEqualSharesSolver
from muoblpsolvers.mes_add1.MethodOfEqualSharesAdd1Solver import (
    MethodOfEqualSharesAdd1Solver,
)
from muoblpsolvers.mes_constrains.MethodOfEqualSharesConstrainsSolver import (
    MethodOfEqualSharesConstrainsSolver,
)
from muoblpsolvers.summed.SummedObjectivesLpSolver import SummedObjectivesLpSolver
from pulp import LpSolver


from helpers.runners.model import Solver


def get_solver(solver_type: Solver, solver_options: List[str] | None) -> LpSolver:
    if solver_type == "SUMMING":
        return SummedObjectivesLpSolver("use-gurobi" in solver_options)
    if solver_type == "MES":
        return MethodOfEqualSharesSolver()
    if solver_type == "MES_ADD1":
        return MethodOfEqualSharesAdd1Solver()
    if solver_type == "MES_CONSTRAINT":
        return MethodOfEqualSharesConstrainsSolver()
    raise Exception("Strategy not implemented for the solver type")
