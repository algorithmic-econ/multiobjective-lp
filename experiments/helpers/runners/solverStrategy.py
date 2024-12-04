from pulp import LpSolver

from .solvers.MethodOfEqualSharesSolver import MethodOfEqualSharesSolver
from ..runners.model import Solver
from .solvers.SummedObjectivesLpSolver import SummedObjectivesLpSolver


def get_solver(solver_type: Solver) -> LpSolver:
    if solver_type == 'SUMMING':
        return SummedObjectivesLpSolver()
    if solver_type == 'MES':
        return MethodOfEqualSharesSolver()
    raise Exception("Strategy not implemented for the solver type")
