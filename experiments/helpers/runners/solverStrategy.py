
from pulp import LpSolver

from ..runners.model import Solvers
from .solvers.SummedObjectivesLpSolver import SummedObjectivesLpSolver


def get_solver(solver_type: Solvers) -> LpSolver:
    if solver_type == Solvers.SUMMING:
        return SummedObjectivesLpSolver()
    raise Exception("Strategy not implemented for the solver type")
