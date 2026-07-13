from collections.abc import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintLE,
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
from muoblpsolvers.types import Utility

# All PB-shaped solvers except SummedObjectivesLpSolver, which is a
# deliberately generic LP/MIP pass-through and stays unvalidated.
PB_SOLVER_CLASSES = [
    GreedySolver,
    PhragmenSolver,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesUtilitySolver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesExponentialSolver,
    SingleTransferableVote,
    ExpandingApprovals,
    SolidCoalitionRefinement,
]


def test_no_objectives_rejected(basic_pb_approval: MultiObjectiveLpProblem):
    basic_pb_approval.set_objectives([])

    with pytest.raises(PulpSolverError, match="no objectives"):
        GreedySolver().actualSolve(basic_pb_approval)


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda v: setattr(v, "cat", "Continuous"), id="continuous"
        ),
        pytest.param(lambda v: setattr(v, "upBound", 5), id="bad-upbound"),
        pytest.param(
            lambda v: setattr(v, "lowBound", 1), id="positive-lowbound"
        ),
    ],
)
def test_non_binary_variable_rejected(
    basic_pb_approval: MultiObjectiveLpProblem,
    mutate: Callable[[LpVariable], None],
):
    variable = basic_pb_approval.variablesDict()["_A"]
    mutate(variable)

    with pytest.raises(PulpSolverError, match="not a 0/1 binary PB variable"):
        GreedySolver().actualSolve(basic_pb_approval)


def test_missing_pb_constraint_rejected(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    del basic_pb_approval.constraints["pb"]

    with pytest.raises(PulpSolverError, match="does not have PB constraint"):
        GreedySolver().actualSolve(basic_pb_approval)


def test_duplicate_pb_constraint_rejected(invalid_pb: MultiObjectiveLpProblem):
    with pytest.raises(PulpSolverError, match="too many PB constraint"):
        GreedySolver().actualSolve(invalid_pb)


def test_negative_objective_coefficient_rejected(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    objective = basic_pb_approval.objectives[0]
    candidate = next(iter(objective.keys()))
    objective[candidate] = -1

    with pytest.raises(PulpSolverError, match="negative coefficient"):
        GreedySolver().actualSolve(basic_pb_approval)


def test_negative_constraint_coefficient_rejected():
    problem = MultiObjectiveLpProblem("neg_constraint")
    variable = LpVariable("_A", cat="Binary")
    problem.addVariables([variable])
    problem.set_objectives([
        LpAffineExpression([(variable, 1)], name="voter1")
    ])
    problem.addConstraint(
        LpConstraint(
            e=lpSum([variable * -100]),
            sense=LpConstraintLE,
            rhs=1000,
            name="pb",
        )
    )

    with pytest.raises(PulpSolverError, match="negative"):
        GreedySolver().actualSolve(problem)


def test_valid_program_not_rejected(
    basic_pb_factory: Callable[[Utility], MultiObjectiveLpProblem],
):
    problem = basic_pb_factory("APPROVAL")
    problem.solve(PhragmenSolver(msg=False))
    assert problem.status is not None


@pytest.mark.parametrize("solver_class", PB_SOLVER_CLASSES)
def test_validation_wired_into_every_pb_solver(
    solver_class,
    basic_pb_approval: MultiObjectiveLpProblem,
):
    """Every PB solver but the generic SummedObjectivesLpSolver must
    validate before doing solver-specific work. Rule logic itself is
    covered per-rule above via GreedySolver; this only proves the wiring.
    """
    solver = solver_class()
    if not solver.available():
        pytest.skip(f"{solver_class.__name__} unavailable (needs bindings)")

    basic_pb_approval.set_objectives([])

    with pytest.raises(PulpSolverError, match="no objectives"):
        solver.actualSolve(basic_pb_approval)
