# T23 Consolidate Aggregators Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One parameterized plotting script `aggregate_results.py` (JSON `AggregatorConfig` — user decision) replacing `aggregate_results.py` (V3 + ~290 commented V1/V2 lines) and `aggregate_grouped_results.py` (hardcoded Zabrze/Amsterdam filters, broken `from src.helpers` imports); legacy variants → archived_code.

**Architecture:** Two existing scripts = two plot modes over the same metrics.json rows: (a) line-plot bucketed by instance size w/ GREEDY-relative normalization + clip + zoomed-cost panel + log-time; (b) bar-plot per city, mean over years, city excludes. Merge = one script, `group_by` switch, all hardcoded knobs → `AggregatorConfig` fields. Structure: pure `load_rows(path) -> list[AnalyzerResult]` (model_validate, skip None/invalid w/ warning — pre-T24 nulls tolerated) → pure `build_dataframe(rows, config) -> pd.DataFrame` (long-form Metric/Value/Solver/City/InstanceSize + normalization/bucketing/filters) → `plot(df, config) -> None` (seaborn, savefig) → thin `main(config_path)`. Imports fixed to `from helpers…` (script runs from `src/`, matching runner/analyzer). Golden `tests/fixtures/golden/metrics.json` (real 3-solver analyzer output) doubles as test input fixture.

**Tech Stack:** T19 models, pandas/seaborn/matplotlib (already deps), pytest w/ `MPLBACKEND=Agg` for plot smoke.

## Global Constraints

