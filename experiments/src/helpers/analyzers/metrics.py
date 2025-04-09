from typing import Dict, Callable, List

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from helpers.analyzers.model import Metric, AnalyzerResult


def get_metrics(
    metrics: List[Metric], problem: MultiObjectiveLpProblem
) -> Dict:
    result: AnalyzerResult = {"metrics": metrics}
    for metric in metrics:
        result |= {metric: get_metric_strategy(metric)(problem)}
    return result


def get_metric_strategy(
    metric: Metric,
) -> Callable[[MultiObjectiveLpProblem], Dict]:
    if metric == "NON_ZERO_OBJECTIVES":
        return non_zero_objectives
    if metric == "SUM_OBJECTIVES":
        return sum_objectives


def non_zero_objectives(problem: MultiObjectiveLpProblem) -> Dict:
    return {
        "non_zero_count": len(
            [1 for obj in problem.objectives if obj.value() != 0]
        ),
        "zero_count": len(
            [1 for obj in problem.objectives if obj.value() == 0]
        ),
    }


def sum_objectives(problem: MultiObjectiveLpProblem) -> Dict:
    return {
        "sum": sum([obj.value() for obj in problem.objectives]),
    }
