# T14 Time & Verbosity Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove manual `time.time()` tracking (pulp `solutionTime` covers it), honor `timeLimit` in pure-python solver loops (abort → `LpStatusNotSolved`), gate all solver output behind `self.msg`. GH #26, #27, #32.

**Architecture:** pulp `LpProblem.solve` already wraps `actualSolve` with `startClock`/`stopClock` → `problem.solutionTime` (wall clock, solve-only). Pure-py loops get a `time.monotonic()` deadline threaded as param into free functions; caller re-checks deadline after return to decide status (free fn just breaks + returns partial `selected`). Binding-backed solvers can't be interrupted → **D8 decision (user-confirmed): warn + ignore** via `warnings.warn`. All logger calls get `if msg:` guards; 2 stray `print()`s become gated logger calls.

**Tech Stack:** pulp 3.3.2 (`LpSolver.__init__` stores `self.msg`/`self.timeLimit` as plain attrs; kwargs with value `None` are dropped from `optionsDict` — attrs unaffected), pytest capsys/caplog (first use in solvers/tests).

## Global Constraints

- Branch `feat/t14-time-verbosity` off `feat/roadmap-base-branch`; PR targets `feat/roadmap-base-branch`.
- Repo GREEN after ticket: `cd solvers && poetry run pytest`, `cd experiments && poetry run pytest` (incl. `-m e2e` golden — **NO regen**; meta `time` field is deleted by `golden_utils.py:40,50` normalization, so switching its source is invisible to goldens), ruff, pyright.
- Abort status = `LpStatusNotSolved` (user-confirmed). Timeout semantics: conservative — if deadline passed when the algorithm returns, status is NotSolved even if it happened to finish.
- D8 (user-confirmed): binding-backed STV/ExpandingApprovals/SolidCoalitionRefinement/MES-Add1/MES-Utility warn+ignore `timeLimit`. MES-Constrains honors it coarsely (python loop, checked per iteration — no warn).
- MES-Exponential in tests always needs `budget_init=1` (pulp drops `None` kwargs).
- AC greps at end: no `time.time()` and no `print(` in `solvers/src`. `time.monotonic()` is allowed (deadline checks).
- EA/STV/SCR cannot solve the standard `basic_pb_approval` fixture (C++ requires unit costs — see T17); their msg-silence solve coverage lands in T17. Here they get: timing removal, `if self.msg:` gates, D8 warn + a warn test that needs no solve (warn fires before validation raises).

---

### Task 1: `set_solved` status parameter

**Files:**
- Modify: `solvers/src/muoblpsolvers/utils.py:12-15`
- Test: `solvers/tests/test_time_verbosity.py` (new file)

**Interfaces:**
- Produces: `set_solved(lp: MultiObjectiveLpProblem, selected: list[str], status: int = LpStatusOptimal) -> None` — every later task's abort path calls it with `LpStatusNotSolved`.

- [ ] **Step 1: Write the failing test**

```python
# solvers/tests/test_time_verbosity.py
# NOTE: imports are added task-by-task as first used — pre-commit ruff
# (F401 autofix) strips not-yet-used imports from intermediate commits.
import logging

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpStatusNotSolved, LpStatusOptimal

from muoblpsolvers.utils import set_solved


def test_set_solved_default_status(basic_pb_approval: MultiObjectiveLpProblem):
    set_solved(basic_pb_approval, ["_A"])
    assert basic_pb_approval.status == LpStatusOptimal
    assert basic_pb_approval.variablesDict()["_A"].value() == 1


def test_set_solved_custom_status(basic_pb_approval: MultiObjectiveLpProblem):
    set_solved(basic_pb_approval, [], LpStatusNotSolved)
    assert basic_pb_approval.status == LpStatusNotSolved
    assert all(v.value() == 0 for v in basic_pb_approval.variables())
```

- [ ] **Step 2: Run to verify failure**

Run: `cd solvers && poetry run pytest tests/test_time_verbosity.py -q`
Expected: FAIL — `TypeError: set_solved() takes 2 positional arguments but 3 were given`

- [ ] **Step 3: Implement**

