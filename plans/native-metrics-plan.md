# Native (C++) metrics via bindings — PoC `exclusion_ratio`

> Planned 2026-10-11 against `7ccd2d5` (`feat/roadmap-base-branch`).

## Context

Analyzer metrics (`experiments/src/helpers/analyzers/metrics.py`) = pure python over pulp objects. Future metrics much heavier → reuse `bindings/` (pybind11/C++20, scikit-build-core) already used for solvers. This PR: mechanism + PoC (`exclusion_ratio` in C++) + parity tests py vs C++. Python impls stay (oracle).

## User decisions (binding)

1. **Separate Metric names** — native = own `Metric` enum entry + own output column; both impls runnable in one analyzer run.
2. **Opaque handle** — `metrics.SolvedInstance(problem)` extracted once per result, passed to every native metric.
3. **Fail loudly** — native metric requested + bindings/metrics module missing → ImportError → `AnalyzerFailure` row, exit 1. No fallback.

## Global constraints

- Branch `feat/native-metrics-bindings` off `feat/roadmap-base-branch`; PR → base. Never main. Stop after PR, wait review.
- No golden regen; `test_e2e_golden.py` + goldens untouched. Existing `EXCLUSION_RATIO` typo kept.
- Poetry venv per project. ruff line-length 79. C++: `bindings/.clang-format`.
- Local bindings build may need (bindings/README): `export SDKROOT=$(xcrun --show-sdk-path); export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"` — try without first.
- Impl by subagents `model: sonnet`, sequential (shared worktree + venv), agents don't commit; main reviews diff + commits per task.

## Verified facts

- experiments already path-deps bindings (`develop=false`) → C++ built on `poetry install`; CI experiments job source-builds, cache key hashes `bindings/src/**` → no CI wiring needed.
- scikit-build-core auto-packages `bindings/src/muoblpbindings/*` (.py/.pyi) → new `metrics.py(i)` shipped automatically.
- Existing `Instance::from_MuoblpProblem` (`bindings/src/common.cpp`) unusable: dense n×m, throws if constraints != 1, no var values. Analyzer problems = multi-constraint (district caps).
- pulp 3.3.2 `LpAffineExpression.value()`: `s = constant; for v,x in items(): s += v.varValue * x` → C++ mirrors same order → bit-identical.
- `prob.variables()` doesn't see vars only in `objectives` → intern objective vars on the fly.
- `analysis_table.py` generic branch handles unknown metric names; `aggregate_results.py` iterates own map → ignores native.
- Lock files record bindings version (`0.0.18`, `type=directory`) → bump needs relock solvers + experiments.

## Design

### C++ (`bindings/`)

New dir `src/metrics/`, namespace `metrics`, static lib `metrics` (PIC) linked into module:

- `solved_instance.hpp/.cpp`
  ```cpp
  struct SolvedInstance {
    struct Term { CandidateId candidate; double coef; };
    struct Voter { double constant; std::vector<Term> terms; };  // pulp dict order
    std::vector<std::string> candidate_names;
    std::unordered_map<std::string, CandidateId> candidate_ids;
    std::vector<double> candidate_values;   // var.varValue snapshot
    std::vector<Voter> voters;              // sparse, 1 per objective
    static SolvedInstance from_MuoblpProblem(py::object prob);
  };
  ```
  Extraction: `prob.variables()` (skip `__dummy`), then `prob.objectives` (`.constant` + items; unknown var → intern). `varValue is None` → `std::invalid_argument`. Constraints/costs/weights NOT extracted (YAGNI; extension point for next metric). Reuse `VoterId`/`CandidateId` from `common.hpp`.
- `metrics.hpp` + `exclusion_ratio.cpp` — pybind-free core: `double metrics::exclusion_ratio(const SolvedInstance&)`; per voter `s = constant; s += value*coef`; count `s == 0`; `/ n`. Empty voters → `std::invalid_argument`.
- `binder.cpp`: `m.def_submodule("metrics")`; `py::class_<SolvedInstance>` (`__init__(prob)`, ro props `num_voters`, `num_candidates`); `metrics.def("exclusion_ratio", ...)` lambda w/ `py::gil_scoped_release` around core (convention for heavy metrics).
- `src/muoblpbindings/metrics.py` (re-export from `.muoblpbindings.metrics`) + `metrics.pyi`. `__init__.py(i)` untouched → `from muoblpbindings import metrics`.
- `CMakeLists.txt`: add lib + link. `pyproject.toml` 0.0.18 → **0.0.19**. Relock solvers + experiments (expect ONLY bindings version line; compare name→version maps).
- README: exposed metrics, `varValue` in core-shape contract, "Adding new metric" steps.

### Python (`experiments/`)

- `helpers/analyzers/model.py`: `Metric.EXCLUSION_RATIO_NATIVE`; `AnalyzerResult.EXCLUSION_RATIO_NATIVE: dict[str, Any] | None = None`.
- NEW `helpers/analyzers/native_metrics.py`:
  - `build_solved_instance(problem)` — lazy `from muoblpbindings.metrics import SolvedInstance`.
  - `exclusion_ratio_native(instance) -> {"exclusion_ratio": float}` (same inner key as python → direct compare).
  - `NATIVE_STRATEGIES: dict[Metric, Callable[[SolvedInstance], dict]]`.
  - `PYTHON_COUNTERPART: dict[Metric, Metric]` = `{EXCLUSION_RATIO_NATIVE: EXCLUSION_RATIO}` — drives parity tests generically.
