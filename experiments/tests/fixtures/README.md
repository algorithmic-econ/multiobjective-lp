# Test fixtures

## `input/krakow_2024_mini/`

Tiny pabulib fixture for the e2e golden test (`tests/test_e2e_golden.py`).
Trimmed from `sample-experiment/input/krakow_2024/` districts
Łagiewniki-Borek Fałęcki + Swoszowice (2 districts → exercises per-district
budget caps + total budget constraint).

Trim rule (applied per file by a one-off script, not committed):

1. Keep top-5 projects by the `votes` column.
2. Keep 15 qualifying ballots (ballot qualifies when ALL 3 voted ids are
   within kept projects — filter, never truncate ballots: truncation would
   change COST_ORDINAL weights and violate `min/max_length` meta).
   Coverage-first pick: per kept project take the first qualifying ballot
   voting for it (zero-vote candidates crash GreedySolver and get dropped by
   MES bindings), then fill to 15 in file order; output in file order.
3. Prefix `voter_id` with district tag (`d9_` / `d10_`) — objectives are keyed
   by voter_id across districts; collisions silently merge voters.
4. META: `num_projects`/`num_votes` updated; `budget` = int(45% of the sum of
   kept project costs) — forces a proper-subset selection.
5. Column layouts unchanged; `votes`/`score`/`selected` project columns are
   stale after trimming (parser ignores them).

Result: 10 projects / 30 voters / 2 districts.

## `golden/`

Golden outputs for the e2e test: `selected.json` (per-solver normalized run
meta) and `metrics.json` (normalized analyzer rows). Normalization (see
`tests/golden_utils.py`): drop `time`, timestamp+uuid in filenames → `ID`,
paths → basename, floats rounded to 6 dp, metrics rows sorted by solver.

### Regenerating goldens

Only when a ticket explicitly allows; regen = separate commit with
justification (ROADMAP §2):

```sh
cd experiments && UPDATE_GOLDEN=1 poetry run pytest -m e2e
```

Writes new goldens and then FAILS the test on purpose (a leaked env var must
not green CI). Inspect the diff, then commit separately.

### Manual mutation check

After touching solver code, verify goldens still discriminate:

1. `solvers/src/muoblpsolvers/greedy_solver.py` — flip `reverse=True` →
   `False` in the candidate sort → `pytest -m e2e` must FAIL with a readable
   diff; revert.
2. `solvers/src/muoblpsolvers/mes/mes_add1.py` — halve the total budget →
   MES_ADD1 golden must FAIL; revert.
3. `git diff` clean afterwards.
