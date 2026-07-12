from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpVariable

from helpers.analyzers.metrics import sum_objectives, total_cost


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


def test_total_cost():
    problem = make_tiny_problem()
    assert total_cost(problem) == {"total_cost": 100}


def test_sum_objectives():
    problem = make_tiny_problem()
    assert sum_objectives(problem) == {"sum": 200}
