import importlib
import sys

import pulp
import pulp.apis
import pytest

import muoblpsolvers  # noqa: F401  (import registers solvers in PuLP)
from muoblpsolvers.registration import SOLVERS, register_solvers

SOLVER_NAMES = [
    "ExpandingApprovals",
    "Greedy",
    "MethodOfEqualSharesAdd1",
    "MethodOfEqualSharesConstrains",
    "MethodOfEqualSharesExponential",
    "MethodOfEqualSharesUtility",
    "Phragmen",
    "SingleTransferableVote",
    "SolidCoalitionRefinement",
    "SummedObjectives",
]


def test_registration_covers_all_solvers():
    assert len(SOLVERS) == 10
    assert {s.name for s in SOLVERS} == set(SOLVER_NAMES)


@pytest.mark.parametrize("name", SOLVER_NAMES)
def test_get_solver_returns_instance(name):
    solver = pulp.getSolver(name)
    assert solver.name == name


@pytest.mark.parametrize("name", SOLVER_NAMES)
def test_list_solvers_includes_solver(name):
    assert name in pulp.listSolvers()


def test_register_solvers_is_idempotent():
    before = len(pulp.apis._all_solvers)
    register_solvers()
    register_solvers()
    assert len(pulp.apis._all_solvers) == before


def test_get_solver_round_trips_options():
    solver = pulp.getSolver(
        "MethodOfEqualSharesConstrains",
        cost_modification_base=1.01,
        max_iterations=50,
    )
    rebuilt = pulp.getSolverFromDict(solver.toDict())

    assert rebuilt.name == "MethodOfEqualSharesConstrains"
    assert rebuilt.optionsDict["cost_modification_base"] == 1.01
    assert rebuilt.optionsDict["max_iterations"] == 50


def test_registration_does_not_import_bindings(monkeypatch):
    # Blocking bindings + reimporting muoblpsolvers must still register all 10:
    # registration only appends classes, never instantiates or imports bindings.
    monkeypatch.setitem(sys.modules, "muoblpbindings", None)
    for module in [m for m in sys.modules if m.startswith("muoblpsolvers")]:
        monkeypatch.delitem(sys.modules, module, raising=False)

    importlib.import_module("muoblpsolvers")

    listed = pulp.listSolvers()
    for name in SOLVER_NAMES:
        assert name in listed
