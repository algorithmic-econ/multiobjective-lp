# T17 Solver Test Coverage Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every solver module has ≥1 unit test on a tiny hand-built instance asserting status + selected vars; rename `test_mes_base.py` to match the utility solver; fix two crashes found while freezing expectations (greedy zero-vote KeyError; C++ `__dummy` rejection that makes EA/STV/SCR unusable via `problem.solve()`).

**Architecture:** 7 solvers lack dedicated tests: Phragmen, MES-Exponential, MES-Constrains, Summed, ExpandingApprovals, STV, SolidCoalitionRefinement. Pure-python + MES ones reuse the existing `basic_pb_factory` fixture (6 projects/10 voters/budget 1M; `LpVariable.dicts("", ...)` prefixes names with `_`). EA/STV/SCR are committee-selection rules with a different C++ contract (`Instance::from_MuoblpProblem`): **exactly one** constraint, ALL candidate costs == 1, budget = committee size k, strictly-ranked positive utilities per voter, and an `objectives_weights` entry per voter (missing → C++ KeyError) — they need a new `ordinal_pb` fixture. **Expected selections below were frozen by running each solver on these exact fixtures (bindings 0.0.17, pulp 3.3.2)** — if any differs at execution time, STOP and investigate (T14/T16 were designed to be behavior-preserving; a diff means a regression, not a stale plan).

**Tech Stack:** pytest, pybind11/scikit-build-core (one 4-line C++ fix + local rebuild), pulp 3.3.2.

## Global Constraints

- Branch `feat/t17-coverage-sweep` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`. Execute AFTER T14+T16 (tests below assume `msg=False` silence and checker-based feasibility exist; frozen values verified stable across both).
- Binding-backed solvers (MES-Constrains, EA, STV, SCR): `if not solver.available(): pytest.skip(...)` guard before solving.
- MES-Exponential requires `budget_init` (pulp drops `None` kwargs) — tests pass `budget_init=1`.
- Summed tests use the CBC path only (`use_gurobi=False` default); no Gurobi in CI.
- **User-confirmed:** the `__dummy` incompatibility is fixed in C++ (skip the var, mirroring every python-side validator), NOT worked around in tests.
- macOS local bindings rebuild needs the broken-CLT workaround: `export SDKROOT=$(xcrun --show-sdk-path); export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"`.
- e2e golden unaffected (NO regen): e2e solvers are GREEDY/MES_UTILS/MES_ADD1; the C++ change only skips `__dummy` in the `Instance` reader used by EA/STV/SCR (MES bindings take pre-filtered decomposed params).

---

### Task 1: Rename `test_mes_base.py` → `test_mes_utility.py`

**Files:**
- Move: `solvers/tests/test_mes_base.py` → `solvers/tests/test_mes_utility.py`

- [ ] **Step 1:** `git mv solvers/tests/test_mes_base.py solvers/tests/test_mes_utility.py`, then inside rename `test_base_mes_solver` → `test_mes_utility_solver` (file tests `MethodOfEqualSharesUtilitySolver`; the old name was the T12-flagged misnomer).
- [ ] **Step 2:** `cd solvers && poetry run pytest tests/test_mes_utility.py -q` → 2 PASS (APPROVAL `["_A", "_D", "_E"]`, COST `["_B", "_D", "_F"]` unchanged).
- [ ] **Step 3:** Commit — `git commit -m "T17: rename test_mes_base -> test_mes_utility"`

---

### Task 2: Greedy zero-vote candidate fix

**Files:**
- Modify: `solvers/src/muoblpsolvers/greedy_solver.py` (sort key + filter, lines ~40-50)
- Test: `solvers/tests/test_greedy.py`

T02 leftover assigned "T13 or T17"; T13 shipped without it. Verified crash: a candidate no voter approves is in `election["candidates"]` (from the PB constraint) but not in `total_utility` (built from `profile`) → `KeyError` in the sort key.

- [ ] **Step 1: Failing test** (append to `test_greedy.py`)

```python
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintLE,
    LpVariable,
    lpSum,
)


def test_greedy_ignores_zero_vote_candidate():
    prob = MultiObjectiveLpProblem("pb_zero_vote")
    variables = LpVariable.dicts("", ["A", "B", "Z"], cat="Binary")
    for variable in variables.values():
        variable.setInitialValue(0)
    costs = {"A": 300, "B": 400, "Z": 100}
    prob.addVariables(variables.values())
    prob.set_objectives([
        LpAffineExpression([(variables["A"], 1)], name="v1"),
        LpAffineExpression(
            [(variables["A"], 1), (variables["B"], 1)], name="v2"
        ),
    ])
    prob.addConstraint(
        LpConstraint(
            e=lpSum(variables[p] * c for p, c in costs.items()),
            sense=LpConstraintLE,
            rhs=1000,
            name="pb",
        )
    )
    prob.solve(GreedySolver(msg=False))

    assert prob.status == LpStatusOptimal
    selected = {v.name for v in prob.variables() if v.value() == 1.0}
    assert selected == {"_A", "_B"}  # _Z has zero votes -> never selected
```

