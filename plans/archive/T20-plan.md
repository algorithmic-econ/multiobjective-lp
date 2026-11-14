# T20 Extract Shared Pipeline Lib Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** New pure-function package `experiments/src/pipeline/` (config expansion, problem steps, analyzer steps, result cache, path/filename logic); runner scripts shrink to thin orchestration (~50 lines); pathlib everywhere; filename scheme deduped (`problemRunner.py:85` ↔ `resultCache.py:52`); analyzer `Pool(processes=3)` → `AnalyzerConfig.concurrency`.

**Architecture:** Lib absorbs the logic currently inlined in the 3 runner scripts + `resultCache.py` + `expand_experiment_config.py`. Single filename template in `pipeline/paths.py` — `result_file_name()` builds names, `meta_file_regex()` matches them, roundtrip unit test guards drift (that IS the dedup). Config-default fill (`results_base_path`) becomes pure `resolve_runner_configs` via `model_copy` — kills the in-place mutation loop in `experimentRunner.main`. `helpers/runners/solverStrategy.py`, `sourceStrategy.py`, `helpers/utils/enhanceFromSolverResult.py` stay put (T21 rename targets) — lib imports them. `resultCache.py` + `expand_experiment_config.py` `git mv` INTO lib (ticket names cache/expansion as lib content); T21 rename list shrinks accordingly (leftovers note).

**Tech Stack:** T19 pydantic models (`StrEnum` f-string == value, `model_copy`, `RunnerResult.model_validate` cache-miss on bad meta), pathlib, pytest, existing e2e golden harness.

## Global Constraints

