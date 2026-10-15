from collections.abc import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintLE,
    LpStatusOptimal,
    LpVariable,
    lpSum,
)

from muoblpsolvers import GreedySolver
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
    assert problem.status == LpStatusOptimal
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

    assert problem.status == LpStatusOptimal
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

    assert problem.status == LpStatusOptimal
    selected = {var.name for var in problem.variables() if var.value() == 1.0}
    total_cost = sum(projects_costs[n] for n in selected)
    assert total_cost <= 1000000


def test_greedy_ignores_zero_vote_candidate():
    prob = MultiObjectiveLpProblem("pb_zero_vote")
    variables = LpVariable.dicts("", ["A", "B", "Z"], cat="Binary")
    for variable in variables.values():
        variable.setInitialValue(0)
    costs = {"A": 300, "B": 400, "Z": 100}
    prob.addVariables(variables.values())
    prob.set_objectives([
        LpAffineExpression([(variables["A"], 1)], name="v1"),
        LpAffineExpression(
            [(variables["A"], 1), (variables["B"], 1)], name="v2"
        ),
    ])
    prob.addConstraint(
        LpConstraint(
            e=lpSum(variables[p] * c for p, c in costs.items()),
            sense=LpConstraintLE,
            rhs=1000,
            name="pb",
        )
    )
    prob.solve(GreedySolver(msg=False))

    assert prob.status == LpStatusOptimal
    selected = {v.name for v in prob.variables() if v.value() == 1.0}
    assert selected == {"_A", "_B"}  # _Z has zero votes -> never selected
