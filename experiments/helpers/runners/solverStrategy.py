from typing import Literal

from pulp import LpSolver

from experiments.helpers.runners.model import Solver
from solvers.mes.MethodOfEqualSharesSolver import MethodOfEqualSharesSolver
from solvers.mes_add1.MethodOfEqualSharesAdd1Solver import MethodOfEqualSharesAdd1Solver
from solvers.summed.SummedObjectivesLpSolver import SummedObjectivesLpSolver



def get_solver(solver_type: Solver) -> LpSolver:
    if solver_type == 'SUMMING':
        return SummedObjectivesLpSolver()
    if solver_type == 'MES':
        return MethodOfEqualSharesSolver()
    if solver_type == 'MES_ADD1':
        return MethodOfEqualSharesAdd1Solver()
    raise Exception("Strategy not implemented for the solver type")