- Branch `feat/t20-pipeline-lib` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`.
- **Execute AFTER T14–T19 merge; rebase if base moved.** Code below assumes post-T14 `problemRunner.py` (meta `time` = `problem.solutionTime`, no manual timing), post-T16 tree (`molpToSimpleElection` archived), post-T19 models (attribute access, `parse_experiment_config`, `Solver`/`Utility` StrEnums, `instance_size` `__dummy` filter fixed). Verify line refs against merged tree before editing.
- e2e golden IDENTICAL, **NO regen.** Byte-preserved contracts: filename scheme `{type}_{MM-DDTHH-MM-SS}_{uuid4[:4]}_{source}_{utility}_{solver}.{ext}`, meta json content/keys, metrics file name `metrics-<results dir name>.json`, metrics row shape. Golden normalization (`tests/golden_utils.py`) strips paths to basename + sorts rows — path-join and discovery-order changes are invisible; filename STEM changes are NOT.
- Do NOT rename existing camelCase entrypoints/helpers (T21's job). New lib modules snake_case from birth; names must not collide with T21 rename targets (`cache.py` not `result_cache.py`; no `experiment_runner.py` etc. — T21 list: experimentRunner, problemRunner, analyzerRunner, solverStrategy, sourceStrategy, resultCache, enhanceFromSolverResult, pabutools*, generate*, aggregate*).
- No pipeline reordering (refactor-only): load/transform still runs BEFORE cache probe (probe needs resolved `utility_type`). Cache-hit still skips solve (T10 leftover).
- All commands from `experiments/`, its poetry venv. Plain `poetry run pytest -q` includes the e2e golden. Sample smoke needs `rm -rf sample-experiment/results/*` + venv python on PATH (T10 leftover).
- Repo GREEN after ticket: experiments pytest (units + e2e) + ruff check/format + pyright (keep post-T19 pyrightconfig, 0 errors). core/solvers/bindings untouched — one confirming pytest each at end.
- AC greps at end: `grep -rn "os\.path\|os\.listdir" experiments/src` → empty; `grep -rn "split('/'\|split(\"/" experiments/src` → empty; `grep -rn "_path}{" experiments/src` → empty; `wc -l` of 3 entrypoints ≤ ~55 each.

---

### Task 1: `pipeline/paths.py` — single source of filename truth

**Files:**
- Create: `experiments/src/pipeline/__init__.py` (empty)
- Create: `experiments/src/pipeline/paths.py`
- Test: `experiments/tests/test_pipeline_paths.py` (new)

**Interfaces:**
- Produces (all later tasks consume): `PROBLEM_ID_REGEX: str`; `new_problem_id() -> str`; `source_name(source_path: str | Path) -> str`; `result_file_name(file_type: Literal["problem","meta"], ext: Literal["lp","json"], problem_id: str, source_path: str | Path, utility_type: Utility, solver_type: Solver) -> str`; `meta_file_regex(source_path, utility_type, solver_type) -> re.Pattern[str]`; `lp_path_for_meta(meta_path: Path) -> Path`; `metrics_output_path(analyzer_result_path: str | Path, experiment_results_base_path: str | Path) -> Path`.

- [ ] **Step 1: Write the failing tests**

```python
# experiments/tests/test_pipeline_paths.py
import re
from pathlib import Path

from helpers.runners.model import Solver, Utility
from pipeline.paths import (
    PROBLEM_ID_REGEX,
    lp_path_for_meta,
    meta_file_regex,
    metrics_output_path,
    new_problem_id,
    result_file_name,
    source_name,
)


def test_result_file_name_matches_legacy_scheme():
    name = result_file_name(
        "problem",
        "lp",
        "07-19T12-00-00_ab12",
        "input/krakow_2024/poland_krakow_2024_bronowice.pb",
        Utility.COST_ORDINAL,
        Solver.GREEDY,
    )
    assert name == (
        "problem_07-19T12-00-00_ab12_poland_krakow_2024_bronowice"
        "_COST_ORDINAL_GREEDY.lp"
    )


def test_source_name_dir_and_pb_file():
    assert source_name("input/krakow_2024_mini") == "krakow_2024_mini"
    assert source_name("input/x/city.pb") == "city"


def test_new_problem_id_format():
    assert re.fullmatch(PROBLEM_ID_REGEX, new_problem_id())


def test_meta_regex_roundtrips_result_file_name():
    # THE dedup contract: regex built from same template as the writer
    meta_name = result_file_name(
        "meta", "json", new_problem_id(), "input/city_x",
        Utility.COST, Solver.MES_ADD1,
    )
    pattern = meta_file_regex("input/city_x", Utility.COST, Solver.MES_ADD1)
    assert pattern.fullmatch(meta_name)
    other = meta_file_regex("input/city_y", Utility.COST, Solver.MES_ADD1)
    assert not other.fullmatch(meta_name)


def test_lp_path_for_meta():
    meta = Path("results/meta_07-19T12-00-00_ab12_x_COST_GREEDY.json")
    assert lp_path_for_meta(meta) == Path(
        "results/problem_07-19T12-00-00_ab12_x_COST_GREEDY.lp"
    )


def test_metrics_output_path_matches_legacy_naming():
    # old: f"{analyzer}metrics-{base.split('/')[-2]}.json" (needed
    # trailing slash); Path(...).name matches WITH slash, fixes WITHOUT
    assert metrics_output_path(
        "analysis/", "results/sample-experiment/"
    ) == Path("analysis/metrics-sample-experiment.json")
    assert metrics_output_path("analysis", "results/sample-experiment") == (
        Path("analysis/metrics-sample-experiment.json")
    )
```

- [ ] **Step 2: Run to verify failure**

Run: `cd experiments && poetry run pytest tests/test_pipeline_paths.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline'`

- [ ] **Step 3: Implement**

`experiments/src/pipeline/__init__.py`: empty file.

```python
# experiments/src/pipeline/paths.py
"""Result-file naming: single source of truth.

Replaces duplicated f-strings (problemRunner get_file_name closure <->
resultCache regex). result_file_name builds, meta_file_regex matches;
roundtrip test guards drift.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from helpers.runners.model import Solver, Utility

# matches new_problem_id() output: MM-DDTHH-MM-SS_<uuid4[:4]>
PROBLEM_ID_REGEX = r"[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}-[0-9]{2}_[a-z0-9]{4}"


def new_problem_id() -> str:
    stamp = (
        datetime.now().isoformat(timespec="seconds").replace(":", "-")[5:]
    )
    return f"{stamp}_{str(uuid4())[:4]}"


def source_name(source_path: str | Path) -> str:
    return Path(source_path).name.removesuffix(".pb")


def result_file_name(
    file_type: Literal["problem", "meta"],
    ext: Literal["lp", "json"],
    problem_id: str,
    source_path: str | Path,
    utility_type: Utility,
    solver_type: Solver,
) -> str:
    return (
        f"{file_type}_{problem_id}_{source_name(source_path)}"
        f"_{utility_type}_{solver_type}.{ext}"
    )


def meta_file_regex(
    source_path: str | Path,
    utility_type: Utility,
    solver_type: Solver,
) -> re.Pattern[str]:
    return re.compile(
        f"meta_{PROBLEM_ID_REGEX}"
        f"_{re.escape(source_name(source_path))}"
        f"_{re.escape(utility_type)}_{re.escape(solver_type)}\\.json"
    )


def lp_path_for_meta(meta_path: Path) -> Path:
    return meta_path.with_name(
        meta_path.name.replace("meta_", "problem_", 1)
    ).with_suffix(".lp")


def metrics_output_path(
    analyzer_result_path: str | Path,
    experiment_results_base_path: str | Path,
) -> Path:
    return Path(analyzer_result_path) / (
        f"metrics-{Path(experiment_results_base_path).name}.json"
    )
```

- [ ] **Step 4: Run** — `poetry run pytest tests/test_pipeline_paths.py -q` → 6 PASS. Full `poetry run pytest -q` still green (lib not wired yet).

- [ ] **Step 5: Commit** — `git add -A && git commit -m "T20: pipeline/paths.py — deduped filename scheme"`

---

### Task 2: `pipeline/config.py` + thin `experimentRunner`

**Files:**
- Move: `experiments/src/helpers/transformers/expand_experiment_config.py` → `experiments/src/pipeline/config.py` (git mv)
- Modify: `experiments/src/experimentRunner.py` (full rewrite — post-T19 shape)
- Modify: `experiments/tests/test_models.py` (import path only)
- Test: `experiments/tests/test_pipeline_config.py` (new)

**Interfaces:**
- Consumes: T19 `parse_experiment_config`, `expand_experiment_config` (moved verbatim), `ExperimentConfig`/`RunnerConfig`.
- Produces: `pipeline.config.parse_experiment_config` (same signature), `resolve_runner_configs(experiment: ExperimentConfig) -> list[RunnerConfig]` — pure, fills `results_base_path` default via `model_copy`, never mutates input. Tasks 4/7 + entrypoint consume.

- [ ] **Step 1: Write the failing tests**

```python
# experiments/tests/test_pipeline_config.py
from pipeline.config import parse_experiment_config, resolve_runner_configs


def _experiment(runner_config: dict):
    return parse_experiment_config(
        {
            "concurrency": 1,
            "experiment_results_base_path": "results/",
            "runner_configs": [runner_config],
        }
    )


def test_resolve_fills_default_without_mutating_input():
    experiment = _experiment(
        {
            "solver_type": "GREEDY",
            "source_type": "PABUTOOLS",
            "source_directory_path": "input/x",
        }
    )
    resolved = resolve_runner_configs(experiment)
    assert resolved[0].results_base_path == "results/"
    # the old experimentRunner loop mutated in place — must NOT anymore
    assert experiment.runner_configs[0].results_base_path is None


def test_resolve_keeps_explicit_path():
    experiment = _experiment(
        {
            "solver_type": "GREEDY",
            "source_type": "PABUTOOLS",
            "source_directory_path": "input/x",
            "results_base_path": "custom/",
        }
    )
    assert resolve_runner_configs(experiment)[0].results_base_path == (
        "custom/"
    )
```

- [ ] **Step 2: Run to verify failure**

Run: `poetry run pytest tests/test_pipeline_config.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.config'`

- [ ] **Step 3: Implement**

```bash
git mv experiments/src/helpers/transformers/expand_experiment_config.py \
  experiments/src/pipeline/config.py
```

Append to `pipeline/config.py` (existing `parse_experiment_config` + `expand_experiment_config` bodies unchanged):

```python
def resolve_runner_configs(
    experiment: ExperimentConfig,
) -> list[RunnerConfig]:
    """Fill results_base_path default. Pure — no in-place mutation."""
    return [
        config
        if config.results_base_path is not None
        else config.model_copy(
            update={
                "results_base_path": (
                    experiment.experiment_results_base_path
                )
            }
        )
        for config in experiment.runner_configs
    ]
```

`experimentRunner.py` full rewrite:

```python
import logging
import multiprocessing
import sys
import time
from pathlib import Path

from helpers.runners.model import CompactExperimentConfig, ExperimentConfig
from helpers.utils.logger import setup_logging
from helpers.utils.utils import read_from_json
from pipeline.config import parse_experiment_config, resolve_runner_configs
from problemRunner import problem_runner

logger = logging.getLogger(__name__)


def main(
    experiment: ExperimentConfig | CompactExperimentConfig | dict,
) -> None:
    experiment = parse_experiment_config(experiment)
    runner_configs = resolve_runner_configs(experiment)
    Path(experiment.experiment_results_base_path).mkdir(
        parents=True, exist_ok=True
    )

    start_time = time.time()
    logger.info(
        "Start experiment",
        extra={
            "concurrency": experiment.concurrency,
            "experiment_results_base_path": (
                experiment.experiment_results_base_path
            ),
        },
    )
    with multiprocessing.Pool(
        processes=experiment.concurrency, initializer=setup_logging
    ) as pool:
        pool.map(problem_runner, runner_configs)

    logger.info("Finish experiment", extra={"time": time.time() - start_time})


if __name__ == "__main__":
    setup_logging()
    main(read_from_json(Path(sys.argv[1])))
```

`tests/test_models.py`: `from helpers.transformers.expand_experiment_config import parse_experiment_config` → `from pipeline.config import parse_experiment_config`. Grep for stragglers: `grep -rn "expand_experiment_config" experiments/src experiments/tests` → only `pipeline/config.py` internal.

- [ ] **Step 4: Run** — `poetry run pytest -q` (incl. e2e golden — resolved copies flow into `pool.map`, metas identical). `wc -l src/experimentRunner.py` ≤ ~50.

- [ ] **Step 5: Commit** — `git commit -am "T20: pipeline/config.py; kill in-place config mutation; thin experimentRunner"`

---

### Task 3: `pipeline/cache.py` — pathlib cache on shared regex

**Files:**
- Move: `experiments/src/helpers/utils/resultCache.py` → `experiments/src/pipeline/cache.py` (git mv + rewrite)
- Modify: `experiments/src/problemRunner.py:14` (import path only, rest of file untouched until Task 4)
- Modify: `experiments/tests/test_models.py` (T19's `test_incompatible_meta_is_cache_miss` imports `helpers.utils.resultCache` → `pipeline.cache`)
- Test: `experiments/tests/test_pipeline_cache.py` (new)

**Interfaces:**
- Consumes: `meta_file_regex`, `lp_path_for_meta` (Task 1); T19 `RunnerResult.model_validate` miss-on-ValidationError behavior (kept verbatim).
- Produces: `pipeline.cache.is_result_present(problem_config: RunnerConfig, utility_type: Utility) -> bool`, `is_metadata_content_matching(meta_path: Path, problem_config: RunnerConfig) -> bool` — same signatures as old module. Task 4 consumes.

- [ ] **Step 1: Write the failing tests**

```python
# experiments/tests/test_pipeline_cache.py
from pathlib import Path

from helpers.runners.model import (
    RunnerConfig,
    RunnerResult,
    Solver,
    Source,
    Utility,
)
from helpers.utils.utils import write_to_json
from pipeline.cache import is_result_present
from pipeline.paths import new_problem_id, result_file_name

SOURCE = "input/krakow_2024_mini"


def _config(tmp_path: Path, **overrides) -> RunnerConfig:
    return RunnerConfig.model_validate(
        {
            "solver_type": "GREEDY",
            "source_type": "PABUTOOLS",
            "source_directory_path": SOURCE,
            "results_base_path": str(tmp_path),
            **overrides,
        }
    )


def _write_result(
    results_dir: Path,
    write_lp: bool = True,
    solver_options: dict | None = None,
) -> None:
    problem_id = new_problem_id()
    lp_name = result_file_name(
        "problem", "lp", problem_id, SOURCE,
        Utility.COST_ORDINAL, Solver.GREEDY,
    )
    meta_name = result_file_name(
        "meta", "json", problem_id, SOURCE,
        Utility.COST_ORDINAL, Solver.GREEDY,
    )
    result = RunnerResult(
        time=0.1,
        solver=Solver.GREEDY,
        solver_options=solver_options or {},
        source_type=Source.PABUTOOLS,
        utility_type=Utility.COST_ORDINAL,
        source_path=SOURCE,
        constraints_configs=[],
        deduplicate_objectives=False,
        problem_path=str(results_dir / lp_name),
        instance_size=10,
        selected=["_A"],
    )
    write_to_json(
        results_dir / meta_name,
        result.model_dump(mode="json", exclude_none=True),
    )
    if write_lp:
        (results_dir / lp_name).write_text("")


def test_cache_hit(tmp_path):
    _write_result(tmp_path)
    assert is_result_present(_config(tmp_path), Utility.COST_ORDINAL)


def test_cache_miss_empty_dir(tmp_path):
    assert not is_result_present(_config(tmp_path), Utility.COST_ORDINAL)


def test_cache_miss_lp_file_gone(tmp_path):
    _write_result(tmp_path, write_lp=False)
    assert not is_result_present(_config(tmp_path), Utility.COST_ORDINAL)


def test_cache_miss_different_solver_options(tmp_path):
    _write_result(tmp_path, solver_options={"eps": 0.1})
    assert not is_result_present(_config(tmp_path), Utility.COST_ORDINAL)


def test_cache_miss_different_solver(tmp_path):
    _write_result(tmp_path)
    config = _config(tmp_path, solver_type="MES_ADD1")
    assert not is_result_present(config, Utility.COST_ORDINAL)
```

- [ ] **Step 2: Run to verify failure**

Run: `poetry run pytest tests/test_pipeline_cache.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.cache'`

- [ ] **Step 3: Implement**

```bash
git mv experiments/src/helpers/utils/resultCache.py \
  experiments/src/pipeline/cache.py
```

Rewrite `pipeline/cache.py` (drops `import os`/`import re`; T19's ValidationError branch + comparison logic kept verbatim):

```python
import logging
from pathlib import Path

from pydantic import ValidationError

from helpers.runners.model import RunnerConfig, RunnerResult, Utility
from helpers.runners.sourceStrategy import resolve_constraints_configs
from helpers.utils.utils import read_from_json
from pipeline.paths import lp_path_for_meta, meta_file_regex

logger = logging.getLogger(__name__)


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
    return lp_path_for_meta(meta_path).exists()


def is_result_present(
    problem_config: RunnerConfig, utility_type: Utility
) -> bool:
    if problem_config.results_base_path is None:
        raise ValueError("results_base_path not set on RunnerConfig")
    pattern = meta_file_regex(
        problem_config.source_directory_path,
        utility_type,
        problem_config.solver_type,
    )
    for meta_path in sorted(
        Path(problem_config.results_base_path).iterdir()
    ):
        if pattern.fullmatch(
            meta_path.name
        ) and is_metadata_content_matching(meta_path, problem_config):
            logger.info(f"Found result {meta_path.name}")
            return True
    return False
```

`problemRunner.py:14`: `from helpers.utils.resultCache import is_result_present` → `from pipeline.cache import is_result_present`. Update `tests/test_models.py` cache-miss test import. Grep: `grep -rn "resultCache" experiments/src experiments/tests` → empty.

- [ ] **Step 4: Run** — `poetry run pytest tests/test_pipeline_cache.py tests/test_models.py -q` → PASS. Full `poetry run pytest -q` incl. e2e (fresh tmp dir → cache misses, behavior identical).

- [ ] **Step 5: Commit** — `git commit -am "T20: pipeline/cache.py — pathlib result cache on shared filename regex"`

---

### Task 4: `pipeline/problem_steps.py` + thin `problemRunner`

**Files:**
- Create: `experiments/src/pipeline/problem_steps.py`
- Modify: `experiments/src/problemRunner.py` (full rewrite — post-T14/T19 shape)
- Test: `experiments/tests/test_pipeline_steps.py` (new)

**Interfaces:**
- Consumes: `new_problem_id`, `result_file_name` (Task 1); `is_result_present` (Task 3); existing `helpers.runners.solverStrategy.get_solver`, `helpers.runners.sourceStrategy.load_and_transform_strategy`/`resolve_constraints_configs` (NOT moved — T21 renames them); T19 `RunnerResult`.
- Produces: `load_problem(config: RunnerConfig) -> tuple[MultiObjectiveLpProblem, list[ConstraintConfig], Utility]`; `build_runner_result(problem, config, constraints_configs, utility_type, problem_path: Path) -> RunnerResult`; `persist_result(problem, config, constraints_configs, utility_type) -> tuple[Path, Path]`.

- [ ] **Step 1: Write the failing tests**

```python
# experiments/tests/test_pipeline_steps.py
from pathlib import Path

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintLE,
    LpVariable,
    lpSum,
)

from helpers.runners.model import RunnerConfig, RunnerResult, Utility
from helpers.utils.utils import read_from_json
from pipeline.cache import is_result_present
from pipeline.problem_steps import build_runner_result, persist_result

SOURCE = "input/krakow_2024_mini"


def _tiny_solved_problem() -> MultiObjectiveLpProblem:
    problem = MultiObjectiveLpProblem("tiny")
    variables = LpVariable.dicts("", ["A", "B"], cat="Binary")
    variables["A"].setInitialValue(1)
    variables["B"].setInitialValue(0)
    problem.addVariables(variables.values())
    problem.set_objectives(
        [LpAffineExpression([(variables["A"], 1)], name="v1")]
    )
    problem.addConstraint(
        LpConstraint(
            e=lpSum([variables["A"] * 10, variables["B"] * 10]),
            sense=LpConstraintLE,
            rhs=10,
            name="pb",
        )
    )
    return problem


def _config(tmp_path: Path) -> RunnerConfig:
    return RunnerConfig.model_validate(
        {
            "solver_type": "GREEDY",
            "source_type": "PABUTOOLS",
            "source_directory_path": SOURCE,
            "results_base_path": str(tmp_path),
        }
    )


def test_build_runner_result_fields(tmp_path):
    problem = _tiny_solved_problem()
    result = build_runner_result(
        problem,
        _config(tmp_path),
        [],
        Utility.COST_ORDINAL,
        Path("results/problem_x.lp"),
    )
    assert result.instance_size == 2
    assert result.selected == ["_A"]
    assert result.time == problem.solutionTime
    assert result.problem_path == "results/problem_x.lp"


def test_persist_result_writes_lp_and_valid_meta(tmp_path):
    problem_path, meta_path = persist_result(
        _tiny_solved_problem(), _config(tmp_path), [], Utility.COST_ORDINAL
    )
    assert problem_path.exists()
    assert meta_path.exists()
    meta = RunnerResult.model_validate(read_from_json(meta_path))
    assert meta.selected == ["_A"]
    assert meta.problem_path == str(problem_path)


def test_persist_then_cache_hit(tmp_path):
    # writer and cache share one filename scheme — persist must be found
    config = _config(tmp_path)
    persist_result(
        _tiny_solved_problem(), config, [], Utility.COST_ORDINAL
    )
    assert is_result_present(config, Utility.COST_ORDINAL)
```

- [ ] **Step 2: Run to verify failure**

Run: `poetry run pytest tests/test_pipeline_steps.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'pipeline.problem_steps'`

- [ ] **Step 3: Implement**

```python
# experiments/src/pipeline/problem_steps.py
from pathlib import Path

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from helpers.runners.model import (
    ConstraintConfig,
    RunnerConfig,
    RunnerResult,
    Utility,
)
from helpers.runners.sourceStrategy import (
    load_and_transform_strategy,
    resolve_constraints_configs,
)
from helpers.utils.utils import write_to_json
from pipeline.paths import new_problem_id, result_file_name


def load_problem(
    config: RunnerConfig,
) -> tuple[MultiObjectiveLpProblem, list[ConstraintConfig], Utility]:
    constraints_configs = resolve_constraints_configs(config)
    return load_and_transform_strategy(
        config.source_type,
        config.utility_type,
        config.source_directory_path,
        constraints_configs,
        config.deduplicate_objectives,
    )


def build_runner_result(
    problem: MultiObjectiveLpProblem,
    config: RunnerConfig,
    constraints_configs: list[ConstraintConfig],
    utility_type: Utility,
    problem_path: Path,
) -> RunnerResult:
    return RunnerResult(
        time=problem.solutionTime,
        solver=config.solver_type,
        solver_options=config.solver_options,
        source_type=config.source_type,
        utility_type=utility_type,
        source_path=config.source_directory_path,
        constraints_configs=constraints_configs,
        deduplicate_objectives=config.deduplicate_objectives,
        problem_path=str(problem_path),
        instance_size=len(
            [
                variable
                for variable in problem.variables()
                if variable.name != "__dummy"
            ]
        ),
        selected=sorted(
            var.name for var in problem.variables() if var.value() == 1.0
        ),
    )


def persist_result(
    problem: MultiObjectiveLpProblem,
    config: RunnerConfig,
    constraints_configs: list[ConstraintConfig],
    utility_type: Utility,
) -> tuple[Path, Path]:
    if config.results_base_path is None:
        raise ValueError("results_base_path not set on RunnerConfig")
    results_dir = Path(config.results_base_path)
    problem_id = new_problem_id()
    problem_path = results_dir / result_file_name(
        "problem", "lp", problem_id,
        config.source_directory_path, utility_type, config.solver_type,
    )
    result = build_runner_result(
        problem, config, constraints_configs, utility_type, problem_path
    )
    # write_lp (not pulp writeLP): appends OBJECTIVES/WEIGHTS sections
    # required by read_lp_file in analyzer
    problem.write_lp(str(problem_path))
    meta_path = results_dir / result_file_name(
        "meta", "json", problem_id,
        config.source_directory_path, utility_type, config.solver_type,
    )
    write_to_json(
        meta_path, result.model_dump(mode="json", exclude_none=True)
    )
    return problem_path, meta_path
```

`problemRunner.py` full rewrite (solver construction stays OUTSIDE try — old behavior: construction errors raise raw, only solve/persist get the "Problem failed" log):

```python
import logging

from helpers.runners.model import RunnerConfig
from helpers.runners.solverStrategy import get_solver
from pipeline.cache import is_result_present
from pipeline.problem_steps import load_problem, persist_result

logger = logging.getLogger(__name__)


def problem_runner(config: RunnerConfig) -> None:
    logger.debug("Start problem", extra={"config": config})
    problem, constraints_configs, utility_type = load_problem(config)
    if is_result_present(config, utility_type):
        logger.info(f"Result already present - {config.results_base_path}")
        return

    solver = get_solver(config.solver_type, config.solver_options)
    try:
        problem.solve(solver)
        persist_result(problem, config, constraints_configs, utility_type)
    except Exception as err:
        logger.error(
            "Problem failed",
            extra={"source": config.source_directory_path, "error": err},
        )
        raise
```

- [ ] **Step 4: Run** — `poetry run pytest tests/test_pipeline_steps.py -q` → 3 PASS. Full `poetry run pytest -q` incl. e2e golden — meta bytes identical: filename from `result_file_name` == old closure output (Task 1 legacy-scheme test), `problem_path` `str(Path(base) / name)` == old `f"{base}{name}"` under trailing-slash configs. `wc -l src/problemRunner.py` ≤ ~30.

- [ ] **Step 5: Commit** — `git commit -am "T20: pipeline/problem_steps.py; thin problemRunner"`

---

### Task 5: `pipeline/analyzer_steps.py` + `AnalyzerConfig.concurrency` + thin `analyzerRunner`

**Files:**
- Create: `experiments/src/pipeline/analyzer_steps.py`
- Modify: `experiments/src/helpers/analyzers/model.py` (T19 `AnalyzerConfig`: add one field)
- Modify: `experiments/src/analyzerRunner.py` (full rewrite — post-T19 shape)
- Test: `experiments/tests/test_pipeline_analyzer.py` (new)

**Interfaces:**
- Consumes: `metrics_output_path`, `source_name` (Task 1); T19 `AnalyzerConfig`/`AnalyzerResult`/`Metric`, `get_metrics`, `RunnerResult`; existing `helpers.utils.enhanceFromSolverResult` (NOT moved — T21 target).
- Produces: `AnalyzerConfig.concurrency: int = 3` (default preserves old hardcode; sample/e2e configs without the field stay valid under `extra="forbid"`); `discover_meta_paths(results_base_path: str | Path) -> list[Path]`; `analyze_runner_result(runner_result_path: Path, metrics: list[Metric]) -> AnalyzerResult | None` (moved from analyzerRunner — Pool workers import it from `pipeline.analyzer_steps`).

- [ ] **Step 1: Write the failing tests**

```python
# experiments/tests/test_pipeline_analyzer.py
from helpers.analyzers.model import AnalyzerConfig
from pipeline.analyzer_steps import discover_meta_paths

BASE = {
    "analyzer_result_path": "analysis/",
    "experiment_results_base_path": "results/",
    "metrics": ["EJR_PLUS"],
}


def test_analyzer_config_default_concurrency():
    # was hardcoded Pool(processes=3) in analyzerRunner
    assert AnalyzerConfig.model_validate(BASE).concurrency == 3


def test_analyzer_config_concurrency_from_config():
    config = AnalyzerConfig.model_validate(BASE | {"concurrency": 5})
    assert config.concurrency == 5


def test_discover_meta_paths_sorted_json_files_only(tmp_path):
    (tmp_path / "b_meta.json").write_text("{}")
    (tmp_path / "a_meta.json").write_text("{}")
    (tmp_path / "problem_x.lp").write_text("")
    (tmp_path / "nested").mkdir()
    names = [path.name for path in discover_meta_paths(tmp_path)]
    assert names == ["a_meta.json", "b_meta.json"]
```

- [ ] **Step 2: Run to verify failure**

Run: `poetry run pytest tests/test_pipeline_analyzer.py -q`
Expected: FAIL — no `pipeline.analyzer_steps`; `concurrency` rejected by `extra="forbid"`.

- [ ] **Step 3: Implement**

`helpers/analyzers/model.py` — `AnalyzerConfig` gains:

```python
class AnalyzerConfig(StrictModel):
    analyzer_result_path: str
    experiment_results_base_path: str
    metrics: list[Metric]
    concurrency: int = 3  # analyzer Pool size (was hardcoded)
```

```python
# experiments/src/pipeline/analyzer_steps.py
import logging
from pathlib import Path

from muoblp.utils.lp_reader_utils import read_lp_file

from helpers.analyzers.metrics import get_metrics
from helpers.analyzers.model import AnalyzerResult, Metric
from helpers.runners.model import RunnerResult
from helpers.utils.enhanceFromSolverResult import (
    enhance_problem_from_solver_result,
)
from helpers.utils.utils import read_from_json
from pipeline.paths import source_name

logger = logging.getLogger(__name__)


def discover_meta_paths(results_base_path: str | Path) -> list[Path]:
    # sorted: deterministic analysis row order (golden sorts anyway)
    return sorted(
        path
        for path in Path(results_base_path).iterdir()
        if path.is_file() and path.suffix == ".json"
    )


def analyze_runner_result(
    runner_result_path: Path, metrics: list[Metric]
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
            city=source_name(solver_result.source_path),
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

(body = T19's `analyze_runner_result` moved verbatim; only `city` now via `source_name` — same value, `.pb`-suffix strip on basename.)

`analyzerRunner.py` full rewrite:

```python
import logging
import multiprocessing
import sys
from itertools import repeat
from pathlib import Path

from helpers.analyzers.analysis_table import (
    transform_metrics_to_markdown_table,
)
from helpers.analyzers.model import AnalyzerConfig
from helpers.utils.logger import setup_logging
from helpers.utils.utils import read_from_json, write_to_json
from pipeline.analyzer_steps import analyze_runner_result, discover_meta_paths
from pipeline.paths import metrics_output_path

logger = logging.getLogger(__name__)


def main(
    config: AnalyzerConfig | dict, console_output_limit: int | None = None
):
    config = AnalyzerConfig.model_validate(config)
    logger.info("Start analysis", extra={"config": config})
    meta_paths = discover_meta_paths(config.experiment_results_base_path)
    Path(config.analyzer_result_path).mkdir(parents=True, exist_ok=True)

    with multiprocessing.Pool(
        processes=config.concurrency, initializer=setup_logging
    ) as pool:
        analysis = pool.starmap(
            analyze_runner_result, zip(meta_paths, repeat(config.metrics))
        )

    result_path = metrics_output_path(
        config.analyzer_result_path, config.experiment_results_base_path
    )
    write_to_json(
        result_path,
        [
            row.model_dump(mode="json", exclude_none=True)
            if row is not None
            else None
            for row in analysis
        ],
    )
    print(transform_metrics_to_markdown_table(result_path, console_output_limit))


if __name__ == "__main__":
    setup_logging()
    main(read_from_json(Path(sys.argv[1])), 25)
```

- [ ] **Step 4: Run** — `poetry run pytest tests/test_pipeline_analyzer.py -q` → 3 PASS. Full `poetry run pytest -q` incl. e2e — output file still `metrics-results.json` (Task 1 legacy-naming test), rows identical after normalization. `wc -l src/analyzerRunner.py` ≤ ~55.

- [ ] **Step 5: Commit** — `git commit -am "T20: pipeline/analyzer_steps.py; Pool size from config; thin analyzerRunner"`

---

### Task 6: pathlib sweep — last `os.path` sites

**Files:**
- Modify: `experiments/src/helpers/transformers/pabutoolsUtils.py:43-59` (`load_pabutools_by_district` file discovery)
- Modify: `experiments/src/helpers/analyzers/analysis_table.py:2,44` (`os.path.basename` → `Path(...).name`)

Existing 54 transform tests + `test_analysis_table.py` + e2e are the spec — no new tests (T26 owns deeper coverage).

- [ ] **Step 1: Implement `pabutoolsUtils.py`**

Replace the discovery block (keep `path: str` signature — callers pass str):

```python
    source = Path(path)
    relevant_files: list[Path] = []
    if source.is_file() and source.suffix == ".pb":
        relevant_files.append(source)
    if source.is_dir():
        # sorted: iteration order is fs-dependent; district order defines
        # LP var order -> solver tie-breaks -> nondeterministic `selected`
        relevant_files.extend(
            sorted(p for p in source.iterdir() if p.suffix == ".pb")
        )

    for file in relevant_files:
        instance, profile = parse_pabulib(str(file))
```

(rest of loop body unchanged; same-dir name-sort order preserved). Drop the inner redundant `endswith(".pb")` re-check, drop `import os`, add `from pathlib import Path`.

- [ ] **Step 2: Implement `analysis_table.py`**

Line 44: `filename = os.path.basename(problem_path)` → `filename = Path(problem_path).name` (`Path` already imported); delete `import os`.

- [ ] **Step 3: Run + grep AC**

Run: `poetry run pytest -q` (incl. transform tests + e2e golden — identical).
Run: `grep -rn "os\.path\|os\.listdir\|import os$" experiments/src --include="*.py"` → empty.
Run: `grep -rn "split('/'\|split(\"/" experiments/src --include="*.py"` → empty.
Run: `grep -rn "_path}{" experiments/src --include="*.py"` → empty.

- [ ] **Step 4: Commit** — `git commit -am "T20: pathlib sweep — drop last os.path/os.listdir sites"`

---

### Task 7: Full verify + sample smoke + PR

- [ ] **Step 1: Full matrix**

`cd experiments && poetry run pytest -q && poetry run pytest -m e2e -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright` → all green, pyright 0 with post-T19 config. Siblings: `cd ../solvers && poetry run pytest -q`; `cd ../core && poetry run pytest -q` (untouched).

- [ ] **Step 2: Thin-entrypoint AC**

Run: `wc -l src/experimentRunner.py src/problemRunner.py src/analyzerRunner.py` → each ≤ ~55 (from 58/101/85).

- [ ] **Step 3: Sample smoke** (ticket Verify: "run sample")

```bash
cd experiments/sample-experiment && rm -rf results/*
PATH="$(poetry -C .. env info --path)/bin:$PATH" ./run.sh
PATH="$(poetry -C .. env info --path)/bin:$PATH" ./analyze.sh
```

Expected: metrics match reference values (APPROVAL 0.0033/219239/167; COST 0.0035/1.34763e11; COST_ORDINAL 0.0032/2.79444e11; bronowice 0.0666/4.35159e9); output file `results/sample-analysis/metrics-sample-experiment.json`. Then re-run `./run.sh` WITHOUT rm → all 4 configs log "Found result" (cache-hit path through new regex).

- [ ] **Step 4: Commit + PR**

Push, PR → `feat/roadmap-base-branch`, title `T20: extract shared pipeline lib`. Body: lib layout map, mutation-kill (resolve_runner_configs), filename dedup + roundtrip test, `AnalyzerConfig.concurrency` (default 3 = old hardcode), trailing-slash concat removed (configs with slashes still work; without now also work), pathlib sweep. Update ROADMAP checkbox + PR link. Update `plans/leftovers.md`: T21 rename list shrinks — `resultCache.py` → `pipeline/cache.py`, `expand_experiment_config.py` → `pipeline/config.py` (both gone); `analyze_runner_result` now in `pipeline/analyzer_steps.py`; e2e test comment "trailing slashes required" stale (harmless — T21 may fix wording); T26 cache tests partly pre-paid here (hit/miss variants exist, invalidation + jsonc roundtrip still owed).

## Unresolved questions

1. Lib package name `pipeline` (`experiments/src/pipeline/`) — OK? Alt: `explib` / `muoblpexp`.
2. `resultCache.py` + `expand_experiment_config.py` git-mv'd INTO lib (originals gone, T21 rename list shrinks). OK, or keep originals as shims until T21?
3. `solverStrategy`/`sourceStrategy`/`enhanceFromSolverResult` NOT absorbed — stay camelCase for T21 rename, lib imports them. OK?
4. `AnalyzerConfig.concurrency` default 3 (old hardcode); sample-analysis-config.jsonc left implicit. Add field explicitly to sample config?
5. `meta_file_regex` uses `fullmatch` + `re.escape` (old: unanchored tail, unescaped dot — `...GREEDY.jsonX` matched). Stricter, only affects stray files in results dir. OK?
6. `source_name` uses `removesuffix(".pb")` (old `replace(".pb", "")` also hit interior occurrences — none exist in real data). OK?
7. e2e test file untouched; its "trailing slashes required" comment becomes stale. Leftovers note only, or update comment in this ticket?
