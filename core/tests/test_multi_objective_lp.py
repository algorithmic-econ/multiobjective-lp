import warnings

import pytest
from pulp import LpAffineExpression, LpConstraint, LpConstraintLE, LpVariable

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem


@pytest.fixture
def variables() -> dict[str, LpVariable]:
    return {name: LpVariable(name, cat="Binary") for name in ("p1", "p2")}


def test_default_objectives_not_shared_between_problems(variables):
    """Regression: mutable default args made every problem share one list."""
    first = MultiObjectiveLpProblem("first")
    second = MultiObjectiveLpProblem("second")

    first.objectives.append(LpAffineExpression({variables["p1"]: 1}, name="o"))
    first.objectives_weights["o"] = 1

    assert second.objectives == []
    assert second.objectives_weights == {}


def test_explicit_objectives_are_kept(variables):
    objective = LpAffineExpression({variables["p1"]: 1}, name="o")
    problem = MultiObjectiveLpProblem(
        "explicit", objectives=[objective], objectives_weights={"o": 2}
    )

    assert problem.objectives == [objective]
    assert problem.objectives_weights == {"o": 2}


def test_iadd_expression_appends_objective(variables):
    problem = MultiObjectiveLpProblem("iadd")
    o1 = LpAffineExpression({variables["p1"]: 1}, name="o1")
    o2 = LpAffineExpression({variables["p2"]: 1}, name="o2")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        problem += o1
        problem += o2

    assert problem.objectives == [o1, o2]
    assert problem.objective is None
    assert caught == []


def test_iadd_variable_appends_objective(variables):
    problem = MultiObjectiveLpProblem("iadd_var")

    problem += variables["p1"]

    assert len(problem.objectives) == 1
    assert problem.objectives[0][variables["p1"]] == 1
    assert problem.objective is None


def test_iadd_tuple_names_the_objective(variables):
    problem = MultiObjectiveLpProblem("iadd_named")

    problem += LpAffineExpression({variables["p1"]: 1}), "named"

    assert [o.name for o in problem.objectives] == ["named"]


def test_iadd_constraint_still_delegates_to_pulp(variables):
    problem = MultiObjectiveLpProblem("iadd_constraint")

    problem += (
        100 * variables["p1"] + 200 * variables["p2"] <= 250,
        "pb_constraint",
    )

    assert list(problem.constraints) == ["pb_constraint"]
    assert problem.objectives == []


def test_iadd_constraint_object_still_delegates_to_pulp(variables):
    problem = MultiObjectiveLpProblem("iadd_constraint_obj")

    problem += LpConstraint(
        LpAffineExpression({variables["p1"]: 100}),
        sense=LpConstraintLE,
        name="c",
        rhs=100,
    )

    assert list(problem.constraints) == ["c"]
    assert problem.objectives == []


def test_iadd_number_still_sets_pulp_objective():
    problem = MultiObjectiveLpProblem("iadd_number")

    problem += 0

    assert problem.objectives == []
    assert problem.objective is not None
