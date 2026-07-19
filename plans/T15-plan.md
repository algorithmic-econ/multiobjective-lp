# T15 Register Solvers in PuLP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `pulp.getSolver(name)` and `pulp.listSolvers()` work for all 10 custom solvers after `import muoblpsolvers`. GH #24.

**Architecture:** pulp 3.3.2 has NO plugin hook — the registry is the module-global list `pulp.apis._all_solvers` (`pulp/apis/__init__.py:18`); `getSolver` builds `{k.name: k for k in _all_solvers}` and `listSolvers` instantiates each entry with `msg=False` and (for `onlyAvailable=True`) calls `available()`. **Gotcha vs ROADMAP wording: `pulp._all_solvers` does NOT exist at top level** (leading underscore not re-exported by `from .apis import *`) — registration must mutate `pulp.apis._all_solvers` IN PLACE. User-confirmed style: auto-register as an import side effect (private `_register_in_pulp()` called at the bottom of `muoblpsolvers/__init__.py`), idempotent via membership check.

**Tech Stack:** pulp 3.3.2. Zero solver-class changes needed: all 10 already define class-level `name`, override `available()`, and accept `msg=` (verified). Registry keys are the `name` strings (`"Greedy"`, `"SummedObjectives"`, …), not class names.

## Global Constraints

- Branch `feat/t15-register-pulp` off `feat/roadmap-base-branch`; PR targets `feat/roadmap-base-branch`.
- Repo GREEN: solvers + experiments pytest (incl. e2e golden, NO regen — registration is additive, no behavior change), ruff, pyright.
- `listSolvers()` instantiates EVERY registered class each call — constructors must stay side-effect-free (they are; do not add work to any `__init__`).
- Bindings-gated solvers (ExpandingApprovals, 4×MES minus Exponential — i.e. Add1/Utility/Constrains — STV, SolidCoalitionRefinement = 6 classes) drop out of `listSolvers(onlyAvailable=True)` without bindings; `getSolver` never calls `available()` so all 10 always construct by name.

---

### Task 1: Registration function + auto-call on import

**Files:**
- Modify: `solvers/src/muoblpsolvers/__init__.py`
- Test: `solvers/tests/test_registration.py` (new)

**Interfaces:**
- Produces: `muoblpsolvers._register_in_pulp() -> None` (idempotent; module-private but importable for tests), auto-invoked at import. Consumers just `import muoblpsolvers` then use `pulp.getSolver`/`pulp.listSolvers`.

- [ ] **Step 1: Write the failing tests**

```python
# solvers/tests/test_registration.py
# NOTE: `import sys` is added in Task 2 (first use) — pre-commit ruff
# strips unused imports.
import pulp
import pulp.apis
import pytest

import muoblpsolvers
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

PURE_PYTHON_NAMES = {
    "Greedy",
    "Phragmen",
    "MethodOfEqualSharesExponential",
    "SummedObjectives",
}


@pytest.mark.parametrize("solver_class", ALL_SOLVERS)
def test_get_solver_by_name(solver_class):
    solver = pulp.getSolver(solver_class.name, msg=False)
    assert isinstance(solver, solver_class)
    assert solver.msg is False


def test_all_names_listed():
    names = {cls.name for cls in ALL_SOLVERS}
    assert names <= set(pulp.listSolvers())


def test_register_idempotent():
    before = len(pulp.apis._all_solvers)
    muoblpsolvers._register_in_pulp()
    muoblpsolvers._register_in_pulp()
    assert len(pulp.apis._all_solvers) == before


def test_get_solver_with_kwargs():
    solver = pulp.getSolver("Phragmen", msg=False, timeLimit=5, kappa=0.5)
    assert solver.timeLimit == 5
    assert solver.optionsDict["kappa"] == 0.5
```

- [ ] **Step 2: Run to verify failure**

Run: `cd solvers && poetry run pytest tests/test_registration.py -q`
Expected: FAIL — `PulpSolverError: The solver Greedy does not exist in PuLP` and `AttributeError: module 'muoblpsolvers' has no attribute '_register_in_pulp'`.

- [ ] **Step 3: Implement.** In `solvers/src/muoblpsolvers/__init__.py`, after the existing `__all__` block (keep imports/`__all__`/logger exactly as-is), add:

```python
import pulp.apis

_ALL_SOLVER_CLASSES: list[type] = [
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


def _register_in_pulp() -> None:
    """Make pulp.getSolver/listSolvers see our solvers.

    pulp has no registration hook; its registry is the module-global list
    pulp.apis._all_solvers (NOT re-exported as pulp._all_solvers), so we
    mutate it in place. Idempotent: safe on repeated import/call.
    """
    for solver_class in _ALL_SOLVER_CLASSES:
        if solver_class not in pulp.apis._all_solvers:
            pulp.apis._all_solvers.append(solver_class)


_register_in_pulp()
```

Place `import pulp.apis` with the top imports (`import logging` line) to satisfy ruff E402; the list + function + call go after `__all__`. If pyright flags private usage (`reportPrivateUsage` is not enabled in basic mode — unlikely), add `# pyright: ignore[reportPrivateUsage]  # pulp has no public registry API` on the two `_all_solvers` lines.

