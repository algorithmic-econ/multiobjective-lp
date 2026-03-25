from typing import Dict, List, Literal, NotRequired, TypedDict

Strategy = Literal[
    "district_budget_minus_max",
    "category_vote_share",
    "category_cost_share",
]

Solver = Literal[
    "SUMMING",
    "MES_ADD1",
    "MES_CONSTRAINT",
    "MES_UTILS",
    "MES_EXPONENTIAL",
    "GREEDY",
    "PHRAGMEN",
]
Source = Literal["PABUTOOLS"]
Utility = Literal[
    "COST",
    "APPROVAL",
    "ORDINAL",
    "CUMULATIVE",
    "COST_ORDINAL",
    "COST_CUMULATIVE",
]


class RunnerConfig(TypedDict):
    solver_type: Solver
    solver_options: Dict | None
    source_type: Source
    utility_type: NotRequired[Utility]
    source_directory_path: str
    constraints_configs_path: NotRequired[str]
    constraints_configs: NotRequired[List["ConstraintConfig"]]
    results_base_path: str


class ExperimentConfig(TypedDict):
    concurrency: int
    experiment_results_base_path: str
    runner_configs: List[RunnerConfig]


class ConstraintConfig(TypedDict):
    key: Literal["CATEGORY", "DISTRICT"]
    value: str  # specific value or "*" for all
    bound: Literal["UPPER", "LOWER"]
    budget_ratio: NotRequired[float]
    strategy: NotRequired[Strategy]


class RunnerResult(TypedDict):
    time: float
    solver: Solver
    solver_options: Dict | None
    source_type: Source
    utility_type: Utility
    source_path: str
    constraints_configs: List[ConstraintConfig]
    problem_path: str
    instance_size: int
    selected: List[str]
