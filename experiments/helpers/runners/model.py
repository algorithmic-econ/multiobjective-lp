from enum import Enum
from typing import List, Tuple, TypedDict


Sources = Enum('Sources', ['PULP', 'PABUTOOLS'])
Solvers = Enum('Solvers', ['SUMMING', 'MES'])


def validate_args(args: List[str]) -> Tuple[Solvers, Solvers, str]:
    if not Solvers[args[0]] in Solvers:
        raise Exception("Unsupported solver type")
    if not Sources[args[1]] in Sources:
        raise Exception("Unsupported source type")
    if not args[2]:
        raise Exception("Missing source directory path")
    return Solvers[args[0]], Sources[args[1]], args[2]


class RunnerResult(TypedDict):
    time: float
    solver: str
    source_type: str
    source: str
    selected: List[str]
    problem: dict
