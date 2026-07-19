import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal

from muoblpsolvers import (
    ExpandingApprovals,
    SingleTransferableVote,
    SolidCoalitionRefinement,
)


@pytest.mark.parametrize(
    "solver_class, expected",
    [
        (ExpandingApprovals, ["_B"]),
        (SingleTransferableVote, ["_A", "_D"]),
        (SolidCoalitionRefinement, ["_A", "_B"]),
    ],
)
def test_ordinal_solver(
    solver_class,
    expected: list[str],
    ordinal_pb: MultiObjectiveLpProblem,
    capsys,
):
    solver = solver_class(msg=False)
    if not solver.available():
        pytest.skip(f"{solver_class.__name__} unavailable (needs bindings)")
    ordinal_pb.solve(solver)  # standard pulp path — exercises __dummy fix

    assert ordinal_pb.status == LpStatusOptimal
    selected = [
        var.name for var in ordinal_pb.variables() if var.value() == 1.0
    ]
    assert sorted(selected) == sorted(expected)
    # closes T14's deferred msg coverage for these three (the old
    # py::print __dummy warning is gone once the var is skipped)
    assert capsys.readouterr().out == ""
