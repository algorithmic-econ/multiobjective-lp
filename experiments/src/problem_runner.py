import logging
from pathlib import Path

from helpers.runners.model import RunnerConfig, RunnerResult
from helpers.runners.solver_strategy import get_solver
from helpers.runners.source_strategy import (
    load_and_transform_strategy,
    resolve_constraints_configs,
)
from helpers.utils.result_naming import (
    data_source_name,
    new_problem_id,
    result_filename,
)
from helpers.utils.result_cache import is_result_present
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
    if is_result_present(config, utility_type):
        logger.info(f"Result already present - {results_base_path}")
        return

    solver = get_solver(solver_type, solver_options)
    try:
        problem.solve(solver)

        results_dir = Path(results_base_path)
        problem_id = new_problem_id()
        data_source = data_source_name(source_directory_path)
        problem_path = results_dir / result_filename(
            "problem", "lp", problem_id, data_source, utility_type, solver_type
        )
        meta_path = results_dir / result_filename(
            "meta", "json", problem_id, data_source, utility_type, solver_type
        )

        result = RunnerResult(
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
