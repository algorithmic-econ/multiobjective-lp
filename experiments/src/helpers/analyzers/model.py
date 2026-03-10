from typing import List, Literal, TypedDict

from helpers.runners.model import Solver, Utility

Metric = Literal[
    "EXCLUSION_RATION",
    "SUM_OBJECTIVES",
    "EJR_PLUS",
    "CONSTRAINTS",
    "INSTANCE_SIZE",
    "TOTAL_COST",
    "METADATA",
]


class AnalyzerConfig(TypedDict):
    analyzer_result_path: str
    experiment_results_base_path: str
    metrics: List[Metric]


class AnalyzerResult(TypedDict):
    problem_path: str
    metrics: List[Metric]
    time: float
    solver: Solver
    solver_options: dict
    utility: Utility
