import multiprocessing
import sys
from pathlib import Path
from typing import List, TypedDict

from experiments.helpers.runners.model import RunnerConfig
from experiments.helpers.utils.utils import read_from_json
from experiments.problemRunner import problem_runner


class ExperimentConfig(TypedDict):
    experiment_results_base_path: str
    runner_configs: List[RunnerConfig]


def main(experiment: ExperimentConfig):

    Path(experiment['experiment_results_base_path']).mkdir(parents=True, exist_ok=True)

    for runner_config in experiment['runner_configs']:
        if 'results_base_path' not in runner_config:
            runner_config['results_base_path'] = experiment['experiment_results_base_path']

    with multiprocessing.Pool(processes=4) as pool:
        pool.map(problem_runner, experiment['runner_configs'])


if __name__ == '__main__':
    config: ExperimentConfig = read_from_json(sys.argv[1])
    main(config)
