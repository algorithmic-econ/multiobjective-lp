# T19 Pydantic v2 Models at IO Boundaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 9 TypedDicts in `helpers/runners/model.py` + `helpers/analyzers/model.py` with Pydantic v2 models validated at every IO boundary (config load, meta read/write, metrics write); wire all 10 solvers into a `Solver` StrEnum + `solverStrategy` dispatch; drop `"METADATA"` metric; dedupe `District`/`AgentId`; fix `__dummy` instance_size bug (goldens regen, separate commit).

**Architecture:** `Literal` aliases become `StrEnum`s (py3.13; str subclass → f-string filename construction in `problemRunner.py`/`resultCache.py` unchanged, dict lookup by plain string still works, `re.escape(member)` works). TypedDicts become `BaseModel(extra="forbid")` — typo'd config key → `ValidationError` with field path. Boundaries: `parse_experiment_config` (new, handles compact-vs-full + dict passthrough so e2e/dict callers keep working), `AnalyzerConfig.model_validate` in analyzer main, `RunnerResult.model_validate` on meta read (analyzer + cache), `model_dump(mode="json", exclude_none=True)` on meta/metrics write. Models pickle fine → `multiprocessing.Pool.map` over `RunnerConfig` unchanged. `AnalyzerResult` keeps the FLAT golden row shape via per-metric optional fields named exactly like `Metric` values; metric payloads typed `dict[str, Any]` on purpose — typing them `float` would coerce golden ints (`"sum": 48069190`) to `48069190.0` and break `metrics.json`.

**Tech Stack:** pydantic ^2 (new experiments dep), py3.13 `enum.StrEnum`, pytest, existing e2e golden harness (`tests/golden_utils.py`, `UPDATE_GOLDEN=1` regen).

## Global Constraints

