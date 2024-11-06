import time
from datetime import datetime
from uuid import uuid4

from helpers.runners.model import RunnerResult, RunnerConfig
from helpers.runners.solverStrategy import get_solver
from helpers.runners.sourceStrategy import load_and_transform_strategy
from helpers.utils.utils import write_to_json


def problem_runner(config: RunnerConfig):
    solver_type = config['solver_type']
    source_type = config['source_type']
    source_directory_path = config['source_directory_path']
    constraints_configs_path = config['constraints_configs_path']
    results_base_path = config['results_base_path']

    start_time = time.time()
    problem, constraints_configs = load_and_transform_strategy(source_type,
                                                               source_directory_path,
                                                               constraints_configs_path)
    solver = get_solver(solver_type)
    problem.solve(solver)

    end_time = time.time()

    result: RunnerResult = {
        "time": end_time - start_time,
        "solver": solver_type,
        "source_type": source_type,
        "source_path": source_directory_path,
        "constraints_configs": constraints_configs,
        "problem_path": None,
        "selected": [project.name[1:] for project in [var for var in problem.variables() if var.value() == 1.0]]
    }

    problem_id = f"{datetime.now().isoformat(timespec='seconds')[5:]}_{str(uuid4())[:8]}"
    result['problem_path'] = f"{results_base_path}problem_{problem_id}.lp"

    problem.writeLP(f"{results_base_path}problem_{problem_id}.lp")
    write_to_json(f"{results_base_path}run_{problem_id}.json",result)

    # problem.writeLP(f"{results_base_path}latest.lp")
    # write_to_json(f"{results_base_path}latest.json", result)
