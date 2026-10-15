# T26 Experiments Coverage Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unit tests for the gaps left after T19–T25: metrics computation (exclusion_ratio, ejr_plus, invalid_constraints, instance_size — only sum_objectives/total_cost covered today), cache invalidation variants + cache-hit-skips-solve assert, module-import audit gap-fill (source_strategy, enhance_from_solver_result, logger, pabutools_utils error paths). Keep existing ~54 transform tests untouched.

**Architecture:** Test-only ticket (zero src changes; if a test exposes a real bug → STOP, file leftover note or fix under systematic-debugging with its own justification — no silent behavior patches). Much is pre-paid: T20 wrote paths/config/cache/steps/analyzer unit tests, T22 generator-helper tests, T23 aggregator tests, T24 failure-path tests, `test_utils.py` covers jsonc roundtrip. This ticket fills what remains + produces the every-module-tested audit for the PR. cache-hit-skips-solve = the one integration-ish assert: real `problem_runner` run on the mini fixture, second run with sabotaged `get_solver` must return via cache path without constructing a solver.

**Tech Stack:** pytest (tmp_path, monkeypatch, caplog), tiny hand-built `MultiObjectiveLpProblem` fixtures (pattern: `tests/test_metrics.py::make_tiny_problem`), `krakow_2024_mini` fixture for the runner-level test.

## Global Constraints

- Branch `feat/t26-coverage` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`.
- **Execute AFTER T20 + T24 merge (deps); phase order = last P3 ticket** — assumes final post-T21 names (`helpers.runners.source_strategy` etc.), T22–T25 landed. Re-derive exact gaps vs merged tree first: skip anything already covered (don't duplicate T20/T22/T23/T24 tests).
- e2e golden IDENTICAL, NO regen. No src edits.
- Hand-computed expectations ONLY for metric tests (derive on paper in test comments); no characterization-by-running-first.
- Repo GREEN: experiments pytest (units+e2e) + ruff + format + pyright; siblings untouched.

---

### Task 1: Metrics unit tests

**Files:**
- Modify: `experiments/tests/test_metrics.py` (extend; keep existing 2 tests)

- [ ] **Step 1: Write tests** (extend `make_tiny_problem` or add variants; expectations hand-derived in comments):
  - `exclusion_ratio`: tiny problem w/ v1 value>0, v2 value 0 → `{"exclusion_ratio": 0.5}` (set var initial values so one objective evaluates 0).
  - `instance_size`: → `{"size": len(variables)}` (note: counts ALL vars incl. pulp `__dummy` if present — assert on a problem without dummy; if a dummy sneaks in via `+=`, document).
  - `invalid_constraints`: satisfied PB constraint → `{"pb_constraint": True, "invalid_count": 0}`; over-budget selection → `invalid_count ≥ 1`, `pb_constraint False`.
  - `ejr_plus` — two hand-built cases on budget-250 instance:
    - satisfied: existing tiny problem (p1 selected, p2 not; p2's supporter has sat 100 ≥ (1/2)·250 − 200) → `{"ejr_plus": 0}`.
    - violated: p2 cost 10, two zero-satisfaction voters approving only p2 (4 voters total) → first coalition member check: 0 ≥ (1/4)·250 − 10 = 52.5 fails → `{"ejr_plus": 1}`. Derive exact numbers in a comment; if the impl disagrees with the paper math → STOP, that's a finding (metric bug), record in leftovers/PR, don't bend the expectation.
  - `get_metric_strategy` unknown metric → raises.
- [ ] **Step 2: Run** — expect PASS (characterizing correct behavior; failures = findings, see constraint).
- [ ] **Step 3: Commit** — `git commit -am "T26: metrics unit tests"`

---

### Task 2: Cache invalidation + cache-hit-skips-solve

**Files:**
- Modify: `experiments/tests/test_pipeline_cache.py` (extend T20's hit/miss/options/solver variants)
- Test: `experiments/tests/test_problem_runner.py` (new)

- [ ] **Step 1: Invalidation gap-fill** (vs T20 tests): meta w/ different `constraints_configs` → miss; different `deduplicate_objectives` → miss; different utility in filename → miss (regex path); corrupt meta json → miss (T19 ValidationError branch — verify not already in `test_models.py`, skip if so).
- [ ] **Step 2: cache-hit-skips-solve** (AC-named assert):

```python
# tests/test_problem_runner.py — real first run, sabotaged second
import problem_runner as problem_runner_module

def _config(tmp_path):  # GREEDY on krakow_2024_mini, results under tmp
    ...