(Adjust the import line to what `test_greedy.py` already imports — it has `MultiObjectiveLpProblem`, `GreedySolver`, `LpStatusOptimal`.)

- [ ] **Step 2: Verify failure** — `poetry run pytest tests/test_greedy.py -k zero_vote -q` → FAIL `KeyError: '_Z'`.

- [ ] **Step 3: Fix** — in `_solve_election`, both reads of `total_utility[candidate]` outside the builder loop become `.get(candidate, 0)`:

```python
        sorted_candidates.sort(
            key=lambda candidate: (
                total_utility.get(candidate, 0) / candidates[candidate]
            ),
            reverse=True,
        )
        sorted_candidates = [
            candidate
            for candidate in sorted_candidates
            if total_utility.get(candidate, 0) > 0
        ]
```

- [ ] **Step 4: Run** — `tests/test_greedy.py` all green.
- [ ] **Step 5: Commit** — `git commit -am "T17: greedy tolerates zero-vote candidates"`

---

### Task 3: Phragmen tests

**Files:**
- Test: `solvers/tests/test_phragmen.py` (new)

- [ ] **Step 1: Write tests** (frozen expectations)

```python
# solvers/tests/test_phragmen.py
from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal

from muoblpsolvers import PhragmenSolver


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_D", "_E", "_F"]),
        ("COST", ["_A", "_C", "_E", "_F"]),
    ],
)
def test_phragmen_solver(
    basic_pb_factory: Callable[[str], MultiObjectiveLpProblem],
    utility_type: str,
    expected: list[str],
):
    solver = PhragmenSolver(msg=False)
    problem = basic_pb_factory(utility_type)
    problem.solve(solver)

    assert problem.status == LpStatusOptimal
    selected = [
        var.name for var in problem.variables() if var.value() == 1.0
    ]
    assert sorted(selected) == sorted(expected)
```

- [ ] **Step 2: Run** — `poetry run pytest tests/test_phragmen.py -q` → 2 PASS (characterization of current behavior; on diff → STOP, see header).
- [ ] **Step 3: Commit** — `git add -A && git commit -m "T17: phragmen unit tests"`

---

### Task 4: MES-Exponential tests

**Files:**
- Test: `solvers/tests/test_mes_exponential.py` (new)

- [ ] **Step 1: Write tests** (same file skeleton as Task 3; frozen with `budget_init=1`)

```python
# solvers/tests/test_mes_exponential.py
from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal

from muoblpsolvers import MethodOfEqualSharesExponentialSolver


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_C", "_D", "_F"]),
        ("COST", ["_A", "_B", "_D"]),
    ],
)
def test_mes_exponential_solver(
    basic_pb_factory: Callable[[str], MultiObjectiveLpProblem],
    utility_type: str,
    expected: list[str],
):
    solver = MethodOfEqualSharesExponentialSolver(msg=False, budget_init=1)
    problem = basic_pb_factory(utility_type)
    problem.solve(solver)

    assert problem.status == LpStatusOptimal
    selected = [
        var.name for var in problem.variables() if var.value() == 1.0
    ]
    assert sorted(selected) == sorted(expected)
```

- [ ] **Step 2: Run** — 2 PASS.
- [ ] **Step 3: Commit** — `git commit -am "T17: mes-exponential unit tests"`

---

### Task 5: MES-Constrains tests

**Files:**
- Test: `solvers/tests/test_mes_constrains.py` (new)

On the plain fixture (no extra GE/LE constraints) MES-Constrains converges at iteration 0 to the plain MES-Utility result — the frozen values below intentionally equal `test_mes_utility.py`'s, which is itself a wiring check (the iteration loop must not perturb the unconstrained case).

- [ ] **Step 1: Write tests**

