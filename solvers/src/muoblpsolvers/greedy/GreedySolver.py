import logging
import time
from collections import defaultdict
from typing import TypedDict

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pulp import LpSolver

logger = logging.getLogger(__name__)


class Election(TypedDict):
    candidates: dict[str, int]
    voters: dict[str, list[str]]


class GreedySolver(LpSolver):
    def __init__(self):
        super().__init__()

    def actualSolve(self, lp: MultiObjectiveLpProblem, **kwargs):
        start_time = time.time()
        election: Election = kwargs["election"]
        candidates = election["candidates"]
        voters = election["voters"]

        logger.info(
            "Start solver",
            extra={"candidates": len(candidates), "voters": len(voters)},
        )

        vote_counts: dict[str, int] = {}

        for candidate in candidates.keys():
            vote_counts[candidate] = 0

        for approved in voters.values():
            for candidate in approved:
                vote_counts[candidate] += 1

        sorted_candidates = list(vote_counts.items())
        sorted_candidates.sort(
            key=lambda cand_count: candidates[cand_count[0]] / cand_count[1],
        )
        sorted_candidates = [
            cand_count for cand_count in sorted_candidates if cand_count[1] > 0
        ]

        for candidate, _ in sorted_candidates:
            candidate_variable = lp.variablesDict()[candidate]
            candidate_variable.setInitialValue(1)
            if not lp.valid():
                candidate_variable.setInitialValue(0)

        logger.info("Finish solver", extra={"time": time.time() - start_time})


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
