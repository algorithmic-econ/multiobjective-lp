# T16 Dedupe Transform + Unify Feasibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One `molp_to_simple_election` (keep solvers'), archive experiments' dead copy; one feasibility implementation (LP-solve `is_feasible`) replacing the point-check `lp.valid()` in Phragmen/MES-Exponential; reuse a warm mirror model instead of building a fresh CBC problem per candidate.

**Architecture:** `lp.valid()` evaluates constraints at the CURRENT point only — under a `LpConstraintGE` lower bound a partial selection is rejected even when completable (that's why greedy's `is_feasible` solves a CBC feasibility MIP for the GE case). New `FeasibilityChecker` class in `election_solver.py`: constructor builds the mirror binary model ONCE (or nothing, when no GE constraint — fast path stays `lp.valid()`); each `is_feasible()` call pins currently-selected vars (`lowBound=1`), solves CBC, unpins. Greedy builds one checker per solve; `phragmen_cardinal` and `equal_shares_exponential` build one per call and use it where they called `lp.valid()` — behavior IDENTICAL when no GE constraint exists (fast path), newly CORRECT under GE.

**Tech Stack:** pulp 3.3.2 (`PULP_CBC_CMD` spawns a CBC subprocess per solve — that part is unavoidable; the win is skipping per-check model reconstruction), pytest.

## Global Constraints

- Branch `feat/t16-dedupe-feasibility` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`. Execute AFTER T14 merges (both touch `phragmen_cardinal`/`equal_shares_exponential`; code below assumes T14's `deadline`/`msg` params + `if self.msg:` gates are in place — if T14 hasn't merged, rebase before starting).
- e2e golden IDENTICAL, **NO regen**: the e2e fixture has no GE constraints (empty `constraints_configs`), so every swapped call site takes the `lp.valid()` fast path.
- Dead code → `archived_code/` at repo root (does NOT exist yet — this ticket creates it). Ruff CI check already excludes it (`.github/workflows/ruff.yml:17`); pre-commit excludes it (`.pre-commit-config.yaml:12`); `ruff format --diff` (ruff.yml:18) does NOT — verify it passes post-move, else add `--exclude archived_code` there too.
- Leave `experiments/src/helpers/analyzers/metrics.py:62,64` alone — those are `LpConstraint.valid()` on individual constraints (metrics), not problem-level feasibility.

---

### Task 1: Archive dead experiments transformer

**Files:**
- Move: `experiments/src/helpers/transformers/molpToSimpleElection.py` → `archived_code/experiments/molpToSimpleElection.py`

Confirmed dead: repo-wide grep finds zero importers; `experiments/src/helpers/transformers/__init__.py` is empty; its `Election` shape (`{candidates, voters:list[str]}`) differs from the kept one — pure archival, not a merge.

- [ ] **Step 1: Move**

```bash
mkdir -p archived_code/experiments
git mv experiments/src/helpers/transformers/molpToSimpleElection.py archived_code/experiments/molpToSimpleElection.py
```

- [ ] **Step 2: Verify nothing breaks + grep AC**

Run: `grep -rn "molpToSimpleElection\|from helpers.transformers.molpToSimpleElection" experiments/src experiments/tests solvers/src solvers/tests` → empty.
Run: `cd experiments && poetry run pytest -q` → green (75 tests). `poetry run ruff check .` in experiments → clean. Repo root: `poetry -C solvers run ruff format --check archived_code` is NOT needed — but confirm pre-commit passes on commit (it excludes `archived_code`).

- [ ] **Step 3: Commit** — `git commit -m "T16: archive dead molpToSimpleElection transformer"`

---

### Task 2: First direct tests for the kept transform

**Files:**
- Test: `solvers/tests/test_election_transform.py` (new)

`molp_to_simple_election` (`solvers/src/muoblpsolvers/election_solver.py:149`) has zero direct tests today (the ~55 experiments transform tests cover `pabutoolsToMoLp`, a different module). Note: the `Candidates mismatch` branch inside it is unreachable through `validate_pb_constraint` (a matched PB constraint by definition covers all candidates) — don't test it, don't remove it (out of scope).

- [ ] **Step 1: Write the tests**

```python
# solvers/tests/test_election_transform.py
import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpVariable, PulpSolverError

