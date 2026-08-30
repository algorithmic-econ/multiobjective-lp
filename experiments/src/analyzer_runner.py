import logging
import multiprocessing
import sys
from itertools import repeat
from pathlib import Path
from typing import List

from muoblp.utils.lp_reader_utils import read_lp_file

from helpers.analyzers.analysis_table import (
    transform_metrics_to_markdown_table,
)
from helpers.analyzers.metrics import get_metrics
from helpers.analyzers.model import (
    AnalyzerConfig,
    AnalyzerFailure,
    AnalyzerResult,
    Metric,
)
from helpers.runners.model import RunnerResult
from helpers.utils.enhance_from_solver_result import (
    enhance_problem_from_solver_result,
)
from helpers.utils.logger import setup_logging
from helpers.utils.utils import read_from_json, write_to_json

logger = logging.getLogger(__name__)


def analyze_runner_result(
    runner_result_path: Path, metrics: List[Metric]
) -> AnalyzerResult | AnalyzerFailure:
    logger.info("Analyse result", extra={"path": runner_result_path})
    try:
        solver_result = RunnerResult.model_validate(
            read_from_json(runner_result_path)
        )
        problem = read_lp_file(solver_result.problem_path)
        problem = enhance_problem_from_solver_result(solver_result, problem)
        metric_values = get_metrics(metrics, problem)
        return AnalyzerResult(
            problem_path=runner_result_path.as_posix(),
            metrics=metrics,
            time=solver_result.time,
            city=Path(solver_result.source_path).name.replace(".pb", ""),
            solver=solver_result.solver,
            solver_options=solver_result.solver_options,
            constraints_configs=solver_result.constraints_configs,
            utility=solver_result.utility_type,
            **metric_values,
        )
    except Exception as err:
        logger.exception(
            "Failed to analyze result", extra={"problem": runner_result_path}
        )
        return AnalyzerFailure(
            meta_path=runner_result_path.as_posix(),
            error_type=type(err).__name__,
            error_message=str(err),
        )


def main(
    config: AnalyzerConfig | dict, console_output_limit: int | None = None
) -> tuple[int, int]:
    config = AnalyzerConfig.model_validate(config)
    logger.info("Start analysis", extra={"config": config})
    runner_results = [
        result_path
        for result_path in Path(config.experiment_results_base_path).iterdir()
        if result_path.is_file() and result_path.suffix == ".json"
    ]

    Path(config.analyzer_result_path).mkdir(parents=True, exist_ok=True)

    with multiprocessing.Pool(
        processes=config.concurrency, initializer=setup_logging
    ) as pool:
        analysis = pool.starmap(
            analyze_runner_result,
            zip(runner_results, repeat(config.metrics)),
        )
        results_dir_name = Path(config.experiment_results_base_path).name
        result_path = (
            Path(config.analyzer_result_path)
            / f"metrics-{results_dir_name}.json"
        )
        write_to_json(
            result_path,
            [
                row.model_dump(mode="json", exclude_none=True)
                for row in analysis
            ],
        )

    failed = sum(1 for row in analysis if isinstance(row, AnalyzerFailure))
    ok = len(analysis) - failed
    if failed:
        logger.error(
            "analysis failed for %d of %d results", failed, len(analysis)
        )
    else:
        logger.info("analysis succeeded for all %d results", ok)

    markdown_output = transform_metrics_to_markdown_table(
        result_path, console_output_limit
    )
    print(markdown_output)
    return ok, failed


if __name__ == "__main__":
    # Example (from sample-experiment/):
    #   python ../src/analyzer_runner.py sample-analysis-config.jsonc
    setup_logging()
    _, failed = main(read_from_json(Path(sys.argv[1])), 25)
    if failed:
        sys.exit(1)