- Branch `feat/t19-pydantic-models` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`.
- **Execute AFTER T14–T18 merge; rebase if base moved.** Code below assumes post-T14 `problemRunner.py` (meta `time` from `problem.solutionTime`, no `import time` — T14 Task 9) and post-T16 tree (`helpers/transformers/molpToSimpleElection.py` archived — last non-model TypedDict in experiments gone).
- Repo GREEN after ticket: `cd experiments && poetry run pytest` incl. `-m e2e`, ruff check+format, pyright. core/solvers/bindings UNTOUCHED (experiments-only ticket) — one confirming `pytest -q` each at the end, no changes expected.
- Golden regen ALLOWED, ONLY `tests/fixtures/golden/selected.json` (`instance_size` 11→10 ×3 — T02 leftover: pulp `__dummy` passes the `name != "dummy"` filter), ONLY in the dedicated Task 4 commit with justification (ROADMAP §2). `metrics.json` must stay byte-identical — Tasks 2–3 keep the `!= "dummy"` bug and the flat metrics row shape verbatim so every non-Task-4 commit passes e2e against OLD goldens.
- T10 contract preserved: `SolverSpec.options` / `RunnerConfig.solver_options` stay free-form `dict[str, Any]` of valid constructor kwargs — NO per-solver option schemas (feature creep). `MES_EXPONENTIAL` `budget_init` stays solve-time-required, not config-time.
- No new features. T20–T26 import these models — keep both `model.py` paths as-is (T21 renames later), models importable with zero side effects.
- All commands from `experiments/`, its poetry venv. Sample smoke needs `rm -rf sample-experiment/results/*` first + venv python on PATH (T10 leftover).

---

### Task 1: Add pydantic dep

**Files:**
- Modify: `experiments/pyproject.toml:25-38` (`[tool.poetry.dependencies]`)

- [ ] **Step 1: Add dep**

After `questionary = "^2.1.1"` (line 38) add:

```toml
pydantic = "^2.12"
```

- [ ] **Step 2: Lock + install**

Run: `cd experiments && poetry lock && poetry install`
Expected: lock adds pydantic + pydantic-core + annotated-types (typing-inspection may ride along); no other bumps. Then `poetry run python -c "import pydantic; print(pydantic.VERSION)"` → 2.x.

- [ ] **Step 3: Commit** — `git add -A && git commit -m "T19: add pydantic dep"`

---

### Task 2: Runner models + runner-pipeline boundaries

One commit — TypedDict→BaseModel flips subscript access to attribute access, so `model.py` and its runtime consumers must move atomically (T10 precedent).

**Files:**
- Modify: `experiments/src/helpers/runners/model.py` (full rewrite, :1-86)
- Modify: `experiments/src/helpers/transformers/expand_experiment_config.py` (full rewrite)
- Modify: `experiments/src/experimentRunner.py:7-58`
- Modify: `experiments/src/problemRunner.py:20-94` (post-T14 shape)
- Modify: `experiments/src/helpers/runners/solverStrategy.py:1-29` (10-solver wiring)
- Modify: `experiments/src/helpers/runners/sourceStrategy.py:17-23`
- Modify: `experiments/src/helpers/utils/resultCache.py:13-66`
- Modify: `experiments/src/helpers/utils/enhanceFromSolverResult.py:6-13`
- Modify: `experiments/src/helpers/analyzers/analysis_table.py:19-26` (`Solver.__args__` dies with the Literal — runtime path of e2e analyzer)
- Modify: `experiments/src/helpers/transformers/pabutoolsUtils.py:11-16` (`_VOTE_TYPE_TO_UTILITY` values → enum members)
- Modify: `experiments/tests/test_solver_strategy.py:1-18`
- Test: `experiments/tests/test_models.py` (new)

**Interfaces:**
- Produces: `Solver`/`Source`/`Utility`/`Strategy` StrEnums; `StrictModel` base; models `ConstraintConfig, RunnerConfig, ExperimentConfig, SolverSpec, RunnerConfigsGenerator, CompactExperimentConfig, RunnerResult` (fields below, exact); `parse_experiment_config(data: dict | ExperimentConfig | CompactExperimentConfig) -> ExperimentConfig` in `expand_experiment_config.py`. Tasks 3–7 consume these names verbatim.

- [ ] **Step 1: Write the failing tests**

```python
# experiments/tests/test_models.py
import pytest
from pydantic import ValidationError

from helpers.runners.model import (
    RunnerConfig,
    RunnerResult,
    Solver,
    Utility,
)
from helpers.transformers.expand_experiment_config import (
    parse_experiment_config,
)


def test_malformed_config_validation_error_has_field_path():
    config = {
        "concurrency": 1,
        "experiment_results_base_path": "results/",
        "runner_configs": [
            {
                "solver_type": "NOT_A_SOLVER",
                "source_type": "PABUTOOLS",
                "source_directory_path": "input/x",
            }
        ],
    }
    with pytest.raises(ValidationError) as exc_info:
        parse_experiment_config(config)
    [error] = exc_info.value.errors()
    assert error["loc"] == ("runner_configs", 0, "solver_type")


def test_unknown_config_key_rejected():
    with pytest.raises(ValidationError) as exc_info:
        RunnerConfig.model_validate(
            {
                "solver_type": "GREEDY",
                "source_type": "PABUTOOLS",
                "source_directory_path": "input/x",
                "solver_optionz": {},
            }
        )
    assert exc_info.value.errors()[0]["loc"] == ("solver_optionz",)


def test_compact_config_expands():
    compact = {
        "compact_config": True,
        "concurrency": 2,
        "experiment_results_base_path": "results/",
        "runner_configs_generator": {
            "solvers": [{"type": "GREEDY"}, {"type": "STV"}],
            "source_type": "PABUTOOLS",
            "sources": ["input/a", "input/b"],
        },
    }
    experiment = parse_experiment_config(compact)
    assert len(experiment.runner_configs) == 4
    first = experiment.runner_configs[0]
    assert first.results_base_path == "results/"
    assert first.solver_options == {}
    assert first.constraints_configs is None


def test_solver_enum_has_all_ten():
    assert len(Solver) == 10
    assert {"STV", "SOLID_COALITION_REFINEMENT", "EXPANDING_APPROVALS"} <= {
        s.value for s in Solver
    }


def test_strenum_formats_to_value_in_filenames():
    # problemRunner/resultCache build filenames via f-strings — contract
    assert f"x_{Utility.COST_ORDINAL}_{Solver.GREEDY}.lp" == (
        "x_COST_ORDINAL_GREEDY.lp"
    )


def test_runner_result_roundtrips_meta_json():
    meta = {
        "constraints_configs": [],
        "deduplicate_objectives": False,
        "instance_size": 10,
        "problem_path": "results/problem_x.lp",
        "selected": ["V_1"],
        "solver": "GREEDY",
        "solver_options": {},
        "source_path": "input/krakow_2024_mini",
        "source_type": "PABUTOOLS",
        "time": 0.5,
        "utility_type": "COST_ORDINAL",
    }
    result = RunnerResult.model_validate(meta)
    assert result.model_dump(mode="json", exclude_none=True) == meta
```

- [ ] **Step 2: Run to verify failure**

Run: `cd experiments && poetry run pytest tests/test_models.py -q`
Expected: FAIL — `ImportError: cannot import name 'parse_experiment_config'` (and `Solver` has no `.value` iteration as Literal).

- [ ] **Step 3: Rewrite `helpers/runners/model.py`**

Full replacement:

```python
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class Strategy(StrEnum):
    DISTRICT_BUDGET_MINUS_MAX = "district_budget_minus_max"
    CATEGORY_VOTE_SHARE = "category_vote_share"
    CATEGORY_COST_SHARE = "category_cost_share"


class Solver(StrEnum):
    SUMMING = "SUMMING"
    MES_ADD1 = "MES_ADD1"
    MES_CONSTRAINT = "MES_CONSTRAINT"
    MES_UTILS = "MES_UTILS"
    MES_EXPONENTIAL = "MES_EXPONENTIAL"
    GREEDY = "GREEDY"
    PHRAGMEN = "PHRAGMEN"
    STV = "STV"
    SOLID_COALITION_REFINEMENT = "SOLID_COALITION_REFINEMENT"
    EXPANDING_APPROVALS = "EXPANDING_APPROVALS"


class Source(StrEnum):
    PABUTOOLS = "PABUTOOLS"


class Utility(StrEnum):
    COST = "COST"
    APPROVAL = "APPROVAL"
    ORDINAL = "ORDINAL"
    CUMULATIVE = "CUMULATIVE"
    COST_ORDINAL = "COST_ORDINAL"
    COST_CUMULATIVE = "COST_CUMULATIVE"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConstraintConfig(StrictModel):
    key: Literal["CATEGORY", "DISTRICT"]
    value: str  # specific value or "*" for all
    bound: Literal["UPPER", "LOWER"]
    budget_ratio: float | None = None
    strategy: Strategy | None = None


class RunnerConfig(StrictModel):
    solver_type: Solver
    # keys MUST be valid solver-constructor kwargs (T10 contract)
    solver_options: dict[str, Any] = {}
    source_type: Source
    utility_type: Utility | None = None
    source_directory_path: str
    constraints_configs_path: str | None = None
    constraints_configs: list[ConstraintConfig] | None = None
    deduplicate_objectives: bool = False
    results_base_path: str | None = None  # None -> experiment default


class ExperimentConfig(StrictModel):
    concurrency: int
    experiment_results_base_path: str
    runner_configs: list[RunnerConfig]


class SolverSpec(StrictModel):
    type: Solver
    options: dict[str, Any] = {}  # constructor kwargs (T10)


class RunnerConfigsGenerator(StrictModel):
    solvers: list[SolverSpec]
    source_type: Source
    sources: list[str]
    constraints_configs_path: str | None = None
    deduplicate_objectives: bool = False


class CompactExperimentConfig(StrictModel):
    compact_config: Literal[True]
    concurrency: int
    experiment_results_base_path: str
    runner_configs_generator: RunnerConfigsGenerator


class RunnerResult(StrictModel):
    time: float
    solver: Solver
    solver_options: dict[str, Any]
    source_type: Source
    utility_type: Utility
    source_path: str
    constraints_configs: list[ConstraintConfig]
    deduplicate_objectives: bool
    problem_path: str
    instance_size: int
    selected: list[str]
```

(Pydantic deep-copies mutable defaults per instance — bare `{}` is safe.)

- [ ] **Step 4: Rewrite `expand_experiment_config.py`**

```python
from helpers.runners.model import (
    CompactExperimentConfig,
    ExperimentConfig,
    RunnerConfig,
)


def parse_experiment_config(
    data: dict | ExperimentConfig | CompactExperimentConfig,
) -> ExperimentConfig:
    """Single config-load boundary: validates + expands compact form."""
    if isinstance(data, ExperimentConfig):
        return data
    if isinstance(data, CompactExperimentConfig):
        return expand_experiment_config(data)
    if data.get("compact_config"):
        return expand_experiment_config(
            CompactExperimentConfig.model_validate(data)
        )
    return ExperimentConfig.model_validate(data)


def expand_experiment_config(
    config: CompactExperimentConfig,
) -> ExperimentConfig:
    gen = config.runner_configs_generator
    runner_configs = [
        RunnerConfig(
            solver_type=solver.type,
            solver_options=solver.options,
            source_type=gen.source_type,
            source_directory_path=source,
            results_base_path=config.experiment_results_base_path,
            constraints_configs_path=gen.constraints_configs_path,
            deduplicate_objectives=gen.deduplicate_objectives,
        )
        for source in gen.sources
        for solver in gen.solvers
    ]
    return ExperimentConfig(
        concurrency=config.concurrency,
        experiment_results_base_path=config.experiment_results_base_path,
        runner_configs=runner_configs,
    )
```

- [ ] **Step 5: Update runtime consumers**

`experimentRunner.py` — `main` body becomes (imports: add `parse_experiment_config` to the `expand_experiment_config` import; keep `ExperimentConfig | CompactExperimentConfig` names):

```python
def main(
    experiment: ExperimentConfig | CompactExperimentConfig | dict,
) -> None:
    experiment = parse_experiment_config(experiment)

    Path(experiment.experiment_results_base_path).mkdir(
        parents=True, exist_ok=True
    )
    for runner_config in experiment.runner_configs:
        if runner_config.results_base_path is None:
            runner_config.results_base_path = (
                experiment.experiment_results_base_path
            )
```

Rest of `main`: `experiment.concurrency` / `experiment.experiment_results_base_path` / `experiment.runner_configs` for the remaining subscripts. `__main__` block: `main(read_from_json(Path(sys.argv[1])))` — drop the annotation, validation happens inside (broken-config feed via `run.sh` now raises ValidationError with field path).

`problemRunner.py` — top of `problem_runner` becomes attribute access; RunnerResult built AFTER paths (kills the `problem_path: None` placeholder):

```python
def problem_runner(config: RunnerConfig) -> None:
    solver_type = config.solver_type
    solver_options = config.solver_options
    source_type = config.source_type
    utility_type = config.utility_type
    source_directory_path = config.source_directory_path
    results_base_path = config.results_base_path
    if results_base_path is None:
        raise ValueError("results_base_path not set on RunnerConfig")
    constraints_configs = resolve_constraints_configs(config)
    deduplicate_objectives = config.deduplicate_objectives
```

`try:` block after `problem.solve(solver)` (keep `get_file_name` closure verbatim — StrEnum f-strings produce old filenames, proven by `test_strenum_formats_to_value_in_filenames`):

```python
        problem_id = f"{datetime.now().isoformat(timespec='seconds').replace(':', '-')[5:]}_{str(uuid4())[:4]}"
        problem_file = get_file_name("problem", "lp", problem_id)
        problem_path = f"{results_base_path}{problem_file}"

        result = RunnerResult(
            time=problem.solutionTime,
            solver=solver_type,
            solver_options=solver_options,
            source_type=source_type,
            utility_type=utility_type,
            source_path=source_directory_path,
            constraints_configs=constraints_configs,
            deduplicate_objectives=deduplicate_objectives,
            problem_path=problem_path,
            # BUG KEPT on purpose: pulp's var is named "__dummy", filter
            # misses it -> instance_size over by 1. Fixed in Task 4 with
            # golden regen; goldens must stay identical in THIS commit.
            instance_size=len(
                [
                    variable
                    for variable in problem.variables()
                    if variable.name != "dummy"
                ]
            ),
            selected=sorted(
                var.name
                for var in problem.variables()
                if var.value() == 1.0
            ),
        )
        # write_lp (not pulp writeLP): appends OBJECTIVES/WEIGHTS sections
        # required by read_lp_file in analyzer
        problem.write_lp(problem_path)
        meta_file = get_file_name("meta", "json", problem_id)
        write_to_json(
            Path(f"{results_base_path}{meta_file}"),
            result.model_dump(mode="json", exclude_none=True),
        )
```

(`utility_type` may arrive as plain str from `detect_utility_from_instances` return path — `RunnerResult` coerces to `Utility`; f-string filename identical either way. `exclude_none` keeps nested `ConstraintConfig` dumps free of `budget_ratio: null` noise, matching old NotRequired-omitted metas.)

`solverStrategy.py` — full dispatch (ticket: wire ALL 10):

```python
from muoblpsolvers import (
    ExpandingApprovals,
    GreedySolver,
    MethodOfEqualSharesAdd1Solver,
    MethodOfEqualSharesConstrainsSolver,
    MethodOfEqualSharesExponentialSolver,
    MethodOfEqualSharesUtilitySolver,
    PhragmenSolver,
    SingleTransferableVote,
    SolidCoalitionRefinement,
    SummedObjectivesLpSolver,
)
from pulp import LpSolver

from helpers.runners.model import Solver

SOLVERS: dict[Solver, type[LpSolver]] = {
    Solver.SUMMING: SummedObjectivesLpSolver,
    Solver.MES_UTILS: MethodOfEqualSharesUtilitySolver,
    Solver.MES_ADD1: MethodOfEqualSharesAdd1Solver,
    Solver.MES_CONSTRAINT: MethodOfEqualSharesConstrainsSolver,
    Solver.MES_EXPONENTIAL: MethodOfEqualSharesExponentialSolver,
    Solver.PHRAGMEN: PhragmenSolver,
    Solver.GREEDY: GreedySolver,
    Solver.STV: SingleTransferableVote,
    Solver.SOLID_COALITION_REFINEMENT: SolidCoalitionRefinement,
    Solver.EXPANDING_APPROVALS: ExpandingApprovals,
}


def get_solver(solver_type: Solver, solver_options: dict | None) -> LpSolver:
    if solver_type not in SOLVERS:
        raise Exception("Strategy not implemented for the solver type")
    # options are keyword args of the solver constructor (pulp optionsDict)
    return SOLVERS[solver_type](**(solver_options or {}))
```

(StrEnum hashes like its value → plain-string lookup `SOLVERS["GREEDY"]` still hits; unknown-string guard stays.)

`sourceStrategy.py:17-23`:

```python
def resolve_constraints_configs(
    config: RunnerConfig,
) -> list[ConstraintConfig]:
    if config.constraints_configs is not None:
        return config.constraints_configs
    path = config.constraints_configs_path
    if not path:
        return []
    return [
        ConstraintConfig.model_validate(entry)
        for entry in read_from_json(Path(path))
    ]
```

Import `ConstraintConfig` from `helpers.runners.model` here (drop the re-import via `pabutoolsToMoLp` — it re-exports the same class; keep `pabutools_to_multi_objective_lp` import). Constraints-file read = validated boundary.

`resultCache.py` — attribute access + invalid-meta = cache miss (imports: add `from pydantic import ValidationError`, `RunnerResult`):

```python
def is_metadata_content_matching(
    meta_path: Path, problem_config: RunnerConfig
) -> bool:
    try:
        existing_result = RunnerResult.model_validate(
            read_from_json(meta_path)
        )
    except ValidationError:
        logger.warning(f"Ignoring incompatible meta file {meta_path}")
        return False

    if existing_result.solver_options != problem_config.solver_options:
        return False
    if existing_result.constraints_configs != resolve_constraints_configs(
        problem_config
    ):
        return False
    if (
        existing_result.deduplicate_objectives
        != problem_config.deduplicate_objectives
    ):
        return False
    ...  # lp-file existence block unchanged
```

`is_result_present`: `problem_config.results_base_path` / `.solver_type` / `.source_directory_path` (f-string pattern unchanged).

`enhanceFromSolverResult.py`: `solver_result.selected`.

`analysis_table.py:19-26`: Literal `__args__` → enum iteration:

```python
    solver_pattern = "|".join(
        re.escape(s) for s in sorted(list(Solver), key=len, reverse=True)
    )
    utility_pattern = "|".join(
        re.escape(u) for u in sorted(list(Utility), key=len, reverse=True)
    )
```

`pabutoolsUtils.py:11-16`: values → members (dict stays `dict[str, Utility]`):

```python
_VOTE_TYPE_TO_UTILITY: dict[str, Utility] = {
    "approval": Utility.COST,
    "ordinal": Utility.COST_ORDINAL,
    "cumulative": Utility.COST_CUMULATIVE,
    "choose-1": Utility.COST,
}
```

`tests/test_solver_strategy.py`: `from typing import get_args` + `get_args(Solver)` → `list(Solver)` (parametrize now covers 10 incl. STV/SCR/EA — constructors are bindings-free post-T11 lazy imports); rest of the file unchanged.

- [ ] **Step 6: Run**

Run: `poetry run pytest tests/test_models.py tests/test_solver_strategy.py -q` → PASS (solver-strategy parametrize = 10). Then full: `poetry run pytest -q && poetry run pytest -m e2e -q` — ALL green against OLD goldens (metrics.json byte-identical, selected.json still shows instance_size 11). If e2e diffs anything except nothing — STOP, a dump-shape regression sneaked in (check `exclude_none` / enum serialization).

- [ ] **Step 7: Commit** — `git add -A && git commit -m "T19: pydantic runner models + 10-solver dispatch"`

---

### Task 3: Analyzer models + analyzer boundaries

**Files:**
- Modify: `experiments/src/helpers/analyzers/model.py` (full rewrite, :1-28)
- Modify: `experiments/src/helpers/analyzers/metrics.py:9-15` (`get_metrics`)
- Modify: `experiments/src/analyzerRunner.py:25-85`
- Test: `experiments/tests/test_models.py` (append)

**Interfaces:**
- Consumes: `StrictModel`, `Solver`, `Utility`, `ConstraintConfig`, `RunnerResult` (Task 2).
- Produces: `Metric` StrEnum (6 members, NO `METADATA`); `AnalyzerConfig(analyzer_result_path, experiment_results_base_path, metrics: list[Metric])`; `AnalyzerResult` with per-metric optional `dict[str, Any]` fields named exactly like `Metric` values; `get_metrics(metrics, problem) -> dict[str, dict]` (keys = metric values, feeds `AnalyzerResult(**metric_values)`). T24 reads meta via these models.

- [ ] **Step 1: Write the failing tests** (append to `test_models.py`)

```python
from helpers.analyzers.model import AnalyzerConfig


def test_metadata_metric_dropped():
    with pytest.raises(ValidationError) as exc_info:
        AnalyzerConfig.model_validate(
            {
                "analyzer_result_path": "analysis/",
                "experiment_results_base_path": "results/",
                "metrics": ["METADATA"],
            }
        )
    assert exc_info.value.errors()[0]["loc"] == ("metrics", 0)


def test_incompatible_meta_is_cache_miss(tmp_path):
    from helpers.utils.resultCache import is_metadata_content_matching

    meta_path = tmp_path / "meta_bad.json"
    meta_path.write_text('{"solver": "GREEDY"}')
    config = RunnerConfig.model_validate(
        {
            "solver_type": "GREEDY",
            "source_type": "PABUTOOLS",
            "source_directory_path": "input/x",
        }
    )
    assert is_metadata_content_matching(meta_path, config) is False
```

(Second test belongs to Task 2's code — landed here where `RunnerConfig` import already exists; runs against Task 2's `except ValidationError` branch.)

- [ ] **Step 2: Run to verify failure**

Run: `poetry run pytest tests/test_models.py -q`
Expected: `test_metadata_metric_dropped` FAILS — `AnalyzerConfig` is still a TypedDict, `model_validate` missing. Cache-miss test PASSES already (Task 2) — fine.

- [ ] **Step 3: Rewrite `helpers/analyzers/model.py`**

```python
from enum import StrEnum
from typing import Any

from helpers.runners.model import (
    ConstraintConfig,
    Solver,
    StrictModel,
    Utility,
)


class Metric(StrEnum):
    EXCLUSION_RATION = "EXCLUSION_RATION"
    SUM_OBJECTIVES = "SUM_OBJECTIVES"
    EJR_PLUS = "EJR_PLUS"
    CONSTRAINTS = "CONSTRAINTS"
    INSTANCE_SIZE = "INSTANCE_SIZE"
    TOTAL_COST = "TOTAL_COST"
    # "METADATA" dropped: never implemented (metrics.py had no strategy)


class AnalyzerConfig(StrictModel):
    analyzer_result_path: str
    experiment_results_base_path: str
    metrics: list[Metric]


class AnalyzerResult(StrictModel):
    # Per-metric fields named exactly like Metric values -> dumped rows keep
    # the flat golden shape (metrics.json). dict[str, Any], NOT float:
    # float-typing would coerce golden ints ("sum": 48069190) to 48069190.0.
    problem_path: str
    metrics: list[Metric]
    time: float
    city: str
    solver: Solver
    solver_options: dict[str, Any]
    constraints_configs: list[ConstraintConfig]
    utility: Utility
    EXCLUSION_RATION: dict[str, Any] | None = None
    SUM_OBJECTIVES: dict[str, Any] | None = None
    EJR_PLUS: dict[str, Any] | None = None
    CONSTRAINTS: dict[str, Any] | None = None
    INSTANCE_SIZE: dict[str, Any] | None = None
    TOTAL_COST: dict[str, Any] | None = None
```

- [ ] **Step 4: Adapt `metrics.py` + `analyzerRunner.py`**

`metrics.py` `get_metrics` (:9-15) — pure metric payloads, no `"metrics"` key smuggling (that was the TypedDict lie; `AnalyzerResult` now owns row assembly):

```python
def get_metrics(
    metrics: list[Metric], problem: MultiObjectiveLpProblem
) -> dict[str, dict]:
    return {
        metric: get_metric_strategy(metric)(problem) for metric in metrics
    }
```

(StrEnum keys ARE str — usable as `**kwargs`. `get_metric_strategy`'s `==` string comparisons keep working; drop the `"METADATA"`-reachable fallthrough comment if any. Drop the now-unused `AnalyzerResult` import.)

`analyzerRunner.py` `analyze_runner_result` — meta read validated, row built as model (keep the broad `except` → None; structured errors are T24's):

```python
def analyze_runner_result(
    runner_result_path: Path, metrics: List[Metric]
) -> AnalyzerResult | None:
    logger.info("Analyse result", extra={"path": runner_result_path})
    try:
        solver_result = RunnerResult.model_validate(
            read_from_json(runner_result_path)
        )
        problem = read_lp_file(solver_result.problem_path)
        problem = enhance_problem_from_solver_result(solver_result, problem)
        metric_values = get_metrics(metrics, problem)
        return AnalyzerResult(
            problem_path=runner_result_path.as_posix(),
            metrics=metrics,
            time=solver_result.time,
            city=Path(solver_result.source_path).name.replace(".pb", ""),
            solver=solver_result.solver,
            solver_options=solver_result.solver_options,
            constraints_configs=solver_result.constraints_configs,
            utility=solver_result.utility_type,
            **metric_values,
        )
    except Exception as err:
        # TODO: return empty result with metadata instead of None (T24)
        logger.error(
            "Failed to analyze results",
            extra={"problem": runner_result_path, "error": err},
        )
```

`main` — validate config boundary (accepts dict OR model: `model_validate` takes both), dump rows preserving None sentinel (golden harness asserts no-None):

```python
def main(
    config: AnalyzerConfig | dict, console_output_limit: int | None = None
):
    config = AnalyzerConfig.model_validate(config)
```

then `config.experiment_results_base_path` / `config.analyzer_result_path` / `config.metrics` for the subscripts; the write becomes:

```python
        write_to_json(
            result_path,
            [
                row.model_dump(mode="json", exclude_none=True)
                if row is not None
                else None
                for row in analysis
            ],
        )
```

`__main__`: `main(read_from_json(Path(sys.argv[1])), 25)` — validation inside `main`.

Note: `aggregateResults.py`/`aggregateGroupedResults.py` import `AnalyzerResult` as annotation only — name survives, no edits (T23 rewrites them).

- [ ] **Step 5: Run**

Run: `poetry run pytest tests/test_models.py -q` → PASS. Full: `poetry run pytest -q && poetry run pytest -m e2e -q` — metrics.json golden byte-identical (flat shape + int values preserved). Any metrics diff → check `dict[str, Any]` typing / `exclude_none`.

- [ ] **Step 6: Commit** — `git commit -am "T19: pydantic analyzer models + validated meta/metrics boundaries"`

---

### Task 4: `__dummy` instance_size fix + golden regen (separate commit — ROADMAP §2)

**Files:**
- Modify: `experiments/src/problemRunner.py` (the filter marked BUG KEPT in Task 2)
- Regen: `experiments/tests/fixtures/golden/selected.json:5,22,39`

- [ ] **Step 1: Fix filter**

```python
            instance_size=len(
                [
                    variable
                    for variable in problem.variables()
                    if variable.name != "__dummy"
                ]
            ),
```

(delete the BUG KEPT comment.)

- [ ] **Step 2: Regen golden**

Run: `UPDATE_GOLDEN=1 poetry run pytest -m e2e -q` (fails by design after writing). Inspect: `git diff tests/fixtures/golden/` — EXACTLY 3 lines change, `"instance_size": 11` → `10` in `selected.json`; `metrics.json` untouched (metric INSTANCE_SIZE was already correct — analyzer re-reads the LP, no `__dummy` there). Any other diff → STOP, revert, find the schema leak.

- [ ] **Step 3: Verify** — `poetry run pytest -m e2e -q` (no env var) → PASS ×2 runs.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "T19: fix instance_size __dummy filter; regen selected.json golden

Golden regen justification (ROADMAP §2): T02 leftover — pulp dummy var is
named '__dummy', old filter checked != 'dummy', meta instance_size counted
11 instead of 10. Only change: instance_size 11->10 x3 in selected.json."
```

---

### Task 5: Sample/test config conformance + generators + alias dedupe

**Files:**
- Modify: `experiments/src/generateExperimentConfig.py:17-59,118-163,253-256`
- Modify: `experiments/src/generateCompactExperimentConfig.py:84-109`
- Modify: `experiments/src/generateExperiment.py:9-55`
- Modify: `experiments/src/generatePhargmenGreedyDistrictExperiment.py:69-99`
- Modify: `experiments/src/helpers/transformers/pabutoolsToMoLp.py:6,34-35`
- Test: `experiments/tests/test_models.py` (append)

- [ ] **Step 1: Sample-config conformance tests** (append; sample configs at `experiments/sample-experiment/*.jsonc` already field-compatible with the new schema — these tests PROVE it and guard drift; the ticket's "update sample-experiment + test configs" resolves to: no field changes needed, e2e test config already validated via Task 2's `parse_experiment_config`)

```python
from pathlib import Path as _Path

from helpers.utils.utils import read_from_json

SAMPLE_DIR = _Path(__file__).parents[1] / "sample-experiment"


def test_sample_experiment_config_validates():
    experiment = parse_experiment_config(
        read_from_json(SAMPLE_DIR / "experiment-config.jsonc")
    )
    assert len(experiment.runner_configs) == 4
    assert experiment.runner_configs[0].solver_type == Solver.MES_ADD1


def test_sample_analyzer_config_validates():
    config = AnalyzerConfig.model_validate(
        read_from_json(SAMPLE_DIR / "sample-analysis-config.jsonc")
    )
    assert len(config.metrics) == 3
```

Run: `poetry run pytest tests/test_models.py -q` → PASS immediately (characterization; if either fails the schema broke the samples — fix schema, not samples).

- [ ] **Step 2: Generators → model construction** (mechanical; scripts are interactive/T22-bound, no unit tests — ruff+pyright+import are the bar)

`generateExperimentConfig.py`:
- `SOLVER_CHOICES` (:17-25) → `[solver.value for solver in Solver]`; `UTILITY_CHOICES` (:27-34) → `[utility.value for utility in Utility]`.
- `SOLVER_OPTION_SPECS` (:39-59): add `"STV": [], "SOLID_COALITION_REFINEMENT": [], "EXPANDING_APPROVALS": []` (binding-backed, no options — T10).
- `generate_experiment_config` (:138-163): dict literals → `RunnerConfig(solver_type=solver, solver_options=options, source_type=source_type, source_directory_path=str(path), results_base_path=experiment_results_base_path, utility_type=utility, constraints_configs_path=constraints_configs_path, deduplicate_objectives=deduplicate_objectives)`; return `ExperimentConfig(...)` (drop the conditional-key dance — None/False defaults now carry it).
- Final write (:255): `write_to_json(output_path, config.model_dump(mode="json", exclude_none=True))`.

`generateCompactExperimentConfig.py` (:84-109): build `CompactExperimentConfig(compact_config=True, concurrency=..., experiment_results_base_path=..., runner_configs_generator=RunnerConfigsGenerator(solvers=[SolverSpec(type=solver, options=options) for solver, options in solvers_with_options], source_type=source_type, sources=[str(p) for p in paths], constraints_configs_path=constraints_cfg, deduplicate_objectives=deduplicate_objectives))`; write via `model_dump(mode="json", exclude_none=True)`.

`generateExperiment.py` (:26-55) + `generatePhargmenGreedyDistrictExperiment.py` (:80-99): same mechanical dict→`RunnerConfig(...)`/`ExperimentConfig(...)` + `model_dump` on write. Minimal edits only — T22 archives/rewrites both.

- [ ] **Step 3: Dedupe `District`/`AgentId`**

`pabutoolsToMoLp.py`: delete `:34-35` (`District: TypeAlias = str` / `AgentId: TypeAlias = str`), add `from .pabutoolsUtils import AgentId, District` to imports (`pabutoolsUtils` doesn't import `pabutoolsToMoLp` — no cycle). Canonical definition stays `pabutoolsUtils.py:8-9`.

- [ ] **Step 4: Run**

`poetry run pytest -q && poetry run pytest -m e2e -q` → green. Greps: `grep -rn "TypeAlias" experiments/src/helpers/transformers/ | grep -c "District\|AgentId"` → 2 (one file); `poetry run python -c "import generateExperimentConfig, generateCompactExperimentConfig"` from `experiments/src` fails on questionary prompts? — no: prompts are under `__main__`, plain import must succeed: `cd experiments && poetry run python -c "import sys; sys.path.insert(0, 'src'); import generateExperimentConfig, generateCompactExperimentConfig, generateExperiment, generatePhargmenGreedyDistrictExperiment"`.

- [ ] **Step 5: Commit** — `git commit -am "T19: sample-config conformance tests, generators on models, dedupe District/AgentId"`

---

### Task 6: pyright ratchet

**Files:**
- Modify: `experiments/pyrightconfig.json`

T03 leftover: 10 rules disabled masking 76 pre-rewrite errors; Phase-3 rewrites are supposed to shrink this. AC "pyright green on models" = model modules + rewritten call sites clean under un-suppressed basic mode.

- [ ] **Step 1: Strip all 10 rule-disables**

Reduce to:

```json
{
  "typeCheckingMode": "basic",
  "extraPaths": ["src"],
  "exclude": ["archived_code", ".venv"]
}
```

- [ ] **Step 2: Run + selectively restore**

Run: `poetry run pyright | tail -5`. For each still-failing rule, count errors and confirm NONE are in `helpers/runners/model.py`, `helpers/analyzers/model.py`, or the files rewritten in Tasks 2–3 (those must be clean — fix them, don't re-suppress). Re-add ONLY still-failing rules (expected residue: pabutools/pandas interop in `pabutoolsToMoLp.py`, aggregators, `preflibToMuoblp.py` — T23/T25 territory). `reportTypedDictNotRequiredAccess` MUST be removable (zero TypedDicts left in experiments/src post-T16+T19 — verify: `grep -rn "TypedDict" experiments/src` → empty).

- [ ] **Step 3: Verify** — `poetry run pyright` → 0 errors with the shrunk config; `poetry run ruff check . && poetry run ruff format --check .` clean.

- [ ] **Step 4: Commit** — `git commit -am "T19: pyright ratchet — re-enable rules cleared by model rewrite"` (list per-rule before/after counts in the message body).

---

### Task 7: Full verify + smoke + broken-config feed + PR

- [ ] **Step 1: Full test matrix**

`cd experiments && poetry run pytest -q && poetry run pytest -m e2e -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright` → all green. Confirm untouched siblings: `cd ../solvers && poetry run pytest -q`; `cd ../core && poetry run pytest -q` (no changes expected — experiments-only ticket).

- [ ] **Step 2: Sample smoke** (ticket Verify: "run sample")

```bash
cd experiments/sample-experiment && rm -rf results/*
PATH="$(poetry -C .. env info --path)/bin:$PATH" ./run.sh
PATH="$(poetry -C .. env info --path)/bin:$PATH" ./analyze.sh
```

Expected: metrics match T01/T05 reference values (APPROVAL 0.0033/219239/167; COST 0.0035/1.34763e11; COST_ORDINAL 0.0032/2.79444e11; bronowice 0.0666/4.35159e9); fresh meta jsons validate (they were written by `RunnerResult`).

- [ ] **Step 3: Broken-config feed** (ticket Verify)

Write to scratchpad `broken-config.json`: `{"concurrency": 1, "experiment_results_base_path": "results/", "runner_configs": [{"solver_type": "MES", "source_type": "PABUTOOLS", "source_directory_path": "input/krakow_2024"}]}`. Run `cd experiments/sample-experiment && PATH=... python ../src/experimentRunner.py <scratchpad>/broken-config.json` → `ValidationError` naming `runner_configs.0.solver_type` (the T09-era invalid `"MES"` literal now dies at load, before any solve).

- [ ] **Step 4: AC greps**

`grep -rn "TypedDict" experiments/src` → empty. `grep -rn "METADATA" experiments/src` → empty. `grep -rn "__args__\|get_args(Solver)" experiments/src experiments/tests` → empty. `grep -rn "District: TypeAlias" experiments/src` → 1 (pabutoolsUtils only).

- [ ] **Step 5: Commit + PR**

Push, PR → `feat/roadmap-base-branch`, title `T19: pydantic v2 models at IO boundaries`. Body: boundary map (config load / meta read+write / metrics write), 10-solver dispatch, METADATA drop, instance_size golden regen commit link + justification, pyright rules re-enabled (before/after counts), note `solver_options` stays kwargs-dict (T10 contract, per-solver schemas out of scope). Update ROADMAP checkbox + PR link and `plans/leftovers.md` (record: new Solver enum spelling for SCR/EA in meta filenames; remaining pyright suppressions; stale pre-T19 results dirs now re-solve as cache misses).

## Unresolved questions

1. New `Solver` enum values spelled `STV` / `SOLID_COALITION_REFINEMENT` / `EXPANDING_APPROVALS` (verbose, lands in meta filenames) — OK, or prefer short `SCR` / `EA` style matching `MES_ADD1` brevity?
2. `solver_options: null` in hand-written configs: plan is strict (dict or absent; explicit `null` → ValidationError). Old configs were deleted in T09, so likely moot — confirm.
3. resultCache on non-validating (pre-T19) meta: plan = warn + treat as cache miss (re-solve overwrites). Alternative = hard fail. OK with silent re-solve of stale results dirs?
4. `extra="forbid"` on ALL models incl. `RunnerResult` meta reads — strictest option, rejects any hand-edited meta with stray keys (surfaces as analyzer None-row / cache miss). Confirm forbid over ignore.
5. Metric payloads typed `dict[str, Any]` (protects golden int-vs-float bytes) — deep value typing deferred to T24/T26. OK?
6. pydantic pin `^2.12` (repo mixes exact pins and carets) — caret OK?