Replace `solvers/src/muoblpsolvers/utils.py:12-15` with:

```python
def set_solved(
    lp: MultiObjectiveLpProblem,
    selected: list[str],
    status: int = LpStatusOptimal,
) -> None:
    vals = {x.name: int(x.name in selected) for x in lp.variables()}
    lp.assignStatus(status)
    lp.assignVarsVals(vals)
```

- [ ] **Step 4: Run tests**

Run: `cd solvers && poetry run pytest tests/test_time_verbosity.py -q`
Expected: 2 PASS. Then full: `poetry run pytest` — all pass (default arg keeps callers working).

- [ ] **Step 5: Commit** — `git add -A && git commit -m "T14: set_solved status param"`

---

### Task 2: `prepare_mes_parameters` — logger + msg gate

**Files:**
- Modify: `solvers/src/muoblpsolvers/mes/common.py` (no logger exists; `print` at line 83)
- Test: `solvers/tests/test_time_verbosity.py`

**Interfaces:**
- Produces: `prepare_mes_parameters(lp, msg: bool = True)` — Tasks 5/6 and the binding solvers (mes_add1/mes_utility) pass `self.msg`.

- [ ] **Step 1: Write the failing test** (append to `test_time_verbosity.py`)

```python
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintLE,
    LpVariable,
    lpSum,
)

from muoblpsolvers.mes.common import prepare_mes_parameters


def _pb_with_zero_vote_project() -> MultiObjectiveLpProblem:
    prob = MultiObjectiveLpProblem("pb_zero_vote")
    variables = LpVariable.dicts("", ["A", "Z"], cat="Binary")
    for variable in variables.values():
        variable.setInitialValue(0)
    prob.addVariables(variables.values())
    prob.set_objectives(
        [LpAffineExpression([(variables["A"], 1)], name="v1")]
    )
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
```

- [ ] **Step 2: Run to verify failure**

Run: `cd solvers && poetry run pytest tests/test_time_verbosity.py -k prepare -q`
Expected: FAIL — `TypeError: prepare_mes_parameters() got an unexpected keyword argument 'msg'`

- [ ] **Step 3: Implement**

In `solvers/src/muoblpsolvers/mes/common.py`: add after imports (line 12):

```python
logger = logging.getLogger(__name__)
```

(and `import logging` at line 1). Change signature (line 35):

```python
def prepare_mes_parameters(
    lp: MultiObjectiveLpProblem,
    msg: bool = True,
) -> tuple[
```

Replace the print at lines 82-85:

```python
    for project in no_vote_projects:
        if msg:
            logger.info("Removing project with zero votes %s", project)
        projects.remove(project)
        del costs[project]
```

- [ ] **Step 4: Run tests** — same command, 2 PASS; full solvers suite still green (default `msg=True`).

- [ ] **Step 5: Commit** — `git commit -am "T14: prepare_mes_parameters print -> gated logger"`

---

### Task 3: GreedySolver — timeLimit + msg

**Files:**
- Modify: `solvers/src/muoblpsolvers/greedy_solver.py`
- Test: `solvers/tests/test_time_verbosity.py`

**Interfaces:**
- Consumes: `set_solved(lp, selected, status)` from Task 1.

- [ ] **Step 1: Write failing tests** (append)

```python
from muoblpsolvers import GreedySolver


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
```

- [ ] **Step 2: Verify failure** — `poetry run pytest tests/test_time_verbosity.py -k greedy -q`. Expected: timelimit test FAILS (status is Optimal — limit ignored today); msg_false FAILS (SOLVER START/END records present).

- [ ] **Step 3: Implement** — rewrite `_solve_election` body (`greedy_solver.py:16-64`); `import time` stays (monotonic only):

