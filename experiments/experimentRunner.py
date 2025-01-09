import multiprocessing
import sys
import time
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

    start_time = time.time()
    print(f"starting experiment {experiment['experiment_results_base_path']}")
    with multiprocessing.Pool(processes=2) as pool:
        pool.map(problem_runner, experiment['runner_configs'])
    print(f"finished experiment {time.time() - start_time}")


if __name__ == '__main__':
    config: ExperimentConfig = read_from_json(sys.argv[1])
    main(config)
