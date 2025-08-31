from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    LpVariable,
    LpAffineExpression,
    LpConstraint,
    lpSum,
    LpConstraintLE,
)


@pytest.fixture
def empty_pb() -> MultiObjectiveLpProblem:
    problem = MultiObjectiveLpProblem("pb")
    return problem


@pytest.fixture
def bos_pb_data() -> tuple[dict[str, int], dict[str, list[str]], int]:
    budget = 1000000
    projects = {
        "A": 300000,
        "B": 400000,
        "C": 300000,
        "D": 240000,
        "E": 170000,
        "F": 100000,
    }
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
    empty_pb: MultiObjectiveLpProblem, bos_pb_data
) -> Callable[[str], MultiObjectiveLpProblem]:
    projects, ballots, budget = bos_pb_data

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
        empty_pb.setObjectives(objectives)
        empty_pb.addConstraint(pb_constraint)

        return empty_pb

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
