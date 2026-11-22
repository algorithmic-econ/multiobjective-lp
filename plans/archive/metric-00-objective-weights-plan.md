# metric-00: Honor objective weights in existing metrics (prelim)

> **FIRST ACTION when implementing:** call AskUserQuestion with every item
> under "Unresolved questions". Do not write code until answered. Record
> answers in a "Decisions (session)" section of this file.
> Prerequisite for ALL other metric plans.

Source: `pabulib-analyzer2/stats.py` (precursor project, sibling dir of
`multiobjective-lp`). Target: `analyzers/src/muoblpanalyzers/metrics.py`.
Index: `plans/metrics-index.md`.

## Decisions (user-confirmed, all metric plans)
- Branching: base `feat/pabulib-metrics-base` (exists; NOT the old
  `feat/roadmap-base-branch`); this plan's branch `feat/metric-objective-weights` off
  base; PR → base. Never main.
- n = len(objectives) semantics kept (after metric-00: Σ weights, = len when
  unweighted); NOT pabulib's "voters w/ ≥1 positive util".
- Var w/o PB cost (objective-only var) in a cost-based metric → raise
  `ValueError` naming the var.
- Objective weights honored (helpers from metric-00).
- Python only. Native C++ twin = separate follow-up plan, only after the
  python metric is merged.

## Decisions (session)
- e2e/goldens never dedup (all w=1) → goldens unchanged, no regen
- `SUM_OBJECTIVES`: same key, now Σ w·value
- weights = float (model `objectives_weights: dict[str, float]`),
  fractional ok; `ValueError` (py + native) only if non-finite or ≤ 0.
  Unnamed objective / name missing from dict → 1

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
Existing metrics (python + native) ignore `problem.objectives_weights`.
Weights = multiplicity of deduplicated identical voters
(`experiments/src/helpers/transformers/pabutools_to_molp.py:52-55`,
`preflib_to_muoblp.py:97-101`). Solvers honor them
(`solvers/src/muoblpsolvers/election_solver.py:239`, `mes/common.py:62`);
C++ `bindings/src/metrics/*` has no weight handling. Deduped objective w/
weight k must count as k voters.

## Spec
- helpers `_weight(problem, voter)` (= `objectives_weights.get(name, 1)`),
  `_voter_count(problem)` (= Σ w)
- `exclusion_ratio` = Σ w over obj w/ value 0 / Σ w
- `sum_objectives` = Σ w·value
- `ejr_plus`: coalition_size += w; voter_count = Σ w
- `instance_size`, `total_cost`, `invalid_constraints`: unaffected
- native (unavoidable — parity tests iterate `PYTHON_COUNTERPART` and would
  break): `SolvedInstance::from_MuoblpProblem` reads `objectives_weights`
  (default 1) into `Voter`; weight `exclusion_ratio.cpp`, `ejr_plus.cpp`

## Pabulib bugs (do not copy)
n/a (bug is in muoblpanalyzers itself)

## Tests
- new fixture `make_weighted_problem` + unweighted equivalent w/ duplicated
  objectives → every affected metric equal on both (py + native parity)
- existing tests unchanged (all weights default 1)

## Unresolved questions
- e2e configs use `deduplicate_objectives`? If yes goldens change → regen
  allowed?
- `SUM_OBJECTIVES` weighted changes on-disk meaning → ok, or new key?
- weight ≤ 0 / non-integer → reject (ValueError) or accept?

## Steps
1. AskUserQuestion (unresolved questions); record decisions
2. `git checkout feat/pabulib-metrics-base && git pull && git checkout -b feat/metric-objective-weights`
3. Helpers + python fixes + tests
4. C++ `SolvedInstance` weights + weighted native metrics + parity tests
   (bindings rebuild; SDKROOT/CXXFLAGS workaround per `bindings/README` if
   needed)
5. Verification block (+ `cd bindings` tests if any); update index status
6. Commit, PR → `feat/pabulib-metrics-base`; stop, wait for review
