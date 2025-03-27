import multiprocessing
import os
import sys
from itertools import repeat
from pathlib import Path
from typing import List

from muoblp.utils.lpReaderUtils import read_lp_file

from helpers.analyzers.model import AnalyzerResult, AnalyzerConfig, Metric
from helpers.analyzers.metrics import get_metrics
from helpers.runners.model import RunnerResult
from helpers.utils.enhanceFromSolverResult import enhance_problem_from_solver_result
from helpers.utils.utils import read_from_json, write_to_json


def method_name(runner_result_path: Path, metrics: List[Metric]) -> AnalyzerResult:
    solver_result: RunnerResult = read_from_json(runner_result_path)
    problem = read_lp_file(solver_result["problem_path"])
    problem = enhance_problem_from_solver_result(solver_result, problem)
    analyzer_result = get_metrics(metrics, problem)
    return {"problem_path": runner_result_path.as_posix()} | analyzer_result


def main(config: AnalyzerConfig):
    runner_results = [
        result_path
        for result_path in Path(config["experiment_results_base_path"]).iterdir()
        if result_path.is_file() and result_path.suffix == ".json"
    ]

    Path(config["analyzer_result_path"]).mkdir(parents=True, exist_ok=True)

    with multiprocessing.Pool(processes=1) as pool:
        analysis = pool.starmap(
            method_name, zip(runner_results, repeat(config["metrics"]))
        )
        write_to_json(
            f"{config['analyzer_result_path']}metrics-{config['experiment_results_base_path'].split('/')[-2]}.json",
            analysis,
        )


if __name__ == "__main__":
    # Example: python analyzerRunner.py resources/input/analyzer-config/sample-analysis.json
    analyzer_config: AnalyzerConfig = read_from_json(sys.argv[1])
    main(analyzer_config)
