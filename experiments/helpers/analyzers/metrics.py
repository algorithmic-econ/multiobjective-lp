from enum import Enum
from typing import Dict, Callable
from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem


Metric = Enum('Metric', ['NON_ZERO_OBJECTIVES', 'SUM_OBJECTIVES'])


def get_metric_strategy(metric: Metric) -> Callable[[MultiObjectiveLpProblem], Dict]:
    if metric == Metric.NON_ZERO_OBJECTIVES:
        return non_zero_objectives
    if metric == Metric.SUM_OBJECTIVES:
        return sum_objectives


def non_zero_objectives(problem: MultiObjectiveLpProblem) -> Dict:
    return {
        "non_zero_objectives": len([1 for obj in problem.objectives if obj.value() != 0]),
        "zero": len([1 for obj in problem.objectives if obj.value() == 0])
    }


def sum_objectives(problem: MultiObjectiveLpProblem) -> Dict:
    return {
        "sum_objectives": sum([obj.value() for obj in problem.objectives]),
    }