from muoblpsolvers.election_solver import molp_to_simple_election


def test_transform_shapes(basic_pb_approval: MultiObjectiveLpProblem):
    election = molp_to_simple_election(basic_pb_approval)
    assert set(election["candidates"]) == {
        "_A", "_B", "_C", "_D", "_E", "_F",
    }
    assert election["candidates"]["_B"] == 400000
    assert election["voters"] == {f"v{i}": 1 for i in range(1, 11)}
    assert election["profile"]["_A"] == {
        "v1": 1, "v2": 1, "v3": 1, "v4": 1, "v5": 1, "v6": 1,
    }


def test_transform_respects_objective_weights(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    basic_pb_approval.set_objectives_weights({"v1": 3})
    election = molp_to_simple_election(basic_pb_approval)
    assert election["voters"]["v1"] == 3
    assert election["voters"]["v2"] == 1  # default weight


def test_transform_requires_pb_constraint():
    prob = MultiObjectiveLpProblem("no_pb")
    variable = LpVariable("_A", cat="Binary")
    prob.addVariables([variable])
    prob.set_objectives(
        [LpAffineExpression([(variable, 1)], name="v1")]
    )
    with pytest.raises(PulpSolverError, match="PB constraint"):
        molp_to_simple_election(prob)
```

- [ ] **Step 2: Run** — `cd solvers && poetry run pytest tests/test_election_transform.py -q` → 3 PASS (characterization tests of existing behavior; if any fails, STOP — the fixture/transform understanding is wrong, investigate before proceeding).

- [ ] **Step 3: Commit** — `git add -A && git commit -m "T16: direct tests for molp_to_simple_election"`

---

### Task 3: `FeasibilityChecker` (warm mirror model)

**Files:**
- Modify: `solvers/src/muoblpsolvers/election_solver.py` (replace `is_feasible` body :44-76 with class + thin wrapper)
- Test: `solvers/tests/test_feasibility.py` (new)

**Interfaces:**
- Produces: `FeasibilityChecker(lp: MultiObjectiveLpProblem)` with method `is_feasible() -> bool` reading the lp's CURRENT `varValue`s (set via `setInitialValue`) each call; `ElectionSolver.is_feasible(lp)` static stays as one-shot wrapper (backward compat). Tasks 4-6 consume both.

- [ ] **Step 1: Write the failing tests**

```python
# solvers/tests/test_feasibility.py
# NOTE: `import pytest` is added in Task 5 (first use: parametrize) —
# pre-commit ruff strips unused imports.
from typing import Callable

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from muoblpsolvers.election_solver import ElectionSolver, FeasibilityChecker


def test_fast_path_no_lowerbound(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    checker = FeasibilityChecker(basic_pb_approval)
    variables = basic_pb_approval.variablesDict()
    # under budget: A(300k) fits in 1M
    variables["_A"].setInitialValue(1)
    assert checker.is_feasible() is True
    # over budget: A+B+C+D+E+F = 1.51M > 1M
    for variable in variables.values():
        variable.setInitialValue(1)
    assert checker.is_feasible() is False


def test_lowerbound_partial_selection_completable(
    pb_with_lb_factory: Callable[[str], MultiObjectiveLpProblem],
):
    problem = pb_with_lb_factory("APPROVAL")
    checker = FeasibilityChecker(problem)
    variables = problem.variablesDict()
    # nothing selected: GE bound on _E not yet met, but completable
    assert checker.is_feasible() is True
    # select everything except _E: budget left 1M-1.34M < 0 -> not completable
    for name, variable in variables.items():
        variable.setInitialValue(int(name != "_E"))
    assert checker.is_feasible() is False


def test_checker_reusable_across_checks(
    pb_with_lb_factory: Callable[[str], MultiObjectiveLpProblem],
):
    problem = pb_with_lb_factory("APPROVAL")
    checker = FeasibilityChecker(problem)
    variables = problem.variablesDict()
    assert checker.is_feasible() is True
    variables["_E"].setInitialValue(1)
    assert checker.is_feasible() is True  # pins must reset between calls
    variables["_E"].setInitialValue(0)
    assert checker.is_feasible() is True


def test_static_wrapper_kept(
    pb_with_lb_factory: Callable[[str], MultiObjectiveLpProblem],
):
    problem = pb_with_lb_factory("APPROVAL")
    assert ElectionSolver.is_feasible(problem) is True
```

Note: `lp.valid()` needs every varValue set — `pb_with_lb_factory` sets all initial values to 0, `basic_pb_approval` too, so the fast-path asserts are well-defined.

- [ ] **Step 2: Verify failure** — `poetry run pytest tests/test_feasibility.py -q` → `ImportError: cannot import name 'FeasibilityChecker'`.

- [ ] **Step 3: Implement.** In `election_solver.py`, replace the whole `is_feasible` staticmethod (lines 44-76) with this wrapper inside `ElectionSolver`:

```python
    @staticmethod
    def is_feasible(lp: MultiObjectiveLpProblem) -> bool:
        return FeasibilityChecker(lp).is_feasible()
```

and add at module level (below the `ElectionSolver` class, above `validate_pb_constraint`):

```python
class FeasibilityChecker:
    """Completion-feasibility probe for partial 0/1 selections.

    lp.valid() checks only the current point: under a GE lower-bound
    constraint every partial selection fails even when completable. With a
    GE constraint present we instead solve a CBC feasibility MIP (selected
    vars pinned to 1, rest free). The mirror model is built once per
    checker; each check only flips the pins.
    """

    def __init__(self, lp: MultiObjectiveLpProblem) -> None:
        self._lp = lp
        self._has_lowerbound = any(
            c.sense == LpConstraintGE for c in lp.constraints.values()
        )
        if not self._has_lowerbound:
            return
        candidates = [
            v.name for v in lp.variables() if v.name != "__dummy"
        ]
        self._mirror_vars = {
            name: LpVariable(name, cat="Binary") for name in candidates
        }
        self._prob = LpProblem("feasibility", LpMinimize)
        self._prob += 0
        for name, constraint in lp.constraints.items():
            items = [
                (self._mirror_vars[v.name], coef)
                for v, coef in constraint.items()
                if v.name in self._mirror_vars
            ]
            if items:
                self._prob += LpConstraint(
                    lpSum(coef * v for v, coef in items),
                    sense=constraint.sense,
                    rhs=-constraint.constant,
                    name=name,
                )

    def is_feasible(self) -> bool:
        if not self._has_lowerbound:
            return self._lp.valid()
        pinned = [
            name
            for name, variable in self._lp.variablesDict().items()
            if name in self._mirror_vars and variable.varValue == 1
        ]
        for name in pinned:
            self._mirror_vars[name].lowBound = 1
        status = self._prob.solve(PULP_CBC_CMD(msg=False))
        for name in pinned:
            self._mirror_vars[name].lowBound = 0
        return status == LpStatusOptimal
```

All names used (`LpConstraintGE`, `LpProblem`, `LpMinimize`, `LpConstraint`, `LpVariable`, `lpSum`, `PULP_CBC_CMD`, `LpStatusOptimal`) are already in the file's pulp import. The aux CBC stays `msg=False` regardless of solver `msg` (probe noise, per T14 decision).

- [ ] **Step 4: Run** — `tests/test_feasibility.py` 5 PASS; full suite: `poetry run pytest -q` — `test_greedy.py` LB tests are the behavioral regression guard for the rewrite.

- [ ] **Step 5: Commit** — `git commit -am "T16: FeasibilityChecker with warm mirror model"`

---

### Task 4: Greedy builds one checker per solve

**Files:**
- Modify: `solvers/src/muoblpsolvers/greedy_solver.py` (selection loop; post-T14 shape)

- [ ] **Step 1: Implement** (existing `test_greedy.py` LB tests are the spec — no new test). In `_solve_election`, before the selection loop add:

```python
        checker = FeasibilityChecker(lp)
```

and in the loop replace `if not self.is_feasible(lp):` with `if not checker.is_feasible():`. Import: `from muoblpsolvers.election_solver import Election, ElectionSolver, FeasibilityChecker`.

- [ ] **Step 2: Run** — `poetry run pytest tests/test_greedy.py tests/test_feasibility.py -q` → green (LB tests exercise the CBC branch through the new path).

- [ ] **Step 3: Commit** — `git commit -am "T16: greedy reuses one FeasibilityChecker per solve"`

---

### Task 5: Phragmen — `lp.valid()` → checker

**Files:**
- Modify: `solvers/src/muoblpsolvers/phragmen.py` (call sites at :120 and :364 pre-T14 numbering; also fix the `-> set[str]` annotation on `phragmen_cardinal` — it returns a list; closes the T03-inventory pyright note)
- Test: `solvers/tests/test_feasibility.py`

- [ ] **Step 1: Write the failing test** (append; add `import pytest` to the file header — first used here). Old behavior under GE: `lp.valid()` is False for every partial selection → the pre-filter drops ALL candidates → empty selection that VIOLATES the lower bound. New behavior: normal run, `_E` (forced by `lb_edu`) ends up selected.

```python
from pulp import LpStatusOptimal

from muoblpsolvers import PhragmenSolver

PB_COSTS = {
    "_A": 300000, "_B": 400000, "_C": 300000,
    "_D": 240000, "_E": 170000, "_F": 100000,
}


@pytest.mark.parametrize("utility_type", ["APPROVAL", "COST"])
def test_phragmen_respects_lowerbound(
    pb_with_lb_factory: Callable[[str], MultiObjectiveLpProblem],
    utility_type: str,
):
    problem = pb_with_lb_factory(utility_type)
    problem.solve(PhragmenSolver(msg=False))
    assert problem.status == LpStatusOptimal
    selected = {
        v.name for v in problem.variables() if v.value() == 1.0
    }
    assert "_E" in selected
    assert sum(PB_COSTS[name] for name in selected) <= 1000000
```

- [ ] **Step 2: Verify failure** — `-k phragmen_respects` → FAIL (`_E` not in empty selection).

- [ ] **Step 3: Implement.** In `phragmen_cardinal`, first line of the body:

```python
    checker = FeasibilityChecker(lp)
```

Replace both `if not lp.valid():` occurrences (pre-filter loop and the post-selection prune loop) with `if not checker.is_feasible():`. Fix annotation: `) -> list[str]:`. Import: add `FeasibilityChecker` to the existing `from muoblpsolvers.election_solver import ...` line.

If the `_E` assert unexpectedly still fails: debug rather than force — print the rank evolution; the expected mechanics are that candidates whose selection leaves `< cost(_E)` budget get pruned by the completion check, so `_E` survives to be ranked. Do NOT weaken the test to "selection non-empty" without understanding why.

- [ ] **Step 4: Run** — `-k phragmen` (both this file and `test_time_verbosity.py` T14 tests) green; full suite green.

- [ ] **Step 5: Commit** — `git commit -am "T16: phragmen feasibility via checker (GE-aware)"`

---

### Task 6: MES-Exponential — `lp.valid()` → checker

**Files:**
- Modify: `solvers/src/muoblpsolvers/mes/mes_exponential.py` (call site :120 pre-T14 numbering, inside `equal_shares_exponential`)
- Test: `solvers/tests/test_feasibility.py`

- [ ] **Step 1: Write the failing test** (append)

```python
from muoblpsolvers import MethodOfEqualSharesExponentialSolver


@pytest.mark.parametrize("utility_type", ["APPROVAL", "COST"])
def test_mes_exponential_respects_lowerbound(
    pb_with_lb_factory: Callable[[str], MultiObjectiveLpProblem],
    utility_type: str,
):
    problem = pb_with_lb_factory(utility_type)
    problem.solve(
        MethodOfEqualSharesExponentialSolver(msg=False, budget_init=1)
    )
    assert problem.status == LpStatusOptimal
    selected = {
        v.name for v in problem.variables() if v.value() == 1.0
    }
    assert "_E" in selected
    assert sum(PB_COSTS[name] for name in selected) <= 1000000
```

- [ ] **Step 2: Verify failure** — under `lp.valid()` the GE constraint makes every tentative selection invalid → all candidates get dropped → `_E` missing. (If it fails differently, record actual old behavior in the PR.)

- [ ] **Step 3: Implement.** In `equal_shares_exponential`, first line of the body:

```python
    checker = FeasibilityChecker(lp)
```

Replace `if not lp.valid():` with `if not checker.is_feasible():`. Import: `from muoblpsolvers.election_solver import FeasibilityChecker, validate_election_program` (extend existing import).

Same debug-don't-weaken instruction as Task 5 if `_E` isn't selected.

- [ ] **Step 4: Run** — `tests/test_feasibility.py` green; full suite green.

- [ ] **Step 5: Commit** — `git commit -am "T16: mes-exponential feasibility via checker (GE-aware)"`

---

### Task 7: Benchmark + full verify + PR

**Files:**
- Create (scratch, NOT committed): `bench_feasibility.py` in the session scratchpad

- [ ] **Step 1: Bench script**

```python
# bench_feasibility.py — run once on feat/roadmap-base-branch, once on this
# branch (same venv), compare wall times; paste both numbers into the PR.
import random
import time

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpsolvers import GreedySolver
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintGE,
    LpConstraintLE,
    LpVariable,
    lpSum,
)

