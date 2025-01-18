import sys
from typing import List, get_args, cast

from experiments.helpers.runners.model import RunnerConfig, Solver, Source
from experiments.problemRunner import problem_runner


def cli_to_runner_config(args: List[str]) -> RunnerConfig:
    if not args[0] in get_args(Solver):
        raise Exception("Unsupported solver type")
    if not args[1] in get_args(Source):
        raise Exception("Unsupported source type")
    if not args[2]:
        raise Exception("Missing source directory path")
    constraints_configs_path = args[3] if len(args) > 3 else None
    results_base_path = args[4] if len(args) > 4 else 'resources/solver-results/'
    return {
        'solver_type': cast(Solver, args[0]),
        'source_type': cast(Source, args[1]),
        'source_directory_path': args[2],
        'constraints_configs_path': constraints_configs_path,
        'results_base_path': results_base_path
    }


if __name__ == '__main__':
    problem_runner(cli_to_runner_config(sys.argv[1:]))
# EXAMPLE parameters: python runner.py SUMMING PABUTOOLS resources/input/warszawa_2023_test/
