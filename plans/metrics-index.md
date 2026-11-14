# Pabulib metrics port — index

Port of `pabulib-analyzer2/stats.py` metrics into `muoblpanalyzers`.
Base branch `feat/pabulib-metrics-base`; one session/PR per plan. Each plan
starts by asking its unresolved questions. Native C++ twins = follow-up
plans after python versions merge. Done plans → `plans/archive/`.

Not planned: `dominance_margin` (compares 2 outcomes), `jr_violations`
(never implemented in pabulib), greedy-relative normalisation (already
`AggregatorConfig.normalize_baseline`).

| NN | Metric | Plan | Depends on | Done |
|---|---|---|---|---|
| 00 | Honor objective weights in existing metrics (prelim) | [metric-00-objective-weights-plan.md](metric-00-objective-weights-plan.md) | — | [ ] |
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
