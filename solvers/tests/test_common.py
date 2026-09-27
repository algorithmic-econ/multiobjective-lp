import pytest
from pulp import PulpSolverError
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.election_solver import validate_pb_constraint


def test_validate_pb_constraint_throws_missing_pb(
    empty_pb: MultiObjectiveLpProblem,
):
    # when
    with pytest.raises(PulpSolverError) as err:
        _ = validate_pb_constraint(empty_pb)

    # then
    assert "Problem does not have PB constraint" in str(err.value)


def test_validate_pb_constraint_throws_too_many_pb(
    invalid_pb: MultiObjectiveLpProblem,
):
    # when
    with pytest.raises(PulpSolverError) as err:
        _ = validate_pb_constraint(invalid_pb)

    # then
    assert "Problem has too many PB constraint" in str(err.value)


def test_validate_pb_constraint(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    # when
    constraint = validate_pb_constraint(basic_pb_approval)

    # then
    assert constraint.value() == -1000000
