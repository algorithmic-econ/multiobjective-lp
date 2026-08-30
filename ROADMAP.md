# ROADMAP — cleanup & redesign

Living document. Tickets sized for one agent session each, executed top-down within phase. Update checkbox + PR link when done. When starting work on a ticket create a new branch, then PR should target the "feat/roadmap-base-branch", only after all tickets are done and verified I will create PR to main branch.

## 1. Context

Monorepo extends PuLP to multiobjective LP (`core` → `muoblp`) with custom solvers from computational social choice (`solvers` → `muoblpsolvers`; key focus: Method of Equal Shares for participatory budgeting) and an experiment pipeline over pabulib instances (`experiments`). Separate repo `muoblpbindings` (pybind11/C++20, scikit-build-core) holds performance-critical algorithm implementations and gets merged in here (#20).

Project grew without clear requirements; this roadmap converts it to a maintainable state. End state: **py3.13 monorepo of 4 poetry projects** (`core`, `solvers`, `experiments`, `bindings`), PuLP-contract-compliant solvers, cleaned script pipeline (Pydantic v2 at IO boundaries, pyright, snake_case, thin entrypoints + shared lib), golden e2e test, full CI (lint/type/test/build/publish), one canonical sample experiment. **Refactor-only: no new features** (see §5).

Backward compat: none required — configs, result formats, and APIs are free to break.

## 2. Conventions for executing agents

- 1 ticket = 1 session = 1 PR/commit-set. Repo GREEN after every ticket: all subproject `poetry run pytest` + ruff + pyright + e2e golden.
- Do NOT start a ticket whose TODO-decide dependency (§6) is unresolved.
- Verify recipe: `cd <proj> && poetry install && poetry run pytest`; e2e: `cd experiments && poetry run pytest -m e2e`; sample smoke: `experiments/sample-experiment/run.sh` + `analyze.sh`.
- Golden files regenerated ONLY when ticket explicitly allows; regen = separate commit with justification.
- No new features. If ticket outgrows a session: split, update this file, finish the split part.
- Dead code moves to `archived_code/` (ruff CI already excludes it), never plain-deleted.
- Follow root `CLAUDE.md` (concision, poetry venv per project).
- Plan docs under `plans/` written BEFORE their dependency ticket merged are NOT trustworthy: re-derive every path/module name from the merged tree. Known-stale: `T21-plan` (fixed in-session), `T24-plan`, `T25-plan`, `T26-plan`, `P3-verify-plan` — all assume an `experiments/src/pipeline/` package that never shipped (T20 kept `helpers/`, added `helpers/utils/result_naming.py`).

## 3. Phases

```
P0 safety net    T01 → T02 → T03
P1 toolchain     T04 → {T05, T06}; T06 → T07 → T08; T09 (after T02)
P2 solver contract T10 → {T11..T16, T18}; T17 (after T12,T13)
P3 experiments   T19 → T20 → T21 → {T22..T25}; T26 (after T20,T24)
P4 core + docs   T27, T28
P5 release+harden T29; T31 (D15); T32; T30 (after T23, T26, T27)
```

| Phase | Goal | Tickets |
|---|---|---|
| P0 | Pipeline runs + golden e2e + baseline CI before any refactor | T01–T03 |
| P1 | py3.13, pulp 3.x, bindings merged, publish fixed, legacy pruned | T04–T09 |
| P2 | Solvers implement PuLP contract | T10–T18 |
| P3 | Experiments cleanup: Pydantic, lib extraction, dedup, tests | T19–T26 |
| P4 | Core micro-fixes + docs | T27–T28 |
| P5 | Release chain + hardening leftovers (added 2026-08-25) | T29–T32 |

## 4. Tickets

### Phase 0 — Safety net

#### [x] T01 Fix pipeline-blocking bugs
Deps: — · GH: — · PR: [#37](https://github.com/algorithmic-econ/multiobjective-lp/pull/37)
- `experiments/src/helpers/analyzers/metrics.py:4` — import `muoblpsolvers.common` doesn't exist (lives in `muoblpsolvers/mes/common.py`); fix import or add re-export.
- `experiments/src/helpers/utils/utils.py` — `write_to_json` compares `path.suffix == "jsonc"` (missing dot, always False); fix jsonc branch.
- `experiments/src/helpers/runners/solverStrategy.py:17` — crashes when `solver_options is None`; guard.
- `experiments/src/helpers/analyzers/analysis_table.py:56` — bare `Exception` on filename-regex miss; raise with offending filename (full fix in T24).

AC: regression unit test per bug; sample-experiment `run.sh` + `analyze.sh` produce metrics json.
Verify: `cd experiments && poetry run pytest`; run sample end-to-end.

#### [x] T02 Tiny fixture + e2e golden test
Deps: T01 · GH: — · PR: [#38](https://github.com/algorithmic-econ/multiobjective-lp/pull/38)
- Trim `sample-experiment/input/krakow_2024` to ~10 projects/~30 voters/1–2 districts → commit under `experiments/tests/fixtures/`.
- Tiny experiment + analyzer configs; pytest e2e invoking runner+analyzer programmatically, `concurrency=1`; solvers: GREEDY, MES_UTILS, MES_ADD1.
- Golden files (selected vars, metrics) committed; normalization layer strips nondeterminism (times, timestamps, abs paths, float precision — propose exact list in PR, see D11); pytest marker `e2e`.

AC: `pytest -m e2e` deterministic across 3 consecutive runs; mutating a solver constant fails the test; diff readable.
Verify: run 3×; mutation test; revert.

#### [x] T03 Baseline CI for all subprojects
Deps: T02 · GH: — · PR: [#39](https://github.com/algorithmic-econ/multiobjective-lp/pull/39)
- Extend `.github/workflows/test.yml` from solvers-only to core + solvers + experiments (poetry install + pytest incl. e2e, every PR).
- Add pyright job per subproject (basic mode; temporary ignores allowed to get green baseline; ratchet later per D12).
- (Pulled forward from T04) experiments python → `>=3.13` so poetry resolves bindings 0.0.17.

AC: green Actions run on branch; e2e golden runs in CI.
Verify: push branch, observe Actions.

### Phase 1 — Toolchain & repo unification

#### [x] T04 Unify Python → 3.13
Deps: T03 · GH: — · PR: [#40](https://github.com/algorithmic-econ/multiobjective-lp/pull/40)
- `core` `>=3.11` → `>=3.13`; (experiments done in T03); regenerate poetry.lock everywhere; fix fallout.
- CI python → 3.13 everywhere (test.yml done in T03; fix `publish.yml` build step, currently 3.12).

AC: core locks+installs+tests green on 3.13; experiments bindings 0.0.17 already satisfied (T03).
Verify: CI green.

#### [x] T05 Bump pulp → latest 3.x
Deps: T04 · GH: — (meeting note: bump to newest) · PR: [#41](https://github.com/algorithmic-econ/multiobjective-lp/pull/41)
- Bump pin in core+solvers+experiments; fix `core/src/muoblp/model/multi_objective_lp.py` import-time monkeypatch (`LpCplexLPLineSize`) + model against pulp 3.x internals; fix `LpSolver` base usage in solvers if signature moved.
- Timeboxed: if 3.x breaks fundamentally, fall back to newest 2.x and file GH issue with findings.

AC: all tests + e2e golden green on new pulp; consistent pin across subprojects.
Verify: full CI; run sample.

#### [x] T06 Merge muoblpbindings into monorepo
Deps: T04 · GH: #20 · PR: [#42](https://github.com/algorithmic-econ/multiobjective-lp/pull/42)
- Squash-import muoblpbindings tree as `bindings/` (history stays in archived old repo — archive it on GH manually after merge).
- Keep scikit-build-core/CMake/pybind11 layout + `.clang-format`; drop stale empty poetry.lock, gitignored wheelhouse artifacts.
- `solvers/pyproject.toml`: `muoblpbindings==0.0.17` → path dep for dev (publish-time range pin in T18).
- Document bindings' implicit dep on core model shape (`common.cpp` reads `.objectives`/`.objectives_weights`) in `bindings/README.md`; update root README + CLAUDE.md repo structure (4 subprojects).

AC: `poetry install` in solvers builds bindings locally (CMake + C++20 toolchain documented); solvers tests green; `python -c "import muoblpbindings"` works.
Verify: fresh-venv install + pytest in solvers.

#### [x] T07 Bindings CI in monorepo
Deps: T06 · GH: #20, #25 (partial) · PR: [#43](https://github.com/algorithmic-econ/multiobjective-lp/pull/43)
- Port `wheels.yml` (cibuildwheel 3.4.1, ubuntu/macos-15/windows, cp313+cp314, OIDC PyPI) with `bindings/` paths; trigger: `bindings@x.y.z` tag (independent semver).
- PR-time job: build bindings wheel on linux + import smoke test; solvers test job runs against built artifact.

AC: PR CI builds bindings + runs solvers tests; wheels workflow passes via `workflow_dispatch` dry run.
Verify: Actions runs, artifacts uploaded.

#### [x] T08 Fix publish workflow
Deps: T04, T06 · GH: #25 · PR: [#44](https://github.com/algorithmic-econ/multiobjective-lp/pull/44)
- Diagnose 400 (likely: version-already-exists re-upload, or solvers wheel metadata carrying path dep). Ensure `poetry build` of solvers rewrites `muoblp` path dep → version pin; drop unnecessary `poetry install` before build.
- Add tag ↔ pyproject-version consistency check; decide `skip-existing` vs hard fail with clear message; route `bindings@x.y.z` tags to wheels workflow.

AC: rc tag publish to test.pypi succeeds for core and solvers; `pip download` METADATA has valid version-pinned deps, no path refs.
Verify: push `solvers@X.Y.Z-rc`, confirm test.pypi upload + METADATA.

#### [x] T09 Prune legacy artifacts, canonicalize sample-experiment
Deps: T02 · GH: — · PR: [#45](https://github.com/algorithmic-econ/multiobjective-lp/pull/45)
- Fix or delete configs with absolute `/Users/jasiek` paths; fix stale configs (invalid `"MES"` solver_type, `no-constraints.json` vs `.jsonc` ref).
- `.gitignore` generated results; keep `sample-experiment/` as the one canonical sample (relative paths only).

AC: `grep -r "/Users/jasiek" --include=*.json*` empty; sample run.sh+analyze.sh work; e2e golden green.
Verify: run sample; git file count drops ~25k.

### Phase 2 — Solver PuLP-contract compliance

#### [x] T10 Unified constructor + PuLP native options
Deps: T05 · GH: #23 · PR: [#46](https://github.com/algorithmic-econ/multiobjective-lp/pull/46)
- All 10 solvers + `ElectionSolver`: `__init__(self, msg=True, timeLimit=None, options=None, ...)` calling `super().__init__(...)`.
- Migrate custom positional `solver_options` (Constrains/Exponential/Phragmen) and `use_gurobi` flag (Summed) into PuLP `options`/kwargs so `toDict()`/`toJson()` serialize them.
- Update `experiments/src/helpers/runners/solverStrategy.py` + config plumbing in SAME ticket (atomically green).

AC: no custom positional `solver_options` remains; every solver instantiable with `(msg=False, timeLimit=10)`; e2e golden green (values unchanged).
Verify: solvers+experiments pytest; e2e; `grep -r solver_options` clean.

#### [x] T11 available() + lazy bindings imports
Deps: T10 · GH: #22 · PR: [#47](https://github.com/algorithmic-econ/multiobjective-lp/pull/47)
- Move 6 top-level `from muoblpbindings import ...` into guarded/function-scope imports; `muoblpsolvers/__init__.py` stops failing eagerly without bindings.
- `available()` on all 10: binding-backed return importability of muoblpbindings; pure-python (Greedy, Exponential, Phragmen, Summed) return True; remove 3 hardcoded `True` stubs.

AC: `import muoblpsolvers` succeeds without bindings installed; `available()` truthful; test simulating missing bindings (sys.modules monkeypatch).
Verify: scratch venv without bindings → import + available checks; full pytest with bindings.

#### [x] T12 Status contract
Deps: T10 · GH: — · PR: [#48](https://github.com/algorithmic-econ/multiobjective-lp/pull/48)
- Greedy, MES-Constrains, MES-Exponential currently never set `lp.status` and return `None` from `actualSolve` — fix: assign status via PuLP constants (reuse `utils.set_solved`), return status. Audit remaining 7.
- Add `lp.status == LpStatusOptimal` assertions to ALL existing solver tests.

AC: no `actualSolve` returns None; every solver test asserts status.
Verify: solvers pytest; e2e golden.

#### [x] T13 Raise for incompatible programs
Deps: T12 · GH: #36 · PR: [#49](https://github.com/algorithmic-econ/multiobjective-lp/pull/49)
- Shared validation in `ElectionSolver`/util: reject continuous vars, non-0/1 bounds, missing objectives etc. (enumerate from #36); raise `PulpSolverError` naming the offending var/feature.
- No capability widening (#31/#34/#35 stay excluded).

AC: solving incompatible program raises with actionable message; negative test per rejection rule.
Verify: solvers pytest.

#### [x] T14 Time & verbosity contract
Deps: T10 · GH: #26, #27, #32 · PR: [#53](https://github.com/algorithmic-econ/multiobjective-lp/pull/53)
- Remove manual `time.time()` tracking (PuLP `solutionTime` covers it — adjust experiments meta accordingly).
- Honor `timeLimit` in pure-python solver loops (abort → defined status). Binding-backed solvers: behavior per **D8** (blocked until decided).
- Gate all solver output behind `self.msg`; logs explain rule decisions (elect/remove candidates etc.).

AC: `msg=False` → zero stdout during solve (capsys tests); `timeLimit=0.001` terminates pure-py solver early with defined status; no `time.time()` in solver bodies.
Verify: solvers pytest; e2e golden (timing fields normalized).

#### [x] T15 Register solvers in PuLP
Deps: T10, T11 · GH: #24 · PR: [#50](https://github.com/algorithmic-econ/multiobjective-lp/pull/50)
- Registration via `pulp._all_solvers` monkeypatch on `muoblpsolvers` import (or explicit `register_solvers()`; pick per pulp 3.x mechanics from T05); document in solvers README.

AC: `pulp.getSolver(name)` works for all 10; `pulp.listSolvers()` includes them; registration test.
Verify: solvers pytest; interactive venv check.

#### [x] T16 Dedupe transform + unify feasibility
Deps: T10 · GH: — · PR: [#51](https://github.com/algorithmic-econ/multiobjective-lp/pull/51)
- Single `molp_to_simple_election`: keep `solvers/src/muoblpsolvers/election_solver.py:104`; experiments' dead `transformers/molpToSimpleElection.py` → `archived_code/`.
- Single feasibility impl: keep LP-solve `is_feasible` (LB constraints make `lp.valid()` insufficient — meeting notes); replace `lp.valid()` call sites (Phragmen, Exponential); optimize (reuse/warm model instead of fresh CBC problem per candidate).

AC: one transform, one feasibility impl; e2e golden identical; measurable is_feasible speedup noted in PR.
Verify: e2e golden; solvers pytest; grep removed symbols.

#### [x] T17 Solver test coverage sweep
Deps: T12, T13 · GH: — · PR: [#54](https://github.com/algorithmic-econ/multiobjective-lp/pull/54)
- Unit tests on tiny hand-built instances for Phragmen, MES-Exponential, MES-Constrains, Summed, ExpandingApprovals, STV, SolidCoalitionRefinement (binding-backed skip-if-unavailable); assert status + selected vars. Rename `test_mes_base.py` → matches utility solver.

AC: every solver module ≥1 test with status+selection asserts.
Verify: `pytest --collect-only`; CI green incl. bindings job.

#### [x] T18 Solvers pyproject hygiene
Deps: T06 · GH: — · PR: [#52](https://github.com/algorithmic-econ/multiobjective-lp/pull/52)
- pytest → dev group (currently runtime dep); single poetry style (drop mixed PEP-621/poetry); bindings dep = path for dev, `>=0.0.17,<0.1` range in published metadata; pulp constraint matches T05.

AC: `poetry check` clean; `poetry install --only main` has no pytest; built wheel METADATA correct.
Verify: `poetry build` + inspect; CI green.

### Phase 3 — Experiments refactor

#### [x] T19 Pydantic v2 models at IO boundaries
Deps: T10 · GH: — · PR: [#55](https://github.com/algorithmic-econ/multiobjective-lp/pull/55)
- Replace TypedDicts in `helpers/runners/model.py` + `helpers/analyzers/model.py` (RunnerConfig, ExperimentConfig, CompactExperimentConfig, RunnerConfigsGenerator, SolverSpec, ConstraintConfig, RunnerResult, AnalyzerConfig, AnalyzerResult) with Pydantic v2 models; validate on config load, meta read/write, metrics write.
- Wire ALL 10 solvers into Solver enum + `solverStrategy` dispatch (add STV, SolidCoalitionRefinement, ExpandingApprovals).
- Drop unimplemented `"METADATA"` metric literal; dedupe `District`/`AgentId` aliases (defined twice); update sample-experiment + test configs to new schema.

AC: malformed config → ValidationError with field path (test); all tests + e2e green; pyright green on models; add `pydantic` dep.
Verify: pytest; run sample; feed broken config.

#### [x] T20 Extract shared pipeline lib
Deps: T19 · GH: — · PR: [#56](https://github.com/algorithmic-econ/multiobjective-lp/pull/56)
- Pure-function lib under `experiments/src/` package: config expansion (kill in-place mutation in experimentRunner), problem pipeline steps (load pabulib → district split → transform → cache → solve → persist), analyzer steps, result cache.
- pathlib everywhere; dedupe filename logic (`problemRunner.py:85` ↔ `resultCache.py:52`); kill trailing-slash f-string concat; un-hardcode analyzer `Pool(processes=3)` → config field.
- Runner scripts become thin orchestration (~50 lines); unit tests for extracted fns (expansion, cache key, path resolution).

AC: thin entrypoints; lib unit-tested; e2e golden identical.
Verify: pytest (units + e2e); run sample.

#### [x] T21 snake_case renames + entrypoint/doc sync
Deps: T20 · GH: — · PR: [#57](https://github.com/algorithmic-econ/multiobjective-lp/pull/57)
- `git mv` all camelCase modules (experimentRunner→experiment_runner, problemRunner, analyzerRunner, solverStrategy, sourceStrategy, resultCache, enhanceFromSolverResult, pabutools*, generate*, aggregate*; fix "Phargmen" misspelling); consistent absolute imports.
- Update run.sh/analyze.sh, experiments README, pyrightconfig, test imports, CI paths in SAME ticket.

AC: no camelCase filenames in experiments/src; sample scripts work; CI green.
Verify: e2e golden; run sample; grep `src/[a-z]+[A-Z]`.

#### [x] T22 Consolidate config generators
Deps: T19, T21 · GH: — · PR: [#58](https://github.com/algorithmic-econ/multiobjective-lp/pull/58)
- Keep interactive generator (owns `discover_sources`/`filter_paths`/`prompt_*` helpers) as base; fold compact-config flow (delete ~50-line dup prompt loop); superseded `generateExperiment.py` → archived_code; rewrite hardcoded sweep generator atop shared helpers with sweep params from config.
- Output via `model_dump` of T19 models.

> **Stale-check 2026-08-25** — post-T21 names: `generate_experiment_config.py` (interactive base; owns `prompt_allowed_solvers:51`, `prompt_solver_options:62`, `discover_sources:82`, `filter_paths:94`), `generate_compact_experiment_config.py` (dup prompt loop `:44-67` ≈ `:175-198`, ~24 lines verbatim + ~14 preceding), `generate_experiment.py` (superseded, 90L), sweep = `generate_phragmen_greedy_district_experiment.py` (own dup `filter_paths:25-35`, params hardcoded `:74-80`). **`model_dump` bullet ALREADY SATISFIED by T19 in all 4 — no work there.** Add to scope: hardcoded `/Users/jasiek` example paths (`generate_experiment.py:62`, `generate_phragmen_greedy_district_experiment.py:39`, `generate_compact_experiment_config.py:113`) and `resources/…` default outputs (`generate_phragmen_…:40,:100`, `generate_experiment.py:79`) pointing at the dir T09 emptied. `plans/T22-plan.md` paths verified current.

AC: one interactive + one sweep entrypoint; zero dup helpers; generated config validates + runs.
Verify: generate → run; pytest on non-interactive helpers.

#### [x] T23 Consolidate aggregators
Deps: T21 · GH: — · PR: [#59](https://github.com/algorithmic-econ/multiobjective-lp/pull/59)
- Merge `aggregateResults.py` + `aggregateGroupedResults.py` → one parameterized plotting script (filters, grouping, output paths via Pydantic model); ~290 commented lines + hardcoded city filters → archived_code; fix broken `from src.helpers` imports.

> **Stale-check 2026-08-25** — post-T21 names `aggregate_results.py` (539L; commented blocks `247-428` + `431-539` ≈ 291L, matches "~290") / `aggregate_grouped_results.py` (170L). Broken imports live at `aggregate_results.py:11` + `aggregate_grouped_results.py:11`. **"Hardcoded city filters" is not literal** — no city-name lists in either file today, only generic `{city}_{year}` parsing (`aggregate_grouped_results.py:37-46`); `plans/T23-plan.md:5` cites Zabrze/Amsterdam filters — re-derive before trusting. `aggregate_results.py:16` already carries a `# … (T23 rewrites aggregators on models)` marker.

AC: one aggregator; no commented-out blocks; produces plots from sample analysis output.
Verify: run on sample metrics; ruff/pyright green.

#### [x] T24 Logging + error propagation
Deps: T20 · GH: — · PR: [#60](https://github.com/algorithmic-econ/multiobjective-lp/pull/60)
- analyzer broad `except → None` (loses metadata, in-code TODO) → structured error entry in results + nonzero failure summary.
- `analysis_table` stops regex-parsing meta FILENAMES for semantics — read fields from meta json content (T19 model).
- print → logging (table output stays print); remove remaining bare excepts.

> **Stale-check 2026-08-25** — target live: `analyzer_runner.py:47-52`, TODO cites T24 by name. Regex still at `analysis_table.py:19-57`; rows already carry `city`/`solver`/`utility` from T19 `AnalyzerResult` (`helpers/analyzers/model.py:29-46`) — swap is a read-fields change, table content identical on happy path. **No bare `except:` exists anywhere in `experiments/src`** — read the bullet as broad `except Exception`: 3 sites, `analyzer_runner.py:47` (the target), `problem_runner.py:89` (re-raises, OK), `logger.py:17` (narrow to `OSError`/`yaml.YAMLError`). print-sweep is ~6 lines, all inside T22's generator scripts — coordinate or defer; `analyzer_runner.py:93` table print stays. Also drop `os.path.basename` (`analysis_table.py:42`). **Removing the regex invalidates `tests/test_analysis_table.py:9` (`test_filename_regex_miss_raises_with_filename`)** — rewrite or delete it in this ticket. **`plans/T24-plan.md` STALE** (assumes `src/pipeline/analyzer_steps.py`).

AC: corrupt meta file → named structured error, not silent None; no filename-as-schema parsing.
Verify: corrupt a meta, run analyzer; e2e golden.

#### [ ] T25 Dead code sweep
Deps: T21 · GH: —
- To `archived_code/`: `preflibToMuoblp.py`, `explore.ipynb`, dead `pabutoolsUtils.filter_projects`/`by_district`, anything else unreferenced (grep imports).

> **Stale-check 2026-08-25** — post-T21 name `preflib_to_muoblp.py` (0 refs, confirmed). `explore.ipynb` at `experiments/src/explore.ipynb` (only ref = ruff-format exclude `experiments/pyproject.toml:57`). `pabutools_utils.py:70,76` `filter_projects`/`by_district` = definitions only, 0 call sites (`load_pabutools_by_district:43` IS used — don't touch). Add: commented dead block `helpers/analyzers/metrics.py:111-175`. Do NOT classify `generate_*`/`aggregate_*` as dead here — they're live unconsolidated entrypoints owned by T22/T23. **`plans/T25-plan.md` assumes T22/T23 already landed — they have not.**

AC: no unreferenced module in experiments/src; ruff F401 clean.
Verify: pytest + e2e; grep archived symbols.

#### [ ] T26 Experiments coverage sweep
Deps: T20, T24 · GH: —
- Unit tests: metrics computation (tiny fixtures), result cache hit/miss/invalidation, utils jsonc read/write roundtrip, generator pure helpers. Keep existing 54 transform tests.

> **Stale-check 2026-08-25** — **already satisfied, drop from scope**: jsonc read/write roundtrip (`tests/test_utils.py:9,15`, added T01) and cache hit/miss (`tests/test_models.py:116,131,166`, added T20). Remaining real gaps: metrics 2/6 covered (`test_metrics.py` has TOTAL_COST + SUM_OBJECTIVES; missing EXCLUSION_RATION, EJR_PLUS, CONSTRAINTS, INSTANCE_SIZE); cache *content-based* invalidation (`result_cache.py:28-40`, `constraints_configs`/`deduplicate_objectives` mismatch) untested; no-test modules = `source_strategy.py`, `enhance_from_solver_result.py`, `logger.py`, `pabutools_utils.py`, generator helpers. "54 transform tests" → 55 by `def test_` count (suite total 87 defs / 104 collected). **`plans/T26-plan.md` STALE** (`pipeline/`, `tests/test_pipeline_*.py`).

AC: every lib module imported by ≥1 test; cache-hit-skips-solve asserted.
Verify: `pytest --cov` informal; CI green.

### Phase 4 — Core micro-fixes + docs

#### [ ] T27 Core micro-fixes (approved subset only)
Deps: T02, T05 · GH: —
- Mutable default args `objectives=[]`/`objectives_weights={}` → None-pattern (`multi_objective_lp.py:18`).
- Writer `int(val)` silently truncates non-integer coefficients (`lp_writer_utils.py:51`) → raise/warn.
- `__iadd__` appends to objectives list (in-code TODO, `multi_objective_lp.py:65`).
- Fix empty `core/example/` referenced by README (populate minimal example or fix README).
- `read_lp_file` fragility (int-coerced coefs, "+"-only LHS split): document as known limitation, do NOT rewrite.

> **Stale-check 2026-08-25** — line refs: mutable defaults at `multi_objective_lp.py:20-21` (not `:18`); `__iadd__` TODO at `:68` (not `:65`); `lp_writer_utils.py:51` correct. `core/example/` **does not exist** (not "empty"); dead link at `core/README.md:15`. `read_lp_file` int-coercion at `lp_reader_utils.py:57,118,127`, `"+"`-split at `:58,84`. Core has only `tests/test_import.py` (1 smoke test) — "unit test per fix" starts from zero scaffolding. Scope note: the pyright-ignore at `multi_objective_lp.py:19` says "fix in T27" but that fix is **not** in T27's bullets → owned by T30.

AC: unit test per fix; core pytest + e2e golden identical.
Verify: core pytest; write/read roundtrip test.

#### [ ] T28 Docs finalization + issue triage
Deps: phases substantially done · GH: closes folded issues
- Per-subproject READMEs (incl. bindings build instructions); root README dev workflow (poetry per project, sample-experiment entry point, tag/publish conventions); CLAUDE.md 4-subproject structure.
- Close folded GH issues with commit refs; triage `documentation/docs/meeting-notes.md` — convert remaining unimplemented ideas (LB strategies, exp-MES B_init, PropRank removal logic, MES generic utilities) into GH issues, trim notes file.

> **Stale-check 2026-08-25** — root `CLAUDE.md:8-13` **already documents the 4 subprojects** → drop that bullet. `mes-standard-experiments`: 0 hits repo-wide → that AC example is moot. Real dead refs: `solvers/README.md:19` (links standalone `jasieksz/muoblpbindings`), `core/README.md:15` (missing `./example/define_pb.py` — T27 may fix first). `bindings/README.md` already covers build + publish adequately. `documentation/docs/meeting-notes.md` = 208L; the 4 named ideas at `:12-30` (LB strategies), `:112-125` (exp-MES B_init), `:101-103` (PropRank removal), `:127-133` (MES generic utilities); `:185-208` is MkDocs admonition boilerplate, also trim-able. 13 GH issues open — #20/#22/#23/#24/#25/#26/#27/#32/#36 all functionally done, close with commit refs. Cosmetic carry-over: solvers `[project.urls]` → `algorithmic-econ/`.

AC: fresh-clone instructions reproduce sample experiment; no doc refs to dead paths (mes-standard-experiments, old bindings repo).
Verify: follow README in scratch venv.

### Phase 5 — Release & hardening

Added 2026-08-25: gaps carried through P1/P2 judge verdicts + T13/T16/T17 deferrals that had no owning ticket.

#### [ ] T29 Release chain: publish bindings 0.0.18 + rc rehearsal
Deps: T18 · GH: #25
- **Active defect**: `solvers/pyproject.toml:18` pins `muoblpbindings>=0.0.18,<0.1`; PyPI has only 0.0.17 (`bindings/pyproject.toml:7` = 0.0.18, never tagged) → any published solvers wheel is uninstallable.
- Push `bindings@0.0.18` → wheels.yml tag path (validate_tag + 6-wheel matrix + OIDC upload; never exercised end-to-end, T07 leftover).
- rc rehearsal (T08 leftover): `core@X.Y.Z-rc`, `solvers@X.Y.Z-rc` → test.pypi; `pip download` METADATA check. Publish order bindings → core → solvers.
- Archive old `algorithmic-econ/muoblpbindings` GH repo (T06 follow-up; still `isArchived:false`).

AC: clean-venv `pip install muoblpsolvers` resolves bindings from the index; wheels.yml tag run green; old repo archived.
Verify: clean venv install from (test.)pypi; `gh repo view … --json isArchived`.

#### [ ] T30 Finish pyright ratchet (D12)
Deps: T23, T26, T27 · GH: —
- solvers: drop config `reportArgumentType: "none"` (15 systemic `Utility`/int + float/int + dict-invariance errors across mes_*, phragmen) — fix or narrow per-file.
- experiments: drop remaining 3 of the original 10 rules (`reportArgumentType`, `reportAttributeAccessIssue`, `reportCallIssue`); T19 already re-enabled 7.
- 6 inline ignores, all pulp-3.3.2 Optional-`name`: `core/…/multi_objective_lp.py:19` (the one labelled "fix in T27"), `solvers/…/mes/common.py:62,63`, `solvers/…/election_solver.py:196`, `experiments/tests/test_constraint_creation.py:278,279`.

AC: no rule suppressions in the 3 pyrightconfigs, 0 errors each; every surviving inline ignore carries an upstream-unfixable justification.
Verify: pyright ×3; full pytest ×3 + e2e golden.

#### [ ] T31 GE/lower-bound constraints in MES-family
Deps: T16 · GH: #36 · **blocked on D15**
- MES-Add1/Utility/Constrains/Exponential, STV, ExpandingApprovals, SCR silently IGNORE GE constraints → wrong answers, not crashes (T13 dropped rule; P2 judge: open, no owner).
- Per **D15**: either reject in `validate_election_program` with `PulpSolverError`, or document as a limitation + open a GH issue. Greedy keeps GE support (`FeasibilityChecker` LP path).
- Also collapse (P2 judge misfiled these under core-only T27): `validate_pb_constraint` double-walk (`validate_election_program` + `molp_to_simple_election` each call it), and the redundant dup-PB check in `mes/common.py::get_total_budget_constraint`.

AC: GE program + MES-family solver either raises an actionable error or is documented and tested as ignored; constraint list walked once per solve; negative test either way.
Verify: solvers pytest; e2e golden (no GE in fixtures → must stay identical).

#### [ ] T32 py3.14 in test matrix (resolves D14)
Deps: — · GH: —
- `.github/workflows/test.yml:22,55,104` are 3.13-only; wheels.yml already builds cp314.
- Add 3.14 to test + pyright matrix, or resolve D14 as "no" and record the rationale.

AC: CI green on 3.13 (+3.14 if adopted), or D14 closed in §6 with rationale.
Verify: Actions run on branch.

## 5. Future / explicitly excluded (no tickets)

- GH #30 (metrics weights), #31/#34 (continuous vars), #35 (arbitrary upBound)
- LB constraint strategies + 5 experiment variants (meeting notes)
- New metrics (EJR+, exclusion ratio extensions, cost utilities)
- Exponential-MES B_init tuning; full CLI package for experiments; uv migration

## 6. TODO: decide

- **D8** DECIDED (T14): binding-backed solvers (STV, ExpandingApprovals, SolidCoalitionRefinement, MES-Add1, MES-Utility) `warnings.warn` + ignore `timeLimit` (C++ changes out of scope). MES-Constrains honors it coarsely per-iteration (no warn).
- **D11** RESOLVED (T02): normalization field list lives in `experiments/tests/golden_utils.py`, confirmed in PR #38.
- **D12** pyright strictness ramp — scoped as **T30**: finish the basic-mode ratchet (remove remaining rule suppressions + inline ignores) first; standard/strict per subproject stays a later question.
- **D14** Add py3.14/cp314 to test matrix (wheels already build cp314)? — owned by **T32**.
- **D15** MES-family (MES-*, STV, ExpandingApprovals, SCR) + GE/lower-bound constraints: reject with `PulpSolverError`, or document as known limitation + GH issue? Blocks **T31**.
- Default kept: `papers/`, `documentation/` MkDocs untouched by this roadmap.

## 7. GH issue map

| Issue | Ticket |
|---|---|
| #20 merge bindings | T06, T07 |
| #22 available() | T11 |
| #23 native options | T10 |
| #24 register in PuLP | T15 |
| #25 fix publish | T08 |
| #26 no manual timing | T14 |
| #27 respect timeLimit | T14 |
| #32 respect msg | T14 |
| #36 raise incompatible | T13, T31 |
| #30 #31 #34 #35 | excluded → §5 |

All folded issues (#20, #22, #23, #24, #25, #26, #27, #32, #36) are still OPEN as of 2026-08-25 — closed with commit refs in T28; #25 also exercised by T29.
