import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.common import get_total_budget_constraint


def test_get_total_budget_constraint_throws_missing_pb(
    empty_pb: MultiObjectiveLpProblem,
):
    # when
    with pytest.raises(Exception) as err:
        _ = get_total_budget_constraint(empty_pb)

    # then
    assert "Problem does not have PB constraint" in str(err.value)


def test_get_total_budget_constraint(basic_pb: MultiObjectiveLpProblem):
    # when
    constraint = get_total_budget_constraint(basic_pb)

    # then
    assert constraint.value() == 1000001
