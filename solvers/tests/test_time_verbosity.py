# NOTE: imports are added task-by-task as first used — pre-commit ruff
# (F401) rejects not-yet-used imports; add them as each task first needs them.
import logging

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintLE,
    LpStatusNotSolved,
    LpStatusOptimal,
    LpVariable,
    PulpSolverError,
    lpSum,
)

from muoblpsolvers import (
    ExpandingApprovals,
    GreedySolver,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesExponentialSolver,
    MethodOfEqualSharesUtilitySolver,
    PhragmenSolver,
    SingleTransferableVote,
    SolidCoalitionRefinement,
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


def test_greedy_timelimit_aborts_not_solved(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    basic_pb_approval.solve(GreedySolver(msg=False, timeLimit=1e-9))
    assert basic_pb_approval.status == LpStatusNotSolved
    assert all(v.value() == 0 for v in basic_pb_approval.variables())


def test_greedy_msg_false_silent(
    basic_pb_approval: MultiObjectiveLpProblem, capsys, caplog
):
    with caplog.at_level(logging.DEBUG):
        basic_pb_approval.solve(GreedySolver(msg=False))
    assert capsys.readouterr().out == ""
    assert [
        r for r in caplog.records if r.name.startswith("muoblpsolvers")
    ] == []


def test_greedy_msg_true_logs(
    basic_pb_approval: MultiObjectiveLpProblem, caplog
):
    with caplog.at_level(logging.INFO):
        basic_pb_approval.solve(GreedySolver())
    messages = [r.getMessage() for r in caplog.records]
    assert "SOLVER START" in messages
    assert "SOLVER END" in messages


def test_phragmen_timelimit_aborts_not_solved(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    basic_pb_approval.solve(PhragmenSolver(msg=False, timeLimit=1e-9))
    assert basic_pb_approval.status == LpStatusNotSolved


def test_phragmen_msg_false_silent(
    basic_pb_approval: MultiObjectiveLpProblem, capsys, caplog
):
    with caplog.at_level(logging.DEBUG):
        basic_pb_approval.solve(PhragmenSolver(msg=False))
    assert capsys.readouterr().out == ""
    assert [
        r for r in caplog.records if r.name.startswith("muoblpsolvers")
    ] == []


def test_mes_exponential_timelimit_aborts_not_solved(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    solver = MethodOfEqualSharesExponentialSolver(
        msg=False, timeLimit=1e-9, budget_init=1
    )
    basic_pb_approval.solve(solver)
    assert basic_pb_approval.status == LpStatusNotSolved


def test_mes_exponential_msg_false_silent(
    basic_pb_approval: MultiObjectiveLpProblem, capsys, caplog
):
    with caplog.at_level(logging.DEBUG):
        basic_pb_approval.solve(
            MethodOfEqualSharesExponentialSolver(msg=False, budget_init=1)
        )
    assert capsys.readouterr().out == ""
    assert [
        r for r in caplog.records if r.name.startswith("muoblpsolvers")
    ] == []


def test_mes_constrains_timelimit_aborts_not_solved(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    solver = MethodOfEqualSharesConstrainsSolver(msg=False, timeLimit=1e-9)
    if not solver.available():
        pytest.skip("muoblpbindings not installed")
    basic_pb_approval.solve(solver)
    assert basic_pb_approval.status == LpStatusNotSolved
    assert all(v.value() == 0 for v in basic_pb_approval.variables())


TIMELIMIT_WARN_SOLVERS = [
    ExpandingApprovals,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesUtilitySolver,
    SingleTransferableVote,
    SolidCoalitionRefinement,
]


@pytest.mark.parametrize("solver_class", TIMELIMIT_WARN_SOLVERS)
def test_binding_backed_timelimit_warns(
    solver_class, basic_pb_approval: MultiObjectiveLpProblem
):
    basic_pb_approval.set_objectives([])
    solver = solver_class(msg=False, timeLimit=10)
    with (
        pytest.warns(UserWarning, match="timeLimit"),
        pytest.raises(PulpSolverError),
    ):
        solver.actualSolve(basic_pb_approval)
