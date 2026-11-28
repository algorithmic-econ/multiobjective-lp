# Pabulib metrics port — index

Port of `pabulib-analyzer2/stats.py` metrics into `muoblpanalyzers`.
Base branch `feat/pabulib-metrics-base`; one session/PR per plan. Each plan
starts by asking its unresolved questions. Native C++ twins = follow-up
plans after python versions merge. Done plans → `plans/archive/`.

## Resolved: MES on deduplicated data (was invalid)
Native MES (MES_UTILS, MES_ADD1, MES_CONSTRAINTS) ignored
`objectives_weights` before bindings 0.0.22; dedup MES results produced
earlier (e.g. old `independent-waw-krk-dedup`) are invalid — rerun them.
Fixed by [fix-mes-weights-plan.md](archive/fix-mes-weights-plan.md):
waw-krk dedup rerun → 0/54 MES_ADD1 differ vs non-dedup (was 50/54), EJR+
violations 0. Exact ties may still differ (unordered_map tie-break).

Not planned: `dominance_margin` (compares 2 outcomes), `jr_violations`
(never implemented in pabulib), greedy-relative normalisation (already
`AggregatorConfig.normalize_baseline`).

| NN | Metric | Plan | Depends on | Done |
|---|---|---|---|---|
| 00 | Honor objective weights in existing metrics (prelim) | [metric-00-objective-weights-plan.md](archive/metric-00-objective-weights-plan.md) | — | [x] |
| 01 | AVG_SATISFACTION | [metric-01-avg-satisfaction-plan.md](metric-01-avg-satisfaction-plan.md) | 00 | [ ] |
| 02 | AVG_SCORE_SATISFACTION | [metric-02-avg-score-satisfaction-plan.md](metric-02-avg-score-satisfaction-plan.md) | 00 | [ ] |
| 03 | AVG_CUMULATIVE_SATISFACTION | [metric-03-avg-cumulative-satisfaction-plan.md](metric-03-avg-cumulative-satisfaction-plan.md) | 00 | [ ] |
| 04 | AVG_CUMULATIVE_SCORE_SATISFACTION | [metric-04-avg-cumulative-score-satisfaction-plan.md](metric-04-avg-cumulative-score-satisfaction-plan.md) | 00 | [ ] |
| 05 | AVG_COST | [metric-05-avg-cost-plan.md](metric-05-avg-cost-plan.md) | 00 | [ ] |
| 06 | BUDGET_EXHAUSTION | [metric-06-budget-exhaustion-plan.md](metric-06-budget-exhaustion-plan.md) | 00 | [ ] |
| 07 | EJR+ strict (up_to_one=False) | [metric-07-ejr-plus-strict-plan.md](metric-07-ejr-plus-strict-plan.md) | 00 | [ ] |
| 08 | EJR+ up to best | [metric-08-ejr-plus-up-to-best-plan.md](metric-08-ejr-plus-up-to-best-plan.md) | 00, 07 | [ ] |
| 09 | EJR_PLUS_DEGREE | [metric-09-ejr-plus-degree-plan.md](metric-09-ejr-plus-degree-plan.md) | 00 | [ ] |
| 10 | POWER_INEQUALITY | [metric-10-power-inequality-plan.md](metric-10-power-inequality-plan.md) | 00 | [ ] |
| 11 | STRONG_EJR_PLUS | [metric-11-strong-ejr-plus-plan.md](metric-11-strong-ejr-plus-plan.md) | 00 | [ ] |
| 12 | COMPARATIVE_EJR_PLUS | [metric-12-comparative-ejr-plus-plan.md](metric-12-comparative-ejr-plus-plan.md) | 00 | [ ] |

## Notes for future sessions (from done plans)
- 00: helpers in `metrics.py`: `_weight(problem, objective)` (float,
  `objectives_weights.get(name, 1)`, unnamed → 1, non-finite/≤0 →
  `ValueError`), `_voter_count(problem)` (Σ w, objectives order). Use them
  for every voter-count / per-voter sum; n = `_voter_count`, never
  `len(objectives)`.
- 00: weights are floats (model `dict[str, float]`), fractional ok; LP
  reader yields floats (`3.0`). Don't require ints.
- 00: weighted coalition pattern (EJR-like): sort by satisfaction, `k += w`
  per approver, check threshold once per voter == w expanded voters.
- 00: weighted-case test fixtures exist: `make_weighted_problem` (w 3/1) ≡
  `make_weighted_problem_expanded` (duplicated voters);
  `make_weighted_objectives_problem` (fractional 3/2.5/0.5). Both in
  `HANDCRAFTED_FACTORIES` → add to every `EXPECTED_*` dict.
- 00: `make_random_problem` voters named `v{i}` w/ float weights
  (0.5..3) → native parity covers weights automatically.
- 00: native: `SolvedInstance::Voter.weight`, `total_weight` (also py ro
  prop). Sum weights in voter order → bit-identical w/ python.
- any C++ change ⇒ bump `bindings/pyproject.toml` version, bump analyzers
  `native` extra pin, relock solvers + analyzers + experiments
  (`poetry lock`), `poetry install --all-extras` in analyzers to rebuild.
- toolchain: Apple clang ≥16 (`std::format`); python 3.13/3.14 (= CI
  matrix). 3.15 fails: pinned `pydantic_core` has no cp315 wheel.
