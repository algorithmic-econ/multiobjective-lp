from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpAffineExpression, LpVariable


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
