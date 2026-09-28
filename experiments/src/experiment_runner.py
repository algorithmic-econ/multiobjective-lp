import logging
import multiprocessing
import sys
import time
from pathlib import Path
from typing import Any

from helpers.runners.model import (
    CompactExperimentConfig,
    ExperimentConfig,
)
from helpers.transformers.expand_experiment_config import (
    parse_experiment_config,
    resolve_runner_configs,
)
from helpers.utils.logger import setup_logging
from helpers.utils.utils import read_from_json
from problem_runner import problem_runner

logger = logging.getLogger(__name__)


def main(
    raw_config: dict[str, Any] | ExperimentConfig | CompactExperimentConfig,
) -> None:
    config = parse_experiment_config(raw_config)

    Path(config.experiment_results_base_path).mkdir(
        parents=True, exist_ok=True
    )
    runner_configs = resolve_runner_configs(config)

    start_time = time.time()
    logger.info(
        "Start experiment",
        extra={
            "concurrency": config.concurrency,
            "experiment_results_base_path": (
                config.experiment_results_base_path
            ),
        },
    )
    with multiprocessing.Pool(
        processes=config.concurrency, initializer=setup_logging
    ) as pool:
        pool.map(problem_runner, runner_configs)

    logger.info("Finish experiment", extra={"time": time.time() - start_time})


if __name__ == "__main__":
    setup_logging()
    main(read_from_json(Path(sys.argv[1])))
