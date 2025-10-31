from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.greedy.GreedySolver import (
    GreedySolver,
)
from muoblpsolvers.types import Utility


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("COST", ["_A", "_C", "_E", "_F"]),
    ],
)
def test_greedy_solver(
    basic_pb_factory: Callable[[Utility], MultiObjectiveLpProblem],
    utility_type: Utility,
    expected: list[str],
):
    # when
    solver = GreedySolver()
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
