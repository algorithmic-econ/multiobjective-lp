from typing import cast

import pytest

from helpers.analyzers.metrics import (
    ejr_plus,
    exclusion_ratio,
    get_metric_strategy,
    get_metrics,
    instance_size,
    invalid_constraints,
    sum_objectives,
    total_cost,
)
from helpers.analyzers import native_metrics
from helpers.analyzers.model import Metric

from .fixtures.problem_factories import (
    make_ejr_violation_problem,
    make_tiny_problem,
)


def test_total_cost():
    problem = make_tiny_problem()
    assert total_cost(problem) == {"total_cost": 100}


def test_sum_objectives():
    problem = make_tiny_problem()
    assert sum_objectives(problem) == {"sum": 200}


def test_exclusion_ratio_no_excluded_voters():
    # v1 = 100*1 = 100, v2 = 100*1 + 200*0 = 100 -> 0 of 2 objectives are 0.
    problem = make_tiny_problem()
    assert exclusion_ratio(problem) == {"exclusion_ratio": 0.0}


def test_exclusion_ratio_counts_zero_value_voters():
    # v1 = v2 = 100 (p1 selected); v3 = v4 = 10*0 = 0 (p2 unselected).
    # 2 of 4 objectives evaluate to 0 -> 0.5.
    problem = make_ejr_violation_problem()
    assert exclusion_ratio(problem) == {"exclusion_ratio": 0.5}


def test_instance_size():
    # Counts problem.variables(): p1 + p2. pulp's `__dummy` is injected by
    # fixObjective inside LpProblem.solve(), which this fixture never calls.
    problem = make_tiny_problem()
    assert instance_size(problem) == {"size": 2}


def test_invalid_constraints_all_satisfied():
    # 100*1 + 200*0 = 100 <= 250 -> PB constraint holds, nothing invalid.
    problem = make_tiny_problem()
    assert invalid_constraints(problem) == {
        "pb_constraint": True,
        "invalid_count": 0,
    }


def test_invalid_constraints_over_budget():
    # Select both: 100*1 + 200*1 = 300 > 250 -> the single (PB) constraint
    # is violated.
    problem = make_tiny_problem()
    variables = {variable.name: variable for variable in problem.variables()}
    variables["p2"].setInitialValue(1)

    assert invalid_constraints(problem) == {
        "pb_constraint": False,
        "invalid_count": 1,
    }


def test_ejr_plus_satisfied():
    # Only p2 is unselected. Its single supporter is v2 (satisfaction 100).
    # coalition_size 1, voter_count 2, budget 250, cost[p2] 200:
    #   100 >= (1/2)*250 - 200 = -75  -> satisfied, no failure recorded.
    problem = make_tiny_problem()
    assert ejr_plus(problem) == {"ejr_plus": 0}


def test_ejr_plus_violated():
    # Only p2 is unselected. Voters are walked in ascending satisfaction, so
    # the first supporter reached is v3 (satisfaction 0).
    # coalition_size 1, voter_count 4, budget 250, cost[p2] 10:
    #   0 >= (1/4)*250 - 10 = 52.5  -> FALSE, p2 recorded as a failure.
    problem = make_ejr_violation_problem()
    assert ejr_plus(problem) == {"ejr_plus": 1}


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        (Metric.EXCLUSION_RATION, exclusion_ratio),
        (Metric.SUM_OBJECTIVES, sum_objectives),
        (Metric.EJR_PLUS, ejr_plus),
        (Metric.CONSTRAINTS, invalid_constraints),
        (Metric.INSTANCE_SIZE, instance_size),
        (Metric.TOTAL_COST, total_cost),
    ],
)
def test_get_metric_strategy_dispatch(metric, expected):
    assert get_metric_strategy(metric) is expected


def test_get_metric_strategy_unknown_raises():
    with pytest.raises(NotImplementedError, match="Metric not implemented"):
        get_metric_strategy(cast(Metric, "NOT_A_METRIC"))


def test_get_metrics_keys_results_by_metric():
    problem = make_tiny_problem()
    assert get_metrics([Metric.TOTAL_COST, Metric.INSTANCE_SIZE], problem) == {
        Metric.TOTAL_COST: {"total_cost": 100},
        Metric.INSTANCE_SIZE: {"size": 2},
    }


@pytest.mark.parametrize(
    "factory", [make_tiny_problem, make_ejr_violation_problem]
)
def test_get_metrics_native_matches_python(factory):
    result = get_metrics(
        [Metric.EXCLUSION_RATION, Metric.EXCLUSION_RATIO_NATIVE], factory()
    )
    assert list(result) == [
        Metric.EXCLUSION_RATION,
        Metric.EXCLUSION_RATIO_NATIVE,
    ]
    assert (
        result[Metric.EXCLUSION_RATIO_NATIVE]
        == result[Metric.EXCLUSION_RATION]
    )


def test_get_metric_strategy_native_not_python_strategy():
    with pytest.raises(NotImplementedError, match="Metric not implemented"):
        get_metric_strategy(Metric.EXCLUSION_RATIO_NATIVE)


def test_handle_not_built_for_python_only_metrics(monkeypatch):
    def boom(problem):
        raise AssertionError("handle must not be built")

    monkeypatch.setattr(native_metrics, "build_solved_instance", boom)
    assert get_metrics([Metric.INSTANCE_SIZE], make_tiny_problem()) == {
        Metric.INSTANCE_SIZE: {"size": 2}
    }


def test_handle_built_once_for_native_metrics(monkeypatch):
    calls = []
    real = native_metrics.build_solved_instance

    def counting(problem):
        calls.append(problem)
        return real(problem)

    monkeypatch.setattr(native_metrics, "build_solved_instance", counting)
    get_metrics(
        [Metric.EXCLUSION_RATIO_NATIVE, Metric.EXCLUSION_RATIO_NATIVE],
        make_tiny_problem(),
    )
    assert len(calls) == 1
