
from pulp import LpSolver

from ..runners.model import Solver
from .solvers.SummedObjectivesLpSolver import SummedObjectivesLpSolver


def get_solver(solver_type: Solver) -> LpSolver:
    if solver_type == 'SUMMING':
        return SummedObjectivesLpSolver()
    raise Exception("Strategy not implemented for the solver type")
