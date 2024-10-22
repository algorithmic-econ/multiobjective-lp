from enum import Enum
from typing import List, Tuple, TypedDict


Sources = Enum('Sources', ['PULP', 'PABUTOOLS'])
Solvers = Enum('Solvers', ['SUMMING', 'MES'])


def validate_args(args: List[str]) -> Tuple[Solvers, Solvers, str, str | None]:
    if not Solvers[args[0]] in Solvers:
        raise Exception("Unsupported solver type")
    if not Sources[args[1]] in Sources:
        raise Exception("Unsupported source type")
    if not args[2]:
        raise Exception("Missing source directory path")
    constraints_configs_path = args[3] if len(args) > 3 else None
    return Solvers[args[0]], Sources[args[1]], args[2], constraints_configs_path


class Constraints(TypedDict):
    source_type: str
    categories: dict


class RunnerResult(TypedDict):
    time: float
    solver: str
    source_type: str
    constraints_configs: str | None
    source: str
    selected: List[str]
    problem: dict
