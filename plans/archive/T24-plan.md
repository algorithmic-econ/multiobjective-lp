# T24 Logging + Error Propagation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Analyzer `except → None` (loses which meta failed and why — T01 leftover, in-code TODO) → structured `AnalyzerFailure` row in metrics.json + "N of M failed" summary + exit 1 from entrypoint (user decision); `analysis_table` stops regex-parsing meta filenames for semantics — reads solver/utility/city from row content (T19 model fields); remaining status prints → logging (markdown table stays print); no broad excepts left.

**Architecture:** `analyze_runner_result` (post-T20: `pipeline/analyzer_steps.py`) returns `AnalyzerResult | AnalyzerFailure` — failure captures meta path + exception type/message, logged with traceback at error level. `analyzer_runner.main` dumps both row kinds to metrics.json (failure rows carry `error_type` key → downstream skips them), logs summary, RETURNS `(ok, failed)` counts; only `__main__` calls `sys.exit(1)` on failures — e2e calls `main` programmatically with 0 failures → golden byte-identical. `analysis_table` drops the filename regex entirely: old code parsed filename → City/Type/Method then DISCARDED Date-Time/ID columns anyway, and every row already carries `city`/`utility`/`solver` since T19 → table content identical on happy path; failure rows skipped w/ warning; empty df → "no rows" message (kills T01 leftover `Location-Year` KeyError).

**Tech Stack:** T19/T20 models + pipeline, pytest (tmp_path corrupt-meta fixtures, capsys/caplog).

## Global Constraints

- Branch `feat/t24-analyzer-errors` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`.
- **Execute AFTER T20 merge; phase order puts T22/T23 before it** — print-sweep scope assumes consolidated generators/aggregator. Verify tree (post-T21 names: `analyzer_runner.py`, `pipeline/analyzer_steps.py`, `helpers/analyzers/analysis_table.py`).
- e2e golden IDENTICAL, NO regen: happy path produces zero failures → metrics.json rows byte-identical; table output identical (see Architecture). If e2e diffs → a dump-shape regression, STOP.
- No new features: no retry logic, no partial-metric salvage; failure = whole-row failure as today, just named + counted.
- Repo GREEN after ticket: experiments pytest (units+e2e) + ruff + format + pyright; siblings untouched.

---

### Task 1: `AnalyzerFailure` + structured error rows

**Files:**
- Modify: `experiments/src/helpers/analyzers/model.py` (append)
- Modify: `experiments/src/pipeline/analyzer_steps.py` (`analyze_runner_result`)
- Test: `experiments/tests/test_analyzer_errors.py` (new)

**Interfaces:**
- `AnalyzerFailure(StrictModel)`: `meta_path: str`, `error_type: str` (exception class name), `error_message: str`.
- `analyze_runner_result(runner_result_path, metrics) -> AnalyzerResult | AnalyzerFailure` (None return GONE).

- [ ] **Step 1: Failing tests** (each writes corrupt input under tmp_path, calls `analyze_runner_result` directly):
  - invalid json meta → `AnalyzerFailure`, `meta_path` names the file, `error_type` set;
  - schema-valid meta but `problem_path` lp missing → `AnalyzerFailure` (`FileNotFoundError`);
  - meta failing `RunnerResult.model_validate` → `AnalyzerFailure` (`ValidationError`);
  - happy path (reuse a persisted tiny result via `pipeline.problem_steps.persist_result`, pattern from `tests/test_pipeline_steps.py`) → `AnalyzerResult`.
- [ ] **Step 2: Verify failure** — currently returns None on all corrupt cases.
- [ ] **Step 3: Implement** — replace the `except Exception → log + implicit None` tail:

```python
    except Exception as err:
        logger.exception(
            "Failed to analyze result", extra={"problem": runner_result_path}
        )
        return AnalyzerFailure(
            meta_path=runner_result_path.as_posix(),
            error_type=type(err).__name__,
            error_message=str(err),
        )
