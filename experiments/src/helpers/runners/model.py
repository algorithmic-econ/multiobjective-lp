from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class Strategy(StrEnum):
    DISTRICT_BUDGET_MINUS_MAX = "district_budget_minus_max"
    CATEGORY_VOTE_SHARE = "category_vote_share"
    CATEGORY_COST_SHARE = "category_cost_share"


class Solver(StrEnum):
    SUMMING = "SUMMING"
    MES_ADD1 = "MES_ADD1"
    MES_CONSTRAINT = "MES_CONSTRAINT"
    MES_UTILS = "MES_UTILS"
    MES_EXPONENTIAL = "MES_EXPONENTIAL"
    GREEDY = "GREEDY"
    PHRAGMEN = "PHRAGMEN"
    STV = "STV"
    SOLID_COALITION_REFINEMENT = "SOLID_COALITION_REFINEMENT"
    EXPANDING_APPROVALS = "EXPANDING_APPROVALS"


class Source(StrEnum):
    PABUTOOLS = "PABUTOOLS"


class Utility(StrEnum):
    COST = "COST"
    APPROVAL = "APPROVAL"
    ORDINAL = "ORDINAL"
    CUMULATIVE = "CUMULATIVE"
    COST_ORDINAL = "COST_ORDINAL"
    COST_CUMULATIVE = "COST_CUMULATIVE"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConstraintConfig(StrictModel):
    key: Literal["CATEGORY", "DISTRICT"]
    value: str  # specific value or "*" for all
    bound: Literal["UPPER", "LOWER"]
    budget_ratio: float | None = None
    strategy: Strategy | None = None


class RunnerConfig(StrictModel):
    solver_type: Solver
    # keys MUST be valid solver-constructor kwargs (pulp optionsDict)
    solver_options: dict[str, Any] = {}
    source_type: Source
    utility_type: Utility | None = None
    source_directory_path: str
    constraints_configs_path: str | None = None
    constraints_configs: list[ConstraintConfig] | None = None
    deduplicate_objectives: bool = False
    results_base_path: str | None = None  # None -> experiment default


class ExperimentConfig(StrictModel):
    concurrency: int
    experiment_results_base_path: str
    runner_configs: list[RunnerConfig]


class SolverSpec(StrictModel):
    type: Solver
    options: dict[str, Any] = {}  # solver-constructor kwargs


class RunnerConfigsGenerator(StrictModel):
    solvers: list[SolverSpec]
    source_type: Source
    sources: list[str]
    constraints_configs_path: str | None = None
    deduplicate_objectives: bool = False


class CompactExperimentConfig(StrictModel):
    compact_config: Literal[True]
    concurrency: int
    experiment_results_base_path: str
    runner_configs_generator: RunnerConfigsGenerator


class SweepSpec(StrictModel):
    mode: Literal["citywide", "independent_districts"]
    root_path: str
    pattern_groups: list[list[str]] = []
    solvers: list[SolverSpec]
    utilities: list[Utility] | None = None
    concurrency: int = 4
    experiment_results_base_path: str
    constraints_configs_path: str | None = None
    deduplicate_objectives: bool = False
    output_path: str


class CacheKey(StrictModel):
    """Everything that defines a run result. Hashed with exclude_defaults:
    new fields MUST default to the previous behaviour to keep old hashes.
    Fields without default are always hashed (incl. schema_version, so
    bumping it invalidates all results)."""

    schema_version: int
    solver: Solver
    solver_options: dict[str, Any] = {}
    source_type: Source
    utility_type: Utility
    data_source: str
    constraints_configs: list[ConstraintConfig] = []
    deduplicate_objectives: bool = False


class RunnerResult(StrictModel):
    cache_key: CacheKey
    key_hash: str
    time: float
    solver: Solver
    solver_options: dict[str, Any]
    source_type: Source
    utility_type: Utility
    source_path: str
    constraints_configs: list[ConstraintConfig]
    deduplicate_objectives: bool
    problem_path: str
    instance_size: int
    selected: list[str]