- Branch `feat/t23-aggregator` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`.
- **Execute AFTER T21 merge** (files named `aggregate_results.py`/`aggregate_grouped_results.py`); T19 models assumed (`AnalyzerResult`, `Solver`, `StrictModel`). If T24 landed first (order says it doesn't), rows may contain failure entries — `load_rows` skip-invalid already covers.
- e2e golden IDENTICAL, NO regen (aggregator sits after analyzer output, outside golden pipeline).
- Refactor-only: reproduce existing plot behaviors behind config; NO new metrics/plot kinds (§5 exclusions). Numeric semantics preserved: bucket = `(size // bucket_size) * bucket_size`; normalization: metric ÷ baseline-solver value per city, clip at `clip_upper`; zoomed panel = IQR-filtered copy (bucket mode + normalization only); time row always added, log y-scale.
- Dead code → `archived_code/experiments/` via `git mv`/copy, never plain-deleted.
- Repo GREEN after ticket: experiments pytest (units+e2e) + ruff + ruff format + pyright; siblings untouched. Pyright note: aggregators were part of the disabled-rules residue (T03/T19 inventory) — after rewrite, retry removing pandas-interop rule disables in `pyrightconfig.json`; keep only rules that still fail OUTSIDE this file.

---

### Task 1: `AggregatorConfig` model

**Files:**
- Modify: `experiments/src/helpers/analyzers/model.py` (append)
- Test: `experiments/tests/test_aggregator.py` (new)

**Interfaces:**
- `AggregatorConfig(StrictModel)`: `metrics_json_path: str`, `output_path: str`, `group_by: Literal["instance_size_bucket","city"]`, `bucket_size: int = 10`, `exclude_cities: list[str] = []`, `include_solvers: list[str] | None = None` (match against composed solver label `SOLVER_{options}`; None = all), `normalize_baseline: Solver | None = None` (bucket mode: SUM_OBJECTIVES/TOTAL_COST relative to this solver; None = raw values), `clip_upper: float = 5.0`.

- [ ] **Step 1: Failing tests** — minimal config validates; unknown key → ValidationError w/ loc; bad group_by rejected.
- [ ] **Step 2: Verify failure** (no `AggregatorConfig`).
- [ ] **Step 3: Implement** model.
- [ ] **Step 4: Run** — green.
- [ ] **Step 5: Commit** — `git commit -am "T23: AggregatorConfig model"`

---

### Task 2: Archive legacy variants

**Files:**
- Copy: `experiments/src/aggregate_results.py` → `archived_code/experiments/aggregate_results_legacy.py` (preserves V1/V2 commented blocks + V3 before rewrite; `git add`)
- Move: `git mv experiments/src/aggregate_grouped_results.py archived_code/experiments/aggregate_grouped_results.py`

- [ ] **Step 1: Copy + move** as above (roadmap: commented blocks + hardcoded city filters → archived_code, not plain-deleted).
- [ ] **Step 2: Run** — pytest/ruff green (archived_code excluded; nothing imported the grouped script).
- [ ] **Step 3: Commit** — `git commit -am "T23: archive legacy aggregator variants"`

---

### Task 3: Rewrite `aggregate_results.py`

**Files:**
- Modify: `experiments/src/aggregate_results.py` (full rewrite)
- Test: `experiments/tests/test_aggregator.py` (append)

**Interfaces:**
- `load_rows(metrics_json_path: Path) -> list[AnalyzerResult]` — model_validate each entry; `None`/ValidationError → `logger.warning`, skip.
- `build_dataframe(rows, config) -> pd.DataFrame` — long form; columns `City, Solver, Metric, Value` (+ `Bucket` in bucket mode); applies exclude_cities/include_solvers; metric extraction via the existing `metric_display_map` value-key pairs; time row appended; normalization + clip + zoomed-cost rows when `normalize_baseline` set (bucket mode).
- `plot(df, config) -> None` — bucket mode: `sns.relplot` line/col-wrap/log-time (V3 styling verbatim); city mode: `sns.catplot` bar/mean-over-years (grouped-script styling verbatim); `savefig(config.output_path)` (mkdir parent).
- `main(config: AggregatorConfig | dict) -> None`; `__main__`: `main(read_from_json(Path(sys.argv[1])))`.

- [ ] **Step 1: Failing tests** (fixture = `tests/fixtures/golden/metrics.json`):
  - `load_rows` on golden → 3 rows, all AnalyzerResult; on `[null, {...bad}]` tmp file → skips, returns valid only.
  - `build_dataframe` bucket mode: expected row count (3 solvers × extracted metrics + time rows); bucket values correct for known instance_size 10 (`bucket_size=10` → 10).
  - normalization: with `normalize_baseline=GREEDY`, GREEDY sum-objectives value == 1.0; other solvers = ratio; clip respected (craft tmp rows w/ ratio > clip_upper).
  - filters: exclude_cities drops rows; include_solvers keeps only listed labels.
  - city mode: no Bucket column; mean-over-years grouping (craft 2 rows same city different values → mean).
  - plot smoke (both modes): `MPLBACKEND=Agg`, output png exists + size > 0 under tmp_path.
- [ ] **Step 2: Verify failure.**
- [ ] **Step 3: Implement** rewrite. Port V3 + grouped bodies into the pure fns; `from src.helpers…` → `from helpers…`; output path from config (old hardcoded `../resources/*.png` dies); city-year parse (`rsplit("_", 1)` capitalize) kept in city mode only.
- [ ] **Step 4: Run** — tests green; `grep -n "^#\|^ *#" src/aggregate_results.py` → only real comments, zero commented-out code blocks (AC); `grep -rn "from src\." experiments/src` → empty.
- [ ] **Step 5: Commit** — `git commit -am "T23: single parameterized aggregator"`

---

### Task 4: Sample verify + pyright ratchet + PR

- [ ] **Step 1: Sample run** — after fresh sample analyze (or reuse existing `sample-experiment/results/sample-analysis/metrics-sample-experiment.json`): write scratch config (city mode, output under scratchpad) → `cd experiments/src && poetry run python aggregate_results.py <cfg>` → png produced (AC "produces plots from sample analysis output"). Repeat bucket mode.
- [ ] **Step 2: Pyright ratchet** — retry deleting pandas-related rule disables from `pyrightconfig.json`; keep only still-failing-elsewhere rules; record before/after counts.
- [ ] **Step 3: Full matrix** — pytest (units+e2e) + ruff + format + pyright green; siblings pytest green.
- [ ] **Step 4: PR** — push, PR → `feat/roadmap-base-branch`, title `T23: consolidate aggregators`. Body: config schema, mode↔legacy-script map, archived files, pyright rules re-enabled. Update ROADMAP + `plans/leftovers.md` (note: T24 failure rows will be skipped by `load_rows` automatically; sample aggregator config example for docs/T28).

## Unresolved questions

1. Merged script keeps name `aggregate_results.py` — OK?
2. `include_solvers` matches composed label (`GREEDY`, `PHRAGMEN_{'kappa': 1.0,…}`) exactly as legacy filters did — OK, or match bare solver enum + separate options filter?
3. `normalize_baseline` default None (raw values) — legacy V3 always normalized; sample configs will set GREEDY explicitly. OK?
4. Commit a checked-in example aggregator config under `sample-experiment/` (handy for T28 docs) or scratch-only in this ticket?

## Steps

1. Task 1: AggregatorConfig model (TDD) + commit
2. Task 2: archive legacy variants + commit
3. Task 3: rewrite single aggregator + tests + commit
4. Task 4: sample runs both modes, pyright ratchet, PR, ROADMAP/leftovers update
