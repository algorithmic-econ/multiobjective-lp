# T01 action plan — fix pipeline-blocking bugs

## Context
First ticket of P0 (safety net). Pipeline currently broken → blocks T02 golden e2e. Refactor-only repo cleanup; this ticket = minimal fixes to make `run.sh` + `analyze.sh` produce metrics json. Branch off `feat/roadmap-base-branch`, PR targets it. Repo GREEN after (pytest + ruff).

## Confirmed bugs (all verified in source)

### B1 broken import — `experiments/src/helpers/analyzers/metrics.py:4`
`from muoblpsolvers.common import get_total_budget_constraint` — module actually `muoblpsolvers/mes/common.py`. Breaks whole analyzer chain (`analyzerRunner` import fails).
Fix: change import → `muoblpsolvers.mes.common` (experiments-only; no solvers API change; T16 reorganizes later anyway).
Test: import `helpers.analyzers.metrics` + run `total_cost`/`sum_objectives` on tiny hand-built `MultiObjectiveLpProblem`.

### B2 jsonc suffix — `experiments/src/helpers/utils/utils.py:8`
`write_to_json`: `path.suffix == "jsonc"` missing dot → always False → json module used for `.jsonc`. (`read_from_json` line 14 correct.)
Fix: `".jsonc"`.
Test: write/read roundtrip for `.jsonc` and `.json` paths (tmp_path).

### B3 None crash — `experiments/src/helpers/runners/solverStrategy.py:17`
`"use-gurobi" in solver_options` → TypeError when `solver_options is None`. Repro: config with explicit `"solver_options": null` (`problemRunner.py:22` defaults only MISSING key to `{}`; explicit null passes through; `RunnerConfig` types it `dict | None`).
Fix: `solver_options = solver_options or {}` at top of `get_solver`.
Test: `get_solver(t, None)` for all 7 Solver literals returns solver instance, no raise.
Out of scope: MES_CONSTRAINT/EXPONENTIAL/PHRAGMEN with `{}` still crash inside `actualSolve` (missing `max_iterations` etc.) — T10/T13 territory.

### B4 regex-miss exception — `experiments/src/helpers/analyzers/analysis_table.py:56`
Roadmap says "raise with offending filename" — current code ALREADY includes filename in message. Residual: `Exception` → `ValueError`, add expected-pattern to message. Full fix (stop parsing filenames for semantics) = T24.
Test: metrics json with one entry whose `problem_path` filename doesn't match → `pytest.raises(ValueError, match=<filename>)`.

### B5 DISCOVERED blocker — `experiments/sample-experiment/experiment-config.jsonc:22,29`
References `empty-constraints-config.json`; file on disk is `empty-constraints-config.jsonc` → `FileNotFoundError` in `resolve_constraints_configs` for runner configs 3–4. Blocks AC ("run.sh produces metrics json"). Same class as T09 item but must fix here.
Fix: config ref → `.jsonc` (1 line).

## Tests
New files under `experiments/tests/` (match existing convention `test_<topic>.py`, plain pytest):
- `test_metrics.py` (B1), `test_utils.py` (B2), `test_solver_strategy.py` (B3), `test_analysis_table.py` (B4). B5 covered by sample-run verification.

## Env setup (experiments venv missing)
```
cd experiments && poetry env use python3.12 && poetry install
```
py3.12 OK: lock resolves `muoblpbindings` 0.0.16 (cp312 macOS arm64 wheel exists). Solvers project untouched.

## Verification
1. `cd experiments && poetry run pytest` — all green incl. 4+ new regression tests.
2. `cd sample-experiment && ./run.sh` → `problem_*.lp` + `meta_*.json` appear in `results/sample-experiment/`.
3. `./analyze.sh` → `results/sample-analysis/metrics-sample-experiment.json` + markdown table printed.
4. `ruff check` experiments (GREEN convention). pyright baseline arrives in T03 — not gating here.

## Risks
- run.sh runtime: 4 runner configs × full krakow_2024 (19 districts), MES_ADD1, concurrency 3 — may take minutes; acceptable.
- Further latent blockers may surface during sample run; fix minimally if 1-liner, else split per roadmap conventions (§2).
- Bindings staleness (0.0.16 vs 0.0.17 pin) known, deferred to T04.

## Deliverables
Branch `fix/t01-pipeline-blocking-bugs` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`; update ROADMAP.md checkbox + PR link.

## Resolved decisions
1. B1: fix import in experiments (`muoblpsolvers.mes.common`), no solvers change.
2. B5: fix config ref → `.jsonc` in T01.

## Unresolved questions
None.

## Steps
1. Branch `fix/t01-pipeline-blocking-bugs` off `feat/roadmap-base-branch`
2. Env: `poetry env use python3.12 && poetry install` in experiments
3. Fix B1–B5 (each + regression test; B5 config-only)
4. `poetry run pytest` green
5. Sample `run.sh` + `analyze.sh` → metrics json + table
6. `ruff check` green
7. Commit(s), PR → `feat/roadmap-base-branch`, tick ROADMAP
