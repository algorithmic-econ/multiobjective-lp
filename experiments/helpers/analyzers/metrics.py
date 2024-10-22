from enum import Enum
from typing import Dict, Callable, List

from ..analyzers.model import Metric, AnalyzerResult
from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem


def get_metrics(metrics: List[Metric], problem: MultiObjectiveLpProblem) -> Dict:
    result: AnalyzerResult = {"metrics": [metric.name for metric in metrics]}
    for metric in metrics:
        result |= {metric.name: get_metric_strategy(metric)(problem)}
    return result


def get_metric_strategy(metric: Metric) -> Callable[[MultiObjectiveLpProblem], Dict]:
    if metric == Metric.NON_ZERO_OBJECTIVES:
        return non_zero_objectives
    if metric == Metric.SUM_OBJECTIVES:
        return sum_objectives


def non_zero_objectives(problem: MultiObjectiveLpProblem) -> Dict:
    return {
        "non_zero_count": len([1 for obj in problem.objectives if obj.value() != 0]),
        "zero_count": len([1 for obj in problem.objectives if obj.value() == 0])
    }


def sum_objectives(problem: MultiObjectiveLpProblem) -> Dict:
    return {
        "sum": sum([obj.value() for obj in problem.objectives]),
    }
