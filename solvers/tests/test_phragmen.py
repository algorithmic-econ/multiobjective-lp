from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal

from muoblpsolvers import PhragmenSolver


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_D", "_E", "_F"]),
        ("COST", ["_A", "_C", "_E", "_F"]),
    ],
)
def test_phragmen_solver(
    basic_pb_factory: Callable[[str], MultiObjectiveLpProblem],
    utility_type: str,
    expected: list[str],
):
    solver = PhragmenSolver(msg=False)
    problem = basic_pb_factory(utility_type)
    problem.solve(solver)

    assert problem.status == LpStatusOptimal
    selected = [var.name for var in problem.variables() if var.value() == 1.0]
    assert sorted(selected) == sorted(expected)
