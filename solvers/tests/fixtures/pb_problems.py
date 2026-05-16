from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintGE,
    LpConstraintLE,
    LpVariable,
    lpSum,
)


@pytest.fixture
def empty_pb() -> MultiObjectiveLpProblem:
    problem = MultiObjectiveLpProblem("pb")
    return problem


@pytest.fixture
def pb_data() -> tuple[dict[str, int], dict[str, list[str]], int]:
    budget = 1000000
    projects = {
        "A": 300000,
        "B": 400000,
        "C": 300000,
        "D": 240000,
        "E": 170000,
        "F": 100000,
    }

    # A: 1,2,3,4,5,6 | 6
    # B: 2,3,4,5,6   | 5
    # C: 2,3,4,5,10  | 5
    # D: 7,8,9,10    | 4
    # E: 2,7,8,9     | 4
    # F: 6,9,10      | 3
    ballots = {
        "v1": ["A"],
        "v2": ["A", "B", "C", "E"],
        "v3": ["A", "B", "C"],
        "v4": ["A", "B", "C"],
        "v5": ["A", "B", "C"],
        "v6": ["A", "B", "F"],
        "v7": ["D", "E"],
        "v8": ["D", "E"],
        "v9": ["D", "E", "F"],
        "v10": ["C", "D", "F"],
    }
    return (projects, ballots, budget)


@pytest.fixture()
def basic_pb_factory(
    empty_pb: MultiObjectiveLpProblem,
    pb_data: tuple[dict[str, int], dict[str, list[str]], int],
) -> Callable[[str], MultiObjectiveLpProblem]:
    projects, ballots, budget = pb_data

    def _factory(utility_type):
        variables = LpVariable.dicts("", projects.keys(), cat="Binary")
        for variable in variables.values():
            variable.setInitialValue(0)

        coef = {
            "APPROVAL": lambda candidate: 1,
            "COST": lambda candidate: projects[candidate],
        }
        objectives = [
            LpAffineExpression(
                [
                    [variables[candidate], coef[utility_type](candidate)]
                    for candidate in approvals
                ],
                name=voter,
            )
            for voter, approvals in ballots.items()
        ]

        pb_constraint = LpConstraint(
            e=lpSum(
                variables[project] * cost for project, cost in projects.items()
            ),
            sense=LpConstraintLE,
            rhs=budget,
            name="pb",
        )

        empty_pb.addVariables(variables.values())
        empty_pb.set_objectives(objectives)
        empty_pb.addConstraint(pb_constraint)

        return empty_pb

    return _factory


@pytest.fixture()
def pb_with_lb_factory(
    pb_data: tuple[dict[str, int], dict[str, list[str]], int],
) -> Callable[[str], MultiObjectiveLpProblem]:
    """Like basic_pb_factory but adds GE constraint forcing E (cost=170000) to be selected.
    E's utility/cost ratio (4/170000) is lower than F's (3/100000), so greedy alone skips E.
    """
    projects, ballots, budget = pb_data

    def _factory(utility_type):
        problem = MultiObjectiveLpProblem("pb_with_lb")
        variables = LpVariable.dicts("", projects.keys(), cat="Binary")
        for variable in variables.values():
            variable.setInitialValue(0)

        coef = {
            "APPROVAL": lambda candidate: 1,
            "COST": lambda candidate: projects[candidate],
        }
        objectives = [
            LpAffineExpression(
                [
                    [variables[candidate], coef[utility_type](candidate)]
                    for candidate in approvals
                ],
                name=voter,
            )
            for voter, approvals in ballots.items()
        ]

        pb_constraint = LpConstraint(
            e=lpSum(variables[p] * c for p, c in projects.items()),
            sense=LpConstraintLE,
            rhs=budget,
            name="pb",
        )
        lb_constraint = LpConstraint(
            e=variables["E"] * projects["E"],
            sense=LpConstraintGE,
            rhs=projects["E"],
            name="lb_edu",
        )

        problem.addVariables(variables.values())
        problem.set_objectives(objectives)
        problem.addConstraint(pb_constraint)
        problem.addConstraint(lb_constraint)

        return problem

    return _factory


@pytest.fixture
def basic_pb_approval(
    basic_pb_factory: Callable[[str], MultiObjectiveLpProblem],
) -> MultiObjectiveLpProblem:
    return basic_pb_factory("APPROVAL")


@pytest.fixture
def invalid_pb(
    basic_pb_approval: MultiObjectiveLpProblem,
) -> MultiObjectiveLpProblem:
    pb_constraint_copy = basic_pb_approval.constraints["pb"].copy()
    basic_pb_approval.addConstraint(pb_constraint_copy)

    return basic_pb_approval
