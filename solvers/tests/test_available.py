import importlib
import sys

import pytest

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
from muoblpsolvers.utils import bindings_available

BINDING_BACKED = [
    ExpandingApprovals,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesUtilitySolver,
    SingleTransferableVote,
    SolidCoalitionRefinement,
]

PURE_PYTHON = [
    GreedySolver,
    MethodOfEqualSharesExponentialSolver,
    PhragmenSolver,
    SummedObjectivesLpSolver,
]

ALL_SOLVERS = BINDING_BACKED + PURE_PYTHON


def _block_bindings(monkeypatch):
    # None in sys.modules => `import muoblpbindings` raises ImportError and
    # find_spec returns None (simulates the package not being installed).
    monkeypatch.setitem(sys.modules, "muoblpbindings", None)


def test_import_muoblpsolvers_without_bindings(monkeypatch):
    _block_bindings(monkeypatch)
    for module in [m for m in sys.modules if m.startswith("muoblpsolvers")]:
        monkeypatch.delitem(sys.modules, module, raising=False)

    # Lazy bindings imports => package imports fine without bindings installed.
    importlib.import_module("muoblpsolvers")


def test_available_without_bindings(monkeypatch):
    _block_bindings(monkeypatch)

    for solver_class in BINDING_BACKED:
        assert solver_class(msg=False).available() is False
    for solver_class in PURE_PYTHON:
        assert solver_class(msg=False).available() is True


def test_available_with_bindings():
    if not bindings_available():
        pytest.skip("muoblpbindings not installed")

    for solver_class in ALL_SOLVERS:
        assert solver_class(msg=False).available() is True