```python
    def _solve_election(
        self,
        lp: MultiObjectiveLpProblem,
        election: Election,
        **kwargs,
    ):
        candidates = election["candidates"]
        voters = election["voters"]
        profile = election["profile"]

        if self.msg:
            logger.info(
                "SOLVER START",
                extra={"candidates": len(candidates), "voters": len(voters)},
            )

        total_utility: dict[CandidateId, float] = {}
        for candidate, votes in profile.items():
            total_utility[candidate] = sum(
                voters[v] * u for v, u in votes.items()
            )

        sorted_candidates = list(candidates.keys())
        sorted_candidates.sort(
            key=lambda candidate: (
                total_utility[candidate] / candidates[candidate]
            ),
            reverse=True,
        )
        sorted_candidates = [
            candidate
            for candidate in sorted_candidates
            if total_utility[candidate] > 0
        ]

        deadline = (
            time.monotonic() + self.timeLimit
            if self.timeLimit is not None
            else None
        )
        status = LpStatusOptimal
        selected: list[str] = []
        for candidate in sorted_candidates:
            if deadline is not None and time.monotonic() > deadline:
                status = LpStatusNotSolved
                break
            candidate_variable = lp.variablesDict()[candidate]
            candidate_variable.setInitialValue(1)
            if not self.is_feasible(lp):
                candidate_variable.setInitialValue(0)
                if self.msg:
                    logger.debug("removed %s: infeasible", candidate)
            else:
                selected.append(candidate)
                if self.msg:
                    logger.debug("elected %s", candidate)

        if self.msg:
            logger.info("SOLVER END", extra={"selected": len(selected)})

        set_solved(lp, selected, status)
        return lp.status
```

Add `LpStatusNotSolved, LpStatusOptimal` import: `from pulp import LpStatusNotSolved, LpStatusOptimal` (new line after existing imports). NOTE: `total_utility[candidate]` stays as-is here — the zero-vote KeyError fix is T17's.

- [ ] **Step 4: Run** — `poetry run pytest tests/test_time_verbosity.py -k greedy -q` → 3 PASS; then `poetry run pytest -q` (test_greedy.py regression must stay green).

- [ ] **Step 5: Commit** — `git commit -am "T14: greedy timeLimit + msg gating"`

---

### Task 4: PhragmenSolver — deadline param + msg

**Files:**
- Modify: `solvers/src/muoblpsolvers/phragmen.py` (`_solve_election` :43-68, `phragmen_cardinal` signature :104-111, outer loop :158)
- Test: `solvers/tests/test_time_verbosity.py`

**Interfaces:**
- Produces: `phragmen_cardinal(lp, election, increasing_scalings=False, kappa=1.0, bos_version=False, eps=1e-6, deadline: float | None = None)` — returns partial rank on deadline hit.

- [ ] **Step 1: Failing tests** (append; same 3-test pattern as Task 3 with `PhragmenSolver`)

```python
from muoblpsolvers import PhragmenSolver


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
```

- [ ] **Step 2: Verify failure** — `-k phragmen` → both FAIL.

- [ ] **Step 3: Implement.** `_solve_election` becomes:

```python
    def _solve_election(
        self,
        lp: MultiObjectiveLpProblem,
        election: Election,
        **kwargs,
    ):
        if self.msg:
            logger.info(
                "SOLVER START",
                extra={"options": self.optionsDict, "instance": lp.name},
            )
        deadline = (
            time.monotonic() + self.timeLimit
            if self.timeLimit is not None
            else None
        )
        selected = phragmen_cardinal(
            lp,
            election,
            increasing_scalings=self.optionsDict["increasing_scalings"],
            kappa=self.optionsDict["kappa"],
            bos_version=self.optionsDict["bos_version"],
            eps=self.optionsDict["eps"],
            deadline=deadline,
        )
        status = LpStatusOptimal
        if deadline is not None and time.monotonic() > deadline:
            status = LpStatusNotSolved
        if self.msg:
            logger.info(
                "SOLVER END",
                extra={"instance": lp.name, "selected": len(selected)},
            )

        set_solved(lp, selected, status)
        return lp.status
```

`phragmen_cardinal` signature gains `deadline=None` (after `eps=1e-6`), and the outer loop head (`while remaining:` line 158) becomes:

```python
    while remaining:
        if deadline is not None and time.monotonic() > deadline:
            break
```

Imports: add `from pulp import LpStatusNotSolved, LpStatusOptimal, LpVariable` (extend existing pulp import line 6). Known limitation, note in PR: inner `while not select_candidate:` doubling loop is not deadline-checked — abort granularity is one selection round.

