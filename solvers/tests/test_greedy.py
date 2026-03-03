from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpConstraint, LpConstraintGE, lpSum

from muoblpsolvers.greedy.GreedySolver import (
    GreedySolver,
)
from muoblpsolvers.types import Utility


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_F", "_E", "_A", "_C"]),
        ("COST", ["_A", "_B", "_C"]),
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

    assert set(selected) == set(expected)


@pytest.mark.parametrize("utility_type", ["APPROVAL", "COST"])
def test_greedy_solver_lb_forces_low_ratio_candidate(
    pb_with_lb_factory: Callable[[Utility], MultiObjectiveLpProblem],
    utility_type: Utility,
):
    """GE constraint forces E even though its utility/cost ratio is worse than F."""
    solver = GreedySolver()
    problem = pb_with_lb_factory(utility_type)
    problem.solve(solver)

    selected = {var.name for var in problem.variables() if var.value() == 1.0}
    assert "_E" in selected


@pytest.mark.parametrize("utility_type", ["APPROVAL", "COST"])
def test_greedy_solver_lb_respects_upper_bound(
    pb_with_lb_factory: Callable[[Utility], MultiObjectiveLpProblem],
    utility_type: Utility,
):
    """Total selected cost must not exceed budget (1000000)."""
    projects_costs = {
        "_A": 300000,
        "_B": 400000,
        "_C": 300000,
        "_D": 240000,
        "_E": 170000,
        "_F": 100000,
    }
    solver = GreedySolver()
    problem = pb_with_lb_factory(utility_type)
    problem.solve(solver)

    selected = {var.name for var in problem.variables() if var.value() == 1.0}
    total_cost = sum(projects_costs[n] for n in selected)
    assert total_cost <= 1000000
