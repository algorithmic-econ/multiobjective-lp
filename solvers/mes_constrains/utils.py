from typing import List

from pulp import LpConstraint, LpConstraintGE, LpConstraintLE


def get_feasibility_ratio(constraint: LpConstraint) -> float:
    """

    :rtype: object
    """
    # ratio: [0, inf)
    value = constraint.value()
    target = constraint.constant
    return (value - target) / abs(target)


def get_modification_ratio(feasibility_ratio: float, smallest: float, largest: float) -> float:
    # ratio: [smallest, largest + delta]
    delta = largest - smallest
    return smallest + delta * feasibility_ratio


def get_infeasible_constraints(self) -> List[LpConstraint]:
    #
    # TODO: Generalise for lower and upper bound, should be LE or GE than 0 based on the LpSense
    #
    return [
        constraint for constraint in self.lp_problem.constraints.values()
        if (constraint.sense == LpConstraintGE and constraint.value() < 0) or
           (constraint.sense == LpConstraintLE and constraint.value() > 0)
    ]