- [ ] **Step 4: Run** — `-k phragmen` PASS; full suite green.

- [ ] **Step 5: Commit** — `git commit -am "T14: phragmen timeLimit + msg gating"`

---

### Task 5: MES-Exponential — deadline + msg into free fns

**Files:**
- Modify: `solvers/src/muoblpsolvers/mes/mes_exponential.py` (`break_ties` :16-31, `equal_shares_exponential` :34-133 incl. `print(i)` :57, `actualSolve` :163-194)
- Test: `solvers/tests/test_time_verbosity.py`

**Interfaces:**
- Consumes: `prepare_mes_parameters(lp, msg=...)` (Task 2).
- Produces: `equal_shares_exponential(voters, projects, cost, approvals_utilities, total_utility, lp, budget_init, deadline: float | None = None, msg: bool = True)`; `break_ties(cost, total_utility, choices, msg: bool = True)`.

- [ ] **Step 1: Failing tests** (append; MES-Exponential is pure python, no skip needed)

```python
from muoblpsolvers import MethodOfEqualSharesExponentialSolver


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
```

- [ ] **Step 2: Verify failure** — `-k exponential` → FAIL (Optimal; records present).

- [ ] **Step 3: Implement.**
  - `break_ties`: add `msg: bool = True` param; wrap the `logger.warning(...)` (lines 26-30) in `if msg:` (fix the "Tie-breakign" typo → "Tie-breaking" while touching it).
  - `equal_shares_exponential`: add `deadline: float | None = None, msg: bool = True` params. Outer loop head (line 50):

```python
    while len(remaining) and max(remaining.values()) > 0:
        if deadline is not None and time.monotonic() > deadline:
            break
```

  Inner loop head (line 60):

```python
        while len(remaining):
            if deadline is not None and time.monotonic() > deadline:
                break
```

  Replace `print(i)` in the OverflowError branch (line 57):

```python
        except OverflowError:
            if msg:
                logger.warning(
                    "budget overflow after %d doublings, stopping", i
                )
            break
```

  Tie-break call (line 110): `selected = break_ties(cost, total_utility, best, msg)`.
  - `actualSolve`: drop `start_time`/both timing lines; gate SOLVER START/END with `if self.msg:` (END without `time` extra); `prepare_mes_parameters(lp, msg=self.msg)`; compute `deadline` (same pattern as Task 4) before the call, pass `deadline=deadline, msg=self.msg`; after the call the same 2-line status re-check, `set_solved(lp, selected, status)`. Imports: add `LpStatusNotSolved, LpStatusOptimal` to the pulp import.

- [ ] **Step 4: Run** — `-k exponential` PASS; full suite green.

- [ ] **Step 5: Commit** — `git commit -am "T14: mes-exponential timeLimit + msg gating"`

---

### Task 6: MES-Constrains — deadline in iteration loop + msg

**Files:**
- Modify: `solvers/src/muoblpsolvers/mes/mes_constrains.py` (`actualSolve` :77-150)
- Test: `solvers/tests/test_time_verbosity.py`

- [ ] **Step 1: Failing tests** (append; binding-backed → skip guard; this task first uses `pytest` — add `import pytest` to the file header)

```python
import pytest

from muoblpsolvers import MethodOfEqualSharesConstrainsSolver


def test_mes_constrains_timelimit_aborts_not_solved(
    basic_pb_approval: MultiObjectiveLpProblem,
):
    solver = MethodOfEqualSharesConstrainsSolver(msg=False, timeLimit=1e-9)
    if not solver.available():
        pytest.skip("muoblpbindings not installed")
    basic_pb_approval.solve(solver)
    assert basic_pb_approval.status == LpStatusNotSolved
    assert all(v.value() == 0 for v in basic_pb_approval.variables())
```

- [ ] **Step 2: Verify failure** — `-k constrains` → FAIL.

- [ ] **Step 3: Implement** in `actualSolve`:
  - Delete `start_time = time.time()` (lines 81 and 99) and the timing debug (line 109 → `logger.debug("FINISHED MES iteration %d", iteration)` gated); delete `time` from the SOLVER END extra.
  - Gate every `logger.*` call (lines 82, 109, 116, 121, 138, 147) with `if self.msg:`.
  - `prepare_mes_parameters(lp, msg=self.msg)`.
  - Before the loop:

