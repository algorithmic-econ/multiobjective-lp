import multiprocessing
import os
from typing import List, TypedDict

from experiments.helpers.runners.model import RunnerConfig
from experiments.helpers.utils.utils import read_from_json
from experiments.problemRunner import problem_runner


class ExperimentConfig(TypedDict):
    experiment_results_base_path: str
    runner_configs: List[RunnerConfig]


def main(experiment: ExperimentConfig):
    os.mkdir(experiment['experiment_results_base_path'])

    with multiprocessing.Pool(processes=4) as pool:
        pool.map(problem_runner, experiment['runner_configs'])


if __name__ == '__main__':
    config: ExperimentConfig = read_from_json("resources/input/experiment-config/sample-experiment.json")
    main(config)