- [ ] **Step 4: Run** — `poetry run pytest tests/test_registration.py -q` → 13 PASS (10 parametrized + 3). Full: `poetry run pytest -q` green.

- [ ] **Step 5: Commit** — `git add -A && git commit -m "T15: register solvers in pulp registry on import"`

---

### Task 2: `onlyAvailable` + serialization round-trip tests

**Files:**
- Test: `solvers/tests/test_registration.py`

**Interfaces:**
- Consumes: `_block_bindings` idiom from `tests/test_available.py` (`monkeypatch.setitem(sys.modules, "muoblpbindings", None)` makes `find_spec` return None).

- [ ] **Step 1: Write the failing tests** (append; add `import sys` to the file header — first used here)

```python
def test_list_solvers_only_available_without_bindings(monkeypatch):
    monkeypatch.setitem(sys.modules, "muoblpbindings", None)
    available = set(pulp.listSolvers(onlyAvailable=True))
    assert PURE_PYTHON_NAMES <= available
    binding_backed = {cls.name for cls in ALL_SOLVERS} - PURE_PYTHON_NAMES
    assert binding_backed.isdisjoint(available)


def test_get_solver_from_dict_round_trip():
    original = PhragmenSolver(msg=False, timeLimit=7, kappa=0.5)
    restored = pulp.getSolverFromDict(original.toDict())
    assert isinstance(restored, PhragmenSolver)
    assert restored.msg is False
    assert restored.timeLimit == 7
    assert restored.optionsDict["kappa"] == 0.5
```

- [ ] **Step 2: Run** — `poetry run pytest tests/test_registration.py -q`. Both should PASS already (registration from Task 1 + existing `toDict` contract from T10). If `test_get_solver_from_dict_round_trip` fails on an unexpected key: inspect `original.toDict()` — `getSolverFromDict` pops `"solver"` and passes the rest as kwargs; T10 made all option keys valid ctor kwargs, so any failure is a real T10 regression — fix there, not here.

Note: `listSolvers(onlyAvailable=True)` also probes every BUILT-IN pulp solver (spawns availability checks, incl. CBC) — expect this single test to take a few seconds; that's normal.

- [ ] **Step 3: Commit** — `git commit -am "T15: registration availability + round-trip tests"`

---

### Task 3: README + final verify

**Files:**
- Modify: `solvers/README.md`

- [ ] **Step 1: Add a "PuLP registration" section** to `solvers/README.md`:

```markdown
## PuLP registration

`import muoblpsolvers` registers all solvers in PuLP's registry
(`pulp.apis._all_solvers`) as a side effect, so the standard PuLP API works:

    import pulp
    import muoblpsolvers  # noqa: F401 — registration side effect

    solver = pulp.getSolver("Greedy", msg=False)
    print(pulp.listSolvers(onlyAvailable=True))

| Class | Registry name |
|---|---|
| GreedySolver | `Greedy` |
| PhragmenSolver | `Phragmen` |
| MethodOfEqualSharesAdd1Solver | `MethodOfEqualSharesAdd1` |
| MethodOfEqualSharesUtilitySolver | `MethodOfEqualSharesUtility` |
| MethodOfEqualSharesConstrainsSolver | `MethodOfEqualSharesConstrains` |
| MethodOfEqualSharesExponentialSolver | `MethodOfEqualSharesExponential` |
| SingleTransferableVote | `SingleTransferableVote` |
| SolidCoalitionRefinement | `SolidCoalitionRefinement` |
| ExpandingApprovals | `ExpandingApprovals` |
| SummedObjectivesLpSolver | `SummedObjectives` |

Binding-backed solvers (all except Greedy, Phragmen,
MethodOfEqualSharesExponential, SummedObjectives) appear in
`listSolvers(onlyAvailable=True)` only when `muoblpbindings` is installed.
```

- [ ] **Step 2: Interactive venv check (AC)**

Run: `cd solvers && poetry run python -c "import pulp, muoblpsolvers; s = pulp.getSolver('MethodOfEqualSharesUtility', msg=False); print(type(s).__name__); print([n for n in pulp.listSolvers() if 'Equal' in n or n in ('Greedy', 'Phragmen', 'SummedObjectives', 'SingleTransferableVote', 'SolidCoalitionRefinement', 'ExpandingApprovals')])"`
Expected: `MethodOfEqualSharesUtilitySolver` + all 10 names.

- [ ] **Step 3: Full verify** — `cd solvers && poetry run pytest -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright`; `cd ../experiments && poetry run pytest -q` (incl. e2e, no regen).

- [ ] **Step 4: Commit + PR** — `git commit -am "T15: document pulp registration"`; push, PR → `feat/roadmap-base-branch`, title `T15: register solvers in PuLP (#24)`. Update ROADMAP checkbox + leftovers (note the `pulp.apis._all_solvers` vs `pulp._all_solvers` gotcha for posterity).

## Unresolved questions

None (auto-on-import user-confirmed).
