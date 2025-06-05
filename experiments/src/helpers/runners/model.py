from typing import List, TypedDict, Literal, Dict

Solver = Literal["SUMMING", "MES", "MES_ADD1", "MES_CONSTRAINT", "MES_UTILS"]
Source = Literal["PULP", "PABUTOOLS"]
Utility = Literal["COST", "APPROVAL", "ORDINAL", "CUMULATIVE"]


class RunnerConfig(TypedDict):
    solver_type: Solver
    solver_options: Dict | None
    source_type: Source
    utility_type: Utility
    source_directory_path: str
    constraints_configs_path: str | None
    results_base_path: str


class ConstraintConfig(TypedDict):
    key: Literal["CATEGORY", "DISTRICT"]
    value: str
    bound: Literal["UPPER", "LOWER"]
    budget_ratio: float


class RunnerResult(TypedDict):
    time: float
    solver: Solver
    solver_options: Dict | None
    source_type: Source
    utility_type: Utility
    source_path: str
    constraints_configs: List[ConstraintConfig]
    selected: List[str]
    problem_path: str
