import logging

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpVariable

from analyzer_runner import analyze_runner_result, main
from helpers.analyzers.model import AnalyzerFailure, AnalyzerResult, Metric
from helpers.runners.model import (
    RunnerResult,
    Solver,
    Source,
    Utility,
)
from helpers.utils.utils import write_to_json


def _make_tiny_problem() -> MultiObjectiveLpProblem:
    p1 = LpVariable("p1", cat="Binary")
    p1.setInitialValue(1)
    v1 = LpAffineExpression({p1: 100})
    problem = MultiObjectiveLpProblem(
        "tiny", objectives=[v1], objectives_weights={}
    )
    problem += 100 * p1 <= 250, "pb_constraint"
    return problem


def _persist_happy_meta(tmp_path):
    problem_path = tmp_path / "problem_ok.lp"
    meta_path = tmp_path / "meta_ok.json"
    _make_tiny_problem().write_lp(str(problem_path))
    result = RunnerResult(
        time=0.1,
        solver=Solver.GREEDY,
        solver_options={},
        source_type=Source.PABUTOOLS,
        utility_type=Utility.COST,
        source_path="krakow_2024",
        constraints_configs=[],
        deduplicate_objectives=False,
        problem_path=str(problem_path),
        instance_size=1,
        selected=["p1"],
    )
    write_to_json(meta_path, result.model_dump(mode="json", exclude_none=True))
    return meta_path


def test_invalid_json_meta_returns_failure(tmp_path):
    meta_path = tmp_path / "meta_bad.json"
    meta_path.write_text("not json")

    result = analyze_runner_result(meta_path, [Metric.SUM_OBJECTIVES])

    assert isinstance(result, AnalyzerFailure)
    assert result.meta_path == meta_path.as_posix()
    assert result.error_type


def test_missing_problem_lp_returns_failure(tmp_path):
    meta_path = tmp_path / "meta_missing_lp.json"
    result_data = RunnerResult(
        time=0.1,
        solver=Solver.GREEDY,
        solver_options={},
        source_type=Source.PABUTOOLS,
        utility_type=Utility.COST,
        source_path="krakow_2024",
        constraints_configs=[],
        deduplicate_objectives=False,
        problem_path=str(tmp_path / "does_not_exist.lp"),
        instance_size=1,
        selected=["p1"],
    )
    write_to_json(
        meta_path, result_data.model_dump(mode="json", exclude_none=True)
    )

    result = analyze_runner_result(meta_path, [Metric.SUM_OBJECTIVES])

    assert isinstance(result, AnalyzerFailure)
    assert result.meta_path == meta_path.as_posix()
    assert result.error_type == "FileNotFoundError"


def test_invalid_runner_result_schema_returns_failure(tmp_path):
    meta_path = tmp_path / "meta_bad_schema.json"
    write_to_json(
        meta_path, {"solver": "GREEDY", "unexpected_extra_key": True}
    )

    result = analyze_runner_result(meta_path, [Metric.SUM_OBJECTIVES])

    assert isinstance(result, AnalyzerFailure)
    assert result.error_type == "ValidationError"


def test_happy_path_returns_analyzer_result(tmp_path):
    meta_path = _persist_happy_meta(tmp_path)

    result = analyze_runner_result(meta_path, [Metric.SUM_OBJECTIVES])

    assert isinstance(result, AnalyzerResult)
    assert result.solver == Solver.GREEDY


def test_main_returns_mixed_counts_and_writes_both_row_kinds(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    _persist_happy_meta(results_dir)
    (results_dir / "meta_bad.json").write_text("not json")

    analysis_dir = tmp_path / "analysis"
    config = {
        "analyzer_result_path": str(analysis_dir),
        "experiment_results_base_path": str(results_dir),
        "metrics": ["SUM_OBJECTIVES"],
    }

    ok, failed = main(config)

    assert (ok, failed) == (1, 1)
    rows = __import__("json").loads(
        (analysis_dir / f"metrics-{results_dir.name}.json").read_text()
    )
    assert len(rows) == 2
    assert sum(1 for row in rows if "error_type" in row) == 1


def test_main_returns_zero_failed_when_all_ok(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    _persist_happy_meta(results_dir)

    analysis_dir = tmp_path / "analysis"
    config = {
        "analyzer_result_path": str(analysis_dir),
        "experiment_results_base_path": str(results_dir),
        "metrics": ["SUM_OBJECTIVES"],
    }

    ok, failed = main(config)

    assert (ok, failed) == (1, 0)


def test_main_logs_failure_summary(tmp_path, caplog):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "meta_bad.json").write_text("not json")

    analysis_dir = tmp_path / "analysis"
    config = {
        "analyzer_result_path": str(analysis_dir),
        "experiment_results_base_path": str(results_dir),
        "metrics": ["SUM_OBJECTIVES"],
    }

    with caplog.at_level(logging.ERROR, logger="analyzer_runner"):
        main(config)

    assert any("failed" in record.message for record in caplog.records)