```python
# solvers/tests/test_mes_constrains.py
from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal

from muoblpsolvers import MethodOfEqualSharesConstrainsSolver


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_D", "_E"]),
        ("COST", ["_B", "_D", "_F"]),
    ],
)
def test_mes_constrains_solver(
    basic_pb_factory: Callable[[str], MultiObjectiveLpProblem],
    utility_type: str,
    expected: list[str],
):
    solver = MethodOfEqualSharesConstrainsSolver(msg=False)
    if not solver.available():
        pytest.skip("muoblpbindings not installed")
    problem = basic_pb_factory(utility_type)
    problem.solve(solver)

    assert problem.status == LpStatusOptimal
    selected = [
        var.name for var in problem.variables() if var.value() == 1.0
    ]
    assert sorted(selected) == sorted(expected)
```

- [ ] **Step 2: Run** — 2 PASS (bindings present locally).
- [ ] **Step 3: Commit** — `git commit -am "T17: mes-constrains unit tests"`

---

### Task 6: SummedObjectives tests

**Files:**
- Test: `solvers/tests/test_summed_objectives.py` (new)

- [ ] **Step 1: Write tests**

```python
# solvers/tests/test_summed_objectives.py
from typing import Callable

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusOptimal

from muoblpsolvers import SummedObjectivesLpSolver


@pytest.mark.parametrize(
    "utility_type, expected",
    [
        ("APPROVAL", ["_A", "_C", "_E", "_F"]),
        ("COST", ["_A", "_B", "_C"]),
    ],
)
def test_summed_objectives_solver(
    basic_pb_factory: Callable[[str], MultiObjectiveLpProblem],
    utility_type: str,
    expected: list[str],
):
    solver = SummedObjectivesLpSolver(msg=False)  # CBC path; no Gurobi in CI
    problem = basic_pb_factory(utility_type)
    problem.solve(solver)

    assert problem.status == LpStatusOptimal
    selected = [
        var.name for var in problem.variables() if var.value() == 1.0
    ]
    assert sorted(selected) == sorted(expected)
```

- [ ] **Step 2: Run** — 2 PASS.
- [ ] **Step 3: Commit** — `git commit -am "T17: summed-objectives unit tests"`

---

### Task 7: C++ `__dummy` fix + ordinal fixture + EA/STV/SCR tests

**Files:**
- Modify: `bindings/src/common.cpp` (`Instance::from_MuoblpProblem`, lines 10-27), `bindings/pyproject.toml` (version), `solvers/pyproject.toml` (+ `poetry lock`)
- Modify: `solvers/tests/fixtures/pb_problems.py`, `solvers/tests/conftest.py`
- Test: `solvers/tests/test_ordinal_solvers.py` (new)

**Interfaces:**
- Produces: `ordinal_pb` fixture — `MultiObjectiveLpProblem`, 4 candidates unit cost, `pb` LE constraint rhs=2 (committee size), 5 voters with strict positive-utility rankings, `objectives_weights` all 1.

Bug (verified): `pulp.LpProblem.solve` calls `fixObjective` BEFORE `actualSolve`; with no scalar objective set (all election solvers), pulp injects a `__dummy` var. `Instance::from_MuoblpProblem` doesn't skip it (every python validator does), so `__dummy` gets candidate cost 0 and the unit-cost check in EA/STV/SCR throws `ValueError: All candidates are expected to have weight 1, but candidate __dummy has 0` — the three solvers are unusable via `problem.solve()`. Direct `actualSolve()` works (no fixObjective).

- [ ] **Step 1: Add the ordinal fixture.** In `solvers/tests/fixtures/pb_problems.py` append:

```python
@pytest.fixture
def ordinal_pb() -> MultiObjectiveLpProblem:
    """Committee-selection instance for the ordinal bindings (EA/STV/SCR).

    C++ Instance contract: exactly one constraint, ALL candidate costs 1,
    rhs = committee size, strictly-decreasing positive utilities per voter
    (rank positions), and an objectives_weights entry per voter.
    """
    rankings = {
        "v1": ["A", "B", "C"],
        "v2": ["A", "B", "C"],
        "v3": ["B", "D"],
        "v4": ["C", "D"],
        "v5": ["D", "A"],
    }
    names = ["A", "B", "C", "D"]
    committee_size = 2
    prob = MultiObjectiveLpProblem("ordinal_pb")
    variables = LpVariable.dicts("", names, cat="Binary")
    for variable in variables.values():
        variable.setInitialValue(0)
    objectives = [
        LpAffineExpression(
            [
                [variables[candidate], len(ranking) - position]
                for position, candidate in enumerate(ranking)
            ],
            name=voter,
        )
        for voter, ranking in rankings.items()
    ]
    prob.addVariables(variables.values())
    prob.set_objectives(objectives)
    prob.set_objectives_weights({voter: 1 for voter in rankings})
    prob.addConstraint(
        LpConstraint(
            e=lpSum(variables[name] * 1 for name in names),
            sense=LpConstraintLE,
            rhs=committee_size,
            name="pb",
        )
    )
    return prob
```

