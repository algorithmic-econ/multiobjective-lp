from collections import defaultdict
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from typing import TypedDict


class Election(TypedDict):
    candidates: dict[str, float]
    voters: dict[str, list[str]]


def molp_to_simple_election(lp: MultiObjectiveLpProblem) -> Election:
    voters: dict[str, list[str]] = defaultdict(list)

    projects: list[str] = [
        candidate.name
        for candidate in lp.variables()
        if candidate.name != "__dummy"
    ]

    costs: dict[str, float] = {
        candidate.name: cost
        for constraint in lp.constraints.values()
        for candidate, cost in constraint.items()
    }

    if len(set(projects).difference(set(costs.keys()))) != 0:
        raise Exception(
            "Candidates mismatch between variables and constraints"
        )

    for voter in lp.objectives:
        for candidate, _ in voter.items():
            voters[voter.name].append(candidate.name)

    return {"candidates": costs, "voters": voters}
