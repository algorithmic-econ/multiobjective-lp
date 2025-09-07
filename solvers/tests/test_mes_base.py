from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.mes_utils.MethodOfEqualSharesUtilitySolver import (
    MethodOfEqualSharesUtilitySolver,
)
from muoblpsolvers.types import Utility


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_D", "_E"]),
        ("COST", ["_B", "_D", "_F"]),  # TODO: check results
        # TODO: Test other utility types
    ],
)
def test_base_mes_solver(
    basic_pb_factory: Callable[[Utility], MultiObjectiveLpProblem],
    utility_type: Utility,
    expected: list[str],
):
    # when
    solver = MethodOfEqualSharesUtilitySolver()
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