Add `ordinal_pb` to the `conftest.py` re-export list.

- [ ] **Step 2: Write the failing tests**

```python
# solvers/tests/test_ordinal_solvers.py
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
```

- [ ] **Step 3: Verify failure** — `poetry run pytest tests/test_ordinal_solvers.py -q` → 3 FAIL with `ValueError: All candidates are expected to have weight 1, but candidate __dummy has 0`.

- [ ] **Step 4: Fix C++.** In `bindings/src/common.cpp`, current lines 10-27:

```cpp
  py::list vars = prob.attr("variables")();
  const size_t m = vars.size();
  if (m > std::numeric_limits<CandidateId>::max()) {
    throw std::invalid_argument(
        std::format("Too many candidates. Got {} while the maximum is {}", m,
                    std::numeric_limits<CandidateId>::max()));
  }
  for (py::handle var : vars) {
    std::string name = var.attr("name").cast<std::string>();
    instance.candidate_names.emplace_back(name);
```

become:

```cpp
  py::list vars = prob.attr("variables")();
  if (vars.size() > std::numeric_limits<CandidateId>::max()) {
    throw std::invalid_argument(
        std::format("Too many candidates. Got {} while the maximum is {}",
                    vars.size(), std::numeric_limits<CandidateId>::max()));
  }
  for (py::handle var : vars) {
    std::string name = var.attr("name").cast<std::string>();
    if (name == "__dummy") {
      // pulp injects __dummy while solving a problem without a scalar
      // objective; python-side validators skip it the same way
      continue;
    }
    instance.candidate_names.emplace_back(name);
```

then after the loop replace the old `m` usages: `const size_t m = instance.candidate_names.size();` inserted right after the loop (before the ids-mapping comment) — the later `resize(m, ...)`/loops keep working unchanged.

- [ ] **Step 5: Version bump + rebuild.** `bindings/pyproject.toml`: `version = "0.0.17"` → `"0.0.18"`. `solvers/pyproject.toml` `[project].dependencies`: `"muoblpbindings>=0.0.17,<0.1"` → `"muoblpbindings>=0.0.18,<0.1"` (published solvers now depend on fixed behavior); then `cd solvers && poetry lock`. Rebuild locally:

```bash
export SDKROOT=$(xcrun --show-sdk-path)
export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"
cd solvers && poetry run pip install --force-reinstall --no-deps ../bindings
```

- [ ] **Step 6: Run** — `poetry run pytest tests/test_ordinal_solvers.py -q` → 3 PASS. Then FULL solvers suite (MES bindings tests must stay green — they don't use `Instance`, but the wheel was rebuilt). Then `cd ../experiments && poetry run pytest -q && poetry run pytest -m e2e -q` (golden identical). Note: do NOT push a `bindings@0.0.18` tag now — PyPI publish stays deferred (P1 leftover); CI PR jobs rebuild from source (cache keys hash `bindings/src/**`, T07).

- [ ] **Step 7: Commit** — `git add -A && git commit -m "T17: skip pulp __dummy in bindings Instance reader (fixes EA/STV/SCR via problem.solve); ordinal fixture + tests; bindings 0.0.18"`

---

### Task 8: AC sweep + PR

- [ ] **Step 1: Coverage AC** — `cd solvers && poetry run pytest --collect-only -q | tail -5` and check every solver module has ≥1 solve test: greedy (test_greedy), phragmen (test_phragmen), mes_add1 (test_mes_add1), mes_utility (test_mes_utility), mes_constrains (test_mes_constrains), mes_exponential (test_mes_exponential + T14 tests), summed (test_summed_objectives), EA/STV/SCR (test_ordinal_solvers). All assert status + selection.
- [ ] **Step 2: Full verify** — solvers: pytest, ruff check, ruff format --check, pyright. experiments: pytest incl. e2e. core: pytest. bindings: `poetry run python -c "import muoblpbindings; print(muoblpbindings.__version__ if hasattr(muoblpbindings, '__version__') else 'ok')"`.
- [ ] **Step 3: Commit + PR** — push, PR → `feat/roadmap-base-branch`, title `T17: solver test coverage sweep`; body: frozen-expectation provenance, the two bug fixes (greedy zero-vote, C++ `__dummy`), bindings 0.0.18 note (tag/publish deferred), CI bindings-cache bust expected. Update ROADMAP + leftovers (strike the T02 zero-vote item).

## Unresolved questions

None (C++ fix user-confirmed).
