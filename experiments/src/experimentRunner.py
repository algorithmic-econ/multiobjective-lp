import logging
import multiprocessing
import sys
import time
from pathlib import Path

from helpers.runners.model import ExperimentConfig
from helpers.utils.logger import setup_logging
from helpers.utils.utils import read_from_json
from problemRunner import problem_runner

logger = logging.getLogger(__name__)


def main(experiment: ExperimentConfig):
    Path(experiment["experiment_results_base_path"]).mkdir(
        parents=True, exist_ok=True
    )

    for runner_config in experiment["runner_configs"]:
        if "results_base_path" not in runner_config:
            runner_config["results_base_path"] = experiment[
                "experiment_results_base_path"
            ]

    start_time = time.time()
    logger.info(
        "Start experiment",
        extra={
            "concurrency": experiment["concurrency"],
            "experiment_results_base_path": experiment[
                "experiment_results_base_path"
            ],
        },
    )
    with multiprocessing.Pool(
        processes=int(experiment["concurrency"]), initializer=setup_logging
    ) as pool:
        pool.map(problem_runner, experiment["runner_configs"])

    logger.info("Finish experiment", extra={"time": time.time() - start_time})


if __name__ == "__main__":
    setup_logging()
    config: ExperimentConfig = read_from_json(Path(sys.argv[1]))
    main(config)
