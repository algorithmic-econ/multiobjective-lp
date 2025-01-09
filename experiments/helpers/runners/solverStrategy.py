from pulp import LpSolver

from .solvers.MethodOfEqualSharesSolver import MethodOfEqualSharesSolver
from .solvers.MethodOfEqualSharesAdd1Solver import MethodOfEqualSharesAdd1Solver
from ..runners.model import Solver
from .solvers.SummedObjectivesLpSolver import SummedObjectivesLpSolver


def get_solver(solver_type: Solver) -> LpSolver:
    if solver_type == 'SUMMING':
        return SummedObjectivesLpSolver()
    if solver_type == 'MES':
        return MethodOfEqualSharesSolver()
    if solver_type == 'MES_ADD1':
        return MethodOfEqualSharesAdd1Solver()
    raise Exception("Strategy not implemented for the solver type")