def test_cache_hit_skips_solve(tmp_path, monkeypatch):
    config = _config(tmp_path)
    problem_runner_module.problem_runner(config)          # real solve, persists
    assert len(list(tmp_path.glob("meta_*.json"))) == 1

    def boom(*args, **kwargs):
        raise AssertionError("solver constructed on cache hit")

    monkeypatch.setattr(problem_runner_module, "get_solver", boom)
    problem_runner_module.problem_runner(config)          # must return via cache
    assert len(list(tmp_path.glob("meta_*.json"))) == 1   # nothing re-written

def test_cache_miss_calls_solver(tmp_path, monkeypatch):
    # fresh dir + counting get_solver wrapper -> called exactly once
    ...
```

(GREEDY on the mini fixture ≈ seconds; keep in default suite, not e2e-marked.)
- [ ] **Step 3: Run** — green.
- [ ] **Step 4: Commit** — `git commit -am "T26: cache invalidation + cache-hit-skips-solve"`

---

### Task 3: Module-import audit + gap-fill units

**Files:**
- Test: `experiments/tests/test_source_strategy.py` (new)
- Test: `experiments/tests/test_utils_misc.py` (new — logger + enhance_from_solver_result + pabutools_utils error paths; or append to nearest existing files)

- [ ] **Step 1: Audit** — enumerate `experiments/src/**/*.py` (excl. `__init__`), grep each import path in `tests/`; produce module→test table (goes in PR body). Expected uncovered (2026-07-19 projection; re-derive): `helpers/runners/source_strategy.py`, `helpers/utils/enhance_from_solver_result.py`, `helpers/utils/logger.py`, `pabutools_utils` error branches. Entrypoints covered via e2e + Task 2; generators/aggregator via T22/T23.
- [ ] **Step 2: Gap-fill tests:**
  - `resolve_constraints_configs`: inline list wins over path; path-only → validated `ConstraintConfig` list from tmp json; neither → `[]`.
  - `load_and_transform_strategy`: PABUTOOLS on mini fixture → returns problem + resolved utility (explicit vs auto-detected `COST_ORDINAL`); unknown source_type → raises.
  - `enhance_problem_from_solver_result`: tiny problem + `RunnerResult.selected=["_A"]` → `_A` value 1, others 0.
  - `setup_logging` bad path → falls back to `basicConfig`, no raise, error logged (caplog).
  - `detect_utility_from_instances`: missing `vote_type` meta → ValueError; inconsistent across districts → ValueError; unmapped vote_type → NotImplementedError.
- [ ] **Step 3: Run** — green; re-run audit → every module ≥1 test (AC).
- [ ] **Step 4: Commit** — `git commit -am "T26: source_strategy/utils gap-fill + module audit"`

---

### Task 4: Coverage snapshot + full verify + PR

- [ ] **Step 1: Informal coverage** (ticket Verify "`pytest --cov` informal") — pytest-cov is not a declared dep: use `poetry run python -m pytest --cov=src --cov-report=term` IF available in venv, else `poetry run coverage run -m pytest && coverage report`; if neither installed, SKIP tooling (do NOT add a dep for an informal number) and rely on the Task 3 audit table. Record whichever output in PR.
- [ ] **Step 2: Matrix** — pytest (units+e2e ×2 runs — determinism spot-check) + ruff + format + pyright green; siblings pytest green.
- [ ] **Step 3: PR** — push, PR → `feat/roadmap-base-branch`, title `T26: experiments coverage sweep`. Body: module→test audit table, new-test inventory, coverage snapshot, any findings (metric-math discrepancies etc.) as explicit follow-ups. Update ROADMAP checkbox + `plans/leftovers.md` (P3 complete → note P3-judge/verify session next, then T27/T28).

## Unresolved questions

1. `ejr_plus` hand-derived expectations: if impl disagrees w/ paper math, this ticket records the finding + keeps test skipped/xfail w/ note (no src fix here) — OK, or fix in-ticket?
2. Coverage tooling: OK to skip `--cov` entirely when pytest-cov absent (audit table instead), or add pytest-cov to dev deps?
3. New test files (`test_problem_runner.py`, `test_source_strategy.py`, `test_utils_misc.py`) vs appending to existing — naming OK?

## Steps

1. Task 1: metrics unit tests + commit
2. Task 2: cache invalidation + hit-skips-solve/miss-calls-solver + commit
3. Task 3: module audit + gap-fill units + commit
4. Task 4: coverage snapshot, matrix ×2, PR, ROADMAP/leftovers update
