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


@pytest.mark.parametrize(
    "solver_type, options",
    [
        ("MES_CONSTRAINT", {"max_iterations": 5}),
        ("MES_EXPONENTIAL", {"budget_init": 100}),
        ("PHRAGMEN", {"kappa": 2.0}),
        ("SUMMING", {"use_gurobi": True}),
    ],
)
def test_get_solver_passes_options_to_options_dict(solver_type, options):
    solver = get_solver(solver_type, options)
    for key, value in options.items():
        assert solver.optionsDict[key] == value


def test_get_solver_pulp_native_kwargs():
    solver = get_solver("GREEDY", {"msg": False, "timeLimit": 10})
    assert solver.msg is False
    assert solver.timeLimit == 10
