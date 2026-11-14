# metric-12: COMPARATIVE_EJR_PLUS

> **FIRST ACTION when implementing:** call AskUserQuestion with every item
> under "Unresolved questions". Do not write code until answered. Record
> answers in a "Decisions (session)" section of this file.
> Prerequisite: `metric-00-objective-weights` merged into base.

Source: `pabulib-analyzer2/stats.py` (precursor project, sibling dir of
`multiobjective-lp`). Target: `analyzers/src/muoblpanalyzers/metrics.py`.
Index: `plans/metrics-index.md`.

## Decisions (user-confirmed, all metric plans)
- Branching: base `feat/pabulib-metrics-base` (exists; NOT the old
  `feat/roadmap-base-branch`); this plan's branch `feat/metric-comparative-ejr-plus` off
  base; PR → base. Never main.
- n = len(objectives) semantics kept (after metric-00: Σ weights, = len when
  unweighted); NOT pabulib's "voters w/ ≥1 positive util".
- Var w/o PB cost (objective-only var) in a cost-based metric → raise
  `ValueError` naming the var.
- Objective weights honored (helpers from metric-00).
- Python only. Native C++ twin = separate follow-up plan, only after the
  python metric is merged.

## Model mapping (verified: `pabulib-analyzer2/utils.py:get_election`)
- pabulib `e.profile[p][v]` = Cost_Sat utility = objective coef `voter[p]`
- voter = objective; weight w_v = `objectives_weights.get(voter.name, 1)`
- selected = var w/ `value() == 1`
- cost = PB constraint coef; budget B = `abs(pb.constant)`
  (`validate_pb_constraint` from `muoblpsolvers.election_solver`)
- pabulib multi-district list → one LP; B = PB rhs (= Σ district budgets)

## Shared helpers (metrics.py; metric-00 adds weight helpers, first metric session adds rest — reuse if present)
- `_weight(problem, voter) -> float`, `_voter_count(problem) -> float` (00)
- `_pb_costs(problem) -> dict[str, float]` via `validate_pb_constraint`
- `_budget(problem) -> float`
- `_selected(problem) -> set[str]`: value()==1 over `problem.variables()`
  AND objective vars (objective-only vars missing from `variables()`, see
  fixture `make_objective_only_variable_problem`)

## Conventions
- new `Metric` enum value in `metric.py` (value = on-disk key, never rename)
- fn `(problem) -> dict`, snake_case inner key; register `PYTHON_STRATEGIES`
- tests in `analyzers/tests/test_metrics.py`, hand-computed on
  `tests/fixtures/problem_factories.py` (arithmetic in comments, like
  existing tests); 1 weighted case per metric (w=2 voter == two identical
  w=1 voters)
- ruff line-length 79; pyright clean; do NOT copy pabulib bugs (listed)

## Verification
- `cd analyzers && poetry run pytest && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright`
- `cd experiments && poetry run pytest && poetry run pytest -m e2e`
  (consumes `Metric`); no golden regen unless decided
- optional: scratchpad script cross-checking pabulib fn vs new metric on 1
  small `.pb` (pabulib needs `pabutools`)

## Context
pabulib `comparative_ejr_plus_violations` + `compute_ejr_timestamp`
(stats.py:352, 456); test helper `comparative_ejr_plus_violations_test`
(stats.py:483, expected 0/81/52). Uses `pabulib-analyzer2/priority_queue.py`.

## Spec
- timestamp ts[c] per candidate (include_cand=True); port via `heapq` +
  lazy invalidation; `compute_ejr_timestamp2` (stats.py:294) = O(n²) oracle
- failures: for unsel c2: tot_cost = Σ cost_sel; for sel c1 by desc ts:
  tot_cost −= cost_c1; count if tot_cost + cost_c2 ≤ B and ts[c2] < ts[c1]
- strong count: ts[c2] < B/n
- keys `comparative_ejr_plus`, `strong_ejr_failures_up_to_one`

## Pabulib bugs (do not copy)
- test helper asserts `val == failures` but fn returns tuple
- debug `print`s in `compute_ejr_timestamp2` → drop

## Tests
- heap impl == oracle (parity) on random small instances
- party-list cases (parties [20,30,50], k=10, outcomes [2,3,5]/[3,1,6]/
  [4,2,5]) → expected 0/81/52

## Unresolved questions
- Drop `strong_ejr_failures_up_to_one` key (overlaps metric-11)?
- Oracle-only first, heap later?
- Party-list expected values 0/81/52 trustworthy?
- Weights in timestamp computation?

## Steps
1. AskUserQuestion (unresolved questions); record decisions
2. `git checkout feat/pabulib-metrics-base && git pull && git checkout -b feat/metric-comparative-ejr-plus`
3. Port ts2 oracle
4. Heap version + parity test
5. Failure counts + party-list tests
6. Verification block; update index status
7. Commit, PR → `feat/pabulib-metrics-base`; stop, wait for review
