from typing import List

from pulp import LpConstraint, LpConstraintGE, LpConstraintLE

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem


def get_feasibility_ratio(constraint: LpConstraint) -> float:
    """
    :rtype: object
    """
    # ratio: [0, inf)
    value = constraint.value()
    target = constraint.constant
    return (value - target) / abs(target)


# def get_modification_ratio(feasibility_ratio: float, lower: float, upper: float) -> float:
#     return lower + (upper - lower) * feasibility_ratio


def get_infeasible_constraints(
    problem: MultiObjectiveLpProblem,
) -> List[LpConstraint]:
    return [
        constraint
        for constraint in problem.constraints.values()
        if (constraint.sense == LpConstraintGE and constraint.value() < 0)
        or (constraint.sense == LpConstraintLE and constraint.value() > 0)
    ]
