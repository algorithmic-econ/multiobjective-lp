import logging
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from helpers.runners.model import RunnerConfig, RunnerResult
from helpers.runners.solverStrategy import get_solver
from helpers.runners.sourceStrategy import (
    load_and_transform_strategy,
    resolve_constraints_configs,
)
from helpers.utils.resultCache import is_result_present
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

        def get_file_name(
            file_type: Literal["problem", "meta"],
            ext: Literal["lp", "json"],
            unique_problem_id: str,
        ) -> str:
            # TODO: Cache checking relies on file structure defined here
            return f"{file_type}_{unique_problem_id}_{source_directory_path.split('/')[-1].replace('.pb', '')}_{utility_type}_{solver_type}.{ext}"

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
        problem.write_lp(problem_path)
        meta_file = get_file_name("meta", "json", problem_id)
        write_to_json(
            Path(f"{results_base_path}{meta_file}"),
            result.model_dump(mode="json", exclude_none=True),
        )

    except Exception as err:
        logger.error(
            "Problem failed",
            extra={"source": source_directory_path, "error": err},
        )
        raise err
