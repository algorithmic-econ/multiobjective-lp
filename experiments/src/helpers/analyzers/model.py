from typing import Any, Literal

from muoblpanalyzers import Metric

from helpers.runners.model import (
    ConstraintConfig,
    Solver,
    StrictModel,
    Utility,
)


class AnalyzerConfig(StrictModel):
    analyzer_result_path: str
    experiment_results_base_path: str
    metrics: list[Metric]
    concurrency: int = 3


class AnalyzerResult(StrictModel):
    # Per-metric fields named exactly like Metric values -> dumped rows keep
    # the flat golden shape (metrics.json). dict[str, Any], NOT float:
    # float-typing would coerce golden ints ("sum": 48069190) to 48069190.0.
    problem_path: str
    metrics: list[Metric]
    time: float
    city: str
    solver: Solver
    solver_options: dict[str, Any]
    constraints_configs: list[ConstraintConfig]
    utility: Utility
    EXCLUSION_RATIO: dict[str, Any] | None = None
    SUM_OBJECTIVES: dict[str, Any] | None = None
    EJR_PLUS: dict[str, Any] | None = None
    CONSTRAINTS: dict[str, Any] | None = None
    INSTANCE_SIZE: dict[str, Any] | None = None
    TOTAL_COST: dict[str, Any] | None = None
    EXCLUSION_RATIO_NATIVE: dict[str, Any] | None = None
    EJR_PLUS_NATIVE: dict[str, Any] | None = None


class AnalyzerFailure(StrictModel):
    meta_path: str
    error_type: str
    error_message: str


class AggregatorConfig(StrictModel):
    metrics_json_path: str
    output_path: str
    group_by: Literal["instance_size_bucket", "city"]
    bucket_size: int = 10
    exclude_cities: list[str] = []
    # matches the composed "SOLVER_{options}" label exactly, None = all
    include_solvers: list[str] | None = None
    # bucket mode only: SUM_OBJECTIVES/TOTAL_COST relative to this solver
    normalize_baseline: Solver | None = None
    clip_upper: float = 5.0
