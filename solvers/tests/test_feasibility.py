from collections.abc import Callable

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.election_solver import ElectionSolver, FeasibilityChecker
from muoblpsolvers.types import Utility


def test_no_lb_delegates_to_valid(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    """Without GE constraints check() mirrors lp.valid() (no CBC solve)."""
    checker = FeasibilityChecker(basic_pb_approval)
    assert checker.has_lowerbound_constraint is False

    for var in basic_pb_approval.variables():
        var.setInitialValue(0)
    assert checker.check() is basic_pb_approval.valid() is True

    # overspend the budget -> both report infeasible
    for var in basic_pb_approval.variables():
        if var.name != "__dummy":
            var.setInitialValue(1)
    assert checker.check() is basic_pb_approval.valid() is False


def test_is_feasible_matches_checker(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    """The static single-shot helper agrees with a reused checker."""
    for var in basic_pb_approval.variables():
        var.setInitialValue(0)
    assert (
        ElectionSolver.is_feasible(basic_pb_approval)
        == FeasibilityChecker(basic_pb_approval).check()
    )


def test_lb_checker_reused_across_checks(
    pb_with_lb_factory: Callable[[Utility], MultiObjectiveLpProblem],
):
    """Reused LB completion model must return identical results to fresh
    FeasibilityChecker instances for the same assignment (model-reuse lock)."""
    lp = pb_with_lb_factory("APPROVAL")
    checker = FeasibilityChecker(lp)
    assert checker.has_lowerbound_constraint is True

    variables = lp.variablesDict()
    for name in ["_A", "_E", "_F"]:
        for var in lp.variables():
            var.setInitialValue(0)
        variables[name].setInitialValue(1)
        # reused checker vs. a freshly built one must agree every time
        assert checker.check() == FeasibilityChecker(lp).check()