```python
        deadline = (
            time.monotonic() + self.timeLimit
            if self.timeLimit is not None
            else None
        )
        status = LpStatusOptimal
        selected: list[str] = []
        iteration = 0
        while iteration < self.optionsDict["max_iterations"]:
            if deadline is not None and time.monotonic() > deadline:
                status = LpStatusNotSolved
                break
```

  (the `selected: list[str] = []` init is REQUIRED — abort before iteration 1 would otherwise hit an unbound local). End: `set_solved(lp, selected, status)`. Imports: add `LpStatusNotSolved, LpStatusOptimal` to the pulp import (line 6). Granularity note for PR: the C++ `equal_shares_utils` call itself is not interruptible — abort happens between iterations (that IS the D8-compatible coarse honoring; no warn for this solver).

- [ ] **Step 4: Run** — `-k constrains` PASS; full suite green.

- [ ] **Step 5: Commit** — `git commit -am "T14: mes-constrains timeLimit + msg gating"`

---

### Task 7: Binding-backed five — D8 warn, drop timing, gate logs

**Files:**
- Modify: `solvers/src/muoblpsolvers/single_transferable_vote.py`, `solid_coalition_refinement.py`, `expanding_approvals.py`, `mes/mes_add1.py`, `mes/mes_utility.py`
- Test: `solvers/tests/test_time_verbosity.py`

