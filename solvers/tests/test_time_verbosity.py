# NOTE: imports are added task-by-task as first used — pre-commit ruff
# (F401) rejects not-yet-used imports; add them as each task first needs them.
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusNotSolved, LpStatusOptimal

from muoblpsolvers.utils import set_solved


def test_set_solved_default_status(basic_pb_approval: MultiObjectiveLpProblem):
    set_solved(basic_pb_approval, ["_A"])
    assert basic_pb_approval.status == LpStatusOptimal
    assert basic_pb_approval.variablesDict()["_A"].value() == 1


def test_set_solved_custom_status(basic_pb_approval: MultiObjectiveLpProblem):
    set_solved(basic_pb_approval, [], LpStatusNotSolved)
    assert basic_pb_approval.status == LpStatusNotSolved
    assert all(v.value() == 0 for v in basic_pb_approval.variables())
