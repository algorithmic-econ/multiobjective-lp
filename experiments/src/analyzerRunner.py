import logging
import multiprocessing
import sys
from itertools import repeat
from pathlib import Path
from typing import List

from muoblp.utils.lpReaderUtils import read_lp_file

from helpers.analyzers.analysis_table import (
    transform_metrics_to_markdown_table,
)
from helpers.analyzers.metrics import get_metrics
from helpers.analyzers.model import AnalyzerConfig, AnalyzerResult, Metric
from helpers.runners.model import RunnerResult
from helpers.utils.enhanceFromSolverResult import (
    enhance_problem_from_solver_result,
)
from helpers.utils.logger import setup_logging
from helpers.utils.utils import read_from_json, write_to_json

logger = logging.getLogger(__name__)


def analyze_runner_result(
    runner_result_path: Path, metrics: List[Metric]
) -> AnalyzerResult | None:
    logger.info("Analyse result", extra={"path": runner_result_path})
    try:
        solver_result: RunnerResult = read_from_json(runner_result_path)
        problem = read_lp_file(solver_result["problem_path"])
        problem = enhance_problem_from_solver_result(solver_result, problem)
        analyzer_result = get_metrics(metrics, problem)
        return {
            "problem_path": runner_result_path.as_posix()
        } | analyzer_result
    except Exception as err:
        # TODO: return empty result with metadata isntead of None
        logger.error(
            "Failed to analyze results",
            extra={"problem": runner_result_path, "error": err},
        )


def main(config: AnalyzerConfig, console_output_limit: int | None = None):
    logger.info("Start analysis", extra={"config": config})
    runner_results = [
        result_path
        for result_path in Path(
            config["experiment_results_base_path"]
        ).iterdir()
        if result_path.is_file() and result_path.suffix == ".json"
    ]

    Path(config["analyzer_result_path"]).mkdir(parents=True, exist_ok=True)

    with multiprocessing.Pool(processes=3, initializer=setup_logging) as pool:
        analysis = pool.starmap(
            analyze_runner_result,
            zip(runner_results, repeat(config["metrics"])),
        )
        result_path = Path(
            f"{config['analyzer_result_path']}metrics-{config['experiment_results_base_path'].split('/')[-2]}.json"
        )
        write_to_json(result_path, analysis)

    markdown_output = transform_metrics_to_markdown_table(
        result_path, console_output_limit
    )
    print(markdown_output)


if __name__ == "__main__":
    # Example: python analyzerRunner.py resources/input/analyzer-config/sample-analysis.json
    setup_logging()
    analyzer_config: AnalyzerConfig = read_from_json(Path(sys.argv[1]))
    main(analyzer_config, 25)
