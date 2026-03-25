import pytest
from pabutools.election import (
    ApprovalBallot,
    CumulativeBallot,
    OrdinalBallot,
)

from helpers.transformers.pabutoolsToMoLp import (
    ballot_to_cost_weights,
    ballot_to_expression_strategy,
)

from .fixtures.pabutools_factories import make_project


@pytest.fixture
def projects():
    p1 = make_project("p1", 100, {"edu"})
    p2 = make_project("p2", 200, {"env"})
    p3 = make_project("p3", 300, {"edu"})
    return {"p1": p1, "p2": p2, "p3": p3}


# -- ballot_to_expression_strategy --


def test_approval_returns_1_per_project(projects):
    fn = ballot_to_expression_strategy("APPROVAL")
    ballot = ApprovalBallot(init=[projects["p1"], projects["p2"]])

    # when
    result = fn(ballot)

    # then
    assert sorted(result) == sorted([["p1", 1], ["p2", 1]])


def test_cost_returns_project_cost(projects):
    fn = ballot_to_expression_strategy("COST")
    ballot = ApprovalBallot(init=[projects["p1"], projects["p2"]])

    result = fn(ballot)

    assert sorted(result) == sorted([["p1", 100], ["p2", 200]])


def test_ordinal_returns_rank_weights(projects):
    fn = ballot_to_expression_strategy("ORDINAL")
    ballot = OrdinalBallot(
        init=[projects["p1"], projects["p2"], projects["p3"]]
    )

    result = fn(ballot)

    # first gets len(ballot)=3, second 2, third 1
    assert result == [["p1", 3], ["p2", 2], ["p3", 1]]


def test_cumulative_returns_points(projects):
    fn = ballot_to_expression_strategy("CUMULATIVE")
    ballot = CumulativeBallot(init={projects["p1"]: 5, projects["p2"]: 3})

    result = fn(ballot)

    assert sorted(result) == sorted([["p1", 5], ["p2", 3]])


def test_cost_ordinal_multiplies(projects):
    fn = ballot_to_expression_strategy("COST_ORDINAL")
    ballot = OrdinalBallot(init=[projects["p1"], projects["p2"]])

    result = fn(ballot)

    # p1: cost=100 * rank=2, p2: cost=200 * rank=1
    assert result == [["p1", 200], ["p2", 200]]


def test_cost_cumulative_multiplies(projects):
    fn = ballot_to_expression_strategy("COST_CUMULATIVE")
    ballot = CumulativeBallot(init={projects["p1"]: 5, projects["p2"]: 3})

    result = fn(ballot)

    assert sorted(result) == sorted([["p1", 500], ["p2", 600]])


def test_unknown_utility_raises():
    with pytest.raises(Exception, match="Unknown utility"):
        ballot_to_expression_strategy("BOGUS")


# -- ballot_to_cost_weights --


def test_cost_weights_approval_ballot(projects):
    ballot = ApprovalBallot(init=[projects["p1"], projects["p2"]])

    result = ballot_to_cost_weights(ballot)

    assert sorted(result) == sorted([["p1", 100], ["p2", 200]])


def test_cost_weights_cumulative_ballot(projects):
    ballot = CumulativeBallot(init={projects["p1"]: 5, projects["p2"]: 3})

    result = ballot_to_cost_weights(ballot)

    # ignores points, uses cost
    assert sorted(result) == sorted([["p1", 100], ["p2", 200]])
