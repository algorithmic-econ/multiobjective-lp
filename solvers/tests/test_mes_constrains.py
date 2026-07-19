from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal

from muoblpsolvers import MethodOfEqualSharesConstrainsSolver


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_D", "_E"]),
        ("COST", ["_B", "_D", "_F"]),
    ],
)
def test_mes_constrains_solver(
    basic_pb_factory: Callable[[str], MultiObjectiveLpProblem],
    utility_type: str,
    expected: list[str],
):
    solver = MethodOfEqualSharesConstrainsSolver(msg=False)
    if not solver.available():
        pytest.skip("muoblpbindings not installed")
    problem = basic_pb_factory(utility_type)
    problem.solve(solver)

    assert problem.status == LpStatusOptimal
    selected = [var.name for var in problem.variables() if var.value() == 1.0]
    assert sorted(selected) == sorted(expected)
