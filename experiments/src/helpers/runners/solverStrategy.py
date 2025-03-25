from typing import List

from pulp import LpSolver
from solvers.mes.MethodOfEqualSharesSolver import MethodOfEqualSharesSolver
from solvers.mes_add1.MethodOfEqualSharesAdd1Solver import MethodOfEqualSharesAdd1Solver
from solvers.mes_constrains.MethodOfEqualSharesConstrainsSolver import (
    MethodOfEqualSharesConstrainsSolver,
)
from solvers.summed.SummedObjectivesLpSolver import SummedObjectivesLpSolver

from src.helpers.runners.model import Solver


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