random.seed(7)
N_CANDIDATES, N_VOTERS, BUDGET = 40, 80, 12000
prob = MultiObjectiveLpProblem("bench")
names = [f"c{i}" for i in range(N_CANDIDATES)]
costs = {n: random.randint(300, 1200) for n in names}
variables = LpVariable.dicts("", names, cat="Binary")
for v in variables.values():
    v.setInitialValue(0)
objectives = [
    LpAffineExpression(
        [(variables[n], 1) for n in random.sample(names, k=6)],
        name=f"v{i}",
    )
    for i in range(N_VOTERS)
]
prob.addVariables(variables.values())
prob.set_objectives(objectives)
prob.addConstraint(LpConstraint(
    e=lpSum(variables[n] * costs[n] for n in names),
    sense=LpConstraintLE, rhs=BUDGET, name="pb",
))
prob.addConstraint(LpConstraint(
    e=variables[names[0]] * costs[names[0]],
    sense=LpConstraintGE, rhs=costs[names[0]], name="lb_0",
))
t0 = time.perf_counter()
prob.solve(GreedySolver(msg=False))
print(f"greedy+LB wall: {time.perf_counter() - t0:.2f}s")
```

Run: `git stash && git checkout feat/roadmap-base-branch && cd solvers && poetry run python <scratchpad>/bench_feasibility.py` → record; `git checkout feat/t16-dedupe-feasibility && poetry run python <scratchpad>/bench_feasibility.py` → record. Expected: branch faster (mirror model built 1× instead of 40×; CBC subprocess count unchanged — say so honestly in the PR; if the delta is negligible, report that and let the correctness unification carry the ticket).

- [ ] **Step 2: Full verify** — `cd solvers && poetry run pytest -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright` (pyright: the `phragmen.py:398` return-type note from the T03 inventory should now be resolvable — if an inline ignore for it exists, remove it); `cd ../experiments && poetry run pytest -q && poetry run pytest -m e2e -q` (golden IDENTICAL); `cd ../core && poetry run pytest -q`.

- [ ] **Step 3: Grep AC** — `grep -rn "lp.valid()" solvers/src/` → only the fast path inside `FeasibilityChecker.is_feasible` (via `self._lp.valid()`); `grep -rn "molp_to_simple_election" experiments/src/` → empty.

- [ ] **Step 4: Commit + PR** — push, PR → `feat/roadmap-base-branch`, title `T16: dedupe transform + unify feasibility`; body: bench numbers, GE-correctness behavior change for Phragmen/MES-Exponential (previously empty/wrong selections under GE — no production configs used GE with these solvers), archived-file note. Update ROADMAP + leftovers (note `mes/common.py::get_total_budget_constraint` duplicate-check redundancy was NOT collapsed — it has standalone callers; T13 leftover stands).

## Unresolved questions

None.