```

(delete the in-code TODO — this IS that fix.)
- [ ] **Step 4: Run** — new tests + full pytest green.
- [ ] **Step 5: Commit** — `git commit -am "T24: AnalyzerFailure rows instead of silent None"`

---

### Task 2: Runner summary + exit code

**Files:**
- Modify: `experiments/src/analyzer_runner.py`
- Test: `experiments/tests/test_analyzer_errors.py` (append)

**Interfaces:**
- `main(config, console_output_limit=None) -> tuple[int, int]` — `(ok, failed)`; writes metrics.json rows via `row.model_dump(mode="json", exclude_none=True)` for BOTH kinds (the `if row is not None else None` dance dies); logs `logger.error("analysis failed for %d of %d results", failed, total)` when failed>0 else info summary; `__main__`: `sys.exit(1)` if failed.

- [ ] **Step 1: Failing tests** — results dir w/ 1 good persisted result + 1 corrupt meta → `main` returns `(1, 1)`; metrics.json has 2 rows, one w/ `error_type`; all-good dir → `(N, 0)`; caplog has summary line.
- [ ] **Step 2: Verify failure** (main currently returns None).
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** — tests + e2e golden (happy path: rows identical, return value ignored by e2e test).
- [ ] **Step 5: Commit** — `git commit -am "T24: failure summary + nonzero exit"`

---

### Task 3: `analysis_table` reads row content, not filenames

**Files:**
- Modify: `experiments/src/helpers/analyzers/analysis_table.py` (rewrite `transform_metrics_to_markdown_table` head)
- Modify: `experiments/tests/test_analysis_table.py` (replace regex-miss test)

- [ ] **Step 1: Failing tests** (replace file content):
  - rows w/ explicit `city`/`utility`/`solver` fields → table contains Location-Year/Type/Method from FIELDS (craft city value a filename-regex would have mangled, e.g. dir-source city `krakow_2024_mini`);
  - failure row (`error_type` key) in input → skipped w/ warning, table still renders remaining rows;
  - all rows failures / empty list → returns "no rows" message string (NOT KeyError — T01 leftover);
  - metric columns unchanged (Exclusion ratio rounding, Sum objectives, EJR+ violations, generic `METRIC_subkey`).
- [ ] **Step 2: Verify failure** — current code regexes `problem_path` filename, raises ValueError on miss.
- [ ] **Step 3: Implement** — delete `Solver`/`Utility` pattern building + filename regex + ValueError branch; per row: skip if `error_type` in row (warn); `row_data = {"City": item["city"], "Type": item["utility"], "Method": item["solver"]}` (+ existing metric loop); drop the now-dead Date-Time/ID drop; keep Location-Year derivation + sort + `to_markdown` verbatim; guard `if not all_rows_data: return "no analyzable rows"`; `os.path.basename`/`import os` leftovers gone if any survived T20.
- [ ] **Step 4: Run** — tests + e2e golden (table print identical for golden rows — same 3 columns from fields).
- [ ] **Step 5: Commit** — `git commit -am "T24: analysis_table from row fields; no filename-as-schema parsing"`

---

### Task 4: print → logging sweep + narrow excepts

**Files:**
- Modify: `experiments/src/helpers/utils/logger.py` (`except Exception` → `except (OSError, yaml.YAMLError)`)
- Modify: any remaining non-interactive `print(` in `experiments/src` (post-T22/T23 tree: expected only generator "saved to …" status prints → `logger.info`; questionary prompt feedback + markdown table print STAY)

- [ ] **Step 1: Inventory** — `grep -rn "print(" experiments/src --include="*.py"`; classify: KEEP markdown table print (`analyzer_runner`) + interactive prompt-loop feedback; CONVERT status prints.
- [ ] **Step 2: Implement** conversions + logger.py narrowing. `grep -rn "except Exception" experiments/src` → only `analyzer_steps` (structured, Task 1) + `problem_runner` (logs + re-raises — keep).
- [ ] **Step 3: Run** — full pytest; run sample analyze — table still prints.
- [ ] **Step 4: Commit** — `git commit -am "T24: print->logging sweep; narrow excepts"`

---

### Task 5: Full verify + corrupt-meta smoke + PR

- [ ] **Step 1: Matrix** — pytest (units+e2e) + ruff + format + pyright green; siblings pytest green.
- [ ] **Step 2: Manual corrupt-meta smoke** (ticket Verify): fresh sample run; truncate one `results/.../meta_*.json`; `analyze.sh` → metrics.json contains failure row naming that file, stderr summary "1 of N", exit code 1 (`echo $?`); restore/rerun clean → exit 0.
- [ ] **Step 3: AC greps** — `grep -n "re.compile\|pattern.match" experiments/src/helpers/analyzers/analysis_table.py` → empty; `grep -rn "return None" experiments/src/pipeline/analyzer_steps.py` → empty.
- [ ] **Step 4: PR** — push, PR → `feat/roadmap-base-branch`, title `T24: analyzer error propagation + logging`. Body: failure-row schema, exit-code contract (`main` returns counts, `__main__` exits), table now field-driven, T01 leftovers closed (silent None, Location-Year KeyError). Update ROADMAP + `plans/leftovers.md` (T26 relies on these failure paths for coverage; aggregator `load_rows` already skips failure rows — T23).

## Unresolved questions

1. Failure rows mixed into metrics.json (distinguished by `error_type` key) vs separate `errors-*.json` file — plan assumes mixed (single artifact, downstream skips). Confirm.
2. Summary log level `error` when failed>0 — or `warning`?
3. `analysis_table` empty-input return string `"no analyzable rows"` printed as table output — OK?

## Steps

1. Task 1: AnalyzerFailure + structured returns (TDD) + commit
2. Task 2: main counts/summary/exit-1 + commit
3. Task 3: table from row fields, tests replaced + commit
4. Task 4: print→logging + except narrowing + commit
5. Task 5: matrix, manual corrupt-meta smoke, AC greps, PR, ROADMAP/leftovers update
