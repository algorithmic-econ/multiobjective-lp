# P2 Verify — Phase 2 Solver-Contract Judge Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans, single session — verification is sequential, findings must accumulate in one context (subagent-per-task NOT recommended). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently verify Phase 2 (T10–T18) complete + green on `feat/roadmap-base-branch`; re-check every ticket AC verbatim; adjudicate leftovers; record `P2 judge verdict` in `plans/leftovers.md` with GO/NO-GO for P3.

**Architecture:** Judge session per P1 precedent (leftovers.md "P1 judge verdict"): independent green matrix + AC re-verification + verdict, bookkeeping-only commit to base. Every check = exact command + expected output. Any failing check → finding: **BLOCKING** (contract/AC broken → NO-GO, file fix ticket) or **NON-BLOCKING** (cosmetic/deferred → leftovers note). Nothing gets fixed in-session.

**Tech Stack:** poetry venvs per subproject, pytest, ruff, pyright, `gh` CLI, scratch python scripts in session scratchpad.

## Global Constraints

- Run ON `feat/roadmap-base-branch` directly (no feature branch), AFTER T14–T18 merged.
- **Verification-only (user-confirmed):** NO src edits, NO golden regen, no fixes — findings → tickets/leftovers. Only allowed edits: ROADMAP checkbox/PR-link reconcile + leftovers.md verdict; single `docs: P2 judge verdict — ...` commit.
- Scratch scripts under session scratchpad, never committed.
- Test counts RECORDED, not asserted (drift across tickets); pass/fail + greps are the assertions.
- Fresh solvers venv (user-confirmed, P2 touched deps/packaging) needs macOS broken-CLT workaround: `export SDKROOT=$(xcrun --show-sdk-path); export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"`.
- Sample smoke needs `rm -rf sample-experiment/results/*` first + venv python on PATH (T10 leftover).
- Exact names below (test files, `budget_init`) frozen from T14–T18 plans — if merged tree differs, re-derive by grep, judge substance not spelling.

---

### Task 1: Preflight — branch, merges, bookkeeping

