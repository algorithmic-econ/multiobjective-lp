import logging
from pathlib import Path

from helpers.runners.model import RunnerConfig, RunnerResult
from helpers.runners.solver_strategy import get_solver
from helpers.runners.source_strategy import (
    load_and_transform_strategy,
    resolve_constraints_configs,
)
from helpers.utils.result_cache import (
    build_cache_key,
    cache_key_hash,
    find_cached_run,
)
from helpers.utils.result_naming import (
    META_FILENAME,
    PROBLEM_FILENAME,
    new_run_id,
    run_dir_name,
)
from helpers.utils.utils import write_to_json

logger = logging.getLogger(__name__)


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

    logger.debug("Start problem", extra={"config": config})

    problem, constraints_configs, utility_type = load_and_transform_strategy(
        source_type,
        utility_type,
        source_directory_path,
        constraints_configs,
        deduplicate_objectives,
    )
    results_dir = Path(results_base_path)
    cache_key = build_cache_key(config, utility_type)
    cached_run = find_cached_run(results_dir, cache_key)
    if cached_run is not None:
        logger.info(f"Result already present - {cached_run}")
        return

    solver = get_solver(solver_type, solver_options)
    try:
        problem.solve(solver)

        key_hash = cache_key_hash(cache_key)
        run_dir = results_dir / run_dir_name(
            new_run_id(),
            cache_key.data_source,
            utility_type,
            solver_type,
            key_hash,
        )
        run_dir.mkdir(parents=True)
        problem_path = run_dir / PROBLEM_FILENAME
        meta_path = run_dir / META_FILENAME

        result = RunnerResult(
            cache_key=cache_key,
            key_hash=key_hash,
            time=problem.solutionTime,
            solver=solver_type,
            solver_options=solver_options,
            source_type=source_type,
            utility_type=utility_type,
            source_path=source_directory_path,
            constraints_configs=constraints_configs,
            deduplicate_objectives=deduplicate_objectives,
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
        # write_lp (not pulp writeLP): appends OBJECTIVES/WEIGHTS sections
        # required by read_lp_file in analyzer
        problem.write_lp(str(problem_path))
        # meta last: marks run complete for find_cached_run
        write_to_json(
            meta_path,
            result.model_dump(mode="json", exclude_none=True),
        )

    except Exception as err:
        logger.error(
            "Problem failed",
            extra={"source": source_directory_path, "error": err},
        )
        raise err
