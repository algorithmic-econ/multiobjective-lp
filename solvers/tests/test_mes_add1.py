from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.mes_add1.MethodOfEqualSharesAdd1Solver import (
    MethodOfEqualSharesAdd1Solver,
)
from muoblpsolvers.types import Utility


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_D", "_E", "_F"]),
        ("COST", ["_B", "_D", "_E", "_F"]),
    ],
)
def test_add1_mes_solver(
    basic_pb_factory: Callable[[Utility], MultiObjectiveLpProblem],
    utility_type: Utility,
    expected: list[str],
):
    # when
    solver = MethodOfEqualSharesAdd1Solver()
    problem = basic_pb_factory(utility_type)
    problem.solve(solver)

    # then
    selected = [
        project.name
        for project in [
            var for var in problem.variables() if var.value() == 1.0
        ]
    ]

    assert selected == expected