- [ ] **Step 1:** `git checkout feat/roadmap-base-branch && git pull` → up to date, clean tree.
- [ ] **Step 2:** `git log --oneline -25` → merge/squash commits for T10–T18 all present (T10–T13 already: #46–#49).
- [ ] **Step 3:** ROADMAP: T10–T18 all `[x]` with PR links (T07/T08 precedent: checkboxes get missed). Stale → note for verdict-commit reconcile (Task 9).
- [ ] **Step 4:** Re-read `plans/leftovers.md` entries T10 onward — build the adjudication checklist for Task 9.

### Task 2: Full green matrix (fresh solvers venv)

- [ ] **Step 1: core** — `cd core && poetry install && poetry run pytest -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright` → all pass, pyright 0. Record count.
- [ ] **Step 2: solvers FRESH venv** (lock/dep-drift catch):

```bash
export SDKROOT=$(xcrun --show-sdk-path)
export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"
cd solvers && poetry env remove --all; poetry env use /opt/homebrew/bin/python3.13 && poetry install
poetry run python -c "import muoblpbindings; print('bindings ok')"
poetry run pytest -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright
```

Expected: bindings builds from source, `bindings ok`, all tests pass (≥51 post-T13; record actual), pyright 0.
- [ ] **Step 3: experiments** — `cd experiments && poetry install && poetry run pytest -q && poetry run pytest -m e2e -q && poetry run pytest -m e2e -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright` → all pass; e2e ×2 identical (determinism), NO regen; pyright 0.

### Task 3: Constructor + serialization + registration contract (T10/T15)

- [ ] **Step 1:** Write scratchpad `verify_contract.py`:

```python
# verify_contract.py — T10 AC (unified ctor, options in optionsDict) +
# T15 AC (pulp registry) in one sweep
import pulp
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

ALL = [
    ExpandingApprovals, GreedySolver, MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver, MethodOfEqualSharesExponentialSolver,
    MethodOfEqualSharesUtilitySolver, PhragmenSolver, SingleTransferableVote,
    SolidCoalitionRefinement, SummedObjectivesLpSolver,
]

for cls in ALL:
    s = cls(msg=False, timeLimit=10)                       # T10 AC literal
    assert s.msg is False and s.timeLimit == 10, cls.__name__
    r = pulp.getSolverFromDict(s.toDict())                 # options serialize
    assert isinstance(r, cls), cls.__name__
    assert r.msg is False and r.timeLimit == 10, cls.__name__
    g = pulp.getSolver(cls.name, msg=False)                # T15 AC
    assert isinstance(g, cls), cls.name
assert {c.name for c in ALL} <= set(pulp.listSolvers())
print("T10/T15 contract OK: 10/10")
```

- [ ] **Step 2:** `cd solvers && poetry run python <scratchpad>/verify_contract.py` → `T10/T15 contract OK: 10/10`.
- [ ] **Step 3:** Grep AC — `grep -rn "solver_options" solvers/src/` → empty (custom positional param gone; experiments-side config field name is allowed and out of scope).

### Task 4: Bindings independence (T11)

- [ ] **Step 1:** Write scratchpad `verify_no_bindings.py`:

```python
# verify_no_bindings.py — T11 AC without bindings installed (simulated)
import sys
sys.modules["muoblpbindings"] = None  # import raises AND find_spec -> None
import muoblpsolvers  # must NOT raise
from muoblpsolvers import (
    ExpandingApprovals, GreedySolver, MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver, MethodOfEqualSharesExponentialSolver,
    MethodOfEqualSharesUtilitySolver, PhragmenSolver, SingleTransferableVote,
    SolidCoalitionRefinement, SummedObjectivesLpSolver,
)

PURE = [GreedySolver, PhragmenSolver,
        MethodOfEqualSharesExponentialSolver, SummedObjectivesLpSolver]
BACKED = [ExpandingApprovals, MethodOfEqualSharesAdd1Solver,
          MethodOfEqualSharesConstrainsSolver,
          MethodOfEqualSharesUtilitySolver, SingleTransferableVote,
          SolidCoalitionRefinement]
assert all(c(msg=False).available() for c in PURE)
assert not any(c(msg=False).available() for c in BACKED)
print("T11 bindings-independence OK")
```

- [ ] **Step 2:** `cd solvers && poetry run python <scratchpad>/verify_no_bindings.py` → `T11 bindings-independence OK` (fresh subprocess each run — never in a REPL that already imported bindings).

### Task 5: Status / validation / time / verbosity ACs (T12/T13/T14)

- [ ] **Step 1:** Grep ACs — `grep -rn "time.time()" solvers/src/` → empty; `grep -rn "print(" solvers/src/` → empty (`time.monotonic()` allowed).
- [ ] **Step 2:** Targeted suites — `cd solvers && poetry run pytest tests/test_time_verbosity.py tests/test_validation.py -q` → all pass (covers: msg=False zero-output sweep, timeLimit abort → NotSolved, D8 warn on binding-backed 5, PulpSolverError per rejection rule). If filenames drifted: `poetry run pytest -k "verbosity or silence or warns or timelimit or validation" -q` → >0 collected, all pass.
- [ ] **Step 3:** Status contract spot-grep — `grep -rn "return lp.status" solvers/src/muoblpsolvers/ | wc -l` → ≥9 (every non-delegating actualSolve; Summed delegates to CBC/Gurobi). `grep -rln "LpStatusOptimal" solvers/tests/` → every solve-test file listed.

### Task 6: Dedup + coverage sweep (T16/T17)

- [ ] **Step 1:** Grep ACs — `grep -rn "lp.valid()\|_lp.valid()" solvers/src/` → exactly 1 hit, the `FeasibilityChecker.is_feasible` fast path; `grep -rn "molp_to_simple_election" experiments/src/` → empty; `ls archived_code/experiments/` → contains `molpToSimpleElection.py`.
- [ ] **Step 2:** Coverage audit — `cd solvers && poetry run pytest --collect-only -q | tail -3` then confirm ≥1 solve test per module; expected map (record actual as 10-row table for verdict):

| module | test file |
|---|---|
| greedy_solver | test_greedy |
| phragmen | test_phragmen |
| mes/mes_add1 | test_mes_add1 |
| mes/mes_utility | test_mes_utility |
| mes/mes_constrains | test_mes_constrains |
| mes/mes_exponential | test_mes_exponential |
| summed_objectives_lp_solver | test_summed_objectives |
| expanding_approvals | test_ordinal_solvers |
| single_transferable_vote | test_ordinal_solvers |
| solid_coalition_refinement | test_ordinal_solvers |

- [ ] **Step 3:** `ls solvers/tests/ | grep mes_base` → empty (T17 rename done). 0 skips in local run (bindings present): `poetry run pytest -q | tail -1` shows no `skipped`, else list which.

### Task 7: Packaging hygiene (T18)

- [ ] **Step 1:** `cd solvers && poetry check` → `All set!`.
- [ ] **Step 2:** `rm -rf dist && poetry build && unzip -p dist/muoblpsolvers-*.whl '*/METADATA' | grep -E '^Requires-Dist'` → exactly muoblp + pulp + muoblpbindings version pins (bindings floor 0.0.17 or 0.0.18 per T17 outcome), NO pytest, NO `file://`.
- [ ] **Step 3:** `poetry sync --only main && poetry run python -c "import pytest" ; echo exit=$?` → import fails (exit≠0). Restore: `poetry sync && poetry run pytest -q` → green.

### Task 8: Sample smoke + CI

- [ ] **Step 1:** Sample end-to-end:

```bash
cd experiments/sample-experiment && rm -rf results/*
PATH="$(poetry -C .. env info --path)/bin:$PATH" ./run.sh
PATH="$(poetry -C .. env info --path)/bin:$PATH" ./analyze.sh
```

Expected metrics == frozen T01/T05 refs: APPROVAL 0.0033/219239/167; COST 0.0035/1.34763e11; COST_ORDINAL 0.0032/2.79444e11; bronowice 0.0666/4.35159e9. Any drift = BLOCKING (behavior change slipped through P2).
- [ ] **Step 2:** Rerun `./run.sh` WITHOUT rm → all configs log "Found result" (cache path intact).
- [ ] **Step 3:** CI — `gh run list --branch feat/roadmap-base-branch --limit 5` → latest runs `completed success` incl. build-bindings + pyright jobs. Red → inspect: Linux-only e2e diff is the known T02/T03 tie-break risk (BLOCKING if present, own ticket).

### Task 9: Leftovers adjudication + verdict + commit

- [ ] **Step 1:** Adjudicate every T10–T18 leftover entry + still-open older items → table (item / status closed-open-deferred / owner). Must cover at least: T01 "empty solver_options crash" (T10 closed?), T02 greedy zero-vote (T17), `test_mes_base` misnomer (T17), D8 resolution recorded (T14), `mes/common.py` duplicate-check redundancy (T16 note), pyright suppression inventory delta vs T03/T05 baseline (D12 ratchet — count inline ignores + config rules now vs then), P1 outstanding (rc-tag publish rehearsal, old bindings GH repo archive — expected still open, NON-BLOCKING).
- [ ] **Step 2:** Write into `plans/leftovers.md`:

```markdown
### P2 judge verdict (<date>)

- **P2 VERIFIED COMPLETE @<commit> — GO for P3.**  (or: **NO-GO — <blocking findings>**)
- Matrix: core <n> / solvers <n> (FRESH venv, bindings source-built) / experiments <n> incl. e2e ×2 deterministic; ruff+format clean ×3; pyright 0 ×3.
- Contract sweep 10/10 (ctor, toDict roundtrip, getSolver, listSolvers); bindings-independence OK; AC greps clean (solver_options / time.time / print / lp.valid).
- Coverage: <10-row module→test table or "all 10 covered">.
- Packaging: METADATA pins OK, no pytest/file://; poetry check clean.
- Sample metrics == T01/T05 refs; cache-hit rerun OK; CI green.
- Findings: BLOCKING <none|list+tickets>; NON-BLOCKING <list>.
- Carried forward: <rc-tag rehearsal, repo archive, D12 remaining suppressions, ...>.
```

- [ ] **Step 3:** Reconcile any stale ROADMAP checkboxes/PR links found in Task 1.
- [ ] **Step 4:** Commit to base: `git add ROADMAP.md plans/leftovers.md && git commit -m "docs: P2 judge verdict — <GO|NO-GO>, findings recorded"` and push. NO other files in the commit.

## Unresolved questions

1. Publish-path rehearsal (rc tag → test.pypi; `bindings@` tag → wheels upload) still unexercised since P1 — stays out of P2-verify scope (re-checked as carried-forward item only), or should this session push a rehearsal rc tag?

## Steps

1. Task 1: preflight — branch, T10–T18 merged, ROADMAP bookkeeping check
2. Task 2: green matrix (core, FRESH solvers venv, experiments incl. e2e ×2)
3. Task 3: T10/T15 contract script + solver_options grep
4. Task 4: T11 bindings-independence script
5. Task 5: T12/T13/T14 greps + targeted suites
6. Task 6: T16/T17 dedup greps + coverage table
7. Task 7: T18 poetry check / METADATA / only-main
8. Task 8: sample smoke vs frozen refs + cache rerun + CI check
9. Task 9: leftovers adjudication, verdict entry, ROADMAP reconcile, docs commit
