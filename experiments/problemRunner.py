import sys
import time

from datetime import datetime

from helpers.utils.utils import write_to_json
from helpers.runners.model import validate_args, RunnerResult
from helpers.runners.sourceStrategy import load_and_transform_strategy
from helpers.runners.solverStrategy import get_solver

# EXAMPLE parameters: python runner.py SUMMING PABUTOOLS resources/input/warszawa_2023_test/
if __name__ == '__main__':
    solver_type, source_type, source_directory_path, constraints_configs_path = validate_args(sys.argv[1:])

    startTime = time.time()
    problem = load_and_transform_strategy(source_type, source_directory_path, constraints_configs_path)
    solver = get_solver(solver_type)
    solver.msg = False  # set to True to see solver logs
    problem.solve(solver)

    endTime = time.time()

    result: RunnerResult = {
        "time": endTime - startTime,
        "solver": solver_type.name,
        "source_type": source_type.name,
        "constraints_configs": constraints_configs_path,
        "source": source_directory_path.split('/')[-2],
        "selected": [project.name[1:] for project in [var for var in problem.variables() if var.value() == 1.0]],
        "problem": problem.toDict()
    }

    basePath = 'resources/solver-results/'
    # write_to_json(
    #     f"{basePath}{datetime.now().isoformat(timespec='seconds')}_{result['source']}_{result['solver']}.json",
    #     result)
    write_to_json(f"{basePath}latest.json", result)
