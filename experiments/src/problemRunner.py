import time
from datetime import datetime
from uuid import uuid4

from typing import Literal

from helpers.runners.model import RunnerConfig, RunnerResult
from helpers.runners.solverStrategy import get_solver
from helpers.runners.sourceStrategy import load_and_transform_strategy
from helpers.utils.utils import write_to_json
from src.helpers.utils.resultCache import is_result_present


def problem_runner(config: RunnerConfig) -> None:
    solver_type = config["solver_type"]
    solver_options = config.get("solver_options", {})
    source_type = config["source_type"]
    source_directory_path = config["source_directory_path"]
    constraints_configs_path = config.get("constraints_configs_path")
    results_base_path = config["results_base_path"]

    print(f"Starting problem - {config}")
    if is_result_present(config):
        print(f"Result already present - {results_base_path}")
        return

    start_time = time.time()
    problem, constraints_configs = load_and_transform_strategy(
        source_type, source_directory_path, constraints_configs_path
    )
    solver = get_solver(solver_type, solver_options)
    problem.solve(solver)

    end_time = time.time()

    result: RunnerResult = {
        "time": end_time - start_time,
        "solver": solver_type,
        "solver_options": solver_options,
        "source_type": source_type,
        "source_path": source_directory_path,
        "constraints_configs": constraints_configs,
        "problem_path": None,
        "selected": [
            project.name
            for project in [
                var for var in problem.variables() if var.value() == 1.0
            ]
        ],
    }

    def get_file_name(
        file_type: Literal["problem", "meta"],
        ext: Literal["lp", "json"],
        unique_problem_id: str,
    ) -> str:
        # TODO: Cache checking relies on file structure defined here
        return f"{file_type}_{unique_problem_id}_{source_directory_path.split('/')[-1]}_{solver_type}.{ext}"

    problem_id = f"{datetime.now().isoformat(timespec='seconds').replace(':', '-')[5:]}_{str(uuid4())[:4]}"
    problem_file = get_file_name("problem", "lp", problem_id)
    result["problem_path"] = f"{results_base_path}{problem_file}"
    problem.writeLP(result["problem_path"])
    meta_file = get_file_name("meta", "json", problem_id)
    write_to_json(f"{results_base_path}{meta_file}", result)
