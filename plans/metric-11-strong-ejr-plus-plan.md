# metric-11: STRONG_EJR_PLUS

> **FIRST ACTION when implementing:** call AskUserQuestion with every item
> under "Unresolved questions". Do not write code until answered. Record
> answers in a "Decisions (session)" section of this file.
> Prerequisite: `metric-00-objective-weights` merged into base.

Source: `pabulib-analyzer2/stats.py` (precursor project, sibling dir of
`multiobjective-lp`). Target: `analyzers/src/muoblpanalyzers/metrics.py`.
Index: `plans/metrics-index.md`.

## Decisions (user-confirmed, all metric plans)
- Branching: base `feat/pabulib-metrics-base` (exists; NOT the old
  `feat/roadmap-base-branch`); this plan's branch `feat/metric-strong-ejr-plus` off
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
pabulib `strong_ejr_plus_violation(s)` (stats.py:234, 265), analyzer keys
`strong_ejr_failures`, `strong_ejr_failures_up_to_one`.

## Spec
Per unsel c: ext = sel ∪ {c}; sat_map[x] = Σ_v u_xv; threshold = B/n;
active = all voters. While active and sat_map[c] > 0:
- voter_sat_i = Σ_{x ∈ ext ∩ approved_i, x ≠ c unless up_to_one}
  u_xi · min(cost_x/sat_map[x], cost_c/sat_map[c])
- remove voters w/ voter_sat > threshold; none removed → violation
- sat_map[x] −= u_xi for removed voters
Count violations; complexity O(rounds·voters·approvals) per candidate
(native candidate later).

## Pabulib bugs (do not copy)
- `for e in elections` w/o tuple unpack → never ran

## Tests
- hand-built small instance + brute-force check
- no div-by-0 when sat_map[x] → 0
- perf check on a real pabulib-size LP

## Unresolved questions
- `up_to_one` looks inverted (includes c when True) — port verbatim?
- 1 Metric w/ 2 keys vs 2 Metrics?
- Weights: sat_map = Σ w·u? threshold B/Σw?
- Acceptable python runtime on large instances?

## Steps
1. AskUserQuestion (unresolved questions); record decisions
2. `git checkout feat/pabulib-metrics-base && git pull && git checkout -b feat/metric-strong-ejr-plus`
3. Add missing shared helpers
4. Enum value + fn + `PYTHON_STRATEGIES` entry
5. Tests (fixture cases below + weighted case + edge cases)
6. Verification block; update `plans/metrics-index.md` status
7. Commit, PR → `feat/pabulib-metrics-base`; stop, wait for review
