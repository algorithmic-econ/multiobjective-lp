from collections.abc import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal

from muoblpsolvers import MethodOfEqualSharesUtilitySolver
from muoblpsolvers.types import Utility


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_D", "_E"]),
        ("COST", ["_B", "_D", "_F"]),  # TODO: check results
        # TODO: Test other utility types
    ],
)
def test_mes_utility_solver(
    basic_pb_factory: Callable[[Utility], MultiObjectiveLpProblem],
    utility_type: Utility,
    expected: list[str],
):
    # when
    solver = MethodOfEqualSharesUtilitySolver()
    problem = basic_pb_factory(utility_type)
    problem.solve(solver)

    # then
    assert problem.status == LpStatusOptimal
    selected = [
        project.name
        for project in [
            var for var in problem.variables() if var.value() == 1.0
        ]
    ]

    assert selected == expected
