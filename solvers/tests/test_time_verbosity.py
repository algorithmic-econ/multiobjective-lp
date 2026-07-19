# NOTE: imports are added task-by-task as first used — pre-commit ruff
# (F401) rejects not-yet-used imports; add them as each task first needs them.
import logging

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintLE,
    LpStatusNotSolved,
    LpStatusOptimal,
    LpVariable,
    lpSum,
)

from muoblpsolvers.mes.common import prepare_mes_parameters
from muoblpsolvers.utils import set_solved


def test_set_solved_default_status(basic_pb_approval: MultiObjectiveLpProblem):
    set_solved(basic_pb_approval, ["_A"])
    assert basic_pb_approval.status == LpStatusOptimal
    assert basic_pb_approval.variablesDict()["_A"].value() == 1


def test_set_solved_custom_status(basic_pb_approval: MultiObjectiveLpProblem):
    set_solved(basic_pb_approval, [], LpStatusNotSolved)
    assert basic_pb_approval.status == LpStatusNotSolved
    assert all(v.value() == 0 for v in basic_pb_approval.variables())


def _pb_with_zero_vote_project() -> MultiObjectiveLpProblem:
    prob = MultiObjectiveLpProblem("pb_zero_vote")
    variables = LpVariable.dicts("", ["A", "Z"], cat="Binary")
    for variable in variables.values():
        variable.setInitialValue(0)
    prob.addVariables(variables.values())
    prob.set_objectives([LpAffineExpression([(variables["A"], 1)], name="v1")])
    prob.addConstraint(
        LpConstraint(
            e=lpSum([variables["A"] * 100, variables["Z"] * 100]),
            sense=LpConstraintLE,
            rhs=1000,
            name="pb",
        )
    )
    return prob


def test_prepare_mes_parameters_msg_false_silent(capsys, caplog):
    with caplog.at_level(logging.DEBUG):
        prepare_mes_parameters(_pb_with_zero_vote_project(), msg=False)
    assert capsys.readouterr().out == ""
    assert caplog.records == []


def test_prepare_mes_parameters_msg_true_logs_removal(capsys, caplog):
    with caplog.at_level(logging.INFO):
        prepare_mes_parameters(_pb_with_zero_vote_project(), msg=True)
    assert capsys.readouterr().out == ""  # logger, never print
    assert any("_Z" in r.getMessage() for r in caplog.records)