- `metrics.py::get_metrics`: build handle once iff any requested metric ∈ `NATIVE_STRATEGIES`; dispatch native → handle, else existing `get_metric_strategy(metric)(problem)` (unchanged, python-only).
- `analysis_table.py`: label `"Exclusion ratio (native)"`, round 4.
- `analyzer_runner.py`: no change (ImportError already → `AnalyzerFailure`).

### Tests (`experiments/tests/`)

- Move `make_tiny_problem`/`make_ejr_violation_problem` → `tests/fixtures/problem_factories.py` (+ new: all-excluded, none-excluded, objective-only var, dedup weights, random seeded generator).
- `test_native_metrics.py` (unit):
  - parity: for every `(native, py)` in `PYTHON_COUNTERPART` × every factory → `get_metrics([py, native], p)` values `==` exactly.
  - seeded random parity: ~200 problems (n≤40, m≤15, random utilities/selection).
  - LP roundtrip parity: `write_lp` → `read_lp_file` → `enhance_problem_from_solver_result` → compare.
  - handle semantics: reuse = same result; snapshot (mutate var after build → unchanged).
  - errors: empty objectives (py `ZeroDivisionError` / native `ValueError`); `varValue None` → native `ValueError`.
  - dispatch: handle not built when no native metric (monkeypatch builder to raise); built once otherwise.
  - fail loudly: `sys.modules["muoblpbindings"]=None` (+`.metrics`) → `get_metrics` raises ImportError; `analyze_runner_result` → `AnalyzerFailure`; python-only metrics still OK.
  - `AnalyzerConfig` accepts new name; analysis_table label.
- `test_e2e_native_parity.py` (`e2e` marker): `experiment_runner.main` on `fixtures/input/krakow_2024_mini`, solvers GREEDY/MES_UTILS/MES_ADD1 × utilities COST_ORDINAL/APPROVAL → `analyzer_runner.main` w/ all python counterparts + natives → per row, per pair `row[native] == row[py]`; assert 0 failed, row count, ≥1 row w/ ratio > 0 (else extend fixture config, report).
- No skip-if-missing: bindings mandatory in experiments.

### CI / docs

- `test.yml` build-bindings smoke: add `from muoblpbindings import metrics`.
- `experiments/README.md`: native metrics section (naming, add-metric recipe, parity requirement). Root `CLAUDE.md` + `README.md`: bindings also consumed by experiments.
- `plans/native-metrics-plan.md` = copy of this plan; append note to `plans/leftovers.md`. ROADMAP untouched.

## Verification

1. bindings: rebuild via `poetry sync` in solvers + experiments; `python -c "from muoblpbindings import metrics; print(metrics.exclusion_ratio)"`.
2. experiments: `poetry run pytest` (all, incl. e2e golden unchanged + new parity), `poetry run pyright` → 0, ruff check + format clean.
3. solvers: `poetry run pytest` + pyright (bindings rebuilt, API additive).
4. `git status experiments/tests/fixtures/golden` clean.
5. Mutation check: C++ `s == 0` → `s == 1`, reinstall (`poetry run pip install --force-reinstall --no-deps ../bindings`) → unit + e2e parity FAIL; revert, rebuild, green.
6. Sample smoke: scratch analysis config w/ both metrics on `sample-experiment` results → equal columns (not committed).
7. PR CI green (14 jobs).

## Unresolved questions

1. Name `EXCLUSION_RATIO_NATIVE` (correct spelling, explicit pairing map) vs `EXCLUSION_RATION_NATIVE` (mirrors typo)? Default: correct spelling.
2. Tag/publish `bindings@0.0.19` after merge? Default: bump only, no tag.
3. Native on `varValue is None` → `ValueError`; python silently counts voter as non-excluded. OK to diverge (unreachable in analyzer flow)?
4. Native metrics in aggregator plots / `sample-analysis-config.jsonc`? Default: no.
5. ROADMAP entry (roadmap says refactor-only, complete)? Default: none, `plans/` + leftovers only.

## Steps

1. `git checkout feat/roadmap-base-branch && git pull && git checkout -b feat/native-metrics-bindings`; copy plan → `plans/native-metrics-plan.md`; commit.
2. Agent A (sonnet) — bindings: `src/metrics/*`, binder submodule, `metrics.py(i)`, CMake, version 0.0.19, relock ×2, rebuild both venvs, smoke, bindings README. Review + commit.
3. Agent B (sonnet) — experiments integration: `Metric` + `AnalyzerResult`, `native_metrics.py`, `get_metrics` dispatch, table label, factories move; existing tests green, ruff, pyright. Review + commit.
4. Agent C (sonnet) — tests + docs: `test_native_metrics.py`, `test_e2e_native_parity.py`, CI smoke line, READMEs/CLAUDE.md, leftovers note; run Verification 2–5. Review + commit.
5. Main: full Verification 1–6 independently, fix findings.
6. Push; `gh pr create --base feat/roadmap-base-branch`; watch CI; report PR link; STOP for review.
