from typing import cast

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpVariable

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
from helpers.analyzers.model import Metric


def make_tiny_problem() -> MultiObjectiveLpProblem:
    """2 candidates: p1 ($100, selected), p2 ($200, not selected).
    2 voters: v1 approves p1, v2 approves both."""
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p1.setInitialValue(1)
    p2.setInitialValue(0)

    v1 = LpAffineExpression({p1: 100})
    v2 = LpAffineExpression({p1: 100, p2: 200})

    problem = MultiObjectiveLpProblem(
        "tiny", objectives=[v1, v2], objectives_weights={}
    )
    # PB constraint: covers all candidates, sense <=
    problem += 100 * p1 + 200 * p2 <= 250, "pb_constraint"
    return problem


def make_ejr_violation_problem() -> MultiObjectiveLpProblem:
    """4 voters, budget 250. p1 ($100, selected), p2 ($10, NOT selected).

    v1/v2 approve only p1 (satisfaction 100 each); v3/v4 approve only p2
    (satisfaction 0 each, since p2 is unselected). p2 is cheap and has a
    2-voter support group that got nothing -> EJR+ violation.
    """
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p1.setInitialValue(1)
    p2.setInitialValue(0)

    v1 = LpAffineExpression({p1: 100})
    v2 = LpAffineExpression({p1: 100})
    v3 = LpAffineExpression({p2: 10})
    v4 = LpAffineExpression({p2: 10})

    problem = MultiObjectiveLpProblem(
        "ejr_violation", objectives=[v1, v2, v3, v4], objectives_weights={}
    )
    problem += 100 * p1 + 10 * p2 <= 250, "pb_constraint"
    return problem


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
    with pytest.raises(Exception, match="Metric not implemented"):
        get_metric_strategy(cast(Metric, "NOT_A_METRIC"))


def test_get_metrics_keys_results_by_metric():
    problem = make_tiny_problem()
    assert get_metrics([Metric.TOTAL_COST, Metric.INSTANCE_SIZE], problem) == {
        Metric.TOTAL_COST: {"total_cost": 100},
        Metric.INSTANCE_SIZE: {"size": 2},
    }
