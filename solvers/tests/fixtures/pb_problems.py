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
def basic_pb(empty_pb: MultiObjectiveLpProblem) -> MultiObjectiveLpProblem:
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

    variables = LpVariable.dicts("", projects.keys(), cat="Binary")
    for variable in variables.values():
        variable.setInitialValue(0)

    objectives = [
        LpAffineExpression(
            [[variables[candidate], 1] for candidate in approvals],
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
