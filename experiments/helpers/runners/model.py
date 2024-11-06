from typing import List, TypedDict, Literal

Solver = Literal['SUMMING', 'MES']
Source = Literal['PULP', 'PABUTOOLS']


class RunnerConfig(TypedDict):
    solver_type: Solver
    source_type: Source
    source_directory_path: str
    constraints_configs_path: str | None
    results_base_path: str


class ConstraintConfig(TypedDict):
    type: Literal['CATEGORY']
    category: str
    bound: Literal['UPPER', 'LOWER']
    budget_ratio: float


class RunnerResult(TypedDict):
    time: float
    solver: Solver
    source_type: Source
    source_path: str
    constraints_configs: List[ConstraintConfig]
    selected: List[str]
    problem_path: str
