# metric-10: POWER_INEQUALITY

> **FIRST ACTION when implementing:** call AskUserQuestion with every item
> under "Unresolved questions". Do not write code until answered. Record
> answers in a "Decisions (session)" section of this file.
> Prerequisite: `metric-00-objective-weights` merged into base.

Source: `pabulib-analyzer2/stats.py` (precursor project, sibling dir of
`multiobjective-lp`). Target: `analyzers/src/muoblpanalyzers/metrics.py`.
Index: `plans/metrics-index.md`.

## Decisions (user-confirmed, all metric plans)
- Branching: base `feat/pabulib-metrics-base` (exists; NOT the old
  `feat/roadmap-base-branch`); this plan's branch `feat/metric-power-inequality` off
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
pabulib `power_inequality` (stats.py:207).

## Spec
- power_v = Σ_{p sel, v approves} u_pv·cost_p / #approvers_p
- m = weighted mean power; result = weighted mean of (x/m − 1)²
- `POWER_INEQUALITY` → `{"power_inequality": float}`

## Pabulib bugs (do not copy)
- `for e in elections` w/o tuple unpack → crashed (never ran)
- u·cost w/ Cost_Sat utils = cost² (likely meant score·cost)

## Tests
(verbatim formula)
- tiny: powers 5000, 5000 → 0
- ejr_violation: 5000, 5000, 0, 0 → m 2500 → (1+1+1+1)/4 = 1.0

## Unresolved questions
- Weight term: u, u/cost (score), or approval indicator?
- m = 0 (nothing selected) → 0 or None?
- #approvers weighted (Σ w)?

## Steps
1. AskUserQuestion (unresolved questions); record decisions
2. `git checkout feat/pabulib-metrics-base && git pull && git checkout -b feat/metric-power-inequality`
3. Add missing shared helpers
4. Enum value + fn + `PYTHON_STRATEGIES` entry
5. Tests (fixture cases below + weighted case + edge cases)
6. Verification block; update `plans/metrics-index.md` status
7. Commit, PR → `feat/pabulib-metrics-base`; stop, wait for review
