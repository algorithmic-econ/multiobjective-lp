"""Native metrics through the experiments harness (analyze_runner_result).

Metric-level parity and unit tests live in the `muoblpanalyzers` package
(analyzers/tests). Here: AnalyzerResult wiring + fail-loudly behaviour.
"""

import sys

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblpanalyzers import Metric
from pulp import LpAffineExpression, LpVariable

from analyzer_runner import analyze_runner_result
from helpers.analyzers.model import AnalyzerFailure, AnalyzerResult
from helpers.runners.model import RunnerResult, Solver, Source, Utility
from helpers.utils.utils import write_to_json

from .fixtures.runner_result_factories import cache_key_fields


def _make_problem() -> MultiObjectiveLpProblem:
    # v1 approves p1, v2 approves p2
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    objectives = [LpAffineExpression({p1: 100}), LpAffineExpression({p2: 200})]
    problem = MultiObjectiveLpProblem(
        "two_voters", objectives=objectives, objectives_weights={}
    )
    problem += 100 * p1 + 200 * p2 <= 250, "pb_constraint"
    return problem


def _persist_happy_meta(tmp_path):
    # same shape analyze_runner_result gets from experiment_runner
    problem_path = tmp_path / "problem_ok.lp"
    meta_path = tmp_path / "meta_ok.json"
    _make_problem().write_lp(str(problem_path))
    result = RunnerResult(
        **cache_key_fields(),
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


def _block_bindings(monkeypatch, module: str) -> None:
    # None in sys.modules -> import raises. An already-imported submodule
    # entry short-circuits the parent check, so evict it for the parent case.
    if module == "muoblpbindings":
        monkeypatch.delitem(
            sys.modules, "muoblpbindings.metrics", raising=False
        )
    monkeypatch.setitem(sys.modules, module, None)


@pytest.mark.parametrize(
    "module", ["muoblpbindings", "muoblpbindings.metrics"]
)
def test_missing_bindings_give_analyzer_failure(tmp_path, monkeypatch, module):
    meta_path = _persist_happy_meta(tmp_path)
    _block_bindings(monkeypatch, module)

    result = analyze_runner_result(meta_path, [Metric.EXCLUSION_RATIO_NATIVE])

    assert isinstance(result, AnalyzerFailure)
    assert result.error_type in ("ImportError", "ModuleNotFoundError")


def test_analyze_runner_result_populates_native_metric(tmp_path):
    meta_path = _persist_happy_meta(tmp_path)

    result = analyze_runner_result(
        meta_path, [Metric.EXCLUSION_RATIO, Metric.EXCLUSION_RATIO_NATIVE]
    )

    # selected p1 -> v2 excluded
    assert isinstance(result, AnalyzerResult)
    assert result.EXCLUSION_RATIO_NATIVE == {"exclusion_ratio": 0.5}
    assert result.EXCLUSION_RATIO_NATIVE == result.EXCLUSION_RATIO


def test_every_metric_has_analyzer_result_field():
    # field names == Metric values -> flat golden shape of metrics.json
    for metric in Metric:
        assert metric.value in AnalyzerResult.model_fields
