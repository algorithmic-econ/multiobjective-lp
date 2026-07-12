from typing import get_args

import pytest
from pulp import LpSolver

from helpers.runners.model import Solver
from helpers.runners.solverStrategy import get_solver


@pytest.mark.parametrize("solver_type", get_args(Solver))
def test_get_solver_with_none_options(solver_type):
    solver = get_solver(solver_type, None)
    assert isinstance(solver, LpSolver)


def test_get_solver_unknown_type_raises():
    with pytest.raises(Exception, match="Strategy not implemented"):
        get_solver("NOT_A_SOLVER", None)