- [ ] **Step 1: Failing test** (append; needs NO solve and NO bindings: warn fires before validation raises on a no-objectives program; add `PulpSolverError` to the file's pulp import)

```python
from muoblpsolvers import (
    ExpandingApprovals,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesUtilitySolver,
    SingleTransferableVote,
    SolidCoalitionRefinement,
)

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
```

- [ ] **Step 2: Verify failure** — `-k warns` → FAIL (`DID NOT WARN`).

- [ ] **Step 3: Implement.** Same edit in all 5 files — STV shown in full, others follow identically (add1/utility keep their `prepare_mes_parameters` call, now `(lp, msg=self.msg)`):

```python
import logging
import warnings

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpSolver

from muoblpsolvers.election_solver import validate_election_program
from muoblpsolvers.utils import bindings_available, set_solved

logger = logging.getLogger(__name__)


class SingleTransferableVote(LpSolver):
    name = "SingleTransferableVote"

    def available(self) -> bool:
        return bindings_available()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs) -> int:
        if self.timeLimit is not None:
            warnings.warn(
                f"{self.name} does not support timeLimit; "
                "solving without limit"
            )
        validate_election_program(lp)
        from muoblpbindings import single_transferable_vote

        if self.msg:
            logger.info("SOLVER START")
        selected = single_transferable_vote(lp)
        if self.msg:
            logger.info("SOLVER END")

        set_solved(lp, selected)
        return lp.status
```

(`import time` removed from all 5; the warn block is the FIRST statement of `actualSolve` in each.)

- [ ] **Step 4: Run** — `-k warns` 5 PASS; full suite green (test_mes_add1 + test_mes_base unaffected).

- [ ] **Step 5: Commit** — `git commit -am "T14: binding solvers warn on timeLimit (D8), drop manual timing"`

---

### Task 8: SummedObjectives — forward msg + timeLimit to backend

**Files:**
- Modify: `solvers/src/muoblpsolvers/summed_objectives_lp_solver.py:44-48`
- Test: `solvers/tests/test_time_verbosity.py`

- [ ] **Step 1: Failing test** (append)

```python
from muoblpsolvers import SummedObjectivesLpSolver


def test_summed_msg_false_silent(
    basic_pb_approval: MultiObjectiveLpProblem, capsys
):
    basic_pb_approval.solve(
        SummedObjectivesLpSolver(msg=False, timeLimit=30)
    )
    assert basic_pb_approval.status == LpStatusOptimal
    assert capsys.readouterr().out == ""
```

- [ ] **Step 2: Verify current state** — this may already pass (CBC msg hardcoded False); the change under test is forwarding. Run it, then:

- [ ] **Step 3: Implement**

```python
        solver_cmd = (
            GUROBI_CMD(msg=self.msg, timeLimit=self.timeLimit)
            if self.optionsDict["use_gurobi"]
            else PULP_CBC_CMD(msg=self.msg, timeLimit=self.timeLimit)
        )
```

CBC/Gurobi enforce timeLimit natively — this makes `SummedObjectivesLpSolver` the one solver with a REAL timeLimit.

- [ ] **Step 4: Run** — test PASSES; full suite green.

- [ ] **Step 5: Commit** — `git commit -am "T14: summed forwards msg+timeLimit to CBC/Gurobi"`

---

### Task 9: experiments meta — `problem.solutionTime`

**Files:**
- Modify: `experiments/src/problemRunner.py` (lines 2, 32, 48, 51)

- [ ] **Step 1: Implement** (no new unit test — the e2e golden is the regression: `time` is normalized away, everything else must be byte-identical)
  - Delete line 32 `start_time = time.time()` and line 48 `end_time = time.time()`.
  - Line 51: `"time": problem.solutionTime,`
  - Line 2 `import time` → delete (datetime import at line 3 stays — used for the problem-id filename).
  - Semantic note for PR: meta `time` now measures ONLY `actualSolve` (pulp start/stopClock around it), no longer load+transform+solve. `RunnerResult.time: float` type unchanged (`helpers/runners/model.py:76`).

- [ ] **Step 2: Verify** — `cd experiments && poetry run pytest -q` (75 tests incl. e2e golden, NO regen) and `poetry run pytest -m e2e -q`.

- [ ] **Step 3: Commit** — `git commit -am "T14: meta time from pulp solutionTime"`

---

### Task 10: Cross-solver silence sweep + AC greps

**Files:**
- Test: `solvers/tests/test_time_verbosity.py`

- [ ] **Step 1: Parametrized silence test** (append; the 7 solvers that can solve the standard fixture — EA/STV/SCR need T17's ordinal fixture)

```python
STANDARD_SOLVERS: list[tuple[type, dict]] = [
    (GreedySolver, {}),
    (PhragmenSolver, {}),
    (MethodOfEqualSharesAdd1Solver, {}),
    (MethodOfEqualSharesUtilitySolver, {}),
    (MethodOfEqualSharesConstrainsSolver, {}),
    (MethodOfEqualSharesExponentialSolver, {"budget_init": 1}),
    (SummedObjectivesLpSolver, {}),
]


@pytest.mark.parametrize("solver_class, kwargs", STANDARD_SOLVERS)
def test_msg_false_zero_output(
    solver_class,
    kwargs,
    basic_pb_approval: MultiObjectiveLpProblem,
    capsys,
    caplog,
):
    solver = solver_class(msg=False, **kwargs)
    if not solver.available():
        pytest.skip(f"{solver_class.__name__} unavailable (needs bindings)")
    with caplog.at_level(logging.DEBUG):
        basic_pb_approval.solve(solver)
    assert capsys.readouterr().out == ""
    assert [
        r for r in caplog.records if r.name.startswith("muoblpsolvers")
    ] == []
```

- [ ] **Step 2: Run full suite** — `cd solvers && poetry run pytest -q` → all green.

- [ ] **Step 3: AC greps**

Run: `grep -rn "time.time()" solvers/src/` → empty. `grep -rn "print(" solvers/src/` → empty.

- [ ] **Step 4: Full verify** — `cd solvers && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright`; `cd ../experiments && poetry run pytest -q && poetry run pyright`; `cd ../core && poetry run pytest -q`.

- [ ] **Step 5: Commit + PR** — `git commit -am "T14: msg silence sweep"`; push branch, PR → `feat/roadmap-base-branch`, title `T14: time & verbosity contract`, body lists D8 resolution (warn+ignore), abort status (NotSolved), meta-time semantic change. Update ROADMAP checkbox+PR link and `plans/leftovers.md` in the PR.

## Unresolved questions

None (D8, abort status user-confirmed).
