from typing import List, TypedDict, Literal

Metric = Literal['NON_ZERO_OBJECTIVES', 'SUM_OBJECTIVES']


class AnalyzerResult(TypedDict):
    problem_path: str
    metrics: List[Metric]
