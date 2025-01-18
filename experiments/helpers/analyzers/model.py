from typing import List, TypedDict, Literal

Metric = Literal['NON_ZERO_OBJECTIVES', 'SUM_OBJECTIVES']


class AnalyzerConfig(TypedDict):
    analyzer_result_path: str
    experiment_results_base_path: str
    metrics: List[Metric]


class AnalyzerResult(TypedDict):
    problem_path: str
    metrics: List[Metric]

