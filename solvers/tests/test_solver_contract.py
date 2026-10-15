import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import PulpSolverError

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
    SummedObjectivesLpSolver,
)

ALL_SOLVERS = [
    ExpandingApprovals,
    GreedySolver,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesExponentialSolver,
    MethodOfEqualSharesUtilitySolver,
    PhragmenSolver,
    SingleTransferableVote,
    SolidCoalitionRefinement,
    SummedObjectivesLpSolver,
]


@pytest.mark.parametrize("solver_class", ALL_SOLVERS)
def test_unified_constructor(solver_class):
    solver = solver_class(msg=False, timeLimit=10)

    assert solver.msg is False
    assert solver.timeLimit == 10


@pytest.mark.parametrize(
    "solver_class, option, value",
    [
        (MethodOfEqualSharesConstrainsSolver, "max_iterations", 5),
        (MethodOfEqualSharesConstrainsSolver, "cost_modification_base", 1.5),
        (MethodOfEqualSharesExponentialSolver, "budget_init", 100),
        (PhragmenSolver, "kappa", 2.0),
        (SummedObjectivesLpSolver, "use_gurobi", True),
    ],
)
def test_options_serialized_in_to_dict(solver_class, option, value):
    solver = solver_class(**{option: value})

    assert solver.optionsDict[option] == value
    assert solver.toDict()[option] == value


def test_option_defaults():
    constrains = MethodOfEqualSharesConstrainsSolver()
    assert constrains.optionsDict["max_iterations"] == 200
    assert constrains.optionsDict["cost_modification_base"] == 1.007

    phragmen = PhragmenSolver()
    assert phragmen.optionsDict == {
        "increasing_scalings": False,
        "kappa": 1.0,
        "bos_version": False,
        "eps": 1e-6,
    }

    assert SummedObjectivesLpSolver().optionsDict["use_gurobi"] is False


def test_exponential_requires_budget_init(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    solver = MethodOfEqualSharesExponentialSolver()

    assert "budget_init" not in solver.optionsDict
    with pytest.raises(PulpSolverError, match="budget_init"):
        solver.actualSolve(basic_pb_approval)
